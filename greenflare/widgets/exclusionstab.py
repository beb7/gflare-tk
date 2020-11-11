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
from re import escape


class ExclusionsTab(ttk.Frame):

    def __init__(self, crawler=None):
        ttk.Frame.__init__(self)
        self.crawler = crawler
        self.widgets = []
        self.bind('<FocusOut>', self.save_exclusions)

        self.center_frame = ttk.Frame(self, width=700)
        self.center_frame.pack(side='top', anchor='center',
                               fill='both', padx=20, pady=20)

        self.topframe = ttk.Frame(self.center_frame)
        self.topframe.pack(anchor='center', fill='x')

        self.lbl_description = ttk.Label(
            self.topframe, text='Exclude URLs that:')
        self.lbl_description.pack(side='left', padx=20)

        self.button_add = ttk.Button(
            self.topframe, text='+', command=self.add_exclusion_widget)
        self.button_add.pack(side='right', padx=20)
        self.button_remove = ttk.Button(
            self.topframe, text='-', command=self.remove_exclusion_widget)
        self.button_remove['state'] = 'disabled'
        self.button_remove.pack(side='right')

        self.operators = [
            'Contain', 'Equal to (=)', 'Start with', 'End with', 'Regex match']
        self.add_exclusion_widget()

    def add_exclusion_widget(self):

        pad_x = (0, 10)

        self.widgets.append(ttk.Frame(self.center_frame))
        self.widgets[-1].pack(anchor='center', padx=20, pady=20, fill='x')

        self.combobox_op = ttk.Combobox(
            self.widgets[-1], values=self.operators, state='readonly')
        self.combobox_op.current(0)
        self.combobox_op.pack(side='left', padx=pad_x)

        self.entry_inex_input = ttk.Entry(self.widgets[-1])
        self.entry_inex_input.pack(side='left', expand=True, fill='x')

        if len(self.widgets) == 10:
            self.button_add['state'] = 'disabled'
        if len(self.widgets) > 1:
            self.button_remove['state'] = 'enabled'

    def remove_exclusion_widget(self):
        self.widgets[-1].pack_forget()
        self.widgets[-1].destroy()
        self.widgets.pop()

        if len(self.widgets) < 2:
            self.button_remove['state'] = 'disabled'
        if len(self.widgets) < 10:
            self.button_add['state'] = 'enabled'

    def save_exclusions(self, event):
        exclusions = []

        for w in self.widgets:
            children = w.winfo_children()
            operator = children[0].get()
            value = children[1].get().strip()
            if not value:
                continue

            exclusions.append((operator, value))

        if exclusions:
            self.crawler.settings['EXCLUSIONS'] = exclusions

    def get_operator_value(self, operator):
        return self.operators.index(operator)

    def update(self):
        try:
            if self.crawler.settings.get('EXCLUSIONS', []):
                counter = 1
                for operator, value in self.crawler.settings['EXCLUSIONS']:
                    if counter > 1:
                        self.add_exclusion_widget()

                    children = self.widgets[-1].winfo_children()
                    combobox_op = children[0]
                    combobox_op.current(self.get_operator_value(operator))
                    entry_input = children[1]
                    entry_input.delete(0, 'end')
                    entry_input.insert(0, value)
                    counter += 1

        except Exception as e:
            print('ERROR: Updating exclusion tab failed!')
            print(e)
