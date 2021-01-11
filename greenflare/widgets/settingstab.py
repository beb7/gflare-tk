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

from tkinter import ttk, StringVar, IntVar
from greenflare.widgets.checkboxgroup import CheckboxGroup
from greenflare.core.defaults import Defaults


class SettingsTab(ttk.Frame):

    def __init__(self, crawler=None):
        ttk.Frame.__init__(self)

        s = ttk.Style()
        s.configure('Green.TFrame', background='green')
        s.configure('Blue.TFrame', background='blue')

        self.crawler = crawler

        self.group_x = (10, 10)
        self.group_y = (10, 0)

        self.frames_y = (15, 0)

        self.group_args = {'side': 'left', 'anchor': 'w',
                           'fill': 'both', 'padx': self.group_x, 'pady': self.group_y}
        self.item_left_args = {'side': 'left',
                               'anchor': 'w', 'padx': (5, 5), 'pady': 3}
        self.item_right_args = {'side': 'right',
                                'anchor': 'e', 'padx': (5, 5), 'pady': 3}

        # First row
        self.frame_first = ttk.Frame(self)
        self.frame_first.pack(anchor='w', fill='x', pady=self.frames_y)

        # Crawler Group
        self.group_crawler = ttk.LabelFrame(self.frame_first, text='Crawler')
        self.group_crawler.pack(**self.group_args)

        self.group_crawler_one = ttk.Frame(self.group_crawler)
        self.group_crawler_one.pack(expand=True, fill='x')

        self.label_threads = ttk.Label(self.group_crawler_one, text='Threads')
        self.label_threads.pack(self.item_left_args)

        self.spinbox_threads = ttk.Spinbox(
            self.group_crawler_one, from_=1, to=100, state='readonly', width=5, command=self.save_threads)
        self.spinbox_threads.set('5')
        self.spinbox_threads.pack(**self.item_right_args)

        self.group_crawler_two = ttk.Frame(self.group_crawler)
        self.group_crawler_two.pack(expand=True, fill='x')

        self.on_off_var = IntVar()
        self.cbtn_limit_urls = ttk.Checkbutton(
            self.group_crawler_two, text='Limit URL/s', onvalue=1, offvalue=0, variable=self.on_off_var, command=self.url_limit_clicked)
        self.cbtn_limit_urls.pack(**self.item_left_args)

        self.spinbox_urls = ttk.Spinbox(
            self.group_crawler_two, from_=0, to=100, state='readonly', width=5, command=self.save_urls)
        self.spinbox_urls['state'] = 'disabled'
        self.spinbox_urls.set('0')
        self.spinbox_urls.pack(**self.item_right_args)

        self.group_crawler_three = ttk.Frame(self.group_crawler)
        self.group_crawler_three.pack(expand=True, fill='x')

        self.label_ua = ttk.Label(self.group_crawler_three, text='User-Agent')
        self.label_ua.pack(**self.item_left_args)

        self.user_agents = Defaults.user_agents
        self.ua_names = [k for k in self.user_agents.keys()]
        self.combobox_ua = ttk.Combobox(
            self.group_crawler_three, values=self.ua_names, state='readonly')
        self.combobox_ua.bind('<<ComboboxSelected>>', self.save_ua)
        self.combobox_ua.current(0)
        self.combobox_ua.pack(**self.item_right_args)

        # Group HTTP Auth

        self.group_auth = ttk.LabelFrame(self.frame_first, text='HTTP Basic Auth')
        self.group_auth.pack(**self.group_args)

        self.group_auth_one = ttk.Frame(self.group_auth)
        self.group_auth_one.pack(expand=True, fill='x')

        self.label_auth_user = ttk.Label(self.group_auth_one, text='User')
        self.label_auth_user.pack(**self.item_left_args)

        self.var_auth_user = StringVar()
        self.entry_auth_user = ttk.Entry(self.group_auth_one, textvariable=self.var_auth_user,
                                    validatecommand=self.save_auth, validate='focusout')
        self.entry_auth_user.insert(0, 'Username')
        self.entry_auth_user.pack(**self.item_right_args)

        self.group_auth_two = ttk.Frame(self.group_auth)
        self.group_auth_two.pack(expand=True, fill='x')

        self.label_auth_password = ttk.Label(self.group_auth_two, text='Password')
        self.label_auth_password.pack(**self.item_left_args)

        self.var_auth_password = StringVar()
        self.entry_auth_password = ttk.Entry(self.group_auth_two, show='*', textvariable=self.var_auth_password,
                                    validatecommand=self.save_auth, validate='focusout')
        self.entry_auth_password.insert(0, '')
        self.entry_auth_password.pack(**self.item_right_args)

        # Group Network/Proxy

        self.group_network = ttk.LabelFrame(self.frame_first, text='Proxy')
        self.group_network.pack(**self.group_args)

        self.group_network_one = ttk.Frame(self.group_network)
        self.group_network_one.pack(expand=True, fill='x')

        self.label_host = ttk.Label(self.group_network_one, text='Host')
        self.label_host.pack(**self.item_left_args)

        self.var_host = StringVar()
        self.entry_host = ttk.Entry(self.group_network_one, textvariable=self.var_host,
                                    validatecommand=self.save_proxy, validate='focusout')
        self.entry_host.insert(0, 'hostname/ip:port')
        self.entry_host.pack(**self.item_right_args)

        self.group_network_two = ttk.Frame(self.group_network)
        self.group_network_two.pack(expand=True, fill='x')

        self.label_user = ttk.Label(self.group_network_two, text='User')
        self.label_user.pack(**self.item_left_args)

        self.var_user = StringVar()
        self.entry_user = ttk.Entry(self.group_network_two, textvariable=self.var_user,
                                    validatecommand=self.save_proxy, validate='focusout')
        self.entry_user.insert(0, '')
        self.entry_user.pack(**self.item_right_args)

        self.group_network_three = ttk.Frame(self.group_network)
        self.group_network_three.pack(expand=True, fill='x')

        self.label_password = ttk.Label(
            self.group_network_three, text='Password')
        self.label_password.pack(**self.item_left_args)

        self.var_password = StringVar()
        self.entry_password = ttk.Entry(
            self.group_network_three, show='*', textvariable=self.var_password, validatecommand=self.save_proxy, validate='focusout')
        self.entry_password.insert(0, '')
        self.entry_password.pack(**self.item_right_args)

        # Second row
        self.frame_second = ttk.Frame(self, width=25, height=50)
        self.frame_second.pack(anchor='w', pady=self.frames_y)

        # On-Page Group
        self.checkboxgroup_onpage = CheckboxGroup(self.frame_second, 'On-Page', [
                                                  'Page Title', 'Meta Description', 'H1', 'H2'], self.crawler.settings, 'CRAWL_ITEMS')
        self.checkboxgroup_onpage.pack(**self.group_args)

        # Links Group
        self.checkboxgroup_links = CheckboxGroup(self.frame_second, 'Links', [
            'Canonicals', 'Pagination', 'Hreflang', 'External Links'], self.crawler.settings, 'CRAWL_ITEMS')
        self.checkboxgroup_links.pack(**self.group_args)

        # # Directives Group
        self.checkboxgroup_directives = CheckboxGroup(self.frame_second, 'Directives', [
            'Canonical Tag', 'Canonical HTTP Header', 'Meta Robots', 'X-Robots-Tag'], self.crawler.settings, 'CRAWL_ITEMS')
        self.checkboxgroup_directives.pack(**self.group_args)

        # Third row
        self.frame_third = ttk.Frame(self, width=25, height=50)
        self.frame_third.pack(anchor='w')

        # robots.txt Group
        self.checkboxgroup_robots_txt = CheckboxGroup(self.frame_third, 'robots.txt', [
                                                      'Respect robots.txt', 'Follow blocked redirects', 'Check blocked URLs'], self.crawler.settings, 'CRAWL_ITEMS')
        self.checkboxgroup_robots_txt.pack(**self.group_args)

        # Resources Group
        self.checkboxgroup_resources = CheckboxGroup(self.frame_third, 'Resources', [
                                                     'Images', 'JavaScript', 'Stylesheets'], self.crawler.settings, 'CRAWL_ITEMS')
        self.checkboxgroup_resources.pack(**self.group_args)

        # Analysis Group
        self.checkboxgroup_misc = CheckboxGroup(self.frame_third, 'Misc', [
            'Unique Inlinks', 'Respect nofollow'], self.crawler.settings, 'CRAWL_ITEMS')
        self.checkboxgroup_misc.pack(**self.group_args)

    def update(self):
        self.spinbox_threads.set(int(self.crawler.settings['THREADS']))
        urls_per_second = int(self.crawler.settings['URLS_PER_SECOND'])
        if urls_per_second > 0:
            self.spinbox_urls.set(urls_per_second)
            self.spinbox_urls['state'] = 'enabled'
        self.combobox_ua.current()

    def save_threads(self):
        self.crawler.settings['THREADS'] = int(self.spinbox_threads.get())

    def save_urls(self):
        self.crawler.settings['URLS_PER_SECOND'] = int(self.spinbox_urls.get())

    def save_ua(self, e):
        value = self.combobox_ua.get()
        self.crawler.settings['USER_AGENT'] = self.user_agents[value]
        self.crawler.settings['UA_SHORT'] = value

    def save_proxy(self):
        self.crawler.settings['PROXY_HOST'] = self.var_host.get()
        self.crawler.settings['PROXY_USER'] = self.var_user.get()
        self.crawler.settings['PROXY_PASSWORD'] = self.var_password.get()

    def save_auth(self):
        self.crawler.settings['AUTH_USER'] = self.var_auth_user.get()
        self.crawler.settings['AUTH_PASSWORD'] = self.var_auth_password.get()

    def url_limit_clicked(self):
        if self.on_off_var.get() == 1:
            self.spinbox_urls['state'] = 'enabled'
            print('enabled', self.on_off_var.get())
        else:
            self.spinbox_urls['state'] = 'disabled'
            print('disabled', self.on_off_var.get())
