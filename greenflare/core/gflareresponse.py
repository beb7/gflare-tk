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

from lxml.html import fromstring
from greenflare.core.gflarerobots import GFlareRobots
from requests import status_codes
import urllib.parse
from re import match, escape
from functools import wraps
from time import time


class GFlareResponse:

    def __init__(self, settings, columns):
        self.settings = settings
        self.all_items = columns
        self.response = None
        self.url = None
        self.url_components = None
        self.robots_txt_ua = "Googlebot"
        self.gfrobots = GFlareRobots('', self.settings.get("USER_AGENT", ''))
        self.robots_txt_status = None

        self.spider_links = "Spider" in self.settings.get("MODE", "")
        
        if self.robots_txt_status == "BLOCKED" and 'respect_robots_txt' in self.settings.get('CRAWL_ITEMS', ''):
            self.spider_links = False

        self.extraction_separator = self.settings.get(
            'EXTRACTION_SEPARATOR', '; ')

        self.xpath_mapping = {
            'canonical_tag': '/html/head/link[@rel="canonical"]/@href',
            'hreflang': '/html/head/link[@rel="alternate"]/@href',
            'pagination': '/html/head/link[@rel="next"]/@href|//link[@rel="prev"]/@href',
            'images': '//img/@src',
            'stylesheets': '//link[@rel="stylesheet"]/@href',
            'javascript': '//script/@src',
            'h1': '//h1/text()',
            'h2': '//h2/text()',
            'page_title': '/html/head/title/text()',
            'meta_description': '/html/head/meta[@name="description"]/@content'
        }

        self.xpath_link_extraction = self.get_link_extraction_xpath()

        self.exclusions_regex = self.exclusions_to_regex(
            self.settings.get('EXCLUSIONS', []))

    def timing(f):
        @wraps(f)
        def wrap(*args, **kw):
            ts = time()
            result = f(*args, **kw)
            te = time()
            print(f'func:{f.__name__} took: {te - ts}')
            return result
        return wrap

    def set_response(self, response):
        self.response = response
        # requests.get() encodes spaces within the path with %25
        # If we encode the path beforehand, request.get() will double encode the path again resulting in the generation of endless new urls
        # we need to decode the path back to what it was before request.get()
        # encoded it
        self.url = self.url_components_to_str(
            self.parse_url(self.unencode_url(self.response.url)))

        if self.is_robots_txt():
            self.response_to_robots_txt()

    def response_to_robots_txt(self):
        if self.response.status_code == 200:
            self.robots_txt = self.response.text
            self.gfrobots.set_robots_txt(
                self.robots_txt, user_agent=self.settings.get("USER_AGENT", ''))
            self.robots_txt_ua = self.gfrobots.get_short_ua(
                self.settings.get("USER_AGENT", ''))

    def get_initial_url(self):
        if len(self.response.history) == 0:
            return str(self.response.url).strip()
        return str(self.response.history[0].url).strip()

    def get_link_extraction_xpath(self):

        xpaths = []
        xpaths.append('//a/@href')

        crawl_items = self.settings['CRAWL_ITEMS']

        if 'canonical_tag' in crawl_items:
            xpaths.append(self.xpath_mapping['canonical_tag'])
        if 'hreflang' in crawl_items:
            xpaths.append(self.xpath_mapping['hreflang'])
        if 'pagination' in crawl_items:
            xpaths.append(self.xpath_mapping['pagination'])
        if 'images' in crawl_items:
            xpaths.append(self.xpath_mapping['images'])
        if 'stylesheets' in crawl_items:
            xpaths.append(self.xpath_mapping['stylesheets'])
        if 'javascript' in crawl_items:
            xpaths.append(self.xpath_mapping['javascript'])

        return '|'.join(xpaths)

    # @timing
    def get_data(self):

        self.url_components = urllib.parse.urlsplit(self.url)
        d = {'url': self.url}
        d['data'] = self.get_header_info()

        if len(self.response.content) > 0:
            self.tree = self.get_tree()
            if self.spider_links:
                d['links'] = self.extract_links()
            d['data'] = {**d['data'], **self.get_crawl_data()}

        d['data'] = {**d['data'], **{'crawl_status': self.get_full_status(self.url, d['data'])}}

        d['data'] = [self.dict_to_row(d['data'])]

        if self.has_redirected():
            d['data'] += self.get_redirects()

        return d

    # @timing
    def get_tree(self):
        try:
            # We need to use page.content rather than page.text because
            # html.fromstring implicitly expects bytes as input.
            return fromstring(self.response.content)
        except Exception as e:
            print("Error parsing", self.url, "with lxml")
            print(e)

    def parse_url(self, url):
        try:
            scheme, netloc, path, query, frag = urllib.parse.urlsplit(
                url.strip())
        except:
            print(f'Error parsing {url}')
            return {"scheme": '', "netloc": '', "path": '', "query": '', "frag": ''}
        if not scheme and not netloc:
            # Hack needed as non RFC tel references are not detected by
            # urlsplit
            if path.startswith("tel:"):
                path.replace("tel:", "")
                scheme = "tel"
            else:
                absolute_url = urllib.parse.urljoin(self.url, url)
                scheme, netloc, path, query, frag = urllib.parse.urlsplit(
                    absolute_url)
        if ':' in netloc:
            if scheme == 'https' and ':443' in netloc:
                netloc = netloc.replace(':443', '')
            elif scheme == 'http' and ':80' in netloc:
                netloc = netloc.replace(':80', '')

        return {"scheme": scheme, "netloc": netloc, "path": path.strip(), "query": query, "frag": frag}

    def url_components_to_str(self, comp):
        url = str(urllib.parse.urlunsplit(
            (comp["scheme"], comp["netloc"], comp["path"], comp["query"], "")))
        if comp['path'] == '':
            url += '/'
        return url

    def unencode_url(self, url):
        parsed = self.parse_url(url)
        parsed["path"] = urllib.parse.unquote(parsed["path"])
        return self.url_components_to_str(parsed)

    def get_domain(self, url):
        domain = self.parse_url(url)["netloc"]
        if "www." in domain:
            return domain.replace("www.", "")
        return domain

    def get_robots_txt_url(self, url):
        comps = self.parse_url(url)
        comps["path"] = "robots.txt"
        return self.url_components_to_str(comps)

    def is_external(self, url):
        if self.settings.get("ROOT_DOMAIN", "") == "":
            return False
        return self.get_domain(url) != self.settings.get("ROOT_DOMAIN", "")

    def is_excluded(self, url):
        if self.exclusions_regex:
            return bool(match(self.exclusions_regex, url))
        return False

    def exclusions_to_regex(self, exclusions):

        rules = []

        for exclusion in exclusions:
            operator, value = exclusion

            if operator == 'Equal to (=)':
                value = escape(value)
                rules.append(f"^{value}$")
            elif operator == 'Contain':
                value = escape(value)
                rules.append(f".*{value}.*")
            elif operator == 'Start with':
                value = escape(value)
                rules.append(f"^{value}.*")
            elif operator == 'End with':
                value = escape(value)
                rules.append(f".*{value}$")
            elif operator == 'Regex match':
                rules.append(value)

        return '|'.join(rules)

    def is_robots_txt(self, url=None):
        if not url:
            url = self.url

        if self.is_external(url):
            return False
        return self.parse_url(url)["path"] == "/robots.txt"

    def get_final_url(self):
        return self.url_components_to_str(self.parse_url(self.response.url))

    def get_text(self):
        return self.response.text

    def get_canonical_http_header(self):
        header = self.response.headers.get("Link", "")
        if "rel=" in header:
            return header.split(";")[0].replace("<", "").replace(">", "")
        return ""

    def get_header_info(self):
        header = {
            'url': self.url,
            'status_code': self.response.status_code,
            'content_type': self.response.headers.get('content-type', ''),
            'robots_txt': self.get_robots_txt_status(self.url),
            'x_robots_tag': self.response.headers.get('x-robots-tag', ''),
            'canonical_http': self.get_canonical_http_header()
        }
        return header

    def valid_url(self, components):
        if not "http" in components['scheme']:
            return False

        url = self.url_components_to_str(components)

        if ' ' in url:
            return False

        # Filter out external links if needed
        if "external_links" not in self.settings.get("CRAWL_ITEMS", "") and self.is_external(url):
            return False

        if self.is_excluded(url):
            return False

        # Do not check and report on on-page links
        if "check_blocked_urls" not in self.settings.get("CRAWL_ITEMS", "") and self.allowed_by_robots_txt(url) == False:
            return False
        return True

    # @timing
    def extract_links(self):
        parsed_links = [self.parse_url(l) for l in self.extract_xpath(
            self.xpath_link_extraction)]
        links = list(set([self.url_components_to_str(l)
                          for l in parsed_links if self.valid_url(l)]))
        return links

    def get_txt_by_selector(self, selector, method="css", get="txt"):
        try:
            if method == "css":
                tree_result = self.tree.cssselect(selector)
            elif method == "xpath":
                tree_result = self.tree.xpath(selector)
            else:
                pass

            txt = ""

            if len(tree_result) > 0:
                if get == "href":
                    txt = tree_result[0].attrib['href']
                elif get != "txt":
                    txt = tree_result[0].get(get)
                else:
                    txt = tree_result[0].text_content()

            if txt == None:
                return ""

            return ' '.join(txt.split())

        except:
            print(f"{selector} failed")
            return ""

    def extract_onpage_elements(self):
        d = {}
        if 'h1' in self.all_items:
            d['h1'] = self.extraction_separator.join(
                self.clean_list(self.extract_xpath(self.xpath_mapping['h1'])))

        if 'h2' in self.all_items:
            d['h2'] = self.extraction_separator.join(
                self.clean_list(self.extract_xpath(self.xpath_mapping['h2'])))

        if 'page_title' in self.all_items:
            d['page_title'] = self.extraction_separator.join(
                self.clean_list(self.extract_xpath(self.xpath_mapping['page_title'])))

        if 'meta_description' in self.all_items:
            d['meta_description'] = self.extraction_separator.join(
                self.clean_list(self.extract_xpath(self.xpath_mapping['meta_description'])))

        return d

    def extract_directives(self):
        d = {}
        if 'canonical_tag' in self.all_items:
            canonicals = self.extract_xpath(
                self.xpath_mapping['canonical_tag'])
            if len(canonicals) > 0:
                d['canonical_tag'] = canonicals[0]
            else:
                d['canonical_tag'] = ''

        if 'canonical_http_header' in self.all_items:
            d['canonical_http_header'] = self.get_canonical_http_header()

        if 'meta_robots' in self.all_items:
            all_fields = self.get_meta_name_fields()
            matching_ua = [f for f in all_fields if f.lower()
                           in self.robots_txt_ua.lower()]
            rules = []

            if len(matching_ua) > 0:
                ua = matching_ua[0]
                rules = self.extract_xpath(f'//meta[@name="{ua}"]/@content')

            rules += self.extract_xpath('//meta[@name="robots"]/@content')

            d['meta_robots'] = ', '.join(rules)

        return d

    def custom_extractions(self):

        for extraction_name, selector, value in self.settings.get('EXTRACTIONS', []):
            if selector == 'CSS Selector':
                return {extraction_name: self.get_txt_by_selector(value, method='css', get='txt')}
            elif selector == 'XPath':
                return {extraction_name: self.extraction_separator.join(self.clean_list(self.extract_xpath(value)))}
            else:
                print('WARNING: regex extraction is not implemented yet')
                return {extraction_name: ''}

        return {}

    def get_crawl_data(self):
        return {**self.extract_onpage_elements(), **self.extract_directives(), **self.custom_extractions()}

    def is_canonicalised(self, url, canonical):
        if not canonical:
            return False
        if self.url_components_to_str(self.parse_url(canonical)) != self.url_components_to_str(self.parse_url(url)):
            return True
        return False

    def get_full_status(self, url, seo_items):
        status = []

        # Evaluate status code
        try:
            code_description = status_codes._codes[
                seo_items['status_code']][0].replace('_', ' ')
        except KeyError:
            code_description = 'non-standard response'
        status.append(code_description)

        # Check against X-Robots
        # No checking against User-Agents is done
        # As the following setup can not be evaluated:
        # X-Robots-Tag: bingbot: noindex
        # X-Robots-Tag: nofollow, nosnippet
        # response.headers['X-Robots-Tag'] would return a combined result
        # 'X-Robots-Tag': 'bingbot: noindex, nofun, norisk, nofollow, nosnippet'
        # Which CANNOT be deconstructed again
        # This is actually compliant to RFC2616
        # https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html#sec4.2
        if 'noindex' in seo_items.get('x_robots_tag', ''):
            status.append('blocked by x-robots-tag')

        # Check against robots.txt
        if 'blocked' in seo_items.get('robots_txt', ''):
            status.append('blocked by robots.txt')

        # Check against meta robots.txt
        if 'noindex' in seo_items.get('meta_robots', ''):
            status.append('noindex')

        # Canonical Tag
        if self.is_canonicalised(url, seo_items.get('canonical_tag', '')):
            status.append('canonicalised')

        # Canonical Header
        if self.is_canonicalised(url, seo_items.get('canonical_http_header', '')):
            status.append('header canonicalised')

        # Avoid ok, blocked by robots.txt and show blocked by robots.txt
        # instead
        if len(status) != 1 and status[0] == 'ok':
            status.pop(0)

        return ', '.join(status)

    def get_meta_name_fields(self):
        fields = []
        try:
            fields = self.tree.xpath('//meta/@name')
        except:
            pass
        return fields

    def dict_to_row(self, data):
        out = tuple(data.get(item, "") for item in self.all_items)
        return out

    def has_redirected(self):
        return len(self.response.history) > 0

    # @timing
    def get_redirects(self):
        data = []
        hist = self.response.history

        if len(hist) > 0:
            for i in range(len(hist)):
                hob_url = self.url_components_to_str(
                    self.parse_url(hist[i].url))

                if 'external_links' not in self.settings.get('CRAWL_ITEMS', ''):
                    if self.is_external(hob_url):
                        break

                robots_status = self.get_robots_txt_status(hob_url)
                if 'respect_robots_txt' in self.settings.get('CRAWL_ITEMS', '') and 'follow_blocked_redirects' not in self.settings.get('CRAWL_ITEMS', '') and robots_status == 'blocked':
                    continue

                if i + 1 < len(hist):
                    redirect_to_url = self.url_components_to_str(
                        self.parse_url(str(hist[i + 1].url).strip()))
                else:
                    redirect_to_url = self.get_final_url()

                hob_data = {"url": hob_url, "content_type": hist[i].headers.get('Content-Type', ""), 'status_code': hist[i].status_code, 'x_robots_tag': hist[
                    i].headers.get('X-Robots-Tag', ''), 'redirect_url': redirect_to_url, 'robots_txt': robots_status}

                hob_data['crawl_status'] = self.get_full_status(
                    hob_url, hob_data)
                hob_row = self.dict_to_row(hob_data)

                data.append(hob_row)

        return data

    def allowed_by_robots_txt(self, url):
        return self.gfrobots.is_allowed(url)

    def get_robots_txt_status(self, url):
        if self.allowed_by_robots_txt(url):
            return "allowed"
        return "blocked"

    def attrib_to_list(self, xpath, attrib):
        try:
            return [self.url_components_to_str(self.parse_url(l.attrib[attrib])) for l in self.tree.xpath(xpath)]
        except:
            return []

    def extract_xpath(self, path):
        try:
            return self.tree.xpath(path)
        except:
            return []

    def clean_list(self, inp):
        try:
            return [' '.join(i.split()) for i in inp if i.strip()]
        except Exception as e:
            print(f'ERROR: cleaning list {inp} failed!')
            return inp

    def get_hreflang_links(self):
        return self.extract_xpath(self.xpath_mapping['hreflang'])

    def get_canonical_links(self):
        return self.extract_xpath(self.xpath_mapping['canonical_tag'])

    def get_pagination_links(self):
        return self.extract_xpath(self.xpath_mapping['pagination'])
