from tkinter import Frame, LEFT, RIGHT, Toplevel, ttk, Text, messagebox
import urllib.parse

class ListModeWindow(Frame):	
	def __init__(self, crawler=None, crawl_tab=None, root=None):
		Frame.__init__(self)

		self.crawler = crawler
		self.crawl_tab = crawl_tab
		self.list_crawl_window = Toplevel(root)

		self.list_crawl_window.resizable(False, False)
		self.list_crawl_window.title("Greenflare SEO Crawler - List Mode Input URLs")

		self.top_frame = Frame(self.list_crawl_window)
		self.top_frame.pack(anchor='center', padx=5, pady=5, fill='x')

		self.middle_frame = Frame(self.list_crawl_window)
		self.middle_frame.pack(anchor='center', padx=5, pady=5, fill='x')

		self.bottom_frame = Frame(self.list_crawl_window)
		self.bottom_frame.pack(anchor='center', padx=5, pady=5, fill='x')

		self.label_input = ttk.Label(self.top_frame, text="Enter or paste URLs to spider list crawl, one per line.")
		self.label_input.pack(side=LEFT)

		self.url_input_field = Text(self.middle_frame)
		self.url_input_field.pack()

		self.list_crawl_btn = ttk.Button(self.bottom_frame, text="OK", command=self.start_list_crawl)
		self.list_crawl_btn.pack(side=RIGHT)

	def start_list_crawl(self):
		urls = self.url_input_field.get("1.0", 'end-1c')
		urls = urls.splitlines()
		
		# Parse urls and only keep valid URLs
		urls = [u for u in urls if self.url_check(u) == True]
		
		# Dedupe URLs
		urls = list(set(urls))

		if len(urls) > 0:
			self.crawler.settings['MODE'] = 'List'
			self.crawler.list_mode_urls = urls
			self.crawl_tab.show_list_mode()
			messagebox.showinfo(title='Reading URLs completed', message=f'Loaded {len(urls)} valid and unique URLs!')
		else:
			messagebox.showerror(title='Reading URLs failed', message=f'No valid URLs found, please check your input!')

	def url_check(self, url):
		try:
			scheme, netloc, path, query, frag = urllib.parse.urlsplit(url)
			if all([scheme, netloc]): return True
			return False
		except:
			return False
