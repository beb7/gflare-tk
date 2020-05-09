from tkinter import Tk, Frame


class GreenflareTk(Frame):
	def __init__(self):
		Frame.__init__(self)


if __name__ == "__main__":
	root = Tk()
	app = GreenflareTk()
	root.mainloop()
