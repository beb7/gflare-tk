from tkinter import ttk, Toplevel, LEFT, RIGHT

class FilterWindow(Toplevel):
	def __init__(self, label, column, columns, title=None):
		Toplevel.__init__(self)
		self.label = label
		self.column = column
		self.columns = columns
		self.widgets = []
		self.operators = ['Equals', 'Does Not Equal', 'Begins Width', 'Ends With', 'Contains', 'Does Not Contain', 'Greater Than', 'Greater Than Or Equal To', 'Less Than', 'Less Than Or Equal To', 'Between', 'Custom Filter']

		if title: 
			self.title(title)

		
		self.top_frame = ttk.Frame(self)
		self.top_frame.pack(anchor='w', padx=20, pady=20, fill='x')

		self.top_lbl = ttk.Label(self.top_frame, text=f'Show rows where {self.column}:')
		self.top_lbl.pack(side='left')

		self.middle_frame = ttk.Frame(self)
		self.middle_frame.pack(anchor='center', padx=20, pady=(0, 20), fill='x')

		self.add_filter_row()
		self.add_filter_row(preselect=False)

		self.bottom_frame = ttk.Frame(self)
		self.bottom_frame.pack(padx=20, pady=(0,20), fill='x')

		self.button_ok = ttk.Button(self.bottom_frame, text="OK", command=self.btn_ok_pushed)
		self.button_ok.pack(side='right', padx=(10, 0))

		self.button_cancel = ttk.Button(self.bottom_frame, text="Cancel", command=self.destroy)
		self.button_cancel.pack(side='right')

		# The window needs to be placed after its elements have been assigned
		# get window width and height

		height = self.master.winfo_height()
		width = self.master.winfo_width()

		pop_up_height = self.winfo_height()
		pop_up_width = self.winfo_width()

		x = self.master.winfo_rootx()
		y = self.master.winfo_rooty()

		x_offset = width // 2 -  pop_up_width
		y_offset = height // 2 - pop_up_height

		# and where it is placed
		self.geometry('+%d+%d' % (x+x_offset, y//2+y_offset))

	def add_filter_row(self, preselect=True):
		
		self.widgets.append(ttk.Frame(self.middle_frame))
		self.widgets[-1].pack(anchor='center', padx=20, pady=(0, 20), fill="x")

		cmb_column = ttk.Combobox(self.widgets[-1], values=self.columns, state="readonly", width=25)
		cmb_column.pack(side=LEFT, padx=10)

		cmb_operators = ttk.Combobox(self.widgets[-1], values=self.operators, state="readonly", width=25)
		cmb_operators.pack(side=LEFT, padx=(0, 10))
		
		if preselect:
			cmb_column.current(self.columns.index(self.column.lower().replace(' ', '_')))
			cmb_operators.current(self.operators.index(self.label))

		entry = ttk.Entry(self.widgets[-1], width=75)
		entry.pack(side=LEFT, padx=10)

	def btn_ok_pushed(self):

		for w in self.widgets:
			children = w.winfo_children()
			operation = children[0].get()
			values = children[1].get()
			print(operation, values)
