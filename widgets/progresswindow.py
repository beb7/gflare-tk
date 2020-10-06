from tkinter import ttk, Toplevel

class ProgressWindow(ttk.Frame):    
	def __init__(self, title=None, msg=None):
		ttk.Frame.__init__(self)
		self.window = Toplevel(self.master)
		
		if title: self.window.title(title)
		if msg:
			self.lbl = ttk.Label(self.window, text=msg)
			self.lbl.pack(padx=20, pady=20)

		self.pb = ttk.Progressbar(self.window, orient='horizontal', mode='indeterminate')
		self.pb.pack(expand=True, fill=BOTH, side=TOP, pady=(0,20), padx=20)
		self.pb.start(50)