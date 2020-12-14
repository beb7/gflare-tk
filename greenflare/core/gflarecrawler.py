"""
@author Benjamin Görler <ben@greenflare.io>

@section LICENSE

Greenflare SEO Web Crawler (https://greenflare.io)
Copyright (C) 2020  Benjamin Görler. This file is part of
Greenflare, an open-source project dedicated to delivering
high quality SEO insights and analysis solutions to the world.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from threading import Thread, Event, enumerate as tenum
from greenflare.core.gflaredb import GFlareDB
from greenflare.core.gflareresponse import GFlareResponse as gf
from greenflare.core.defaults import Defaults
from requests import Session, exceptions
from time import sleep, time
import queue


class GFlareCrawler:

    def __init__(self, settings=None, gui_mode=False, lock=None, stats=True):
        self.url_queue = queue.Queue()
        self.data_queue = queue.Queue(maxsize=25)
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

    def _connect_to_db(self):
        try:
            return GFlareDB(self.db_file, crawl_items=self.settings.get("CRAWL_ITEMS"), extractions=self.settings.get('EXTRACTIONS', []))
        except Exception as e:
            raise

    def init_crawl_headers(self):
        if not self.settings.get('USER_AGENT', ''):
            self.settings['USER_AGENT'] = "Greenflare SEO Spider/1.0"
        self.HEADERS = {'User-Agent': self.settings['USER_AGENT'], **Defaults.headers}

    def request_robots_txt(self, url):
        robots_txt_url = self.gf.get_robots_txt_url(url)
        response = self.crawl_url(robots_txt_url)
        
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            return response
            
        return self.response_to_data(response)

    def start_crawl(self):
        print("Crawl started")
        self.init_crawl_headers()
        self.init_session()

        # Set speed limit
        if int(self.settings.get("URLS_PER_SECOND", 0)) > 0:
            self.parallel_requests_limit = (
                1 / int(self.settings["URLS_PER_SECOND"])) * int(self.settings["THREADS"])

        db = self._connect_to_db()
        db.create()

        # # Reset response object
        self.gf = gf(self.settings, columns=None)

        self.columns = self.gf.all_items = db.get_columns()

        if self.settings["MODE"] == "Spider":
            self.settings['STARTING_URL'] = self.gf.url_components_to_str(
                self.gf.parse_url(self.settings['STARTING_URL']))
            self.settings["ROOT_DOMAIN"] = self.gf.get_domain(
                self.settings['STARTING_URL'])
            response = self.crawl_url(self.settings['STARTING_URL'])

            # Check if we are dealing with a reachable host
            if response == 'SKIP_ME':
                self.crawl_timed_out.set()
                self.crawl_running.set()
                db.close()
                return

            data = self.response_to_data(response)

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

        try:
            db = self._connect_to_db()
            self.urls_crawled = db.get_urls_crawled()
            self.urls_total = db.get_total_urls()
            self.settings = db.get_settings()
            print('Loaded:', self.settings)
            db.extractions = self.settings.get("EXTRACTIONS", "")
            self.columns = db.columns.copy()
            db.close()
        except Exception as e:
            print('load_crawl failed!')
            print(e)
            raise

    def reset_crawl(self):
        # Reset queue
        if self.settings['MODE'] != 'List':
            self.data_queue = queue.Queue(maxsize=25)
            self.url_queue = queue.Queue()
            self.gui_url_queue = []
            self.url_attempts = {}

        self.gf = gf(self.settings, columns=None)

        self.crawl_running.clear()
        self.crawl_completed.clear()
        self.crawl_timed_out.clear()

        self.urls_crawled = 0
        self.urls_total = 0

    def resume_crawl(self):
        print("Resuming crawl ...")
        self.init_crawl_headers()
        # Reinit session
        self.init_session()

        self.reset_crawl()

        db = self._connect_to_db()

        self.urls_crawled = db.get_urls_crawled()
        self.urls_total = db.get_total_urls()

        # Reset response object
        self.gf = gf(self.settings, columns=db.get_columns())

        if self.settings['MODE'] != 'List':
            response = self.request_robots_txt(
                self.settings.get('STARTING_URL'))
            if response == 'SKIP_ME':
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
        self.consumer_thread = Thread(
            target=self.consumer_worker, name="consumer")
        self.consumer_thread.start()

    def spawn_threads(self):
        if self.crawl_running.is_set() == False:
            threads = int(self.settings["THREADS"])
            for i in range(threads):
                tname = f"worker-{i}"
                t = Thread(target=self.crawl_worker, name=tname, args=(tname,))
                t.start()
        if self.stats:
            Thread(target=self.urls_per_second_stats, name="stats").start()

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
        if url_limit > 0:
            self.rate_limit_delay = 1 / url_limit * \
                int(self.settings.get("THREADS", 1)) * step
        while self.crawl_running.is_set() == False:
            with self.lock:
                old = self.urls_crawled

            # Wait for 1 second to pass
            sleep(1)

            with self.lock:
                self.current_urls_per_second = self.urls_crawled - old

                if url_limit > 0 and self.current_urls_per_second > url_limit:
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
                self.session.proxies = {'https': f"https://{self.settings['PROXY_USER']}:{self.settings['PROXY_PASSWORD']}@{self.settings['PROXY_HOST']}"}

    def response_to_data(self, response):
        self.gf.set_response(response)
        return self.gf.get_data()

    def crawl_url(self, url, header_only=False):
        header = None
        body = None

        # timeout (connection, response)
        timeout = (3, 5)
        issue = ""

        with self.lock:
            if self.gf.is_external(url):
                header_only = True

        try:
            if header_only:
                header = self.session.head(
                    url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
                return header

            header = self.session.head(
                url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)

            content_type = header.headers.get("content-type", "")
            if "text" in content_type:
                body = self.session.get(
                    url, headers=self.HEADERS, allow_redirects=True, timeout=timeout)
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
            return {'url': url, 'data': [tuple([url, issue.lower(), '0', ''] + [''] * (len(self.columns) - 4))], 'links': []}

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
        self.data_queue.put(data)

    def crawl_worker(self, name):
        busy = Event()
        response = None
        timeout = 0.25
        backoff_factor = 1
        adj_timeout = timeout

        with self.lock:
            self.worker_status.append(busy)

        while self.crawl_running.is_set() == False:
            sleep(self.rate_limit_delay)

            if not response:
                url = self.url_queue.get()
                if url == "END":
                    break
                busy.set()
                response = self.crawl_url(url)

            if response == "SKIP_ME":
                response = None
                busy.clear()
                continue
            try:
                adj_timeout = timeout
                self.data_queue.put(response, timeout=adj_timeout)
                response = None
            except queue.Full:
                    # print(f'{name} has hit a full queue, retrying in
                    # {adj_timeout} ...')
                adj_timeout += backoff_factor * timeout
                continue
                if self.crawl_running.is_set():
                    busy.clear()
                    break
            busy.clear()

    def consumer_worker(self):
        db = self._connect_to_db()
        do_commit = False
        with self.lock:
            urls_last = self.urls_crawled

        while not self.crawl_running.is_set():
            ts = time()
            with self.lock:
                if self.url_queue.empty() and self.data_queue.empty() and all([not i.is_set() for i in self.worker_status]):
                    self.crawl_running.set()
                    self.crawl_completed.set()
                    break
            after_lock = time() - ts
            try:
                # print(f"Queue size: {self.data_queue.qsize()}")
                wait_before = time()
                response = self.data_queue.get()
                wait_after = time() - wait_before
            except queue.Empty:
                print("Consumer thread timed out")
                self.crawl_running.set()
                self.crawl_timed_out.set()
                for t in tenum():
                    if "worker-" in t.name:
                        self.url_queue.put("END")
                break

            response_to_data_time = 0
            if isinstance(response, dict):
                data = response
            else:
                before = time()
                data = self.response_to_data(response)
                response_to_data_time = time() - before

            crawl_data = data['data']

            before_insert = time()
            new, updated = db.insert_new_data(crawl_data)
            after_insert = time() - before_insert

            before_gui = time()
            with self.lock:
                self.urls_crawled += len(updated) + len(new)
                self.urls_total += len(new)
            if self.gui_mode:
                if new or updated:
                    self.add_to_gui_queue(new + updated)
            after_gui = time() - before_gui

            before_links = time()
            extracted_links = data.get("links", []) + data.get("hreflang_links", []) + data.get(
                "canonical_links", []) + data.get("pagination_links", [])
            after_links = 0
            after_inlink = 0

            if len(extracted_links) > 0:
                new_urls = db.get_new_urls(extracted_links)

                if len(new_urls) > 0:
                    db.insert_new_urls(new_urls)
                    self.add_to_url_queue(new_urls)
                after_links = time() - before_links

                inlink_before = time()
                if "unique_inlinks" in self.settings.get("CRAWL_ITEMS", ""):
                    db.insert_inlinks(extracted_links, data['url'])
                after_inlink = time() - inlink_before

            with self.lock:
                if self.urls_crawled - urls_last >= 100:
                    do_commit = True
                    urls_last = self.urls_crawled

            after_commit = 0
            before_commit = time()
            if do_commit:
                db.commit()
                do_commit = False
                after_commit = time() - before_commit

            # print(f"Iteration took {time() - ts:.2f} sec | waited
            # {wait_after:.2f} sec | response_to_data
            # {response_to_data_time:.2f} sec | insert took {after_insert:.2f}
            # sec | commit took {after_commit:.2f} | links took
            # {after_links:.2f}| inlinks took {after_inlink:.2f} sec | gui took
            # {after_gui:.2f} | locked for {after_lock:.2f} secs")

        # Outside while loop, wrap things up
        self.crawl_running.set()

        # Empty our URL Queue first
        with self.url_queue.mutex:
            self.url_queue.queue.clear()
        # Add signals for our waiting workers that they are done for today
        [self.url_queue.put("END")
         for _ in range(int(self.settings["THREADS"]))]

        # Always commit to db at the very end
        db.commit()
        db.close()

        self.session.close()
        print("Consumer thread finished")

    def get_crawl_data(self, filters, table, columns=None):
        if self.db_file:
            db = self._connect_to_db()
            data = db.query(filters, table, columns=columns)
            if columns == '*' or not columns:
                columns = db.get_table_columns(table=table)
            db.close()
            return columns, data
        return []

    def save_config(self, settings):
        if self.db_file:
            db = self._connect_to_db()
            db.insert_config(settings)
            db.commit()
            db.close()

    def get_columns(self, table='crawl'):
        if self.db_file:
            db = self._connect_to_db()
            columns =  db.get_table_columns(table=table)
            db.close()
            return columns
        return []

    def get_inlinks(self, url):
        if self.db_file:
            db = self._connect_to_db()
            inlinks = db.get_inlinks(url)
            db.close()
            return inlinks
        return []

    def end_crawl_gracefully(self):
        print("Ending all worker threads gracefully ...")
        self.crawl_running.set()
        self.wait_for_threads()
        try:
            self.save_config(self.settings)
        except Exception as e:
            print('ERROR: Saving config failed!')
            print(e)
