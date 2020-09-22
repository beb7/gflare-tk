from tkinter import Frame, LEFT, ttk, W, NO, filedialog as fd, messagebox
from os import path, remove
from threading import Thread
import queue

class CrawlTab(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		self.crawler = crawler
		self.lock = crawler.lock

		self.style = ttk.Style(self)
		self.style.layout('text.Horizontal.TProgressbar', [('Horizontal.Progressbar.trough', {'children': [('Horizontal.Progressbar.pbar', {'side': 'left', 'sticky': 'ns'})], 'sticky': 'nswe'}), ('Horizontal.Progressbar.label', {'sticky': ''})])
		self.style.configure('text.Horizontal.TProgressbar', text='0 %')

		self.topframe = Frame(self)
		self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

		self.entry_url_input = ttk.Entry(self.topframe)
		self.entry_url_input.insert(0, "Enter URL to crawl")
		self.entry_url_input.bind('<Return>', self.enter_hit)
		self.entry_url_input.pack(side=LEFT, padx=(0, 20), expand=True, fill="x")

		self.button_crawl = ttk.Button(self.topframe, text="Start", command=self.btn_crawl_pushed)
		self.button_crawl.pack(side=LEFT, padx=(0, 20))

		self.progressbar = ttk.Progressbar(self.topframe, orient="horizontal", length=150, mode="determinate", maximum=100, value=0, style='text.Horizontal.TProgressbar')
		self.progressbar.pack(side=LEFT, fill="x")
		
		self.treeview_table = ttk.Treeview(self, selectmode="browse")

		self.scrollbar_vertical = ttk.Scrollbar(self, orient="vertical", command=self.treeview_table.yview)
		self.scrollbar_vertical.pack(side="right", fill="y")
		self.scrollbar_horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.treeview_table.xview)
		self.scrollbar_horizontal.pack(side="bottom", fill="x")
		self.treeview_table.configure(yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=self.scrollbar_horizontal.set)
		self.treeview_table.pack(fill="both", expand=1)

		self.populate_columns()
		self.row_counter = 1

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
		self.treeview_table.column("#0", width=50, stretch=NO)
		for i in self.treeview_table["columns"]:
			self.treeview_table.heading(i, text=i, anchor=W)
			if "url" in i.lower():
				self.treeview_table.column(i, width=250, stretch=NO)
			else:
				self.treeview_table.column(i, width=100, stretch=NO)

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

			self.after(10, self.add_to_outputtable)
			self.after(10, self.change_btn_text)

	def btn_crawl_pushed(self):
		url = self.entry_url_input.get()
		if self.button_crawl["text"] == "Start" and url != "":
			self.start_new_crawl(url)

		elif self.button_crawl["text"] == "Pause":
			self.crawler.end_crawl_gracefully()
			self.after(10, self.change_btn_text)
			# self.enable_settings(True)
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
		try:
			while not self.crawler.gui_url_queue.empty():
				items.append(self.crawler.gui_url_queue.get_nowait())
		except queue.Empty:
			pass

		for item in items:
			if item == "CRAWL_COMPLETED":
				self.update_progressbar()
				self.button_crawl["text"] = "Restart"
				messagebox.showinfo(title='Crawl completed', message=f'Crawl of {self.crawler.settings.get("ROOT_DOMAIN", "")} has been completed successfully!')
				return
			if item == "CRAWL_TIMED_OUT":
				messagebox.showerror(title='Error - Timed Out', message=f'Crawl timed out!')
				self.button_crawl["text"] = "Restart"
				return
			if item == "END":
				return

			self.add_item_to_outputtable(item)

		self.treeview_table.yview_moveto(1)
		self.update_progressbar()
		
		self.after(200, self.add_to_outputtable)

	def load_crawl_to_outputtable(self):
		items = self.crawler.get_crawl_data()
		self.clear_output_table()
		for item in items:
			self.add_item_to_outputtable([item])

	def update_progressbar(self):
		with self.lock:
			print("urls crawled:", self.crawler.urls_crawled)
			print("urls total:", self.crawler.urls_total)
			if self.crawler.urls_total > 0:
				percentage = int((self.crawler.urls_crawled / self.crawler.urls_total) * 100)
				self.progressbar["value"] = percentage
				self.style.configure('text.Horizontal.TProgressbar', text=f'{percentage} %')

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
		self.entry_url_input.delete(0, 'end')
		self.entry_url_input.insert(0, "List Mode ...")
		self.entry_url_input["state"] = "disabled"
