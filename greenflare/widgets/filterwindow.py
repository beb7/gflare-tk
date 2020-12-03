"""
@author Benjamin Görler <ben@greenflare.io>

@section LICENSE

Greenflare SEO Web Crawler (https://greenflare.io)
Copyright (C) 2020  Benjamin Görler. This file is part of
Greenflare, an open-source project dedicated to delivering
high quality SEO insights and analysis solutions to the world.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from tkinter import ttk, Toplevel, LEFT, RIGHT
from greenflare.core.defaults import Defaults
from greenflare.widgets.windowhelper import center_on_parent


class FilterWindow(Toplevel):

    def __init__(self, crawl_tab, label, column, columns, table=None, title=None):
        Toplevel.__init__(self)

        self.crawl_tab = crawl_tab
        self.label = label
        self.column = column
        self.columns = columns
        self.table = table
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

        self.viewed_table = 'crawl'

        center_on_parent(self.master, self)

    def add_filter_row(self, preselect=True):

        self.widgets.append(ttk.Frame(self.middle_frame))
        self.widgets[-1].pack(anchor='center', padx=20, pady=(0, 20), fill="x")

        columns = [c.replace('_', ' ').title() for c in self.columns]

        cmb_column = ttk.Combobox(
            self.widgets[-1], values=columns, state="readonly", width=12)
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

        if self.table == 'crawl':
            self.crawl_tab.load_crawl_to_outputtable(filters, self.table)
        else:
            self.crawl_tab.load_crawl_to_outputtable(
                filters, self.table, columns="*")

        if not '(Filtered View)' in self.master.title():
            self.master.title(self.master.title() + ' (Filtered View)')
        self.withdraw()
        self.destroy()

    def enter_hit(self, event=None):
        self.btn_ok_pushed()
