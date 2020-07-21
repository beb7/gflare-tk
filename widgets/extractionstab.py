from tkinter import Frame, ttk, LEFT, RIGHT
from re import escape

class ExtractionsTab(Frame):
	def __init__(self, crawler=None):
		Frame.__init__(self)
		self.crawler = crawler
		self.widgets = []
		self.bind("<FocusOut>", self.save_extractions)
		self.pack()

		self.topframe = Frame(self)
		self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

		self.button_add = ttk.Button(self.topframe, text="+", command=self.add_extraction)
		self.button_add.pack(side=RIGHT, padx=(0, 20))
		self.button_remove = ttk.Button(self.topframe, text="-", command=self.remove_extraction)
		self.button_remove["state"] = "disabled"
		self.button_remove.pack(side=RIGHT, padx=(0, 20))

		self.add_extraction()


	def add_extraction(self):
		
		pad_x = (0, 10)
		
		self.widgets.append(Frame(self))
		self.widgets[-1].pack(anchor='center', padx=20, pady=20, fill="x")

		self.entry_input_name = ttk.Entry(self.widgets[-1], width=20)
		self.entry_input_name.insert(0, f"Extraction {str(len(self.widgets))}")
		self.entry_input_name.pack(side=LEFT, padx=pad_x)
		
		self.combobox_selector_type = ttk.Combobox(self.widgets[-1], values=['CSS Selector', 'XPath'], state="readonly")
		self.combobox_selector_type.current(0)
		self.combobox_selector_type.pack(side=LEFT, padx=pad_x)

		self.entry_input_selector_value = ttk.Entry(self.widgets[-1], width=75)
		self.entry_input_selector_value.pack(side=LEFT, padx=pad_x)

		if len(self.widgets) > 10: self.button_add["state"] = "disabled"
		if len(self.widgets) > 1: self.button_remove["state"] = "enabled"

	def remove_extraction(self):
		self.widgets[-1].pack_forget()
		self.widgets[-1].destroy()
		self.widgets.pop()

		if len(self.widgets) < 2: self.button_remove["state"] = "disabled"
		if len(self.widgets) < 10: self.button_add["state"] = "enabled"

	def save_extractions(self, event):
		
		if len(self.widgets) == 1 and self.widgets[0].winfo_children()[2] == "": return
		
		# Resetting the extractions and overriding self.settings['EXTRACTIONS'] ensures removed items disappear, too
		
		extractions = {}

		for w in self.widgets:
			children = w.winfo_children()

			name = children[0].get()
			selector = children[1].get()
			value = children[2].get()
		
			col_name = name.lower().replace(" ", "_")
			
			# Do not allow to name a custom extraction like an existing crawl item
			if col_name in self.crawler.settings.get("CRAWL_ITEMS", ""): col_name += "_custom"
			extractions[col_name] = {"selector": selector, "value": value}

		self.crawler.settings["EXTRACTIONS"] = extractions		


	def update(self):
		
		counter = 1
		for name, v in self.crawler.settings.get("EXTRACTIONS", {}).items():
			# First item does not need a new widget
			if counter > 1: self.add_extraction()
			children = self.widgets[-1].winfo_children()
			children[0].delete(0, 'end')
			children[0].insert(0, name)
			if "CSS Selector" in v["selector"]:
				children[1].current(0)
			elif "XPath" in v["selector"]:
				children[1].current(1)
			else:
				children[1].current(2)
				
			children[2].delete(0, 'end')
			children[2].insert(0, v["value"])
			counter += 1