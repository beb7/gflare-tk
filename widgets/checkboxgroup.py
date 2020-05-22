from tkinter import W, LabelFrame, Checkbutton, IntVar

class CheckboxGroup(LabelFrame):
	def __init__(self, parent, text, boxes, settings, column):
		self.parent = parent
		self.boxes = boxes
		self.text = text
		self.settings = settings
		self.column = column

		LabelFrame.__init__(self, self.parent, text=self.text)

		self.widgets = []
		self.populate_checkboxes()

	def populate_checkboxes(self):
		for i,e in enumerate(self.boxes):
			self.widgets.append(Checkbutton(self, text=e, variable=IntVar(), onvalue=1, offvalue=0))
			self.widgets[-1].grid(row=i, column=0, sticky=W)
			if  e.lower().replace(" ", "_").replace(".", "_") in self.settings[self.column]: self.widgets[-1].select()