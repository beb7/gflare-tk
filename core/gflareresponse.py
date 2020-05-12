from lxml.html import fromstring
from .gflarerobots import GFlareRobots
import urllib.parse
# import grobots
import re

class GFlareResponse:
	def __init__(self, settings, essential_items=[ "url", "content_type", "status_code", "redirect_url"]):
		self.settings = settings
		self.essential_items = essential_items
		self.all_items = None
		self.response = None
		self.url = None
		self.url_components = None
		self.robots_txt_ua = "Googlebot"
		self.robots_txt = ""
		self.gfrobots = GFlareRobots(self.robots_txt)
		self.robots_txt_status = None
		
		self.spider_links = "Spider" in self.settings.get("MODE", "")
		if self.robots_txt_status == "BLOCKED": self.spider_links = False

		self.exclusions = None
		if bool(self.settings.get("EXCLUSIONS", False)):
			self.exclusions = re.compile(self.settings["EXCLUSIONS"])

		self.extractions = self.settings.get("EXTRACTIONS", {})

		self.CHECK_REDIRECTS_BLOCKED_BY_ROBOTS = False
		self.CHECK_NOFOLLOW = False

		self.data = None

	def get_all_items(self):
		items = self.essential_items + self.settings.get("CRAWL_ITEMS", []) + self.settings.get("CUSTOM_ITEMS", []) + self.settings.get("CRAWL_DIRECTIVES", [])
		if "report_on_status" in self.settings.get("ROBOTS_SETTINGS", ""): items += ["robots_txt"]
		return items

	def set_response(self, response):
		self.response = response
		self.data = {}
		self.all_items = self.get_all_items()
		self.url = self.get_initial_url()

	def response_to_robots_txt(self, response):
		self.data["data"] = self.get_header_info()
		self.settings["ROOT_DOMAIN"] = self.get_domain(self.url)
		if self.data["data"]["status_code"] == 200:
			self.robots_txt = self.response.text
			self.gfrobots.set_robots_txt(self.robots_txt)

	def get_initial_url(self):
		if len(self.response.history) == 0:
			return str(self.response.url).strip()
		return str(self.response.history[0].url).strip()

	def get_data(self):
		if not self.response: return {}

		self.url = self.get_initial_url()
		self.url_components = urllib.parse.urlsplit(self.url)
		self.data = {"url": self.url}

		if self.is_robots_txt(self.url):
			self.response_to_robots_txt(self.response)

		else:			
		
			if len(self.response.content) > 0:
				self.tree = self.get_tree()
				if self.spider_links:
					self.data["links"] = self.extract_links()
					if "hreflang" in self.settings.get("CRAWL_LINKS", ""): self.data["hreflang_links"] = self.get_hreflang_links()
					if "canonicals" in self.settings.get("CRAWL_LINKS", ""): self.data["canonical_links"] = self.get_canonical_links()
					if "pagination" in self.settings.get("CRAWL_LINKS", ""): self.data["pagination_links"] = self.get_pagination_links()
				self.data["data"] = self.get_crawl_data()
			else:
				self.data["data"] = self.get_header_info()

			if self.has_redirected(): self.data["redirects"] = self.process_redirects()

		d = self.data.copy()
		d["data"] = [self.dict_to_row(self.data["data"])]
		return d

	def get_tree(self):
		try:
			# We need to use page.content rather than page.text because html.fromstring implicitly expects bytes as input.
			return fromstring(self.response.content)
		except Exception as e:
			print("Error parsing", self.url, "with lxml")
			print(e)
	
	# def set_robots_txt(self, robots_txt):
	# 	self.robots_txt = robots_txt

	def parse_url(self, url):
		scheme, netloc, path, query, frag = urllib.parse.urlsplit(url)
		if not scheme and not netloc:
			# Hack needed as non RFC tel references are not detected by urlsplit  
			if path.startswith("tel:"):
				path.replace("tel:", "")
				scheme = "tel"
			else:
				joined_url = urllib.parse.urljoin(self.url, url)
				scheme, netloc, path, query, frag = urllib.parse.urlsplit(joined_url)

		args = urllib.parse.parse_qsl(query)
		query = urllib.parse.urlencode(args)
		path = urllib.parse.quote_plus(path, safe="/+|;")
		return {"scheme": scheme, "netloc": netloc, "path": path, "query": query, "frag": frag}

	def url_components_to_str(self, comp):
		return str(urllib.parse.urlunsplit((comp["scheme"], comp["netloc"], comp["path"], comp["query"], "")))

	def get_domain(self, url=None):
		domain = self.parse_url(url)["netloc"]
		if "www." in domain:
			return domain.replace("www.", "")
		return domain

	def get_robots_txt_url(self, url):
		comps = self.parse_url(url)
		comps["path"] = "robots.txt"
		return self.url_components_to_str(comps)

	def is_external(self, url):
		if self.settings.get("ROOT_DOMAIN", "") == "": return False
		return self.get_domain(url) != self.settings.get("ROOT_DOMAIN", "")

	def is_excluded(self, url):
		return bool(re.match(self.exclusions, url))

	def is_robots_txt(self, url):
		if self.is_external(url): return False
		return self.parse_url(url)["path"] == "/robots.txt"

	def get_final_url(self):
		return str(self.response.url).strip()

	def get_text(self):
		return self.response.text

	def get_canonical_http_header(self):
		header = self.response.headers.get("Link", "")
		if "rel=" in header:
			return header.split(";")[0].replace("<", "").replace(">", "")
		return ""
	
	def get_header_info(self):
		return {"url": self.url, "status_code": self.response.status_code, "content_type": self.response.headers.get("content-type", ""), "robots_txt": self.get_robots_txt_status(self.url), "x_robots_tag": self.response.headers.get("x_robots_tag", ""), "canonical_http": self.get_canonical_http_header()}
	
	def extract_links(self):
		links = self.tree.cssselect('a')

		valid_links = []
		
		for link in links:
			if 'href' in link.attrib:
				if 'rel' in link.attrib:
					if self.CHECK_NOFOLLOW == False:
						if "nofollow" in link.attrib["rel"]:
							continue
			
				onpage_url = link.attrib['href'].strip()
				onpage_url_components = self.parse_url(onpage_url)
				onpage_url = self.url_components_to_str(onpage_url_components)

				# Do not crawl schemes like tel:
				# Do crawl urls such as news/april
				if "http" not in onpage_url_components["scheme"]:
					continue

				if "external_links" not in self.settings.get("CRAWL_LINKS", ""):
					if self.get_domain(onpage_url) != "":
						if self.is_external(onpage_url):
							continue				

				# Avoid duplicate URLs
				if onpage_url in valid_links:
					continue

				if bool(self.exclusions) == True:
					if self.is_excluded(onpage_url) == True:
						continue

				# Do not check and report on on-page links 
				if "check_blocked_urls" not in self.settings.get("ROBOTS_SETTINGS", ""):
					if self.allowed_by_robots_txt(onpage_url) == False:
						continue

				if " " in onpage_url:
					print("Critical flaw in parsing URL see below")
					print(link.attrib['href'])
					print(onpage_url_components)
					print(onpage_url)

				valid_links.append(onpage_url)

		return valid_links
	
	def get_txt_by_selector(self, selector, method="css", get="txt"):
		try:
			if method == "css": tree_result = self.tree.cssselect(selector)
			elif method == "xpath": tree_result = self.tree.xpath(selector)
			else: pass

		except:
			print(f"{selector} failed")
			return ""
		
		txt = ""

		if len(tree_result) > 0:
			if get == "href":
				txt = tree_result[0].attrib['href']
				# print(txt)

			elif get != "txt":
				txt = tree_result[0].get(get)
			else:
				txt = tree_result[0].text_content()
		
		if txt == None:
			return ""

		return txt.strip()

	def extract_onpage_elements(self):
		d = {}
		if "h1" in self.all_items: d["h1"] = self.get_txt_by_selector('h1')
		if "h2" in self.all_items: d["h2"] = self.get_txt_by_selector('h2')
		if "page_title" in self.all_items: d["page_title"] = self.get_txt_by_selector('title')
		if "meta_description" in self.all_items: d["meta_description"] = self.get_txt_by_selector('[name="description"]', get="content")
		return d

	def extract_directives(self):
		d = {}
		if "canonical_tag" in self.all_items: d["canonical_tag"] = self.get_txt_by_selector('link[rel="canonical"]', get="href")
		if "canonical_http_header" in self.all_items: d["canonical_http_header"] = self.get_canonical_http_header()
		if "meta_robots" in self.all_items: d["meta_robots"] = self.get_txt_by_selector('[name="robots"]', get="content")
		return d

	def custom_extractions(self):
		d = {}
		
		for extraction_name, settings in self.extractions.items():
			method = settings.get("selector", "")
			if method == "CSS Selector": method = "css"
			elif method == "XPath": method = "xpath"
			else: method = "regex" 

			d[extraction_name] = self.get_txt_by_selector(settings['value'], method=method, get="txt")

		return d

	def get_crawl_data(self):

		# if status_code == 200 and "text/html" in content_type and robots_txt_status == "ALLOWED":
		
		onpage_elements = self.extract_onpage_elements()
		directives = self.extract_directives()

		extraction = {**onpage_elements, **directives, **self.custom_extractions()}

		canonical_tag = extraction.get("canonical_tag", "")

		"""
		Indexability based on status codes:
		Indexable: 200 OK status codes
		Non-Idexable: Non 200 OK status codes
		"""

		indexability = "indexable"

		"""
		Indexability based on canonicals:
		Indexable: No canonical tag present
		
		Indexable: Root without trailing "/" equaling canonical tag with trailing "/"
		Example:	url: https://www.ayima.com		canonical tag: https://www.ayima.com/
		"""

		if canonical_tag != "" and canonical_tag != self.url and (self.url + "/") != canonical_tag:
			indexability = "non-indexable"

		"""
		Indexability based on meta robots
		If the comma separated list contains a noindex - non indexable
		"""
		if indexability == "indexable":
			meta_robots = extraction.get("meta_robots", "")
			if meta_robots != "":
				if "noindex" in meta_robots.lower().split(","):
					indexability = "non-indexable"

		extraction["indexability"] = indexability
		
		data = {**self.get_header_info(), **extraction}

		return data

	def dict_to_row(self, data):
		return tuple(data.get(item, "") for item in self.all_items)

	def has_redirected(self):
		return len(self.response.history) > 0

	def process_redirects(self):
		data = []
		hist = self.response.history

		if len(hist) > 0:
		
			for i in range(len(hist)):
				hob_url = str(hist[i].url).strip()

				if "external_links" not in self.settings.get("CRAWL_LINKS", ""):
					if self.is_external(hob_url):
						break
				
				robots_status = self.get_robots_txt_status(hob_url)
				if "respect_robots_txt" in self.settings.get("ROBOTS_SETTINGS", "") and "follow_blocked_redirects" not in self.settings.get("ROBOTS_SETTINGS", "") and robots_status == "blocked":
					continue

				if i + 1 < len(hist):
					redirect_to_url = str(hist[i + 1].url).strip()
				else:
					redirect_to_url = self.get_final_url()
					
				hob_data = {"url": hob_url, "content_type": hist[i].headers.get('Content-Type', ""), "status_code" : hist[i].status_code, "indexability": "non-indexable", "x_robots_tag": hist[i].headers.get('X-Robots-Tag', ""), "redirect_url": redirect_to_url, "robots_txt": robots_status}
				hob_row = self.dict_to_row(hob_data)

				data.append(hob_row)				

		return data
	
	def allowed_by_robots_txt(self, url):
		return self.gfrobots.is_allowed(url)
		# result = grobots.allowed_by_robots(self.robots_txt, self.robots_txt_ua, url)
		# return result[0]

	def get_robots_txt_status(self, url):
		if self.allowed_by_robots_txt(url): return "allowed"
		return "blocked"

	def attrib_to_list(self, xpath, attrib):
		try:
			return [self.url_components_to_str(self.parse_url(l.attrib[attrib])) for l in self.tree.xpath(xpath)]
		except:
			return []

	def get_hreflang_links(self):
		return self.attrib_to_list("//link[@rel='alternate']", "href")

	def get_canonical_links(self):
		return self.attrib_to_list("//link[@rel='canonical']", "href")

	def get_pagination_links(self):
		return self.attrib_to_list("//link[@rel='next']|//link[@rel='prev']", "href")