import sqlite3 as sqlite
import functools
import re


class GFlareDB:

    def __init__(self, db_name, crawl_items=None, extractions=None, exclusions=None):
        self.db_name = db_name

        self.columns_map = {
            "url": "TEXT type UNIQUE",
            "crawl_status": "TEXT",
            "status_code": "INT",
            "content_type": "TEXT",
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

        self.crawl_items = crawl_items
        self.extractions = extractions

        self.con, self.cur = self.db_connect()
        self.con.create_function("REGEXP", 2, self.regexp)
        self.columns = self.get_columns()
        self.columns_total = len(self.columns)
        self.table_created = False

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

    @exception_handler
    def check_if_table_exists(self, table_name):
        self.cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = self.cur.fetchone()[0]
        return result

    @exception_handler
    def load_columns(self):
        print("REPLACE me with get_columns()!")

    @exception_handler
    def get_soft_columns(self):
        if not self.crawl_items:
            self.crawl_items = []
        if not self.extractions:
            self.extractions = []
        return [k for k in self.columns_map.keys() if k in self.crawl_items] + [e[0] for e in self.extractions]

    @exception_handler
    def get_table_columns(self):
        self.cur.execute("""SELECT * FROM crawl""")
        out = [description[0] for description in self.cur.description]

        # remove id from our output
        out.pop(0)
        return out

    @exception_handler
    def get_columns(self):
        if self.check_if_table_exists("crawl") == 0:
            out = self.get_soft_columns()
            return out

        out = self.get_table_columns()
        return out

    @exception_handler
    def get_sql_columns(self):
        if not self.crawl_items:
            self.crawl_items = []
        if not self.extractions:
            self.extractions = []
        out = [(k, v) for k, v in self.columns_map.items(
        ) if k in self.crawl_items] + [(e[0], 'TEXT') for e in self.extractions]
        print("get_sql_columns:", out)
        return out

    def create(self):
        self.create_data_table()
        self.create_config_table()
        self.create_inlinks_table()
        self.create_exclusions_table()
        self.create_extractions_table()

    @exception_handler
    def db_connect(self):
        con = sqlite.connect(self.db_name)
        cur = con.cursor()
        return (con, cur)

    @exception_handler
    def items_to_sql(self, items, op=None, remove=None):
        if op and not remove:
            return ", ".join(f"{i} {op}" for i in items)
        elif op and remove:
            return ", ".join(f"{i} {op}" for i in items if i != remove)
        return ", ".join(f"{i[0]} {i[1]}" for i in items)

    @exception_handler
    def create_data_table(self):
        self.cur.execute(f"CREATE TABLE IF NOT EXISTS crawl(id INTEGER PRIMARY KEY, {self.items_to_sql(self.get_sql_columns())})")
        self.cur.execute(
            "CREATE INDEX IF NOT EXISTS url_index ON crawl (url);")

    @exception_handler
    def create_config_table(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS config(setting TEXT type UNIQUE, value TEXT)")

    @exception_handler
    def create_inlinks_table(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS inlinks(url_from_id INTEGER, url_to_id INTEGER, UNIQUE(url_from_id, url_to_id))")

    @exception_handler
    def create_extractions_table(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS extractions(name TEXT, type TEXT, value TEXT)")

    @exception_handler
    def create_exclusions_table(self):
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS exclusions(operator TEXT, value TEXT)')

    @exception_handler
    def insert_config(self, settings):

        special_settings = ['EXTRACTIONS', 'EXCLUSIONS', 'CRAWL_ITEMS']
        rows = [(key, value)
                for key, value in settings.items() if key not in special_settings]

        if 'CRAWL_ITEMS' in settings:
            rows += [('CRAWL_ITEMS', ', '.join(settings['CRAWL_ITEMS']))]

        if 'EXTRACTIONS' in settings:
            self.cur.execute('DROP TABLE IF EXISTS extractions')
            self.create_extractions_table()
            self.cur.executemany(
                'REPLACE INTO extractions (name, type, value) VALUES (?, ?, ?)', settings['EXTRACTIONS'])

        if 'EXCLUSIONS' in settings:
            self.cur.execute('DROP TABLE IF EXISTS exclusions')
            self.create_exclusions_table()
            self.cur.executemany(
                'REPLACE INTO exclusions (operator, value) VALUES (?, ?)', settings['EXCLUSIONS'])

        self.cur.executemany(
            'REPLACE INTO config (setting, value) VALUES (?, ?)', rows)

    def get_settings(self):
        self.cur.execute("SELECT * FROM config")
        result = dict(self.cur.fetchall())
        for k, v in result.items():
            if "CRAWL" in k or "ROBOTS_SETTINGS" in k or "CUSTOM_ITEMS" in k:
                result[k] = result[k].split(",")

        self.cur.execute("SELECT * FROM extractions")
        extractions = self.cur.fetchall()

        self.cur.execute('SELECT * FROM exclusions')
        exclusions = self.cur.fetchall()
        return {**result, 'EXCLUSIONS': exclusions, 'EXTRACTIONS': extractions}

    @exception_handler
    def print_version(self):
        self.cur.execute('SELECT SQLITE_VERSION()')
        data = self.cur.fetchone()[0]
        print(f"SQLite version: {data}")

    @exception_handler
    def url_in_db(self, url):
        result = self.cur.execute(
            '''SELECT EXISTS(SELECT 1 FROM crawl WHERE url = ?)''', (url,))
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
        self.cur.execute(
            """SELECT count(*) FROM crawl WHERE status_code != ''""")
        return self.cur.fetchone()[0]

    @exception_handler
    def get_crawl_data(self):
        self.cur.execute(f"SELECT {', '.join(self.columns)} FROM crawl WHERE status_code != ''")
        return self.cur.fetchall()

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

    def regexp(self, expr, item):
        reg = re.compile(expr)
        return reg.search(item) is not None

    def query(self, filters, columns=None):

        operator_mapping = {
            'Equals': '==', 'Does Not Equal': '!=',
            'Begins With': 'LIKE',
            'Ends With': 'LIKE',
            'Contains': 'LIKE',
            'Does Not Contain': 'NOT LIKE',
            'Greater Than': '>',
            'Greater Than Or Equal To': '>=',
            'Less Than': '<',
            'Less Than Or Equal To': '<='
        }

        if columns:
            columns = f"{', '.join(columns)}"
        else:
            columns = f"{', '.join(self.columns)}"

        query_head = f'SELECT {columns} FROM crawl '
        queries = []
        order_cols = []

        for f in filters:
            column, operator, value = f

            if operator == 'Begins With':
                value = f'{value}%'
            elif operator == 'Ends With':
                value = f'%{value}'
            elif 'Contain' in operator:
                value = f'%{value}%'
            elif operator == 'Sort A-Z' or operator == 'Sort Smallest To Largest':
                order_cols.append(f'{column} ASC')
                continue
            elif operator == 'Sort Z-A' or operator == 'Sort Largest To Smallest':
                order_cols.append(f'{column} DESC')
                continue

            operator = operator_mapping[operator]
            queries.append(f"WHERE {column} {operator} '{value}'")

        if queries:
            query = query_head + \
                ' AND '.join(queries) + " AND status_code != ''"
        else:
            query = query_head + "WHERE status_code != ''"

        if order_cols:
            query += ' ORDER BY ' + ', '.join(order_cols)

        print(query)
        self.cur.execute(query)
        rows = self.cur.fetchall()
        if rows != None:
            return rows
        return []

    @exception_handler
    def chunk_list(self, l: list, chunk_size=100) -> list:
        return [l[i * chunk_size:(i + 1) * chunk_size] for i in range((len(l) + chunk_size - 1) // chunk_size)]

    def get_new_urls(self, links, chunk_size=999, check_crawled=False):
        self.cur.row_factory = lambda cursor, row: row[0]
        chunked_list = self.chunk_list(links, chunk_size=chunk_size)
        urls_in_db = []

        for chunk in chunked_list:
            try:
                sql = f"SELECT url FROM crawl WHERE url in ({','.join(['?']*len(chunk))})"
                if check_crawled:
                    sql = f"SELECT url FROM crawl WHERE url in ({','.join(['?']*len(chunk))}) AND status_code != ''"
                self.cur.execute(sql, chunk)
                urls_in_db += self.cur.fetchall()
                self.cur.row_factory = None
            except Exception as e:
                print("ERROR returning new urls")
                print(e)
                print(f"input: {links}")

        urls_not_in_db = list(set(links) - set(urls_in_db))

        if not urls_not_in_db:
            return []
        return urls_not_in_db

    @exception_handler
    def insert_new_urls(self, urls):
        urls = list(set(urls))
        rows = [tuple([url] + [""] * (self.columns_total - 1)) for url in urls]
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
            self.cur.executemany(
                "INSERT OR IGNORE INTO inlinks VALUES(?, ?)", rows)
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
    def insert_new_data(self, redirects):
        new_data = []
        updated_data = []

        all_urls = [u[0] for u in redirects]
        new_urls = self.get_new_urls(all_urls)

        # Redirect URLs that were unknown before will be added immediately to
        # the db
        new_data = [d for d in redirects if d[0] in new_urls]

        if new_data:
            self.insert_crawl_data(new_data, new=True)

        # All other URLs have at least been discovered (but not necessarily
        # been crawled)
        other_urls = [u for u in all_urls if u not in new_urls]

        # check how many of the other URLs actually need updating
        to_be_updated_urls = self.get_new_urls(other_urls, check_crawled=True)
        updated_data = [d for d in redirects if d[0] in to_be_updated_urls]

        if updated_data:
            self.insert_crawl_data(updated_data, new=False)

        return (new_data, updated_data)

    
    def get_broken_inlinks(self, status_code='4'):

        query = f"SELECT crawl.url as 'URL From', url_to as 'URL To', sc as 'Status Code' FROM (SELECT url_from_id, url as url_to, status_code as sc FROM crawl INNER JOIN inlinks ON inlinks.url_to_id = crawl.id WHERE status_code LIKE '{status_code}%') INNER JOIN crawl ON crawl.id = url_from_id"

        self.cur.execute(query)
        rows = self.cur.fetchall()
        columns = [description[0] for description in self.cur.description]

        return (columns, rows)