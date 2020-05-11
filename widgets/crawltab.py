from tkinter import Frame, RIGHT, LEFT, ttk


class CrawlTab(Frame):
	def __init__(self):
		Frame.__init__(self)
		self.topframe = Frame(self, width=700)
		self.topframe.pack(anchor='center', padx=20, pady=20)


		self.entry_url_input = ttk.Entry(self.topframe, width=100)
		self.entry_url_input.insert(0, "Enter URL to crawl")
		self.entry_url_input.pack(side=LEFT, padx=(0, 20))

		self.button_crawl = ttk.Button(self.topframe, text="Start", command=self.btn_crawl_pushed)
		self.button_crawl.pack(side=LEFT, padx=(0, 20))

		self.progressbar = ttk.Progressbar(self.topframe, orient="horizontal", length=90, mode="determinate", maximum=100, value=0)
		self.progressbar.pack(side=LEFT, fill="x")
		self.progressbar.start()


	def btn_crawl_pushed(self):
		print("Button clicked")