from tkinter import Frame, LEFT, ttk, W, NO, filedialog as fd
from os import path, remove
from threading import Thread
import queue

class CrawlTab(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		self.crawler = crawler
		self.lock = crawler.lock

		self.topframe = Frame(self, width=500)
		self.topframe.pack(anchor='center', padx=20, pady=20)

		self.entry_url_input = ttk.Entry(self.topframe, width=100)
		self.entry_url_input.insert(0, "Enter URL to crawl")
		self.entry_url_input.bind('<Return>', self.enter_hit)
		self.entry_url_input.pack(side=LEFT, padx=(0, 20))

		self.button_crawl = ttk.Button(self.topframe, text="Start", command=self.btn_crawl_pushed)
		self.button_crawl.pack(side=LEFT, padx=(0, 20))

		self.progressbar = ttk.Progressbar(self.topframe, orient="horizontal", length=90, mode="determinate", maximum=100, value=0)
		self.progressbar.pack(side=LEFT, fill="x")
		self.progressbar.start()

		self.y_scrollbar = ttk.Scrollbar(self)
		self.y_scrollbar.pack(side="right", fill="y")
		self.x_scrollbar = ttk.Scrollbar(self, orient="horizontal")
		self.x_scrollbar.pack(side="bottom", fill="x")
		self.treeview_table = ttk.Treeview(self, yscrollcommand=self.y_scrollbar.set, xscrollcommand=self.x_scrollbar.set)
		self.treeview_table.pack(fill="both", expand=1)

		self.populate_columns()
		self.row_counter = 1

	def populate_columns(self):
		items = [i.title().replace("_", " ") for i in self.crawler.gf.get_all_items()]
		items[items.index("Url")] = "URL"
		items[items.index("Redirect Url")] = "Redirect URL"
		self.treeview_table["columns"] = tuple(items)
		self.treeview_table.heading("#0", text="id", anchor=W)
		self.treeview_table.column("#0", width=50, stretch=NO)
		for i in self.treeview_table["columns"]:
			self.treeview_table.heading(i, text=i, anchor=W)
			if "url" in i.lower():
				self.treeview_table.column(i, width=250, stretch=NO)
			else:
				self.treeview_table.column(i, width=100)

	def enter_hit(self, event=None):
		self.btn_crawl_pushed()

	def btn_crawl_pushed(self):
		url = self.entry_url_input.get()
		if self.button_crawl["text"] == "Start" and url != "":
			files = [('Greenflare DB', '*.gflaredb'), ('All files', '.*')]
			db_file = fd.asksaveasfilename(filetypes=files)
			if db_file:
				if not db_file.endswith(".gflaredb"): db_file += ".gflaredb"
				if path.isfile(db_file): remove(db_file)
				self.crawler.db_file = db_file
				self.crawler.settings["STARTING_URL"] = url
				self.crawler.start_crawl()

				self.after(10, self.add_to_outputtable)
				self.after(10, self.change_btn_text)

		elif self.button_crawl["text"] == "Pause":
			self.crawler.end_crawl_gracefully()
			self.after(10, self.change_btn_text)
			# self.enable_settings(True)
		elif self.button_crawl["text"] == "Resume":
			self.populate_columns()
			self.crawler.resume_crawl()
			self.after(10, self.add_to_outputtable)
			self.after(10, self.change_btn_text)


	def change_btn_text(self):
		if self.button_crawl["text"] == "Start": self.button_crawl["text"] = "Pause"
		elif self.button_crawl["text"] == "Pause": self.button_crawl["text"] = "Resume"
		elif self.button_crawl["text"] == "Resume": self.button_crawl["text"] = "Pause"

	def add_to_outputtable(self):
		items = []
		try:
			while not self.crawler.gui_url_queue.empty():
				items.append(self.crawler.gui_url_queue.get_nowait())
		except queue.Empty:
			pass
		
		for item in items:
			if item == "CRAWL_COMPLETED":
				return
			if item == "CRAWL_TIMED_OUT":
				return
			if item == "END":
				return

			for row in item:
				self.treeview_table.insert('', 'end', text=self.row_counter, values=row)
				with self.lock: self.row_counter += 1

		self.treeview_table.yview_moveto(1)
		self.after(200, self.add_to_outputtable)