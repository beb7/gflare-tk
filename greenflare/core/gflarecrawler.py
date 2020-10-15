from threading import Thread, Event, enumerate as tenum
from .gflaredb import GFlareDB
from .gflareresponse import GFlareResponse as gf
from requests import Session, exceptions
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from time import sleep
import queue

class GFlareCrawler:
	def __init__(self, settings=None, gui_mode=False, lock=None, stats=True):
		self.data_queue = queue.Queue()
		self.url_queue = queue.Queue()
		self.gui_url_queue = None
		self.gui_mode = gui_mode
		self.lock = lock
		self.stats = stats

		self.list_mode_urls = None

		self.gui_url_queue = None
		if self.gui_mode: self.gui_url_queue = queue.Queue()

		self.url_attempts = {}
		self.retries = 5

		self.settings = settings
		self.gf = gf(self.settings, columns=None)
		self.crawl_running = Event()
		self.robots_txt_found = Event()
		self.robots_thread = None
		self.worker_status = []
		self.db_file = None

		self.rate_limit_delay = 0
		self.current_urls_per_second = 0
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
		if not self.settings.get('USER_AGENT', ''): self.settings['USER_AGENT'] = "Greenflare SEO Spider/1.0"
		self.HEADERS = {'User-Agent': self.settings['USER_AGENT'], 'Accept-Language': 'en-gb', 'Accept-Encoding': 'gzip', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}

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
			self.parallel_requests_limit = (1 / int(self.settings["URLS_PER_SECOND"])) * int(self.settings["THREADS"])

		db = self.connect_to_db()
		db.create()

		# Reset response object
		self.gf = gf(self.settings, columns=None)
		
		self.columns = self.gf.all_items = db.get_columns()

		if self.settings["MODE"] == "Spider":
			if not self.settings["STARTING_URL"].endswith("/"): self.settings["STARTING_URL"] += "/"
			self.request_robots_txt()
			db.insert_new_urls([self.settings["STARTING_URL"]])
			self.url_queue.put(self.settings["STARTING_URL"])
			self.urls_total += 1

		elif self.settings["MODE"] == "List":
			self.robots_txt_found.set()

			if len(self.list_mode_urls) > 0:
				self.add_to_url_queue(self.list_mode_urls)
				db.insert_new_urls(self.list_mode_urls)
			else:
				print("ERROR: No urls to list crawl found!")

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
		# db.load_columns()
		# db.populate_columns()
		self.columns = db.columns.copy()
		# print("Loaded settings:\n", self.settings)
		db.close()


	def reset_crawl(self):
		# Reset queue
		if self.settings['MODE'] != 'List':
			self.data_queue = queue.Queue()
			self.url_queue = queue.Queue()
			self.timestamps_queue = queue.Queue()
		self.crawl_running.clear()
		self.robots_txt_found.clear()
		
		self.urls_crawled = 0
		self.urls_total = 0

		self.settings["ROOT_DOMAIN"] = ""

	def resume_crawl(self):
		print("Resuming crawl ...")
		self.init_crawl_headers()
		# Reinit session
		self.init_session()

		db = self.connect_to_db()
		db.extractions = self.settings.get("EXTRACTIONS", "")
		# # db.populate_columns()
		# db.load_columns()
		# db.add_remove_columns()

		self.reset_crawl()

		self.urls_crawled = db.get_urls_crawled()
		self.urls_total = db.get_total_urls()

		# Reset response object
		self.gf = gf(self.settings, columns=db.get_columns())

		if self.settings['MODE'] != 'List':
			self.request_robots_txt()
		else:
			self.robots_txt_found.set()
		
		# Reinit URL queue
		self.add_to_url_queue(db.get_url_queue(), count=False)

		db.commit()
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
		if self.stats: Thread(target=self.urls_per_second_stats, name="stats").start()

	def wait_for_threads(self):
		ts = tenum()
		for t in ts:
			if "worker-" in t.name:
				t.join()
		if self.gui_mode: self.gui_url_queue.put("END")
		print("All workers joined ...")

	def urls_per_second_stats(self):
		url_limit = int(self.settings.get("URLS_PER_SECOND", 0))
		step = 0.1
		
		# Set initial limit depending on the number of threads
		if url_limit > 0 :
			self.rate_limit_delay = 1 / url_limit * int(self.settings.get("THREADS", 1)) * step
		while self.crawl_running.is_set() == False:
			with self.lock:
				old = self.urls_crawled
			
			# Wait for 1 second to pass
			sleep(1)
		
			with self.lock:
				self.current_urls_per_second = self.urls_crawled - old

				if  url_limit > 0 and self.current_urls_per_second > url_limit:
					self.rate_limit_delay += step
				elif url_limit > 0 and self.current_urls_per_second <= url_limit:
					if self.rate_limit_delay - step > 0:
						self.rate_limit_delay -= step
					else:
						self.rate_limit_delay = 0
		with self.lock:
			self.current_urls_per_second = 0

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
		# adapter = HTTPAdapter(max_retries=retry)
		adapter = HTTPAdapter()
		self.session.mount("http://", adapter)
		self.session.mount("https://", adapter)
	
	def crawl_url(self, url):

		header = None
		body = None

		# timeout (connection, response)
		timeout = (3, 5)
		issue = ""

		try:
			if self.header_only: 
				header = self.session.head(url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
				return header
			
			header = self.session.head(url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
			
			content_type = header.headers.get("content-type", "")
			if "text" in content_type:
				body = self.session.get(url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
				return body
			
			return header
		except exceptions.TooManyRedirects:
			return self.deal_with_exception(url, "Too Many Redirects")
		
		except exceptions.ConnectionError:
			return self.deal_with_exception(url, "Connection Refused")

		except exceptions.ReadTimeout:
			return self.deal_with_exception(url, "Read timed out")

		except exceptions.InvalidURL:
			return self.deal_with_exception(url, "Invalid URL")

		except Exception as e:
			return self.deal_with_exception(url, "Unknown Exception")

	
	def deal_with_exception(self, url, issue):
		with self.lock:
			attempts = self.url_attempts.get(url, 0)

		if attempts >= self.retries:
			print(f"{url} {issue} after {attempts} attempts.")
			return [tuple([url, '', '0', issue] + [''] * (len(self.columns) - 4))]

		with self.lock:
			self.url_attempts[url] = self.url_attempts.get(url, 0) + 1
		
		self.add_to_url_queue([url], count=False)
		return "SKIP_ME"


	def add_to_gui_queue(self, data):
		self.gui_url_queue.put(data)

	def crawl_worker(self, name):
		busy = Event()
		with self.lock:
			self.worker_status.append(busy)
		
		while self.crawl_running.is_set() == False:
			url = self.url_queue.get()
			if url == "END": break
			busy.set()
			
			# print(f"{name}: sleeping for {self.rate_limit_delay} seconds ...")
			sleep(self.rate_limit_delay)
			
			response = self.crawl_url(url)
			
			if response == "SKIP_ME": 
				busy.clear()
				continue

			self.data_queue.put(response)
			busy.clear()

	def consumer_worker(self):
		db = self.connect_to_db()
		with self.lock:
			inserted_urls = 0
			threads = int(self.settings["THREADS"])
			# new = bool(self.settings.get("MODE", "") == "List")

		while True:
			try:
				with self.lock:
					if self.url_queue.empty() and self.data_queue.empty() and self.robots_txt_found.is_set() and all([not i.is_set() for i in self.worker_status]):
						[self.url_queue.put("END") for _ in range(int(self.settings["THREADS"]))]
						if self.gui_mode: self.add_to_gui_queue("CRAWL_COMPLETED")
						break

				# FIXME: Remove timeout as no worker should wait for a requested URL forever. If it takes them longer than 30 secs the crawl will wrongly time out
				response = self.data_queue.get(timeout=30)

				if "end" in response:
					self.crawl_running.set()
					break

				if isinstance(response, list):
					db.insert_crawl_data(response)
					if self.gui_mode: self.add_to_gui_queue(response)
					with self.lock:
						inserted_urls += 1
						self.urls_crawled += 1
					continue

				self.gf.set_response(response)
				data = self.gf.get_data()
				# print("\n", ">>", data["data"], "\n")

				if self.robots_txt_found.is_set() == False and "url" in data:
					url = data["url"]
					if url == self.gf.get_robots_txt_url(url): self.robots_txt_found.set()
					continue

				if "data" in data:
					urls = [u[0] for u in data["data"]]
					new_urls = db.get_new_urls(urls, check_crawled=True)
					new_data = [d for d in data["data"] if d[0] in new_urls]
					newly_discovered_urls = len(db.get_new_urls(urls, check_crawled=False))
					db.insert_crawl_data(new_data)
					with self.lock:
						inserted_urls += len(new_data)
						self.urls_crawled += len(new_data)
						if newly_discovered_urls > 0:
							self.urls_total += newly_discovered_urls
					if self.gui_mode: self.add_to_gui_queue(new_data)

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
				for t in tenum():
					if "worker-" in t.name:
						self.url_queue.put("END")
				if self.gui_mode: self.add_to_gui_queue("CRAWL_TIMED_OUT")
				break

		# Always commit to db at the very end
		db.commit()
		db.close()

		self.crawl_running.set()
		self.session.close()
		print("Consumer thread finished")

	def add_to_url_queue(self, urls, count=True):
		if count:
			with self.lock:
				self.urls_total += len(urls)
		for url in urls:
			self.url_queue.put(url)

	def get_crawl_data(self):
		if self.db_file:
			db = self.connect_to_db()
			data = db.get_crawl_data()
			db.close()
			return data
		return []

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