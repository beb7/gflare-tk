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
        self.active_workers = 0
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

    def _connect_to_db(self) -> GFlareDB:
        """Connects to the database and returns a GFLareDB object if successful"""
        try:
            return GFlareDB(self.db_file, crawl_items=self.settings.get("CRAWL_ITEMS"), extractions=self.settings.get('EXTRACTIONS', []))
        except Exception as e:
            raise

    def init_crawl_headers(self) -> None:
        """Initialises headers to be used in the requests session. Uses default settings if no user-agent has been specified."""
        if not self.settings.get('USER_AGENT', ''):
            self.settings['USER_AGENT'] = "Greenflare SEO Spider/1.0"
        self.HEADERS = {'User-Agent': self.settings['USER_AGENT'], **Defaults.headers}

    def request_robots_txt(self, url: str):
        """
        Determines and crawls the robots.txt of any given URL.

        Returns:
            skip_url (str): string that says SKIP_ME
            issue_response (dict): dict crafted by the deal_with_response method
            data (dict): parsed results of a valid response
        """
        robots_txt_url = self.gf.get_robots_txt_url(url)
        response = self.crawl_url(robots_txt_url)

        if isinstance(response, str):
            skip_url = response
            return skip_url
        if isinstance(response, dict):
            issue_response = response
            return issue_response

        data = self.response_to_data(response)
        return data

    def start_crawl(self) -> None:
        """Starts a new crawl using the config from self.settings"""
        print('Crawl started')
        self.init_crawl_headers()
        self.init_session()

        # Set speed limit
        if int(self.settings.get('URLS_PER_SECOND', 0)) > 0:
            self.parallel_requests_limit = (
                1 / int(self.settings['URLS_PER_SECOND'])) * int(self.settings['THREADS'])

        db = self._connect_to_db()
        db.create()
        db.insert_config(self.settings)

        # # Reset response object
        self.gf = gf(self.settings, columns=None)

        self.columns = self.gf.all_items = db.get_columns()

        if self.settings['MODE'] == 'Spider':
            self.settings['ROOT_DOMAIN'] = self.gf.get_domain(
                self.settings['STARTING_URL'])
            response = self.crawl_url(self.settings['STARTING_URL'])

            # Check if we are dealing with a reachable host
            if isinstance(response, str):
                self.crawl_timed_out.set()
                self.crawl_running.set()
                db.close()
                return

            self.request_robots_txt(response.url)
            data = self.response_to_data(response)

            self.add_to_data_queue(data)

        elif self.settings['MODE'] == 'List':
            if len(self.list_mode_urls) > 0:
                self.add_to_url_queue(self.list_mode_urls)
                db.insert_new_urls(self.list_mode_urls)
            else:
                print('ERROR: No urls to list crawl found!')

        db.close()

        self.start_consumer()
        Thread(target=self.spawn_threads).start()

    def load_crawl(self, db_file: str) -> None:
        """Load a database by using the file path as string. Raises Exception if it fails."""
        self.db_file = db_file

        try:
            db = self._connect_to_db()
            # Add new views if any
            db.create()
            self.urls_crawled = db.get_urls_crawled()
            self.urls_total = db.get_total_urls()
            self.settings = db.get_settings()
            db.extractions = self.settings.get('EXTRACTIONS', '')
            self.columns = db.columns.copy()
            db.close()
        except Exception as e:
            print('load_crawl failed!')
            raise e

    def reset_crawl(self) -> None:
        """Reset crawl to default state in preparation for a new crawl. """
        # Reset queue
        if self.settings['MODE'] != 'List':
            self.data_queue = queue.Queue(maxsize=25)
            self.url_queue = queue.Queue()
            self.gui_url_queue = []
            self.url_attempts = {}

        self.init_crawl_headers()
        self.init_session()

        self.active_workers = 0

        self.gf = gf(self.settings, columns=None)

        self.crawl_running.clear()
        self.crawl_completed.clear()
        self.crawl_timed_out.clear()

        self.urls_crawled = 0
        self.urls_total = 0

    def resume_crawl(self) -> None:
        """Resumes a crawl using the settings from the connected database."""
        print('Resuming crawl ...')
        self.reset_crawl()
        db = self._connect_to_db()
        self.urls_crawled = db.get_urls_crawled()
        self.urls_total = db.get_total_urls()

        # Create a new response object with the columns from the loaded databse
        self.gf = gf(self.settings, columns=db.get_columns())

        if self.settings['MODE'] != 'List':
            response = self.request_robots_txt(
                self.settings.get('STARTING_URL'))
            if isinstance(response, str):
                self.crawl_timed_out.set()
                self.crawl_running.set()
                db.close()
                return

        # Reinit URL queue
        self.add_to_url_queue(db.get_url_queue(), count=False)

        db.close()

        self.start_consumer()
        Thread(target=self.spawn_threads).start()

    def start_consumer(self) -> None:
        """Starts a single thread responsible for storing crawl data in the database."""
        self.consumer_thread = Thread(
            target=self.consumer_worker, name='consumer')
        self.consumer_thread.start()

    def spawn_threads(self) -> None:
        """Starts n crawl worker threads as defined in self.settings"""
        if self.crawl_running.is_set() == False:
            threads = int(self.settings['THREADS'])
            for i in range(threads):
                tname = f'worker-{i}'
                t = Thread(target=self.crawl_worker, name=tname, args=(tname,))
                t.start()
        if self.stats:
            Thread(target=self.urls_per_second_stats, name='stats').start()

    def wait_for_workers(self) -> None:
        """Waits for all worker threads to join/finish."""
        for t in tenum():
            if 'worker-' in t.name:
                t.join()
        print('All workers joined ...')

    def urls_per_second_stats(self) -> None:
        """Thread-safe: Sets crawl statistics. Meant to be run as single tread. Controls URL limit."""

        url_limit = int(self.settings.get('URLS_PER_SECOND', 0))
        step = 0.1

        # Set initial limit depending on the number of threads
        # FIXME: Move the url_limit control to a dedicated function
        if url_limit > 0:
            self.rate_limit_delay = 1 / url_limit * \
                int(self.settings.get('THREADS', 1)) * step
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
        self.session.headers.update(self.HEADERS)
        status_forcelist = (500, 502, 504)
        retries = self.settings.get('MAX_RETRIES', 0)
        self.header_only = False

        if self.settings.get('PROXY_HOST', '') != '':
            if self.settings.get('PROXY_USER', '') == '':
                self.session.proxies = {'https': f'{self.settings["PROXY_HOST"]}'}
            else:
                self.session.proxies = {'https': f'https://{self.settings["PROXY_USER"]}:{self.settings["PROXY_PASSWORD"]}@{self.settings["PROXY_HOST"]}'}

        if self.settings.get('AUTH_USER', '') != '':
            self.session.auth = (
                self.settings['AUTH_USER'], self.settings['AUTH_PASSWORD'])

    def response_to_data(self, response) -> dict:
        """Function to parse a requests object into a gflare resposne dict."""
        self.gf.set_response(response)
        return self.gf.get_data()

    def crawl_url(self, url, header_only=False) -> dict:
        """Crawl any given URL."""

        header = None
        body = None

        # timeout (connection, response)
        timeout = (3, 5)
        issue = ''

        self.session.cookies.clear()

        with self.lock:
            if self.gf.is_external(url):
                header_only = True

        try:
            if header_only:
                header = self.session.head(
                    url, allow_redirects=True, timeout=timeout)
                return header

            header = self.session.head(
                url, allow_redirects=True, timeout=timeout)

            content_type = header.headers.get('content-type', '')
            if 'text' in content_type:
                body = self.session.get(
                    url, allow_redirects=True, timeout=timeout)
                return body

            return header
        except exceptions.TooManyRedirects:
            return self.deal_with_exception(url, 'Too Many Redirects')

        except exceptions.ConnectionError:
            return self.deal_with_exception(url, 'Connection Refused')

        except exceptions.ReadTimeout:
            return self.deal_with_exception(url, 'Read timed out')

        except exceptions.InvalidURL:
            return self.deal_with_exception(url, 'Invalid URL')

        except Exception as e:
            return self.deal_with_exception(url, 'Unknown Exception')

    def deal_with_exception(self, url: str, issue: str) -> dict:
        """Adds URL back to the URL queue until the retry threshold has been reached. Returns mock string instead."""
        with self.lock:
            attempts = self.url_attempts.get(url, 0)

        if attempts >= self.retries:
            print(f"{url} {issue} after {attempts} attempts.")
            return {'url': url, 'data': [tuple([url, issue.lower(), '0', ''] + [''] * (len(self.columns) - 4))], 'links': []}

        with self.lock:
            self.url_attempts[url] = self.url_attempts.get(url, 0) + 1

        self.add_to_url_queue([url], count=False)
        return 'SKIP_ME'

    def add_to_url_queue(self, urls: list, count=True) -> None:
        """Append and count (enabled by default) a list of URLs to the URL queue."""
        if count:
            with self.lock:
                self.urls_total += len(urls)
        for url in urls:
            self.url_queue.put(url)

    def add_to_gui_queue(self, data: dict) -> None:
        """Add gflare response dict data object to GUI queue."""
        with self.lock:
            self.gui_url_queue += data

    def add_to_data_queue(self, data: dict) -> None:
        """Add gflare response dict data object to data queue."""
        self.data_queue.put(data)

    def clock_workers(self, increase: bool) -> None:
        """Increases or decreases the count of active workers (Thread safe)."""

        if increase:
            with self.lock:
                self.active_workers += 1
        else:
            with self.lock:
                self.active_workers -= 1

    def get_buys_workers(self) -> int:
        """Get number of active workers (Thread safe)."""
        with self.lock:
            return self.active_workers

    def crawl_worker(self, name: str) -> None:
        """Function to be run as a worker Thread. Requests URLs and inserts responses into the data queue."""
        response = None
        timeout = 0.25
        backoff_factor = 1
        adj_timeout = timeout

        # Set to active
        self.clock_workers(True)

        while self.crawl_running.is_set() == False:
            if not response:
                sleep(self.rate_limit_delay)
                self.clock_workers(False)
                url = self.url_queue.get()
                self.clock_workers(True)

                if url == "END":
                    break

                response = self.crawl_url(url)

            if isinstance(response, str):
                response = None
                continue
            try:
                adj_timeout = timeout
                self.data_queue.put(response, timeout=adj_timeout)
                response = None
            except queue.Full:
                adj_timeout += backoff_factor * timeout
                continue

        self.clock_workers(False)

    def notify_crawl_workers_to_stop(self) -> None:
        """ Notifies all crawl workers to stop by inserting an END element into the URL queue."""

        for t in tenum():
            if 'worker-' in t.name:
                self.url_queue.put('END')

    def consumer_worker(self) -> None:
        """Function to be run as a _single_ consumer Thread. Extracts information from request responses and inserts data into the database."""

        db = self._connect_to_db()
        
        while not self.crawl_running.is_set():
            try:
                response = self.data_queue.get(timeout=1)
            except queue.Empty:
                if self.get_buys_workers() == 0 and self.url_queue.empty():
                    # Ugly hack to ensure that ALL remaining URLs have been crawled
                    # Otherwise, the above check is not fail safe and URLs may be overlooked
                    remaining_urls = db.get_url_queue()
                    if remaining_urls:
                        self.add_to_url_queue(remaining_urls, count=False)
                    else:
                        self.crawl_running.set()
                        self.crawl_completed.set()
                        self.notify_crawl_workers_to_stop()
                        break
                continue

            if isinstance(response, dict):
                data = response
            else:
                data = self.response_to_data(response)

            crawl_data = data['data']
            new, updated = db.insert_new_data(crawl_data)

            with self.lock:
                self.urls_crawled += len(updated) + len(new)
                self.urls_total += len(new)
            if self.gui_mode:
                if new or updated:
                    self.add_to_gui_queue(new + updated)

            extracted_links = data.get('links', [])

            if len(extracted_links) > 0:
                new_urls = db.get_new_urls(extracted_links)
                if len(new_urls) > 0:
                    db.insert_new_urls(new_urls)
                    self.add_to_url_queue(new_urls)

                if 'unique_inlinks' in self.settings.get('CRAWL_ITEMS', ''):
                    db.insert_inlinks(extracted_links, data['url'])

        # Outside while loop, wrap things up
        self.crawl_running.set()

        if not self.crawl_completed.is_set():
            # Empty our URL Queue first
            with self.url_queue.mutex:
                self.url_queue.queue.clear()
            self.notify_crawl_workers_to_stop()

        db.close()
        self.session.close()
        print('Consumer thread finished')

    def get_crawl_data(self, filters: list, table: str, columns=None):
        """Requests data from a db table based on optional filters and columns.

            Returns:
                data (tuple): list of columns and list of data.
                empty list (list): empty list if no db_file has been defined yet.
        """
        if self.db_file:
            db = self._connect_to_db()
            data = db.query(filters, table, columns=columns)
            if columns == '*' or not columns:
                columns = db.get_table_columns(table=table)
            db.close()
            return columns, data
        return []

    def save_config(self, settings: str) -> None:
        """Save settings dict to database (if exists)."""
        if self.db_file:
            db = self._connect_to_db()
            db.insert_config(settings)
            db.close()

    def get_columns(self, table='crawl') -> list:
        """Retrieve columns from database table. Return empty list if no db file is known."""
        if self.db_file:
            db = self._connect_to_db()
            columns = db.get_table_columns(table=table)
            db.close()
            return columns
        return []

    def get_inlinks(self, url: str) -> list:
        """Returns a list of URLs linking to input url."""
        if self.db_file:
            db = self._connect_to_db()
            inlinks = db.get_inlinks(url)
            db.close()
            return inlinks
        return []

    def end_crawl_gracefully(self) -> None:
        """End all crawl workers and save config before exit."""
        print('Ending all worker threads gracefully ...')
        self.crawl_running.set()
        self.wait_for_workers()
        try:
            self.save_config(self.settings)
        except Exception as e:
            print('ERROR: Saving config failed!')
            print(e)
