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

from tkinter import ttk


class EnhancedEntry(ttk.Frame):

    def __init__(self, parent, default_text_):
        ttk.Frame.__init__(self, parent)
        self.default_text = default_text_

        self.style = ttk.Style()
        self.style.configure('Grey.TEntry', foreground='grey')
        self.style.configure('Black.TEntry', foreground='black')

        self.entry = ttk.Entry(parent, style='Grey.TEntry')
        self.entry.pack(side='left', padx=(0, 20), expand=True, fill='x')

        self.entry.insert(0, self.default_text)
        self.entry.bind('<FocusIn>', self.handle_focus_in)
        self.entry.bind('<FocusOut>', self.handle_focus_out)

    def handle_focus_in(self, _):
        if self.entry.get() == self.default_text:
            self.entry.delete(0, 'end')
            self.entry.config(style='Black.TEntry')

    def handle_focus_out(self, _):
        if not self.entry.get().strip():
            self.entry.delete(0, 'end')
            self.entry.config(style='Grey.TEntry')
            self.entry.insert(0, self.default_text)

    def get(self):
        return self.entry.get()