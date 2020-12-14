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

from tkinter import ttk, Toplevel, RIGHT, filedialog as fd
from os import path, remove
from greenflare.widgets.helpers import export_to_csv, run_in_background_with_window, tk_after
from greenflare.widgets.windowhelper import center_on_parent
import sys


class ViewInlinks(Toplevel):

    def __init__(self, url, query_func):
        Toplevel.__init__(self)
        center_on_parent(self.master, self)

        self.geometry('750x400')
        self.url = url
        self.query_func = query_func

        self.title(f'View Inlinks - {self.url}')

        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(anchor='center', fill='x')
        
        self.btn_export =  ttk.Button(self.top_frame, text='Export', command=self.export_button_pushed)
        self.btn_export.pack(side=RIGHT, padx=20, pady=20)

        self.frame_tbl = ttk.Frame(self)
        self.frame_tbl.pack(anchor='center', fill='both', expand=True)

        self.tbl = ttk.Treeview(self.frame_tbl, selectmode="browse")

        self.scrollbar_vertical = ttk.Scrollbar(self.frame_tbl, orient='vertical', command=self.tbl.yview)
        self.scrollbar_vertical.pack(side="right", fill="y")
        
        self.scrollbar_horizontal = ttk.Scrollbar(self.frame_tbl, orient='horizontal', command=self.tbl.xview)
        self.scrollbar_horizontal.pack(side="bottom", fill="x")
        
        self.tbl.configure(yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=self.scrollbar_horizontal.set)
        self.tbl.pack(fill="both", expand=True)
        
        column_name = 'Linking URL'
        self.tbl["columns"] = tuple([column_name])

        self.tbl.heading("#0", text="id", anchor='w')
        self.tbl.column("#0", width=55, stretch=False)

        self.tbl.heading(column_name, text=column_name, anchor='w')
        self.tbl.column(column_name, width=750, stretch=True)

        self._query_func()

    @tk_after
    def add_inlinks(self, inlinks):
        for i, link in enumerate(inlinks, 1):
            self.tbl.insert('', 'end', text=i, values=link)

    @run_in_background_with_window([], title='Running query ...', msg='Please wait while the data is being requested')
    def _query_func(self):
        inlinks = self.query_func(self.url)
        self.add_inlinks(inlinks)
 
    def export_button_pushed(self):
        files = [('CSV files', '*.csv')]
        self.withdraw()
        export_file = fd.asksaveasfilename(filetypes=files)

        if not export_file:
            return

        if not export_file.endswith(".csv"):
            export_file += ".csv"
        if path.isfile(export_file):
            remove(export_file)

        data = [self.tbl.item(
            child)['values'] for child in self.tbl.get_children()]

        export_to_csv(
            export_file, self.tbl['columns'], data)