from tkinter import ttk, Toplevel, BOTH, TOP

class ProgressWindow(ttk.Frame):    
	def __init__(self, title=None, msg=None):
		ttk.Frame.__init__(self)
		self.window = Toplevel(self.master)
		
		self.topframe = ttk.Frame(self.window)
		self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

		if title: self.window.title(title)
		if msg:
			self.lbl = ttk.Label(self.topframe, text=msg)
			self.lbl.pack(padx=20, pady=20, side=TOP, expand=True)

		self.pb = ttk.Progressbar(self.topframe, orient='horizontal', mode='indeterminate')
		self.pb.pack(fill="x", pady=(0,20), padx=20, side=TOP, expand=True)
		self.pb.start(50)

		# The window needs to be placed after its elements have been assigned
		# get window width and height

		# this always returns 200, so setting the window size manually at the moment ...
		# w = self.window.winfo_reqwidth()
		# h = self.window.winfo_reqheight()

		w = 300
		h = 150

		# get screen width and height
		ws = self.master.winfo_screenwidth() # width of the screen
		hs = self.master.winfo_screenheight() # height of the screen

		# calculate x and y coordinates for the Tk root window
		x = (ws/2) - (w/2)
		y = (hs/2) - (h/2)

		# set the dimensions of the screen 
		# and where it is placed
		self.window.geometry('%dx%d+%d+%d' % (w, h, x, y))
