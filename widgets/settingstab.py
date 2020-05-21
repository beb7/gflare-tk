from tkinter import Frame, ttk, LEFT, W, E

class SettingsTab(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)

		self.crawler = crawler

		self.label_threads =  ttk.Label(self, text="Threads")
		self.label_threads.grid(row=0, column=0, sticky=W)

		self.spinbox_threads = ttk.Spinbox(self, from_=1, to=20, state="readonly", width=5, command=self.save_threads)
		self.spinbox_threads.set("5")
		self.spinbox_threads.grid(row=0, column=1, padx=15, pady=5, sticky=E)

		self.label_urls = ttk.Label(self, text="URLs/s")
		self.label_urls.grid(row=1, column=0, sticky=W)

		self.spinbox_urls = ttk.Spinbox(self, from_=0, to=100, state="readonly", width=5, command=self.save_urls)
		self.spinbox_urls.set("15")
		self.spinbox_urls.grid(row=1, column=1, padx=15, pady=5, sticky=E)

		self.label_ua = ttk.Label(self, text="User-Agent")
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
		self.combobox_ua = ttk.Combobox(self, values=self.ua_names, state="readonly")
		self.combobox_ua.current(0)
		self.combobox_ua.grid(row=3, column=1, padx=15, pady=5, sticky=E)

	def update(self):
		self.spinbox_threads.set(int(self.crawler.settings["THREADS"]))

	def save_threads(self):
		self.crawler.settings["THREADS"] = int(self.spinbox_threads.get())
	
	def save_urls(self):
		self.crawler.settings["URLS_PER_SECOND"] = int(self.spinbox_urls.get())

	def save_ua(self):
		value = self.combobox_ua.get()
		self.crawler.settings["USER_AGENT"] = self.user_agents[value]
		self.crawler.settings["UA_SHORT"] = value
