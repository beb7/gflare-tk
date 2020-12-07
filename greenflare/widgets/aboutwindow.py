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

from tkinter import ttk, Toplevel, TOP, LEFT, Text, END
from PIL import ImageTk, Image
from greenflare.core.defaults import Defaults
from greenflare.widgets.windowhelper import center_on_parent
from webbrowser import open as open_in_browser


class AboutWindow(Toplevel):

    def __init__(self):
        Toplevel.__init__(self)
        self.geometry('750x400')
        self.resizable(False, False)

        self.title('About Greenflare SEO Crawler')

        self.leftframe = ttk.Frame(self)
        self.leftframe.pack(side=LEFT, padx=20, pady=20, fill="x")

        self.rightframe = ttk.Frame(self)
        self.rightframe.pack(side=LEFT, padx=20, pady=20, fill="x")

        self.render = ImageTk.PhotoImage(Image.open(Defaults.about_icon()))
        self.img = ttk.Label(self.leftframe, image=self.render)
        self.img.pack(padx=(20, 0))

        self.info_text = Text(self)
        self.info_text.pack(padx=(0, 20), pady=20)

        self.info_text.tag_configure('h1', font=('Arial', 16, 'bold'))
        self.info_text.tag_configure('h2', font=('Arial', 14))
        self.info_text.tag_configure('website', foreground='blue')
        self.info_text.tag_configure('twitter', foreground='blue')
        self.info_text.tag_configure('github', foreground='blue')

        heading_1 = 'Greenflare SEO Crawler'
        heading_2 = f'\nVersion {Defaults.version}'

        text = '\n\n© Greenflare Developers 2020\n\nCreated By Benjamin Görler (ben@greenflare.io)\n\nWebsite: '
        website = 'https://greenflare.io'
        twitter = 'https://twitter.com/GreenflareEN'
        github = 'https://github.com/beb7/gflare-tk/'
        self.info_text.tag_bind('link',"<Button-1>", lambda event, link=website: self.link_clicked(event, link))
        self.info_text.tag_bind('twitter',"<Button-1>", lambda event, link=twitter: self.link_clicked(event, link))
        self.info_text.tag_bind('github',"<Button-1>", lambda event, link=github: self.link_clicked(event, link))

        self.info_text.insert(END, heading_1, 'h1')
        self.info_text.insert(END, heading_2, 'h2')
        self.info_text.insert(END, text)
        self.info_text.insert(END, website, 'website')
        self.info_text.insert(END, '\n\nTwitter: ')
        self.info_text.insert(END, twitter, 'twitter')
        self.info_text.insert(END, '\n\nGithub: ')
        self.info_text.insert(END, github, 'github')
        self.info_text.configure(state='disabled')

        center_on_parent(self.master, self)

        self.lift()

    def link_clicked(self, e, link):
        open_in_browser(link, new=2)
