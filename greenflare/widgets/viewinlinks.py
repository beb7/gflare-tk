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

from tkinter import ttk, Toplevel
import sys


class ViewInlinks(Toplevel):

    def __init__(self, url, query_func):
        Toplevel.__init__(self)
        self.url = url
        self.query_func = query_func

        self.title(f'View Inlinks - {self.url}')

        self.top_frame = ttk.Frame(self)

        self.middle_frame = ttk.Frame(self)
        self.middle_frame.pack(anchor='center', fill='both', expand=True)

        self.treeview_table = ttk.Treeview(
            self.middle_frame, selectmode="browse")

        # Capture right clicks on table
        right_click = '<Button-3>'

        if sys.platform == 'darwin':
            right_click = '<Button-2>'

        # self.treeview_table.bind(right_click, self.assign_treeview_click)

        self.scrollbar_vertical = ttk.Scrollbar(
            self.middle_frame, orient="vertical")
        self.scrollbar_vertical.pack(side="right", fill="y")
        self.scrollbar_horizontal = ttk.Scrollbar(
            self.middle_frame, orient="horizontal", command=self.treeview_table.xview)
        self.scrollbar_horizontal.pack(side="bottom", fill="x")
        self.treeview_table.configure(
            yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=self.scrollbar_horizontal.set)
        self.treeview_table.pack(fill="both", expand=1)

        
        column_name = 'Linking URL'
        self.treeview_table["columns"] = tuple([column_name])

        self.treeview_table.heading("#0", text="id", anchor='w')
        self.treeview_table.column("#0", width=55, stretch=False)

        self.treeview_table.heading(column_name, text=column_name, anchor='w')
        self.treeview_table.column(column_name, stretch=True)

        self.add_inlinks()


    def add_inlinks(self):
        inlinks = self.query_func(self.url)

        for i, link in enumerate(inlinks, 1):
            self.treeview_table.insert('', 'end', text=i, values=link)



