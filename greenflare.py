import tkinter as tk
from tkinter import Frame, ttk
from core.gflarecrawler import GFlareCrawler
from widgets.crawltab import CrawlTab


class mainWindow(Frame):
	def __init__(self):
		Frame.__init__(self)
		self.tab_parent = ttk.Notebook()
		self.tab_crawl = CrawlTab()

		self.tab_parent.add(self.tab_crawl, text="Crawl")
		self.tab_parent.pack(expand=1, fill="both")
		self.master.title("Greenflare SEO Crawler")

if __name__ == "__main__":
	root = tk.Tk()
	root.geometry("1024x768")
	root.iconphoto(False, tk.PhotoImage(file='icons/greenflare-icon-64x64.png'))
	app = mainWindow()
	root.mainloop()
