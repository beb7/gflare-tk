from tkinter import ttk, Toplevel, LEFT, RIGHT
from core.defaults import Defaults
from widgets.windowhelper import center_on_parent


class FilterWindow(Toplevel):

    def __init__(self, crawl_tab, label, column, columns, title=None):
        Toplevel.__init__(self)

        self.crawl_tab = crawl_tab
        self.label = label
        self.column = column
        self.columns = columns
        self.widgets = []
        self.operators = [l for l in Defaults.popup_menu_labels if l != '_']

        if title:
            self.title(title)

        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(anchor='w', padx=20, pady=20, fill='x')

        self.top_lbl = ttk.Label(self.top_frame, text=f'Show rows where {self.column}:')
        self.top_lbl.pack(side='left')

        self.middle_frame = ttk.Frame(self)
        self.middle_frame.pack(anchor='center', padx=20,
                               pady=(0, 20), fill='x')

        self.add_filter_row()
        self.add_filter_row(preselect=False)

        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(padx=20, pady=(0, 20), fill='x')

        self.button_ok = ttk.Button(
            self.bottom_frame, text="OK", command=self.btn_ok_pushed)
        self.button_ok.pack(side='right', padx=(10, 0))

        self.button_cancel = ttk.Button(
            self.bottom_frame, text="Cancel", command=self.destroy)
        self.button_cancel.pack(side='right')

        self.filters = []

        center_on_parent(self.master, self)

    def add_filter_row(self, preselect=True):

        self.widgets.append(ttk.Frame(self.middle_frame))
        self.widgets[-1].pack(anchor='center', padx=20, pady=(0, 20), fill="x")

        cmb_column = ttk.Combobox(
            self.widgets[-1], values=self.columns, state="readonly", width=12)
        cmb_column.pack(side=LEFT, padx=10)

        cmb_operators = ttk.Combobox(
            self.widgets[-1], values=self.operators, state="readonly", width=20)
        cmb_operators.pack(side=LEFT, padx=(0, 10))

        if preselect:
            cmb_column.current(self.columns.index(
                self.column.lower().replace(' ', '_')))
            cmb_operators.current(self.operators.index(self.label))

        entry = ttk.Entry(self.widgets[-1], width=40)
        entry.pack(side=LEFT, padx=10)
        entry.bind('<Return>', self.enter_hit)

    def btn_ok_pushed(self):

        if len(self.widgets) == 1 and self.widgets[0].winfo_children()[2] == "":
            return

        filters = []

        for w in self.widgets:
            children = w.winfo_children()
            column = children[0].get()
            operation = children[1].get()
            values = children[2].get()

            if not values:
                continue

            filters.append((column, operation, values))

        self.crawl_tab.filters = filters
        self.crawl_tab.load_crawl_to_outputtable(filters=filters)

        if not '(Filtered View)' in self.master.title():
            self.master.title(self.master.title() + ' (Filtered View)')
        self.withdraw()

    def enter_hit(self, event=None):
        self.btn_ok_pushed()
