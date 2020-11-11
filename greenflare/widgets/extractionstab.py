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


class ExtractionsTab(ttk.Frame):

    def __init__(self, crawler=None):
        ttk.Frame.__init__(self)
        self.crawler = crawler
        self.widgets = []
        self.bind('<FocusOut>', self.save_extractions)

        self.center_frame = ttk.Frame(self, width=700)
        self.center_frame.pack(side='top', anchor='center',
                               fill='both', padx=20, pady=20)

        self.topframe = ttk.Frame(self.center_frame)
        self.topframe.pack(anchor='center', fill='x')

        self.button_add = ttk.Button(
            self.topframe, text='+', command=self.add_extraction)
        self.button_add.pack(side='right', padx=20)
        self.button_remove = ttk.Button(
            self.topframe, text='-', command=self.remove_extraction)
        self.button_remove['state'] = 'disabled'
        self.button_remove.pack(side='right')

        self.selectors = ['CSS Selector', 'XPath']

        self.add_extraction()

    def add_extraction(self):

        pad_x = (0, 10)

        self.widgets.append(ttk.Frame(self.center_frame))
        self.widgets[-1].pack(anchor='center', padx=20, pady=20, fill='x')

        self.entry_input_name = ttk.Entry(self.widgets[-1], width=20)
        self.entry_input_name.insert(0, f'Extraction {str(len(self.widgets))}')
        self.entry_input_name.pack(side='left', padx=pad_x)

        self.combobox_selector_type = ttk.Combobox(
            self.widgets[-1], values=self.selectors, state='readonly')
        self.combobox_selector_type.current(0)
        self.combobox_selector_type.pack(side='left', padx=pad_x)

        self.entry_input_selector_value = ttk.Entry(self.widgets[-1], width=75)
        self.entry_input_selector_value.pack(
            side='left', expand=True, fill='x')

        if len(self.widgets) == 10:
            self.button_add['state'] = 'disabled'
        if len(self.widgets) > 1:
            self.button_remove['state'] = 'enabled'

    def remove_extraction(self):
        self.widgets[-1].pack_forget()
        self.widgets[-1].destroy()
        self.widgets.pop()

        if len(self.widgets) < 2:
            self.button_remove['state'] = 'disabled'
        if len(self.widgets) < 10:
            self.button_add['state'] = 'enabled'

    def save_extractions(self, event):
        extractions = []

        for w in self.widgets:
            children = w.winfo_children()

            # Make name SQL friendly
            name = children[0].get().lower().replace(' ', '_')
            selector = children[1].get()
            value = children[2].get()

            if not value:
                continue

            # Do not allow to name a custom extraction
            # like an existing crawl item

            if name in self.crawler.settings.get('CRAWL_ITEMS', ''):
                name += '_custom'

            extractions.append((name, selector, value))

        # Only save extractions if there are any
        if extractions:
            self.crawler.settings['EXTRACTIONS'] = extractions

    def get_selector_value(self, selector):
        return self.selectors.index(selector)

    def update(self):
        try:
            if self.crawler.settings.get('EXTRACTIONS', []):
                counter = 1
                for name, selector, value in self.crawler.settings['EXTRACTIONS']:
                    if counter > 1:
                        self.add_extraction()

                    children = self.widgets[-1].winfo_children()

                    name = name.replace('_', ' ')
                    name_inp = children[0]
                    name_inp.delete(0, 'end')
                    name_inp.insert(0, name)

                    combo_selector = children[1]
                    combo_selector.current(self.get_selector_value(selector))

                    entry_input = children[2]
                    entry_input.delete(0, 'end')
                    entry_input.insert(0, value)

                    counter += 1

        except Exception as e:
            print('ERROR: Updating extractions tab failed!')
            print(e)
