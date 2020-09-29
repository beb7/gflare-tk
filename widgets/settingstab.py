from tkinter import ttk, LEFT, W, E, NW, Checkbutton, StringVar
from .checkboxgroup import CheckboxGroup

class SettingsTab(ttk.Frame):
	def __init__(self, crawler=None):
		ttk.Frame.__init__(self)

		self.crawler = crawler

		"""
		First row
		"""
		self.frame_first = ttk.Frame(self)
		self.frame_first.grid(row=0, column=0, sticky=W, padx=10, pady=10)


		"""
		Crawler Group
		"""	
		self.group_crawler = ttk.LabelFrame(self.frame_first, text="Crawler")
		self.group_crawler.grid(row=0, column=0, sticky=W, padx=10, pady=10)

		self.label_threads =  ttk.Label(self.group_crawler, text="Threads")
		self.label_threads.grid(row=0, column=0, sticky=W)

		self.spinbox_threads = ttk.Spinbox(self.group_crawler, from_=1, to=100, state="readonly", width=5, command=self.save_threads)
		self.spinbox_threads.set("5")
		self.spinbox_threads.grid(row=0, column=1, padx=15, pady=5, sticky=E)

		self.label_urls = ttk.Label(self.group_crawler, text="URLs/s")
		self.label_urls.grid(row=1, column=0, sticky=W)

		self.spinbox_urls = ttk.Spinbox(self.group_crawler, from_=0, to=100, state="readonly", width=5, command=self.save_urls)
		self.spinbox_urls.set("15")
		self.spinbox_urls.grid(row=1, column=1, padx=15, pady=5, sticky=E)

		self.label_ua = ttk.Label(self.group_crawler, text="User-Agent")
		self.label_ua.grid(row=3, column=0, sticky=W)
        
		self.user_agents = {"Greenflare": "Greenflare SEO Crawler/1.0",
		"Windows Chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36", 
		"Macintosh Chrome": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36",
		"Googlebot Desktop": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
		"Googlebot Mobile": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
		"Bingbot Desktop": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
		"Bingbot Mobile": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Mobile Safari/537.36 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
		}

		self.ua_names = [k for k in self.user_agents.keys()]
		self.combobox_ua = ttk.Combobox(self.group_crawler, values=self.ua_names, state="readonly")
		self.combobox_ua.bind("<<ComboboxSelected>>", self.save_ua)
		self.combobox_ua.current(0)
		self.combobox_ua.grid(row=3, column=1, padx=15, pady=5, sticky=E)

		self.group_network = ttk.LabelFrame(self.frame_first, text="Proxy")
		self.group_network.grid(row=0, column=1, sticky=W, padx=10, pady=10)

		self.label_host = ttk.Label(self.group_network, text="Host")
		self.label_host.grid(row=0, column=0, sticky=W)

		self.var_host = StringVar()
		self.entry_host = ttk.Entry(self.group_network, textvariable=self.var_host, validatecommand=self.save_proxy, validate="focusout")
		self.entry_host.insert(0, "hostname/ip:port")
		self.entry_host.grid(row=0, column=1, sticky=E, padx=15, pady=5)
		
		self.label_user = ttk.Label(self.group_network, text="User")
		self.label_user.grid(row=1, column=0, sticky=W)

		self.var_user = StringVar()
		self.entry_user = ttk.Entry(self.group_network, textvariable=self.var_user, validatecommand=self.save_proxy, validate="focusout")
		self.entry_user.insert(0, "")
		self.entry_user.grid(row=1, column=1, sticky=E, padx=15, pady=5)
		
		self.label_password = ttk.Label(self.group_network, text="Password")
		self.label_password.grid(row=2, column=0, sticky=W)

		self.var_password = StringVar()
		self.entry_password = ttk.Entry(self.group_network, show="*", textvariable=self.var_password, validatecommand=self.save_proxy, validate="focusout")
		self.entry_password.insert(0, "")
		self.entry_password.grid(row=2, column=1, sticky=E, padx=15, pady=5)

		
		"""
		Second row
		"""
		self.frame_second = ttk.Frame(self)
		self.frame_second.grid(row=1, column=0, sticky=W, padx=10, pady=10)

		"""
		On-Page Group
		"""
		self.checkboxgroup_onpage = CheckboxGroup(self.frame_second, "On-Page", ["Indexability", "Page Title", "Meta Description", "H1", "H2"], self.crawler.settings, "CRAWL_ITEMS")
		self.checkboxgroup_onpage.grid(row=0, column=0, sticky=NW, padx=10, pady=10)

		"""
		Links Group
		"""
		self.checkboxgroup_links = CheckboxGroup(self.frame_second, "Links", ["Unique Inlinks", "External Links", "Canonicals", "Pagination", "Hreflang"], self.crawler.settings, "CRAWL_ITEMS")
		self.checkboxgroup_links.grid(row=0, column=1, sticky=NW, padx=10, pady=10)
		
		"""
		Directives Group
		"""
		self.checkboxgroup_directives = CheckboxGroup(self.frame_second, "Directives", ["Canonical Tag", "Canonical HTTP Header", "Meta Robots", "X-Robots-Tag"], self.crawler.settings, "CRAWL_ITEMS")
		self.checkboxgroup_directives.grid(row=0, column=2, sticky=NW, padx=10, pady=10)

		"""
		robots.txt Group
		"""
		self.checkboxgroup_robots_txt = CheckboxGroup(self.frame_second, "robots.txt", ["Respect robots.txt", "Report on status", "Check blocked URLs", "Follow blocked redirects"], self.crawler.settings, "CRAWL_ITEMS")
		self.checkboxgroup_robots_txt.grid(row=0, column=3, sticky=NW, padx=10, pady=10)

	def update(self):
		self.spinbox_threads.set(int(self.crawler.settings["THREADS"]))
		self.spinbox_urls.set(int(self.crawler.settings["URLS_PER_SECOND"]))
		self.combobox_ua.current()

	def save_threads(self):
		self.crawler.settings["THREADS"] = int(self.spinbox_threads.get())
	
	def save_urls(self):
		self.crawler.settings["URLS_PER_SECOND"] = int(self.spinbox_urls.get())

	def save_ua(self, e):
		value = self.combobox_ua.get()
		self.crawler.settings["USER_AGENT"] = self.user_agents[value]
		self.crawler.settings["UA_SHORT"] = value

	def save_proxy(self):
		self.crawler.settings["PROXY_HOST"] = self.var_host.get()
		self.crawler.settings["PROXY_USER"] = self.var_user.get()
		self.crawler.settings["PROXY_PASSWORD"] = self.var_password.get()