from tkinter import ttk, LEFT, RIGHT
from re import escape

class ExclusionsTab(ttk.Frame):
	def __init__(self, crawler=None):
		ttk.Frame.__init__(self)
		self.crawler = crawler
		self.widgets = []
		self.bind("<FocusOut>", self.save_inexes)
		self.pack()

		self.topframe = ttk.Frame(self)
		self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

		self.button_add = ttk.Button(self.topframe, text="+", command=self.add_inex_widget)
		self.button_add.pack(side=RIGHT, padx=(0, 20))
		self.button_remove = ttk.Button(self.topframe, text="-", command=self.remove_inex_widget)
		self.button_remove["state"] = "disabled"
		self.button_remove.pack(side=RIGHT, padx=(0, 20))

		self.add_inex_widget()


	def add_inex_widget(self):
		
		pad_x = (0, 10)

		self.widgets.append(ttk.Frame(self))
		self.widgets[-1].pack(anchor='center', padx=20, pady=20, fill="x")
		self.combobox_inexclude = ttk.Combobox(self.widgets[-1], values=['Exclude'], state="readonly")
		self.combobox_inexclude.current(0)
		self.combobox_inexclude.pack(side=LEFT, padx=pad_x)

		self.combobox_item = ttk.Combobox(self.widgets[-1], values=['URL'], state="readonly")
		self.combobox_item.current(0)
		self.combobox_item.pack(side=LEFT, padx=pad_x)

		self.operators = ['Equal to (=)', 'Contain', 'Start with', 'End with', 'Regex match']
		self.combobox_op = ttk.Combobox(self.widgets[-1], values=self.operators, state="readonly")
		self.combobox_op.current(0)
		self.combobox_op.pack(side=LEFT, padx=pad_x)

		self.entry_inex_input = ttk.Entry(self.widgets[-1], width=75)
		self.entry_inex_input.pack(side=LEFT, padx=pad_x)

		if len(self.widgets) > 10: self.button_add["state"] = "disabled"
		if len(self.widgets) > 1: self.button_remove["state"] = "enabled"

	def remove_inex_widget(self):
		self.widgets[-1].pack_forget()
		self.widgets[-1].destroy()
		self.widgets.pop()

		if len(self.widgets) < 2: self.button_remove["state"] = "disabled"
		if len(self.widgets) < 10: self.button_add["state"] = "enabled"

	def save_inexes(self, event):
		
		if len(self.widgets) == 1 and self.widgets[0].winfo_children()[3] == "": self.crawler.settings["EXCLUSIONS"] = ""
		
		rules = []

		for w in self.widgets:
			children = w.winfo_children()

			operator = children[2].get()
			value = children[3].get()
			
			if operator == self.operators[0]:
				value = escape(value)
				rules.append(f"^{value}$")
			elif operator == self.operators[1]:
				value = escape(value)
				rules.append(f".*{value}.*")
			elif operator == self.operators[2]:
				value = escape(value)
				rules.append(f"^{value}.*")
			elif operator == self.operators[3]:
				value = escape(value)
				rules.append(f".*{value}$")
			elif operator == self.operators[4]:
				rules.append(value)

		self.crawler.settings["EXCLUSIONS"] = "|".join(rules)

	def update(self):
		children = self.widgets[-1].winfo_children()
		children[-2].current(4)
		children[3].insert(0, self.crawler.settings.get('EXCLUSIONS', ''))