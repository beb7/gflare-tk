from tkinter import LEFT, RIGHT, ttk, W, NO, filedialog as fd, messagebox, StringVar
from widgets.progresswindow import ProgressWindow
from concurrent import futures
import functools
from os import path, remove
import queue
import sys

class CrawlTab(ttk.Frame):
	def __init__(self, crawler=None):
		ttk.Frame.__init__(self)
		self.crawler = crawler
		self.lock = crawler.lock

		self.executor = futures.ThreadPoolExecutor(max_workers=1)
		self.win_progress = None

		self.topframe = ttk.Frame(self)
		self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

		self.entry_url_input = ttk.Entry(self.topframe)
		self.entry_url_input.insert(0, "Enter URL to crawl")
		self.entry_url_input.bind('<Return>', self.enter_hit)
		self.entry_url_input.pack(side=LEFT, padx=(0, 20), expand=True, fill="x")

		self.button_crawl = ttk.Button(self.topframe, text="Start", command=self.btn_crawl_pushed)
		self.button_crawl.pack(side=LEFT, padx=(0, 20))

		# macOS and linux have issues with the below style so only use it on windows for now
		if sys.platform != "win32":
			self.progressbar = ttk.Progressbar(self.topframe, orient="horizontal", length=150, mode="determinate", maximum=100, value=0)
		elif sys.platform == "win32":
			self.style = ttk.Style(self)
			self.style.layout('text.Horizontal.TProgressbar', [('Horizontal.Progressbar.trough', {'children': [('Horizontal.Progressbar.pbar', {'side': 'left', 'sticky': 'ns'})], 'sticky': 'nswe'}), ('Horizontal.Progressbar.label', {'sticky': ''})])
			self.style.configure('text.Horizontal.TProgressbar', text='0 %')
			self.progressbar = ttk.Progressbar(self.topframe, orient="horizontal", length=150, mode="determinate", maximum=100, value=0, style='text.Horizontal.TProgressbar')
		
		self.progressbar.pack(side=LEFT, fill="x")
		
		self.middle_frame = ttk.Frame(self)
		self.middle_frame.pack(anchor='center', fill='y', expand=1)

		self.treeview_table = ttk.Treeview(self.middle_frame, selectmode="browse")

		self.scrollbar_vertical = ttk.Scrollbar(self.middle_frame, orient="vertical", command=self.treeview_table.yview)
		self.scrollbar_vertical.pack(side="right", fill="y")
		self.scrollbar_horizontal = ttk.Scrollbar(self.middle_frame, orient="horizontal", command=self.treeview_table.xview)
		self.scrollbar_horizontal.pack(side="bottom", fill="x")
		self.treeview_table.configure(yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=self.scrollbar_horizontal.set)
		self.treeview_table.pack(fill="both", expand=1)

		self.bottom_frame = ttk.Frame(self)
		self.bottom_frame.pack(anchor='center', padx=5, pady=5, fill='x')

		self.urls_string_var = StringVar()
		self.urls_string_var.set("Speed: - URL/s")
		self.label_urls_per_second = ttk.Label(self.bottom_frame, textvariable=self.urls_string_var)
		self.label_urls_per_second.pack(side=LEFT)

		self.urls_crawled_string_var = StringVar()
		self.urls_crawled_string_var.set("URLs crawled/discovered: 0/0")
		self.label_urls_crawled = ttk.Label(self.bottom_frame, textvariable=self.urls_crawled_string_var)
		self.label_urls_crawled.pack(side=RIGHT)

		self.populate_columns()
		self.row_counter = 1

	def daemonize(title=None, msg=None):
		def decorator(target):
			@functools.wraps(target)
			def wrapper(*args, **kwargs):
				args[0].win_progress = ProgressWindow(title=title, msg=msg)
				args[0].win_progress.focus_force()
				args[0].win_progress.grab_set()
				result = args[0].executor.submit(target, *args, **kwargs)
				result.add_done_callback(args[0].daemon_call_back)
				return result
	 
			return wrapper
	 
		return decorator
 
 
	def daemon_call_back(self, future):
		self.win_progress.grab_release()
		self.win_progress.window.destroy()
		exception = future.exception()
		if exception:
			raise exception

	def clear_output_table(self):
		# Clear table
		self.treeview_table.delete(*self.treeview_table.get_children())
		self.row_counter = 1

	def populate_columns(self):
		columns = ["url", "content_type", "indexability", "status_code", "h1", "page_title", "canonical_tag", "robots_txt", "redirect_url"]
		if self.crawler.columns: 
			columns = self.crawler.columns.copy()
			# if 'unique_inlinks' in columns: columns.remove('unique_inlinks')

		items = [i.title().replace("_", " ") for i in columns]
		items[items.index("Url")] = "URL"
		items[items.index("Redirect Url")] = "Redirect URL"

		self.treeview_table["columns"] = tuple(items)
		self.treeview_table.heading("#0", text="id", anchor=W)
		self.treeview_table.column("#0", width=75, stretch=True)
		for i in self.treeview_table["columns"]:
			self.treeview_table.heading(i, text=i, anchor=W)
			if "url" in i.lower():
				self.treeview_table.column(i, minwidth=250, width=400, stretch=True)
			else:
				self.treeview_table.column(i, width=100, stretch=False)

	def enter_hit(self, event=None):
		self.btn_crawl_pushed()
	
	def start_new_crawl(self, url):
		files = [('Greenflare DB', '*.gflaredb'), ('All files', '.*')]
		db_file = fd.asksaveasfilename(filetypes=files)
		if db_file:
			if not db_file.endswith(".gflaredb"): db_file += ".gflaredb"
			if path.isfile(db_file): remove(db_file)
			self.crawler.reset_crawl()
			self.run_first_time = False
			self.crawler.db_file = db_file
			self.crawler.settings["STARTING_URL"] = url
			self.entry_url_input["state"] = "disabled"
			self.crawler.start_crawl()
			self.clear_output_table()
			self.populate_columns()
			print("db_file", self.crawler.db_file)
			print("STARTING_URL", self.crawler.settings["STARTING_URL"])
			self.master.title(f"{self.crawler.gf.get_domain(self.crawler.settings['STARTING_URL'])} - Greenflare SEO Crawler")

			self.after(10, self.add_to_outputtable)
			self.after(10, self.change_btn_text)

	@daemonize(title="Stopping crawl ...", msg="Waiting for the crawl to finish ...")
	def stop_crawl(self):
		self.crawler.end_crawl_gracefully()
		self.after(10, self.change_btn_text)

	def btn_crawl_pushed(self):
		url = self.entry_url_input.get()
		if self.button_crawl["text"] == "Start" and url != "":
			self.start_new_crawl(url)

		elif self.button_crawl["text"] == "Pause":
			self.stop_crawl()
		
		elif self.button_crawl["text"] == "Resume":
			self.populate_columns()
			self.crawler.resume_crawl()
			self.after(10, self.add_to_outputtable)
			self.after(10, self.change_btn_text)
		
		elif self.button_crawl["text"] == "Restart":
			self.start_new_crawl(url)
		
		print(self.crawler.settings)

	def change_btn_text(self):
		btn_txt = self.button_crawl["text"]
		if btn_txt == "Start": self.button_crawl["text"] = "Pause"
		elif btn_txt == "Pause": self.button_crawl["text"] = "Resume"
		elif btn_txt == "Resume": self.button_crawl["text"] = "Pause"
		elif btn_txt == "Restart": self.button_crawl["text"] = "Pause"

	def add_item_to_outputtable(self, item):
		for row in item:
			self.treeview_table.insert('', 'end', text=self.row_counter, values=row)
			with self.lock: self.row_counter += 1

	def add_to_outputtable(self):
		items = []
		end = False
		try:
			while not self.crawler.gui_url_queue.empty():
				items.append(self.crawler.gui_url_queue.get_nowait())
		except queue.Empty:
			pass

		for item in items:
			if item == "CRAWL_COMPLETED":
				self.update_progressbar()
				self.button_crawl["text"] = "Restart"
				if self.crawler.settings.get("MODE", "") == "Spider":
					messagebox.showinfo(title='Crawl completed', message=f'{self.crawler.settings.get("ROOT_DOMAIN", "")} has been crawled successfully!')
				else:
					messagebox.showinfo(title='Crawl completed', message='List Mode Crawl has been completed successfully!')
				end = True
				continue
			if item == "CRAWL_TIMED_OUT":
				messagebox.showerror(title='Error - Timed Out', message='Crawl timed out!')
				self.button_crawl["text"] = "Resume"
				end = True
				continue
			if item == "END":
				end = True
				continue

			self.add_item_to_outputtable(item)

		self.treeview_table.yview_moveto(1)
		self.update_progressbar()
		self.update_bottom_stats()
		
		if end: return
		self.after(200, self.add_to_outputtable)

	# @daemonize(title="Loading crawl ...", msg="Please wait while the crawl is loading ...")
	def load_crawl_to_outputtable(self):
		items = self.crawler.get_crawl_data()
		self.clear_output_table()
		for item in items:
			self.add_item_to_outputtable([item])		

	def update_progressbar(self):
		with self.lock:
			if self.crawler.urls_total > 0:
				percentage = int((self.crawler.urls_crawled / self.crawler.urls_total) * 100)
				self.progressbar["value"] = percentage
				if sys.platform == "win32": self.style.configure('text.Horizontal.TProgressbar', text=f'{percentage} %')

	def update_bottom_stats(self):
		with self.lock:
			self.urls_string_var.set(f"Speed: {self.crawler.current_urls_per_second} URL/s")
			self.urls_crawled_string_var.set(f"URLs crawled/discovered: {self.crawler.urls_crawled}/{self.crawler.urls_total}")

	def update(self):
		self.button_crawl["text"] = "Resume"
		self.entry_url_input.delete(0, 'end')
		self.entry_url_input.insert(0, self.crawler.settings["STARTING_URL"])
		self.row_counter = self.crawler.urls_crawled
		self.populate_columns()
		self.update_progressbar()

	def reset(self):
		self.entry_url_input["state"] = "enabled"
		self.entry_url_input.delete(0, 'end')
		self.entry_url_input.insert(0, "Enter URL to crawl")
		self.progressbar["value"] = 0
		self.clear_output_table()
		self.populate_columns()
		self.button_crawl["text"] = "Start"

	def show_list_mode(self):
		self.reset()
		self.master.title("List Mode - Greenflare SEO Crawler")
		self.entry_url_input.delete(0, 'end')
		self.entry_url_input.insert(0, "List Mode ...")
		self.freeze_input()

	def freeze_input(self):
		self.entry_url_input["state"] = "disabled"