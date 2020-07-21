from threading import Thread, Event
from .gflaredb import GFlareDB
from .gflareresponse import GFlareResponse as gf
from requests import Session, exceptions
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from time import sleep, perf_counter
import functools
import queue
import threading
import sys, os 

class GFlareCrawler:
	def __init__(self, settings=None, gui_mode=False, lock=None):
		self.data_queue = queue.Queue()
		self.url_queue = queue.Queue()
		self.gui_url_queue = None
		self.gui_mode = gui_mode
		self.lock = lock

		self.gui_url_queue = None
		if self.gui_mode: self.gui_url_queue = queue.Queue()

		self.settings = settings
		self.gf = gf(self.settings, columns=None)
		self.crawl_running = Event()
		self.robots_txt_found = Event()
		self.robots_thread = None
		self.worker_status = []
		self.db_file = None

		self.url_per_second_limit = 0
		self.urls_crawled = 0
		self.urls_total = 0
		self.HEADERS = ""
		self.robots_txt = ""
		self.columns = None

		self.consumer_thread = None

		self.session = None
		self.header_only = False

	def connect_to_db(self):
		return GFlareDB(self.db_file, crawl_items=self.settings.get("CRAWL_ITEMS"), extractions=self.settings.get("EXTRACTIONS", None))
	
	def init_crawl_headers(self):
		ua = "Greenflare SEO Spider/1.0"
		self.HEADERS = {'User-Agent': self.settings.get("USER_AGENT", ua), 'Accept-Language': 'en-gb', 'Accept-Encoding': 'gzip', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}

	def request_robots_txt(self):
		start_url = self.settings["STARTING_URL"]
		self.url_queue.put(self.gf.get_robots_txt_url(start_url))
		self.url_queue.put("END")
		self.robots_thread  = Thread(target=self.crawl_worker, name="worker-robots-0", args=("worker-robots-0",))
		self.robots_thread.start()

	def start_crawl(self):
		print("Crawl started")
		self.init_crawl_headers()
		self.init_session()
		
		# Set speed limit
		if int(self.settings.get("URLS_PER_SECOND", 0)) > 0:
			self.url_per_second_limit = (1 / int(self.settings["URLS_PER_SECOND"])) * int(self.settings["THREADS"])

		db = self.connect_to_db()
		db.create()
		self.columns = db.columns
		self.gf.all_items = self.columns

		if self.settings["MODE"] == "Spider":
			if not self.settings["STARTING_URL"].endswith("/"): self.settings["STARTING_URL"] += "/"
			self.request_robots_txt()
			db.insert_new_urls([self.settings["STARTING_URL"]])
			self.url_queue.put(self.settings["STARTING_URL"])
			self.urls_total += 1

		elif self.settings["MODE"] == "List":
			self.robots_txt_found.set()
			
		db.commit()
		db.close()

		self.start_consumer()
		Thread(target=self.spawn_threads).start()

	
	def load_crawl(self, db_file):
		self.db_file = db_file
		db = self.connect_to_db()

		self.urls_crawled = db.get_urls_crawled()
		self.urls_total = db.get_total_urls()
		self.settings = db.get_settings()
		db.extractions = self.settings.get("EXTRACTIONS", "")
		db.populate_columns()
		self.columns = db.columns
		print("Loaded settings:\n", self.settings)
		db.close()


	def resume_crawl(self):
		print("Resuming crawl ...")
		self.init_crawl_headers()
		# Reinit session
		self.init_session()

		db = self.connect_to_db()
		db.add_remove_columns()

		# Reset queue
		self.data_queue = queue.Queue()
		self.url_queue = queue.Queue()
		self.crawl_running.clear()

		self.request_robots_txt()
		
		# Reinit URL queue
		self.add_to_url_queue(db.get_url_queue())

		# Reset response object
		self.gf = gf(self.settings, db.columns)

		db.close()

		self.start_consumer()
		Thread(target=self.spawn_threads).start()
		
	def start_consumer(self):
		self.consumer_thread = Thread(target=self.consumer_worker, name="consumer")
		self.consumer_thread.start()

	def spawn_threads(self):
		if self.settings["MODE"] == "Spider": self.robots_thread.join()
		if self.crawl_running.is_set() == False:
			threads = int(self.settings["THREADS"])
			for i in range(threads):
				tname = f"worker-{i}"
				t = Thread(target=self.crawl_worker, name=tname, args=(tname,))
				t.start()

	def wait_for_threads(self):
		ts = threading.enumerate()
		for t in ts:
			if "worker-" in t.name:
				t.join()
		if self.gui_mode: self.gui_url_queue.put("END")
		print("All workers joined ...")


	def init_session(self):
		"""
		All worker threads share the same session object.
		This is only thread-safe as long as no session object attributes are being altered (headers, proxies etc.)
		"""

		self.session = Session()
		status_forcelist = (500, 502, 504)
		retries = self.settings.get("MAX_RETRIES", 0)
		self.header_only = False
		
		if self.settings.get("PROXY_HOST", "") != "":
			if self.settings.get("PROXY_USER", "") == "":
				self.session.proxies = {"https": f"{self.settings['PROXY_HOST']}"}
			else:
				self.session.proxies = { 'https' : f"https://{self.settings['PROXY_USER']}:{self.settings['PROXY_PASSWORD']}@{self.settings['PROXY_HOST']}"}

		retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=0.3, status_forcelist=status_forcelist)
		adapter = HTTPAdapter(max_retries=retry)
		self.session.mount("http://", adapter)
		self.session.mount("https://", adapter)
	
	def crawl_url(self, url):

		header = None
		body = None

		try:
			if self.header_only: return self.session.head(url, headers=self.HEADERS, timeout=3) 
			header = self.session.head(url, headers=self.HEADERS, timeout=5)
			if "text" in header.headers.get("content-type", ""):
				body = self.session.get(url, headers=self.HEADERS, timeout=5)
				return body
			return header
		except exceptions.TooManyRedirects:
			print(f"{url} has too many redirects")
			return header
		except Exception as e:
			return [tuple([url, '', 'Timed Out', ''] + [''] * len(self.settings.get("CRAWL_ITEMS", None) - 4 ))]
	
	def add_to_gui_queue(self, data):
		self.gui_url_queue.put(data)

	def crawl_worker(self, name):
		busy = Event()
		with self.lock:
			url_per_second_limit = self.url_per_second_limit
			self.worker_status.append(busy)
		
		while self.crawl_running.is_set() == False:
			url = self.url_queue.get()
			if url == "END": break

			busy.set()
			response = self.crawl_url(url)
			
			if response == None:
				print("Skipping none type response")
				busy.clear()
				continue

			self.data_queue.put(response)
			busy.clear()

	def consumer_worker(self):
		db = self.connect_to_db()
		with self.lock:
			inserted_urls = 0
			threads = int(self.settings["THREADS"])
			new = bool(self.settings.get("MODE", "") == "List")

		while True:
			try:
				with self.lock:
					if self.url_queue.empty() and self.data_queue.empty() and self.robots_txt_found.is_set() and all([not i.is_set() for i in self.worker_status]):
						[self.url_queue.put("END") for _ in range(int(self.settings["THREADS"]))]
						if self.gui_mode: self.add_to_gui_queue("CRAWL_COMPLETED")
						break

				response = self.data_queue.get(timeout=30)

				if "end" in response:
					self.crawl_running.set()
					break

				if isinstance(response, list):
					db.insert_crawl_data(response)
					with self.lock:
						inserted_urls += 1
					continue

				self.gf.set_response(response)
				data = self.gf.get_data()

				if "data" in data:
					print("url:", data["url"])
					print("data:", data["data"])
					url = data["url"]
					if self.robots_txt_found.is_set() == False:
						if url == self.gf.get_robots_txt_url(url): self.robots_txt_found.set()
					else:
						db.insert_crawl_data(data["data"], new=new)
						with self.lock:
							inserted_urls += 1
							self.urls_crawled += 1
						if self.gui_mode: self.add_to_gui_queue(data["data"])

				if "redirects" in data:
					redirect_urls = [data[0] for data in data["redirects"]]
					new_redirects = db.get_new_urls(redirect_urls)
					number_new_redirects = len(new_redirects)
					db.insert_redirects(data["redirects"])
					if number_new_redirects > 0:
						with self.lock:
							self.urls_crawled += number_new_redirects
							self.urls_total += number_new_redirects
						if self.gui_mode: self.add_to_gui_queue([redirect for redirect in data["redirects"] if redirect[0] in new_redirects])
				
				extracted_links = data.get("links", []) + data.get("hreflang_links", []) + data.get("canonical_links", []) + data.get("pagination_links", [])

				if len(extracted_links) > 0:
					new_urls = db.get_new_urls(extracted_links)
					if len(new_urls) > 0 :
						db.insert_new_urls(new_urls)
						self.add_to_url_queue(new_urls)
						inserted_urls += len(new_urls)
					if "unique_inlinks" in self.settings.get("CRAWL_ITEMS", ""): db.insert_inlinks(extracted_links, data["url"])

				if inserted_urls >= (100 * threads):
					db.commit()
					inserted_urls = 0

			except queue.Empty:
				print("Consumer thread timed out")
				self.crawl_running.set()
				self.robots_txt_found.set()
				for t in threading.enumerate():
					if "worker-" in t.name:
						self.url_queue.put("END")
				if self.gui_mode: self.add_to_gui_queue("CRAWL_TIMED_OUT")
				break
			# except Exception as e:
			# 	print("Consumer thread crashed ...")
			# 	exc_type, exc_obj, exc_tb = sys.exc_info()
			# 	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			# 	print(exc_type, fname, exc_tb.tb_lineno)
			# 	print(e)
			# 	self.crawl_running.set()			

		# Always commit to db at the very end
		db.commit()
		db.close()

		self.crawl_running.set()
		print("Consumer thread finished")

	def add_to_url_queue(self, urls):
		with self.lock:
			self.urls_total += len(urls)
		[self.url_queue.put(url) for url in urls]

	def save_config(self, settings):
		if self.db_file:
			db = self.connect_to_db()
			db.insert_config(settings)
			db.commit()
			db.close()

	def end_crawl_gracefully(self):
		print("Ending all worker threads gracefully ...")
		self.data_queue.put({"end": ""})
		self.wait_for_threads()
		self.save_config(self.settings)