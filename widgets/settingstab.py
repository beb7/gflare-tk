from tkinter import Frame, ttk, LEFT

class SettingsTab(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)

		self.label_threads =  ttk.Label(self, text="Threads")
		self.label_threads.pack(padx=(0, 20))

	def update(self):
		pass