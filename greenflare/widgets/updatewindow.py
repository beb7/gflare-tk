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
from greenflare.core.defaults import Defaults
from greenflare.widgets.windowhelper import center_on_parent
from webbrowser import open as open_in_browser


class UpdateWindow(Toplevel):

    def __init__(self, title, version):
        Toplevel.__init__(self)
        self.version = version

        if title:
            self.title(title)

        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(anchor='center', padx=20, pady=20, fill='x', expand=True)

        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(anchor='center', padx=20, pady=(0, 20), fill='x', expand=True)

        self.top_lbl = ttk.Label(self.top_frame, text=f'A new Greenflare version is available: v{self.version}')
        self.top_lbl.pack(side='left')

        self.button_ok = ttk.Button(
            self.bottom_frame, text='Download', command=self.btn_ok_pushed)
        self.button_ok.pack(side='left', padx=(10, 0))

        self.button_cancel = ttk.Button(
            self.bottom_frame, text='Cancel', command=self.destroy)
        self.button_cancel.pack(side='right')


        self.resizable(False, False)
        center_on_parent(self.master, self)


    def btn_ok_pushed(self):
        open_in_browser(Defaults.download_url, new=2)
        self.destroy()

    def enter_hit(self, event=None):
        self.btn_ok_pushed()
