import sqlite3 as sqlite
from csv import writer as csvwriter
import functools
from time import perf_counter
import re

class GFlareDB:
	def __init__(self, db_name, crawl_items=None, extractions=None):
		self.db_name = db_name
		self.con, self.cur = self.db_connect()
		self.con.create_function("REGEXP", 2, self.regexp)
		self.crawl_items = crawl_items
		self.columns_map = {"url": "TEXT type UNIQUE",
							"content_type": "TEXT",
							"status_code": "INT",
							"indexability": "TEXT",
							"h1": "TEXT",
							"h2": "TEXT",
							"page_title": "TEXT",
							"meta_description": "TEXT",
							"canonical_tag": "TEXT",
							"robots_txt": "TEXT",
							"redirect_url": "TEXT",
							"meta_robots": "TEXT",
							"x_robots_tag": "TEXT",
							"unique_inlinks": "INT"
							}

		self.sql_columns = [(k, v) for k,v in self.columns_map.items() if k in self.crawl_items]
		self.columns = [k for k in self.columns_map.keys() if k in self.crawl_items]
		self.columns_total = len(self.columns)
	
	def create(self):
		self.columns = [k for k in self.columns_map.keys() if k in self.crawl_items]
		self.columns_total = len(self.columns)
		self.create_data_table()
		self.create_config_table()
		self.create_inlinks_table()
		self.create_extractions_table()

	def exception_handler(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except Exception as e:
				print(f"Function {func.__name__!r} failed")
				print(f"args: {args}")
				print(f"kwargs: {kwargs}")
				print(e)
		return wrapper
	
	def timer(func):
	    @functools.wraps(func)
	    def wrapper_timer(*args, **kwargs):
	        tic = perf_counter()
	        value = func(*args, **kwargs)
	        toc = perf_counter()
	        elapsed_time = toc - tic
	        print(f"{func.__name__!r}: took {elapsed_time:0.8f} seconds")
	        return value
	    return wrapper_timer

	@exception_handler
	def db_connect(self):
		con = sqlite.connect(self.db_name)
		cur = con.cursor()
		return (con,cur)
	
	@exception_handler
	def items_to_sql(self, items, op=None, remove=None):
		if op and not remove: return ", ".join(f"{i} {op}" for i in items)
		elif op and remove: return ", ".join(f"{i} {op}" for i in items if i != remove)
		return ", ".join(f"{i[0]} {i[1]}" for i in items)

	@exception_handler
	def create_data_table(self):
		query = f"CREATE TABLE IF NOT EXISTS crawl(id INTEGER PRIMARY KEY, {self.items_to_sql(self.sql_columns)})"
		self.cur.execute(query)
		self.cur.execute("CREATE INDEX IF NOT EXISTS url_index ON crawl (url);")

	@exception_handler
	def create_config_table(self):
		self.cur.execute("CREATE TABLE IF NOT EXISTS config(setting TEXT type UNIQUE, value TEXT)")

	@exception_handler
	def create_inlinks_table(self):
		self.cur.execute("CREATE TABLE IF NOT EXISTS inlinks(url_from_id INTEGER, url_to_id INTEGER, UNIQUE(url_from_id, url_to_id))")

	@exception_handler
	def create_extractions_table(self):
		self.cur.execute("CREATE TABLE IF NOT EXISTS extractions(name TEXT, type TEXT, value TEXT)")

	@exception_handler
	def insert_config(self, inp):
		settings = inp.copy()

		to_list = {key:",".join(value) for (key, value) in settings.items() if isinstance(value, list)}
		settings = {**settings, **to_list}

		if "EXTRACTIONS" in settings:
			rows = [(k, v["selector"], v["value"]) for k, v in settings["EXTRACTIONS"].items()]
			self.cur.execute("DROP TABLE IF EXISTS extractions")
			self.create_extractions_table()
			self.cur.executemany("REPLACE INTO extractions (name, type, value) VALUES (?, ?, ?)", rows)
		
		rows = [(k, v) for k, v in settings.items() if isinstance(v, str) or isinstance(v, int)] 
		self.cur.executemany("REPLACE INTO config (setting, value) VALUES (?, ?)", rows)

	@exception_handler
	def get_settings(self):
		self.cur.execute("SELECT * FROM config")
		result = dict(self.cur.fetchall())
		for k,v in result.items():
			if "CRAWL" in k or "ROBOTS_SETTINGS" in k or "CUSTOM_ITEMS" in k or "EXCLUSIONS" in  k:
				result[k] = result[k].split(",")

		self.cur.execute("SELECT * FROM extractions")
		exc = self.cur.fetchall()
		exc = {row[0]:{"selector": row[1], "value": row[2]} for row in exc}
		out = {"EXTRACTIONS": exc}
		return {**result, **out}

	@exception_handler
	def print_version(self):
		self.cur.execute('SELECT SQLITE_VERSION()')
		data = self.cur.fetchone()[0]
		print(f"SQLite version: {data}")

	@exception_handler
	def url_in_db(self, url):
		result = self.cur.execute('''SELECT EXISTS(SELECT 1 FROM crawl WHERE url = ?)''', (url,))
		if result != None:
			if result.fetchone()[0] == 0:
				return False
			return True
		return False

	@exception_handler
	def commit(self):
		self.con.commit()

	@exception_handler
	def get_total_urls(self):
		self.cur.execute("""SELECT count(*) FROM crawl""")
		result = self.cur.fetchone()[0]
		return result

	@exception_handler
	def is_empty(self):
		return self.get_total_urls() > 0

	@exception_handler
	def get_urls_crawled(self):
		self.cur.execute("""SELECT count(*) FROM crawl WHERE status_code != ''""")
		return self.cur.fetchone()[0]

	@exception_handler
	def close(self):
		self.con.close()

	@exception_handler
	def print_db(self):
		self.cur.execute("SELECT * FROM crawl")
		rows = self.cur.fetchall()
		[print(row) for row in rows]

	@exception_handler
	def get_url_queue(self):
		self.cur.row_factory = lambda cursor, row: row[0]
		self.cur.execute("SELECT url from crawl where status_code = ''")
		rows = self.cur.fetchall()
		self.cur.row_factory = None
		return rows

	@exception_handler
	def to_csv(self, file_name, filters=None, columns=None):
		print( "Exporting crawl to", file_name, "...")
		
		if not columns and not filters:
			query = f"SELECT url, content_type, indexability, status_code, h1, h2, page_title, robots_txt, meta_robots, x_robots_tag, redirect_url, meta_description, count(*) AS unique_inlinks FROM inlinks INNER JOIN crawl ON crawl.id = inlinks.url_to_id WHERE crawl.status_code != '' GROUP BY url_to_id"
		elif filters and columns:
			negate, column, operator, value = filters
			inlink_query = ""
			group_by = ""
			if "unique_inlinks" in columns:
				inlink_query = ", count(*) AS unique_inlinks FROM inlinks INNER JOIN crawl ON crawl.id = inlinks.url_to_id"
				group_by = "GROUP BY url_to_id"
				query = f"SELECT {', '.join(columns)}{inlink_query} WHERE {column} {negate} {operator} '{value}' AND status_code != '' {group_by}"
			else:
				query =  f"SELECT {', '.join(columns)} FROM crawl WHERE {column} {negate} {operator} '{value}' AND status_code != ''"
		else:
			inlink_query = ""
			group_by = ""
			if "unique_inlinks" in columns: 
				inlink_query = ", count(*) AS unique_inlinks FROM inlinks INNER JOIN crawl ON crawl.id = inlinks.url_to_id"
				group_by = "GROUP BY url_to_id"
				query = f"SELECT {', '.join(columns)}{inlink_query} WHERE status_code != '' {group_by}"
			else:
				query =  f"SELECT {', '.join(columns)} FROM crawl WHERE status_code != ''"

		print(query)
		self.cur.execute(query)
		
		with open(file_name, "w", newline='', encoding='utf-8-sig') as csv_file:
			csv_writer = csvwriter(csv_file, delimiter=",", dialect='excel')
			csv_writer.writerow([i[0] for i in self.cur.description])
			csv_writer.writerows(self.cur)

	def regexp(self, expr, item):
		reg = re.compile(expr)
		return reg.search(item) is not None

	@exception_handler
	def query(self, negate, column, operator, value, columns=None):
		selection = f"{', '.join(columns)}"
		query = f"SELECT {selection} FROM crawl WHERE {column} {negate} {operator} '{value}' AND status_code != ''"
		print(query)
		self.cur.execute(query)
		rows = self.cur.fetchall()
		if rows != None: return rows
		return []

	@exception_handler
	def chunk_list(self, l: list, chunk_size=100) -> list:
		return [l[i * chunk_size:(i + 1) * chunk_size] for i in range((len(l) + chunk_size - 1) // chunk_size )] 

	def get_new_urls(self, links, chunk_size=999):
		self.cur.row_factory = lambda cursor, row: row[0]
		chunked_list = self.chunk_list(links, chunk_size=chunk_size)
		urls_in_db = []
	
		for chunk in chunked_list:
			try:
				sql = f"SELECT url FROM crawl WHERE url in ({','.join(['?']*len(chunk))})"
				self.cur.execute(sql, chunk)
				urls_in_db += self.cur.fetchall()
				self.cur.row_factory = None
			except Exception as e:
				print("ERROR returning new urls")
				print(e)
				print(f"input: {links}")
		
		urls_not_in_db = list(set(links)-set(urls_in_db))

		if len(urls_not_in_db) == 0:
			return []
		return urls_not_in_db

	@exception_handler
	def insert_new_urls(self, urls):
		urls = list(set(urls))
		rows = [tuple([url]+[""]*(self.columns_total - 1)) for url in urls]
		query = f"INSERT OR IGNORE INTO crawl VALUES(NULL, {','.join(['?'] * self.columns_total)})"
		self.cur.executemany(query, rows)

	@exception_handler
	def get_ids(self, urls):
		chunks = self.chunk_list(urls, chunk_size=999)
		self.cur.row_factory = lambda cursor, row: row[0]
		results = []

		for chunk in chunks:
			sql = f"SELECT id FROM crawl WHERE url IN ({','.join(['?']*len(chunk))})"
			self.cur.execute(sql, chunk)
			results += self.cur.fetchall()
		
		self.cur.row_factory = None
		return results

	@exception_handler
	def insert_inlinks(self, urls, from_url):
		from_id = self.get_ids([from_url])
		if len(from_id) == 1:
			from_id = from_id[0]
			ids = self.get_ids(urls)
			rows = [(from_id, to_id) for to_id in ids]
			self.cur.executemany("INSERT OR IGNORE INTO inlinks VALUES(?, ?)", rows)
		else:
			print(f"{from_url} not in db!")

	def tuple_front_to_end(self, t):
		l = list(t)
		top = l.pop(0)
		l.append(top)
		return tuple(l) 

	@exception_handler
	def insert_crawl_data(self, data, new=False):
		if new == False:
			rows = [self.tuple_front_to_end(t) for t in data]
			query = f"UPDATE crawl SET {self.items_to_sql(self.columns, op='= ?', remove='url')} WHERE url = ?"
			# print("columns:", self.columns)
			# print("query:", query)
			self.cur.executemany(query, rows)
		else:
			query = f"INSERT INTO crawl VALUES(NULL, {','.join(['?'] * self.columns_total)})"
			self.cur.executemany(query, data)

	@exception_handler
	def insert_redirects(self, redirects):
		for redirect in redirects:
			redirect_url = redirect[0]
			if self.url_in_db(redirect_url) == True:
				self.insert_crawl_data([redirect], new=False)
			else:
				self.insert_crawl_data([redirect], new=True)

	@exception_handler
	def add_remove_columns(self):
		print("FIXME: Not implemented yet")