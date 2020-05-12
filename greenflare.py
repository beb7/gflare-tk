import tkinter as tk
from tkinter import Frame, ttk
from core.gflarecrawler import GFlareCrawler
from widgets.crawltab import CrawlTab
from threading import Lock
from os import path
import sys


class mainWindow(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		self.tab_parent = ttk.Notebook()
		self.tab_crawl = CrawlTab(crawler)

		self.tab_parent.add(self.tab_crawl, text="Crawl")
		self.tab_parent.pack(expand=1, fill="both")
		self.master.title("Greenflare SEO Crawler")

if __name__ == "__main__":
	if getattr(sys, 'frozen', False): WorkingDir = path.dirname(sys.executable)
	else: WorkingDir = path.dirname(path.realpath(__file__))

	root = tk.Tk()
	root.geometry("1024x768")
	root.iconphoto(False, tk.PhotoImage(file=WorkingDir + path.sep + 'greenflare-icon-64x64.png'))
	globalLock = Lock()
	Settings  = {"MODE": "Spider", "THREADS": 5, "URLS_PER_SECOND": 15, "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36", "UA_SHORT": "Windows Chrome", "MAX_RETRIES": 3, "CRAWL_ITEMS": ["indexability", "h1", "h2","page_title", "meta_description", "canonical_tag", "robots_txt", "meta_robots", "x_robots_tag", "unique_inlinks"]}
	Crawler = GFlareCrawler(settings=Settings, gui_mode=True, lock=globalLock)

	app = mainWindow(Crawler)
	root.mainloop()
