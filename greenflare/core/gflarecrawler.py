from threading import Thread, Event, enumerate as tenum
from .gflaredb import GFlareDB
from .gflareresponse import GFlareResponse as gf
from requests import Session, exceptions
from time import sleep, time
import queue

class GFlareCrawler:
	def __init__(self, settings=None, gui_mode=False, lock=None, stats=True):
		self.url_queue = queue.Queue()
		self.data_queue = []
		self.gui_url_queue = []
		self.gui_mode = gui_mode
		self.lock = lock
		self.stats = stats

		self.list_mode_urls = None
		self.url_attempts = {}
		self.retries = 5

		self.settings = settings
		self.gf = gf(self.settings, columns=None)
		self.crawl_running = Event()
		self.crawl_completed = Event()
		self.crawl_timed_out = Event()
		self.data_available = Event()
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

	def request_robots_txt(self, url):
		robots_txt_url = self.gf.get_robots_txt_url(url)
		return self.crawl_url(robots_txt_url)

	def start_crawl(self):
		print("Crawl started")
		self.init_crawl_headers()
		self.init_session()

		# Set speed limit
		if int(self.settings.get("URLS_PER_SECOND", 0)) > 0:
			self.parallel_requests_limit = (1 / int(self.settings["URLS_PER_SECOND"])) * int(self.settings["THREADS"])

		db = self.connect_to_db()
		db.create()

		# # Reset response object
		self.gf = gf(self.settings, columns=None)

		self.columns = self.gf.all_items = db.get_columns()

		if self.settings["MODE"] == "Spider":
			self.settings['STARTING_URL'] = self.gf.url_components_to_str(self.gf.parse_url(self.settings['STARTING_URL']))
			self.settings["ROOT_DOMAIN"] = self.gf.get_domain(self.settings['STARTING_URL'])
			data = self.crawl_url(self.settings['STARTING_URL'])
			print('STARTING_URL', self.settings['STARTING_URL'])
			# Check if we are dealing with a reachable host

			if data == 'SKIP_ME':
				self.crawl_timed_out.set()
				self.crawl_running.set()
				db.close()
				return

			self.add_to_data_queue(data)
			self.request_robots_txt(data['url'])

		elif self.settings["MODE"] == "List":
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
		self.columns = db.columns.copy()
		db.close()

	def reset_crawl(self):
		# Reset queue
		if self.settings['MODE'] != 'List':
			self.data_queue = []
			self.url_queue = queue.Queue()

		self.gf = gf(self.settings, columns=None)

		self.crawl_running.clear()
		self.crawl_completed.clear()
		self.crawl_timed_out.clear()

		self.urls_crawled = 0
		self.urls_total = 0

		self.settings['STARTING_URL'] = ''
		self.settings["ROOT_DOMAIN"] = ""

	def resume_crawl(self):
		print("Resuming crawl ...")
		self.init_crawl_headers()
		# Reinit session
		self.init_session()

		db = self.connect_to_db()
		db.extractions = self.settings.get("EXTRACTIONS", "")

		self.reset_crawl()

		self.urls_crawled = db.get_urls_crawled()
		self.urls_total = db.get_total_urls()

		# Reset response object
		self.gf = gf(self.settings, columns=db.get_columns())

		if self.settings['MODE'] != 'List':
			check = self.request_robots_txt(self.settings.get('STARTING_URL'))
			if check == 'SKIP_ME':
				self.crawl_timed_out.set()
				self.crawl_running.set()
				db.close()
				return

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

	def response_to_data(self, response):
		with self.lock:
			self.gf.set_response(response)
			return self.gf.get_data()

	def crawl_url(self, url, header_only=False):
		header = None
		body = None

		# timeout (connection, response)
		timeout = (3, 5)
		issue = ""

		try:
			if header_only:
				header = self.session.head(url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
				return self.response_to_data(header)

			header = self.session.head(url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)

			content_type = header.headers.get("content-type", "")
			if "text" in content_type:
				body = self.session.get(url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
				return self.response_to_data(body)

			return self.response_to_data(header)
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
			return {'url': url, 'data': [tuple([url, '', '0', issue] + [''] * (len(self.columns) - 4))], 'links': []}

		with self.lock:
			self.url_attempts[url] = self.url_attempts.get(url, 0) + 1

		self.add_to_url_queue([url], count=False)
		return "SKIP_ME"

	def add_to_url_queue(self, urls, count=True):
		if count:
			with self.lock:
				self.urls_total += len(urls)
		for url in urls:
			self.url_queue.put(url)

	def add_to_gui_queue(self, data):
		with self.lock:
			self.gui_url_queue += data

	def add_to_data_queue(self, data):
		with self.lock:
			# print(">>", data)
			self.data_queue.append(data)
			self.data_available.set()

	def get_data_queue(self):
		with self.lock:
			data, self.data_queue = self.data_queue, []
			self.data_available.clear()
			return data

	def crawl_worker(self, name):
		busy = Event()
		with self.lock:
			self.worker_status.append(busy)

		while self.crawl_running.is_set() == False:
			url = self.url_queue.get()
			if url == "END": break
			busy.set()

			sleep(self.rate_limit_delay)

			data = self.crawl_url(url)

			if data == "SKIP_ME":
				busy.clear()
				continue

			self.add_to_data_queue(data)
			busy.clear()

	def consumer_worker(self):
		db = self.connect_to_db()
		do_commit = False
		with self.lock:
			urls_last = self.urls_crawled

		while not self.crawl_running.is_set():
			ts = time()
			with self.lock:
				if self.url_queue.empty() and len(self.data_queue) == 0 and all([not i.is_set() for i in self.worker_status]):
					self.crawl_running.set()
					self.crawl_completed.set()
					break

			try:
				self.data_available.wait(timeout=30)
			except:
				print("Consumer thread timed out")
				self.crawl_running.set()
				self.crawl_timed_out.set()
				for t in tenum():
					if "worker-" in t.name:
						self.url_queue.put("END")
				break

			# data structure:
			# [{'url': 'https://example.com/page.html', 'data': [(...), (...)]}]
			data = self.get_data_queue()

			x_data = [d['data'] for d in data]
			all_data = [item for list_of_tuples in x_data for item in list_of_tuples]
			new, updated = db.insert_new_data(all_data)
			# print(">>", [(d[0],d[2]) for d in all_data])

			with self.lock:
				self.urls_crawled += len(updated) + len(new)
				self.urls_total += len(new)
			if self.gui_mode:
				if new or updated:
					self.add_to_gui_queue(new + updated)

			x_links = [d.get("links", []) + d.get("hreflang_links", []) + d.get("canonical_links", []) + d.get("pagination_links", []) for d in data]
			extracted_links = list(set([item for list_of_lists in x_links for item in list_of_lists]))

			if len(extracted_links) > 0:
				new_urls = db.get_new_urls(extracted_links)
				if len(new_urls) > 0 :
					db.insert_new_urls(new_urls)
					self.add_to_url_queue(new_urls)

				before = time()
				if "unique_inlinks" in self.settings.get("CRAWL_ITEMS", ""):
					for d in data:
						inlinks = d.get("links", []) + d.get("hreflang_links", []) + d.get("canonical_links", []) + d.get("pagination_links", [])
						db.insert_inlinks(inlinks, d['url'])
				# print(f"Inserting inlinks took {time() - before}")

			with self.lock:
				if self.urls_crawled - urls_last >= 100:
					do_commit = True
					urls_last = self.urls_crawled

			if do_commit:
				db.commit()
				do_commit = False

			time_spent = time() - ts
			if time_spent < 0.25:
				sleep_time = 0.25 - time_spent
				# print("sleeping", sleep_time, "seconds")
				sleep(sleep_time)
			# print(f"Iteration took {time() - ts}")

		# Outside while loop, wrap things up
		self.crawl_running.set()

		# Empty our URL Queue first
		with self.url_queue.mutex:
			self.url_queue.queue.clear()
		# Add signals for our waiting workers that they are done for today
		[self.url_queue.put("END") for _ in range(int(self.settings["THREADS"]))]

		# Always commit to db at the very end
		db.commit()
		db.close()

		self.session.close()
		print("Consumer thread finished")

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
		self.crawl_running.set()
		self.wait_for_threads()
		self.save_config(self.settings)
