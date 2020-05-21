import tkinter as tk
from tkinter import Frame, ttk, Menu, filedialog as fd
from core.gflarecrawler import GFlareCrawler
from widgets.crawltab import CrawlTab
from widgets.settingstab import SettingsTab
from widgets.exclusionstab import ExclusionsTab
from widgets.extractionstab import ExtractionsTab
from threading import Lock
from os import path
import sys


class mainWindow(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		
		self.crawler = crawler
		print(self.crawler.settings)
		self.tab_parent = ttk.Notebook()
		self.tab_crawl = CrawlTab(crawler)
		self.tab_settings = SettingsTab(crawler)
		self.tab_exclusions = ExclusionsTab(crawler)
		self.tab_extractions = ExtractionsTab(crawler)

		self.tab_parent.add(self.tab_crawl, text="Crawl")
		self.tab_parent.add(self.tab_settings, text="Settings")
		self.tab_parent.add(self.tab_exclusions, text="Exclusions")
		self.tab_parent.add(self.tab_extractions, text="Extractions")
		self.tab_parent.pack(expand=1, fill="both")
		self.master.title("Greenflare SEO Crawler")

		self.menubar = Menu(self)

		self.filemenu = Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label="Load Crawl", command=self.load_crawl)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Full Export", command=self.full_export)
		self.menubar.add_cascade(label="File", menu=self.filemenu)

		self.modemenu = Menu(self.menubar, tearoff=0)
		self.modemenu.add_command(label="Spider", command=self.spider_mode)
		self.modemenu.add_command(label="List", command=self.list_mode)
		self.menubar.add_cascade(label="Mode", menu=self.modemenu)

		self.aboutmenu = Menu(self.menubar, tearoff=0)
		self.aboutmenu.add_command(label="About", command=self.show_about)
		self.menubar.add_cascade(label="Help", menu=self.aboutmenu)

		root.config(menu=self.menubar)


	def load_crawl(self):
		files = [('Greenflare DB', '*.gflaredb'), ('All files', '.*')]
		db_file = fd.askopenfilename(filetypes=files)
		if not db_file: return
		self.crawler.load_crawl(db_file)
		print(self.crawler.settings)

		if self.crawler.settings["MODE"] == "Spider": self.spider_mode()
		elif self.crawler.settings["MODE"] == "List": self.list_mode()

		self.update_gui()

	def full_export(self):
		pass

	def spider_mode(self):
		pass

	def list_mode(self):
		pass

	def show_about(self):
		pass

	def update_gui(self):

		self.master.title(f"{self.crawler.settings['ROOT_DOMAIN']} - Greenflare SEO Crawler")

		self.tab_crawl.update()
		self.tab_settings.update()
		self.tab_exclusions.update()
		self.tab_extractions.update()
		
if __name__ == "__main__":
	if getattr(sys, 'frozen', False): WorkingDir = path.dirname(sys.executable)
	else: WorkingDir = path.dirname(path.realpath(__file__))

	root = tk.Tk()
	root.geometry("1024x768")
	root.iconphoto(False, tk.PhotoImage(file=WorkingDir + path.sep + 'greenflare-icon-64x64.png'))

	globalLock = Lock()
	columns = [("url", "TEXT type UNIQUE"), ("content_type" , "TEXT"), ("status_code", "INT"), ("indexability", "TEXT"), ("h1", "TEXT"), ("h2", "TEXT"), ("page_title", "TEXT"), ("meta_description", "TEXT"), ("canonical_tag", "TEXT"), ("robots_txt", "TEXT"), ("redirect_url", "TEXT"), ("meta_robots", "TEXT"), ("x_robots_tag", "TEXT"), ("unique_inlinks", "INT")]
	crawl_items = [t[0] for t in columns]
	Settings  = {"MODE": "Spider", "THREADS": 5, "URLS_PER_SECOND": 15, "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36", "UA_SHORT": "Windows Chrome", "MAX_RETRIES": 3, "CRAWL_ITEMS": crawl_items}
	Crawler = GFlareCrawler(settings=Settings, gui_mode=True, lock=globalLock, columns=columns)

	app = mainWindow(crawler=Crawler)
	root.mainloop()
