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
        }

        self.crawl_items = crawl_items
        self.extractions = extractions

        self.con = sqlite.connect(self.db_name)
        self.con.create_function("REGEXP", 2, self.regexp)
        self.columns = self.get_columns()
        self.columns_total = len(self.columns)

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
        cur = self.con.cursor()
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = cur.fetchone()[0]
        cur.close()
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
    def get_table_columns(self, table='crawl'):
        cur = self.con.cursor()
        cur.execute(f"SELECT * FROM {table}")
        out = [description[0] for description in cur.description]
        cur.close()
        # remove id from our output
        if 'id' in out:
            out.remove('id')
            # out.pop(0)
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
        return out

    def create(self):
        self.create_data_table()
        self.create_config_table()
        self.create_inlinks_table()
        self.create_exclusions_table()
        self.create_extractions_table()
        self.create_views()
        self.commit()

    @exception_handler
    def items_to_sql(self, items, op=None, remove=None):
        if op and not remove:
            return ", ".join(f"{i} {op}" for i in items)
        elif op and remove:
            return ", ".join(f"{i} {op}" for i in items if i != remove)
        return ", ".join(f"{i[0]} {i[1]}" for i in items)

    @exception_handler
    def create_data_table(self):
        cur = self.con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS crawl(id INTEGER PRIMARY KEY, {self.items_to_sql(self.get_sql_columns())})")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS url_index ON crawl (url);")
        cur.close()

    @exception_handler
    def create_config_table(self):
        cur = self.con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS config(setting TEXT type UNIQUE, value TEXT)")
        cur.close()

    @exception_handler
    def create_inlinks_table(self):
        cur = self.con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS inlinks(id INTEGER PRIMARY KEY, url_from_id INTEGER, url_to_id INTEGER, UNIQUE(url_from_id, url_to_id))")
        cur.close()

    @exception_handler
    def create_extractions_table(self):
        cur = self.con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS extractions(name TEXT, type TEXT, value TEXT)")
        cur.close()

    @exception_handler
    def create_exclusions_table(self):
        cur = self.con.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS exclusions(operator TEXT, value TEXT)')
        cur.close()

    @exception_handler
    def insert_config(self, settings):

        special_settings = ['EXTRACTIONS', 'EXCLUSIONS', 'CRAWL_ITEMS']
        rows = [(key, value)
                for key, value in settings.items() if key not in special_settings]
        cur = self.con.cursor()

        if 'CRAWL_ITEMS' in settings:
            rows += [('CRAWL_ITEMS', ', '.join(settings['CRAWL_ITEMS']))]

        if 'EXTRACTIONS' in settings:
            cur.execute('DROP TABLE IF EXISTS extractions')
            self.create_extractions_table()
            cur.executemany(
                'REPLACE INTO extractions (name, type, value) VALUES (?, ?, ?)', settings['EXTRACTIONS'])

        if 'EXCLUSIONS' in settings:
            cur.execute('DROP TABLE IF EXISTS exclusions')
            self.create_exclusions_table()
            cur.executemany(
                'REPLACE INTO exclusions (operator, value) VALUES (?, ?)', settings['EXCLUSIONS'])

        cur.executemany(
            'REPLACE INTO config (setting, value) VALUES (?, ?)', rows)

        self.commit()
        cur.close()

    def get_settings(self):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM config")
        result = dict(cur.fetchall())

        for k, v in result.items():
            if 'CRAWL_ITEMS' in k:
                result[k] = [r.strip() for r in result[k].split(',')]

        cur.execute("SELECT * FROM extractions")
        extractions = cur.fetchall()

        cur.execute('SELECT * FROM exclusions')
        exclusions = cur.fetchall()
        cur.close()
        return {**result, 'EXCLUSIONS': exclusions, 'EXTRACTIONS': extractions}

    @exception_handler
    def print_version(self):
        cur = self.con.cursor()
        cur.execute('SELECT SQLITE_VERSION()')
        data = cur.fetchone()[0]
        cur.close()
        print(f"SQLite version: {data}")

    @exception_handler
    def url_in_db(self, url):
        cur = self.con.cursor()
        result = cur.execute(
            '''SELECT EXISTS(SELECT 1 FROM crawl WHERE url = ?)''', (url,))
        cur.close()
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
        cur = self.con.cursor()
        cur.execute("""SELECT count(*) FROM crawl""")
        result = cur.fetchone()[0]
        cur.close()
        return result

    @exception_handler
    def is_empty(self):
        return self.get_total_urls() > 0

    @exception_handler
    def get_urls_crawled(self):
        cur = self.con.cursor()
        cur.execute(
            """SELECT count(*) FROM crawl WHERE status_code != ''""")
        out = cur.fetchone()[0]
        cur.close()
        return out

    @exception_handler
    def get_crawl_data(self):
        cur = self.con.cursor()
        cur.execute(f"SELECT {', '.join(self.columns)} FROM crawl WHERE status_code != ''")
        out = cur.fetchall()
        cur.close()
        return out

    @exception_handler
    def close(self):
        self.con.close()

    @exception_handler
    def print_db(self):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM crawl")
        rows = cur.fetchall()
        cur.close()
        [print(row) for row in rows]

    @exception_handler
    def get_url_queue(self):
        cur = self.con.cursor()
        cur.row_factory = lambda cursor, row: row[0]
        cur.execute("SELECT url from crawl where status_code = ''")
        rows = cur.fetchall()
        cur.row_factory = None
        cur.close()
        return rows

    def regexp(self, expr, item):
        reg = re.compile(expr)
        return reg.search(item) is not None

    def query(self, filters, table, columns=None):

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

        if not table:
            table = 'crawl'

        if columns:
            columns = f"{', '.join(columns)}"
        elif table == 'crawl':
            columns = f"{', '.join(self.columns)}"
        else:
            columns = '*'

        query = f'SELECT {columns} FROM {table} '

        if filters:

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
                queries.append(f"{column} {operator} '{value}'")

            if queries:
                query += 'WHERE ' + \
                    ' AND '.join(queries) + " AND status_code != ''"
            else:
                query += "WHERE status_code != ''"

            if order_cols:
                query += ' ORDER BY ' + ', '.join(order_cols)
        else:
            query += "WHERE status_code != ''"

        cur = self.con.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        if rows != None:
            return rows
        return []

    def get_inlinks(self, url):
        url_id = self.get_ids([url]).pop()
        query = fr"SELECT url as inlink FROM crawl LEFT JOIN inlinks ON crawl.id = inlinks.url_from_id WHERE inlinks.url_to_id = {url_id}"
        cur = self.con.cursor()
        cur.execute(query)
        inlinks = cur.fetchall()
        cur.close()
        if inlinks:
            return inlinks
        return []

    @exception_handler
    def chunk_list(self, l: list, chunk_size=100) -> list:
        return [l[i * chunk_size:(i + 1) * chunk_size] for i in range((len(l) + chunk_size - 1) // chunk_size)]

    def get_new_urls(self, links, chunk_size=999, check_crawled=False):
        cur = self.con.cursor()
        cur.row_factory = lambda cursor, row: row[0]
        chunked_list = self.chunk_list(links, chunk_size=chunk_size)
        urls_in_db = []

        for chunk in chunked_list:
            try:
                sql = f"SELECT url FROM crawl WHERE url in ({','.join(['?']*len(chunk))})"
                if check_crawled:
                    sql = f"SELECT url FROM crawl WHERE url in ({','.join(['?']*len(chunk))}) AND status_code != ''"
                cur.execute(sql, chunk)
                urls_in_db += cur.fetchall()
            except Exception as e:
                print("ERROR returning new urls")
                print(e)
                print(f"input: {links}")
        
        cur.row_factory = None
        cur.close()
        
        urls_not_in_db = list(set(links) - set(urls_in_db))

        if not urls_not_in_db:
            return []
        return urls_not_in_db

    @exception_handler
    def insert_new_urls(self, urls):
        urls = list(set(urls))
        rows = [tuple([url] + [""] * (self.columns_total - 1)) for url in urls]
        query = f"INSERT OR IGNORE INTO crawl VALUES(NULL, {','.join(['?'] * self.columns_total)})"
        cur = self.con.cursor()
        cur.executemany(query, rows)
        cur.close()

    @exception_handler
    def get_ids(self, urls):
        chunks = self.chunk_list(urls, chunk_size=999)
        cur = self.con.cursor()
        cur.row_factory = lambda cursor, row: row[0]
        results = []

        for chunk in chunks:
            sql = f"SELECT id FROM crawl WHERE url IN ({','.join(['?']*len(chunk))})"
            cur.execute(sql, chunk)
            results += cur.fetchall()

        cur.row_factory = None
        cur.close()
        return results

    @exception_handler
    def insert_inlinks(self, urls, from_url):
        from_id = self.get_ids([from_url])
        if len(from_id) == 1:
            from_id = from_id[0]
            ids = self.get_ids(urls)
            rows = [(from_id, to_id) for to_id in ids]
            cur = self.con.cursor()
            cur.executemany(
                "INSERT OR IGNORE INTO inlinks VALUES(NULL, ?, ?)", rows)
            cur.close()
            self.commit()
        else:
            print(f"{from_url} not in db!")

    def tuple_front_to_end(self, t):
        l = list(t)
        top = l.pop(0)
        l.append(top)
        return tuple(l)

    @exception_handler
    def insert_crawl_data(self, data, new=False):
        cur = self.con.cursor()
        if new == False:
            rows = [self.tuple_front_to_end(t) for t in data]
            query = f"UPDATE crawl SET {self.items_to_sql(self.columns, op='= ?', remove='url')} WHERE url = ?"
            cur.executemany(query, rows)
        else:
            query = f"INSERT INTO crawl VALUES(NULL, {','.join(['?'] * self.columns_total)})"
            cur.executemany(query, data)
        cur.close()
        self.commit()

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

    def create_view_non_ok_inlinks(self, table_name):
        query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT crawl.url as url_from, url_to, sc as status_code FROM (SELECT url_from_id, url as url_to, status_code as sc FROM crawl INNER JOIN inlinks ON inlinks.url_to_id = crawl.id WHERE status_code != 200) INNER JOIN crawl ON crawl.id = url_from_id"
        cur = self.con.cursor()
        cur.execute(query)
        cur.close()

    def create_view_broken_inlinks(self, table_name, from_status_code, to_status_code):
        query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT crawl.url as url_from, url_to, sc as status_code FROM (SELECT url_from_id, url as url_to, status_code as sc FROM crawl INNER JOIN inlinks ON inlinks.url_to_id = crawl.id WHERE status_code BETWEEN {from_status_code} AND {to_status_code}) INNER JOIN crawl ON crawl.id = url_from_id"
        cur = self.con.cursor()
        cur.execute(query)
        cur.close()

    def create_view_status_codes(self, table_name, from_status_code, to_status_code):
        columns = f"{', '.join(self.columns)}"
        query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT {columns} FROM crawl WHERE status_code BETWEEN {from_status_code} AND {to_status_code}"
        cur = self.con.cursor()
        cur.execute(query)
        cur.close()

    def create_view_content_type(self, table_name, content_type):
        columns = f"{', '.join(self.columns)}"
        query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT {columns} FROM crawl WHERE content_type LIKE '%{content_type}%' AND status_code != ''"
        cur = self.con.cursor()
        cur.execute(query)
        cur.close()

    def create_view_crawl_status(self, table_name, crawl_status):
        columns = f"{', '.join(self.columns)}"

        query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT {columns} FROM crawl WHERE crawl_status LIKE '%{crawl_status}%' AND status_code !=''"

        if crawl_status == 'not ok':
            query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT {columns} FROM crawl WHERE crawl_status NOT LIKE '%ok%' AND status_code !=''"
        elif crawl_status == 'ok':
            query = f"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT {columns} FROM crawl WHERE crawl_status = 'ok' AND status_code !=''"
        cur = self.con.cursor()
        cur.execute(query)
        cur.close()

    def create_onpage_view_length(self, table_name, column):
        query = fr"CREATE VIEW IF NOT EXISTS {table_name} AS SELECT url, {column}, LENGTH(column) as length FROM crawl ORDER BY length DESC"

    def create_views(self):
        self.create_view_non_ok_inlinks('broken_inlinks_non_ok')
        self.create_view_broken_inlinks('broken_inlinks_3xx', 300, 399)
        self.create_view_broken_inlinks('broken_inlinks_4xx', 400, 499)
        self.create_view_broken_inlinks('broken_inlinks_5xx', 500, 599)

        self.create_view_status_codes('status_codes_200', 200, 200)
        self.create_view_status_codes('status_codes_3xx', 300, 399)
        self.create_view_status_codes('status_codes_4xx', 400, 499)
        self.create_view_status_codes('status_codes_5xx', 500, 599)

        self.create_view_content_type('content_type_html', 'html')
        self.create_view_content_type('content_type_image', 'image')
        self.create_view_content_type('content_type_css', 'css')
        self.create_view_content_type('content_type_font', 'font')
        self.create_view_content_type('content_type_json', 'json')
        self.create_view_content_type('content_type_xml', 'xml')
        self.create_view_content_type('content_type_javascript', 'javascript')

        self.create_view_crawl_status('crawl_status_ok', 'ok')
        self.create_view_crawl_status('crawl_status_not_ok', 'not ok')
        self.create_view_crawl_status(
            'crawl_status_canonicalised', 'canonicalised')
        self.create_view_crawl_status(
            'crawl_status_blocked_by_robots', 'blocked')
        self.create_view_crawl_status('crawl_status_noindex', 'noindex')
