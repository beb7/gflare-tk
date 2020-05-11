from tkinter import Frame, LEFT, ttk, W, filedialog as fd
from os import path, remove

class CrawlTab(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		self.crawler = crawler

		self.topframe = Frame(self, width=700)
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

		self.treeview_table = ttk.Treeview(self)
		self.treeview_table.pack(fill="both", expand=1)

		self.populate_columns()

	def populate_columns(self):
		items = [i.title().replace("_", " ") for i in self.crawler.gf.get_all_items()]
		items[items.index("Url")] = "URL"
		items[items.index("Redirect Url")] = "Redirect URL"
		self.treeview_table["columns"] = tuple(items)
		self.treeview_table.heading("#0", text="id", anchor=W)
		[self.treeview_table.heading(i, text=i, anchor=W) for i in self.treeview_table["columns"]]

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