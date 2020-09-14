import tkinter as tk
from tkinter import Frame, ttk, Menu, filedialog as fd, messagebox
from core.gflarecrawler import GFlareCrawler
from widgets.crawltab import CrawlTab
from widgets.settingstab import SettingsTab
from widgets.exclusionstab import ExclusionsTab
from widgets.extractionstab import ExtractionsTab
from threading import Lock
from os import path, remove, environ
from pathlib import Path
import sys


class mainWindow(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		
		self.crawler = crawler
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
		self.filemenu.add_command(label="New", command=self.reset_ui)
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


	def reset_ui(self):
		self.tab_crawl.reset()

	def load_crawl(self):
		files = [('Greenflare DB', '*.gflaredb'), ('All files', '.*')]
		db_file = fd.askopenfilename(filetypes=files)
		if not db_file: return
		self.crawler.load_crawl(db_file)

		if self.crawler.settings["MODE"] == "Spider": self.spider_mode()
		elif self.crawler.settings["MODE"] == "List": self.list_mode()

		self.update_gui()

	def full_export(self):
		files = [('CSV files', '*.csv')]
		export_file = fd.asksaveasfilename(filetypes=files)
		if not export_file: return
		if not export_file.endswith(".csv"): export_file += ".csv"
		if path.isfile(export_file): remove(export_file)
		db = self.crawler.connect_to_db()
		db.to_csv(export_file, columns=self.crawler.columns)
		db.close()
		messagebox.showinfo(title='Export completed', message=f'All data has been successfully saved to {export_file}!')

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
	if getattr(sys, 'frozen', False): 
		WorkingDir = path.dirname(sys.executable)
		if sys.platform == "darwin":
			#environ['TK_LIBRARY'] = str(Path(WorkingDir).parent) + '/Resources/tk8.6/'
			#environ['TCL_LIBRARY'] = str(Path(WorkingDir).parent) + '/Resources/tcl8.6/'
			print(environ['TCL_LIBRARY'])
			print(environ['TK_LIBRARY'])
	else:
		WorkingDir = path.dirname(path.realpath(__file__))

	root = tk.Tk()
	root.geometry("1024x768")
	# root.iconphoto(False, tk.PhotoImage(file=WorkingDir + path.sep + 'greenflare-icon-64x64.png'))

	globalLock = Lock()
	crawl_items = ["url", "content_type", "status_code", "indexability", "page_title", "meta_description", "h1", "h2", "unique_inlinks", "canonicals", "canonical_tag", "robots_txt", "redirect_url", "meta_robots", "x_robots_tag", "respect_robots_txt", "report_on_status", "follow_blocked_redirects"]
	Settings  = {"MODE": "Spider", "THREADS": 5, "URLS_PER_SECOND": 15, "USER_AGENT": "Greenflare SEO Spider/1.0",
				 "UA_SHORT": "Greenflare", "MAX_RETRIES": 3, "CRAWL_ITEMS": crawl_items}
	Crawler = GFlareCrawler(settings=Settings, gui_mode=True, lock=globalLock)

	app = mainWindow(crawler=Crawler)
	root.mainloop()
