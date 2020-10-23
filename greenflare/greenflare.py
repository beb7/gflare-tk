import tkinter as tk
from tkinter import ttk, Menu, filedialog as fd, messagebox, TclError
from core.gflarecrawler import GFlareCrawler
from core.defaults import Defaults
from widgets.crawltab import CrawlTab
from widgets.settingstab import SettingsTab
from widgets.exclusionstab import ExclusionsTab
from widgets.extractionstab import ExtractionsTab
from widgets.listcrawl import ListModeWindow
from widgets.progresswindow import ProgressWindow
from widgets.aboutwindow import AboutWindow
from concurrent import futures
import functools
from threading import Lock
from os import path, remove
from pathlib import Path
import sys
import argparse

class mainWindow(ttk.Frame):
	def __init__(self, crawler=None):
		ttk.Frame.__init__(self)

		self.crawler = crawler
		self.executor = futures.ThreadPoolExecutor(max_workers=1)
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
		self.filemenu.add_command(label="Export View", command=self.export_view)
		self.menubar.add_cascade(label="File", menu=self.filemenu)

		self.modemenu = Menu(self.menubar, tearoff=0)
		self.modemenu.add_command(label="Spider", command=self.spider_mode)
		self.modemenu.add_command(label="List", command=self.list_mode)
		self.menubar.add_cascade(label="Mode", menu=self.modemenu)

		self.aboutmenu = Menu(self.menubar, tearoff=0)
		self.aboutmenu.add_command(label="About", command=self.show_about)
		self.menubar.add_cascade(label="Help", menu=self.aboutmenu)

		root.config(menu=self.menubar)

	def daemonize(title=None, msg=None, callbacks=None):
		def decorator(target):
			@functools.wraps(target)
			def wrapper(*args, **kwargs):

				args[0].win_progress = ProgressWindow(title=title, msg=msg)
				args[0].win_progress.focus_force()
				args[0].win_progress.grab_set()

				result = args[0].executor.submit(target, *args, **kwargs)
				result.add_done_callback(args[0].daemon_call_back)

				if callbacks:
					for func in callbacks:
						result.add_done_callback(func)
				return result

			return wrapper

		return decorator

	def daemon_call_back(self, future):
		self.win_progress.grab_release()
		self.win_progress.destroy()
		exception = future.exception()
		if exception:
			raise exception

	def reset_ui(self):
		self.tab_crawl.reset()
		self.crawler.reset_crawl()
		self.master.title("Greenflare SEO Crawler")

	def load_crawl(self, db_file=None):
		files = [('Greenflare DB', '*.gflaredb'), ('All files', '.*')]

		if not db_file: db_file = fd.askopenfilename(filetypes=files)
		# Don't do anything if user does not select a file
		if not db_file: return

		self.crawler.load_crawl(db_file)

		if self.crawler.settings["MODE"] == "Spider": self.master.title(f"{self.crawler.settings['ROOT_DOMAIN']} - Greenflare SEO Crawler")
		elif self.crawler.settings["MODE"] == "List":
			self.tab_crawl.show_list_mode()

		self.update_gui()
		self.tab_crawl.freeze_input()
		self.tab_crawl.load_crawl_to_outputtable()
		self.tab_crawl.update_bottom_stats()


	def full_export(self):
		files = [('CSV files', '*.csv')]
		export_file = fd.asksaveasfilename(filetypes=files)

		# Don't do anything if no file is being selected
		if not export_file:
			return

		self.export_to_csv(export_file)

	def export_view(self):
		files = [('CSV files', '*.csv')]
		export_file = fd.asksaveasfilename(filetypes=files)

		# Don't do anything if no file is being selected
		if not export_file:
			return

		self.export_to_csv(export_file, filters=self.tab_crawl.filters)		

	def show_export_completed_msg(self):
		messagebox.showinfo(title='Export completed', message=f'All data has been successfully exported!')

	@daemonize(title="Exporting crawl ...", msg="Exporting to CSV, that might take a while ...", callbacks=[show_export_completed_msg])
	def export_to_csv(self, filename, filters=None):
		if not filename.endswith(".csv"):
			 filename += ".csv"
		if path.isfile(filename):
			remove(filename)

		db = self.crawler.connect_to_db()
		db.to_csv(filename, columns=self.crawler.columns, filters=filters)
		db.close()

	def spider_mode(self):
		self.crawler.settings['MODE'] = 'Spider'
		self.tab_crawl.reset()

	def list_mode(self):
		lm_wnd = ListModeWindow(crawler=self.crawler, crawl_tab=self.tab_crawl, root=self.master)

	def show_about(self):
		AboutWindow()

	def update_gui(self):
		self.tab_crawl.update()
		self.tab_settings.update()
		self.tab_exclusions.update()
		self.tab_extractions.update()

	def on_closing(self):
		self.crawler.end_crawl_gracefully()
		self.master.destroy()

	def open_file_on_macos(self, *args):
		for f in args:
			if f.endswith('.gflaredb'): self.load_crawl(db_file=f)
			break

if __name__ == "__main__":
	
	# Check if Greenflare has been launched as part of a binary bundle as this impacts the working_dir
	if getattr(sys, 'frozen', False):
		Defaults.set_working_dir(path.dirname(sys.executable))
	else:
		Defaults.set_working_dir(path.dirname(path.realpath(__file__)))

	# Linux specific settings
	if sys.platform == 'linux':

		import importlib
		check = importlib.util.find_spec("ttkthemes")

		# Use arc theme if available
		if check:
			from ttkthemes import ThemedTk
			root = ThemedTk(theme=Defaults.linux_theme)
		else:
			root = tk.Tk()

		# This ugly step is needed to initialise the filemanager variables we are setting below
		try:
			root.tk.call('tk_getOpenFile', '-foobarbaz')
		except TclError:
			pass

		# Disable hidden files in file dialogues by default but show option to show them
		root.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
		root.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')

	else:
		root = tk.Tk()

	root.geometry("1024x768")
	# macOS tkinter cannot handle iconphotos at the time being, disabling it for now
	if sys.platform != "darwin":
		root.iconphoto(False, tk.PhotoImage(file=Defaults.root_icon()))

	globalLock = Lock()
	crawl_items = Defaults.crawl_items
	Settings  = Defaults.settings
	Crawler = GFlareCrawler(settings=Settings, gui_mode=True, lock=globalLock)

	app = mainWindow(crawler=Crawler)
	
	# running on macOS
	if sys.platform == "darwin":
		# Use TK's Apple Event Handler to react to clicked/open documents
		root.createcommand("::tk::mac::OpenDocument", app.open_file_on_macos)

	# Parse and load db file if provided
	parser = argparse.ArgumentParser()
	parser.add_argument("file_path", type=Path, nargs='*')

	p = parser.parse_args()

	if p.file_path and p.file_path[0].exists():
		app.load_crawl(db_file=p.file_path[0])

	root.protocol("WM_DELETE_WINDOW", app.on_closing)
	root.mainloop()