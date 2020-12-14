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

from tkinter import ttk, Toplevel, TOP
from greenflare.widgets.windowhelper import center_on_parent


class ProgressWindow(Toplevel):

    def __init__(self, title=None, msg=None):
        Toplevel.__init__(self)
        self.topframe = ttk.Frame(self)
        self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

        if title:
            self.title(title)
        if msg:
            self.lbl = ttk.Label(self.topframe, text=msg)
            self.lbl.pack(padx=20, pady=20, side=TOP, expand=True)

        self.pb = ttk.Progressbar(
            self.topframe, orient='horizontal', mode='indeterminate')
        self.pb.pack(fill="x", pady=(0, 20), padx=20, side=TOP, expand=True)
        self.pb.start(50)

        center_on_parent(self.master, self)

        self.lift()
