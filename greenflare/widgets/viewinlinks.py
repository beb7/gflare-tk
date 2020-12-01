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

from tkinter import ttk, LEFT, RIGHT


class URLTab(ttk.Frame):

    def __init__(self, data):
        ttk.Frame.__init__(self)
        self.data = data

        self.lblframe_onpage = ttk.LabelFrame(self, text='On-Page Elements')
        self.lblframe_onpage.pack(side='left', padx=20, pady=20)

        self.onpage_elements = [
            ('URL:', self.data.get('url', '')),
            ('Page Title:', self.data.get('page_title', '')),
            ('Meta Description:', self.data.get('meta_description', ''))
        ]

        for name, text in self.onpage_elements:
            self.generate_label_group(self.lblframe_onpage, name, text)

        self.frame_bottom = ttk.Frame(self)
        self.frame_bottom.pack(anchor='w')

        self.btn_close = ttk.Button(
            self.frame_bottom, text='Close', command=self.destroy)
        self.btn_close.pack(anchor='e', padx=20, pady=20)

        print(data)

    def generate_label_group(self, lblframe, label_name, label_text):
        lbl_name = ttk.Label(lblframe, text=label_name, width=75)
        lbl_name.pack(anchor='w')

        lbl_text = ttk.Label(lblframe, text=label_text)
        lbl_text.pack()
