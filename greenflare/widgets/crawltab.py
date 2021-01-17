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

from tkinter import LEFT, RIGHT, ttk, W, NO, filedialog as fd, messagebox, StringVar, Menu
from greenflare.widgets.progresswindow import ProgressWindow
from greenflare.widgets.filterwindow import FilterWindow
from greenflare.widgets.enhancedentry import EnhancedEntry
from greenflare.widgets.viewinlinks import ViewInlinks
from greenflare.widgets.helpers import generate_menu
from greenflare.core.defaults import Defaults
from greenflare.widgets.helpers import run_in_background_with_window, tk_after
from os import path, remove
from webbrowser import open as open_in_browser
from urllib.parse import urlsplit, urlunsplit
import queue
import sys


class CrawlTab(ttk.Frame):

    def __init__(self, root, crawler=None, freeze_tabs=None, unfreeze_tabs=None):
        ttk.Frame.__init__(self)
        self.root = root
        self.crawler = crawler
        self.lock = crawler.lock
        self.freeze_tabs = freeze_tabs
        self.unfreeze_tabs = unfreeze_tabs

        self.topframe = ttk.Frame(self)
        self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

        self.entry_url_input = EnhancedEntry(
            self.topframe, 'Enter URL to crawl')
        self.entry_url_input.entry.bind('<Return>', self.enter_hit)

        self.button_crawl = ttk.Button(
            self.topframe, text="Start", command=self.btn_crawl_pushed)
        self.button_crawl.pack(side=LEFT, padx=(0, 20))

        self.button_clear = ttk.Button(self.topframe, text="Clear", command=self.btn_clear_pushed)
        self.button_clear.pack(side=LEFT, padx=(0, 20))
        self.button_clear['state'] = 'disabled'

        # macOS and linux have issues with the below style so only use it on
        # windows for now
        if sys.platform != "win32":
            self.progressbar = ttk.Progressbar(
                self.topframe, orient="horizontal", length=150, mode="determinate", maximum=100, value=0)
        elif sys.platform == "win32":
            self.style = ttk.Style(self)
            self.style.layout('text.Horizontal.TProgressbar', [('Horizontal.Progressbar.trough', {'children': [('Horizontal.Progressbar.pbar', {
                              'side': 'left', 'sticky': 'ns'})], 'sticky': 'nswe'}), ('Horizontal.Progressbar.label', {'sticky': ''})])
            self.style.configure('text.Horizontal.TProgressbar', text='0 %')
            self.progressbar = ttk.Progressbar(self.topframe, orient="horizontal", length=150,
                                               mode="determinate", maximum=100, value=0, style='text.Horizontal.TProgressbar')

        self.progressbar.pack(side=LEFT, fill="x")

        self.middle_frame = ttk.Frame(self)
        self.middle_frame.pack(anchor='center', fill='both', expand=True)

        self.treeview_table = ttk.Treeview(
            self.middle_frame, selectmode='browse')

        # Capture left clicks on table
        # Left clicks work best on all three platforms (right clicks are tricky on darwin)
        left_click = '<Button-1>'

        self.treeview_table.bind(left_click, self.assign_treeview_click)

        self.scrollbar_vertical = ttk.Scrollbar(
            self.middle_frame, orient="vertical", command=self.vertical_scrollbar_clicked)
        self.scrollbar_vertical.pack(side="right", fill="y")
        self.scrollbar_horizontal = ttk.Scrollbar(
            self.middle_frame, orient="horizontal", command=self.treeview_table.xview)
        self.scrollbar_horizontal.pack(side="bottom", fill="x")
        self.treeview_table.configure(
            yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=self.scrollbar_horizontal.set)
        self.treeview_table.pack(fill="both", expand=1)

        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(anchor='center', padx=5, pady=5, fill='x')

        self.urls_string_var = StringVar()
        self.urls_string_var.set("Speed: - URL/s")
        self.label_urls_per_second = ttk.Label(
            self.bottom_frame, textvariable=self.urls_string_var)
        self.label_urls_per_second.pack(side=LEFT)

        self.urls_crawled_string_var = StringVar()
        self.urls_crawled_string_var.set("URLs crawled/discovered: 0/0 (0%)")
        self.label_urls_crawled = ttk.Label(
            self.bottom_frame, textvariable=self.urls_crawled_string_var)
        self.label_urls_crawled.pack(side=RIGHT)

        self.percentage = 0

        self.populate_columns()
        self.row_counter = 1

        # pop up menu for treeview header items
        self.popup_menu = Menu(self, tearoff=0)
        self.popup_menu.add_command(
            label='Reset Filters', command=self.reset_filters)
        self.popup_menu.add_separator()
        labels = Defaults.popup_menu_labels
        generate_menu(self.popup_menu, labels, self.show_filter_window)
        self.selected_column = ''

        self.filter_window = None

        # action menu for treeview row items
        self.action_menu = Menu(self, tearoff=0)
        labels = ['Copy URL', 'Open URL in Browser', '_', 'View Inlinks']
        generate_menu(self.action_menu, labels, self.show_action_window)
        self.row_values = []
        self.suspend_auto_scroll = False

        self.viewed_table = 'crawl'
        self.filters = []

    def clear_output_table(self):
        # Clear table
        self.treeview_table.delete(*self.treeview_table.get_children())
        self.row_counter = 1

    def get_display_columns(self, table=None):
        if not table:
            if self.crawler.columns:
                return self.crawler.columns.copy()
            return Defaults.display_columns.copy()
        return self.crawler.get_columns(table)

    def populate_columns(self, columns=None):
        column_default_width = 80
        column_url_width = 700
        column_titles_width = 250

        display_column_mapping = {
            'url': ('URL', column_url_width),
            'redirect_url': ('Redirect URL', column_url_width),
            'canonical_tag': ('Canonical Tag', column_url_width),
            'content_type': ('Content Type', 100),
            'h1': ('H1', column_titles_width),
            'page_title': ('Page Title', column_titles_width),
            'url_from': ('URL From', column_url_width),
            'url_to': ('URL To', column_url_width)
        }

        if not columns:
            columns = self.get_display_columns()

        self.treeview_table["columns"] = tuple(columns)

        self.treeview_table.heading("#0", text="id", anchor=W)
        self.treeview_table.column("#0", width=55, stretch=False)

        for e in self.treeview_table["columns"]:
            name, width = display_column_mapping.get(e, (None, None))
            if not name:
                name = e.replace('_', ' ').title()
                width = column_default_width

            self.treeview_table.heading(e, text=name, anchor=W)
            self.treeview_table.column(e, width=width, stretch=False)

    def enter_hit(self, event=None):
        self.btn_crawl_pushed()

    def start_new_crawl(self, url):
        files = [('Greenflare DB', f'*{Defaults.file_extension}'), ('All files', '.*')]
        db_file = fd.asksaveasfilename(filetypes=files)
        if db_file:
            if not db_file.endswith(Defaults.file_extension):
                db_file += Defaults.file_extension
            if path.isfile(db_file):
                remove(db_file)
            self.crawler.reset_crawl()
            self.run_first_time = False
            self.crawler.db_file = db_file
            self.crawler.settings["STARTING_URL"] = url
            self.entry_url_input.entry["state"] = "disabled"
            self.crawler.start_crawl()
            self.clear_output_table()
            self.populate_columns()
            self.master.title(f"{self.crawler.gf.get_domain(self.crawler.settings['STARTING_URL'])} - {Defaults.window_title}")

            self.after(10, self.add_to_outputtable)
            self.after(10, self.update_buttons)

    @run_in_background_with_window([], title='Stopping crawl ...', msg='Waiting for crawl to finish ...')
    def stop_crawl(self):
        self.crawler.end_crawl_gracefully()
        self.after(10, self.update_buttons)

    def btn_crawl_pushed(self):
        url = self.entry_url_input.get().strip()

        if self.button_crawl['text'] == 'Start':
            # Validate input url
            url_components = urlsplit(url)

            if self.crawler.settings.get('MODE', '') == 'Spider':

                if url_components.scheme == '':
                    url = 'http://' + url
                    url_components = urlsplit(url)

                if url_components.netloc == '' or ' ' in url_components.netloc:
                    messagebox.showerror(
                        title='Invalid URL', message='Please enter a valid URL!')
                    return

            url = urlunsplit(url_components)
            url = self.crawler.gf.sanitise_url(url, base_url='')

            self.entry_url_input.entry.delete(0, 'end')
            self.entry_url_input.entry.insert(0, url)

            self.start_new_crawl(url)

        elif self.button_crawl["text"] == "Pause":
            self.stop_crawl()

        elif self.button_crawl["text"] == "Resume":
            self.populate_columns()
            self.crawler.resume_crawl()
            self.row_counter = self.crawler.urls_crawled + 1
            self.after(10, self.add_to_outputtable)
            self.after(10, self.update_buttons)

        elif self.button_crawl["text"] == "Restart":
            self.start_new_crawl(url)

    def update_buttons(self):
        btn_txt = self.button_crawl["text"]
        if btn_txt == "Start":
            self.button_crawl["text"] = "Pause"
            self.button_clear['state'] = 'disabled'
            self.freeze_tabs()
        elif btn_txt == "Pause":
            self.button_crawl["text"] = "Resume"
            self.button_clear['state'] = 'enabled'
            self.unfreeze_tabs()
        elif btn_txt == "Resume":
            self.button_crawl["text"] = "Pause"
            self.button_clear['state'] = 'enabled'
            self.freeze_tabs()
        elif btn_txt == "Restart":
            self.button_crawl["text"] = "Pause"
            self.button_clear['state'] = 'enabled'

    def btn_clear_pushed(self):
        msg = messagebox.askquestion ('Clear View','Are you sure you want clear the view? All data has been saved.', icon = 'warning')
        
        if msg == 'yes':
            self.reset(reset_url_input=False)
        else:
            return
        
    def add_item_to_outputtable(self, item):
        self.treeview_table.insert(
            '', 'end', text=self.row_counter, values=item)
        with self.lock:
            self.row_counter += 1

        # Allow user to scroll up and only continue autoscroll if the
        # scroll bar is near the bottom edge
        if not self.suspend_auto_scroll:
            self.treeview_table.yview_moveto(1)

    def add_to_outputtable(self):
        items = []

        with self.lock:
            if self.crawler.gui_url_queue:
                items = self.crawler.gui_url_queue.copy()
                self.crawler.gui_url_queue = []

        if len(items) > 0:
            for item in items:
                # item = self.remove_unicode_from_item(item)
                self.add_item_to_outputtable(item)

            self.update_progressbar()
            self.update_bottom_stats()

        if self.crawler.crawl_completed.is_set():
            self.button_crawl["text"] = "Restart"
            self.unfreeze_tabs()
            self.button_clear['state'] = 'enabled'
            if self.crawler.settings.get("MODE", "") == "Spider":
                messagebox.showinfo(title='Crawl completed', message=f'{self.crawler.settings.get("ROOT_DOMAIN", "")} has been crawled successfully!')
            else:
                messagebox.showinfo(
                    title='Crawl completed', message='List Mode Crawl has been completed successfully!')
            self.update_bottom_stats()
            return
        if self.crawler.crawl_timed_out.is_set():
            messagebox.showerror(title='Error - Timed Out',
                                 message='Crawl timed out!')
            self.button_crawl["text"] = "Resume"
            self.button_clear['state'] = 'enabled'
            self.update_bottom_stats()
            return
        if self.crawler.crawl_running.is_set():
            self.update_bottom_stats()
            return

        self.after(250, self.add_to_outputtable)

    @tk_after
    def add_items(self, items):
        for i, item in enumerate(items, 1):
            self.treeview_table.insert('', 'end', text=i, values=item)

    @run_in_background_with_window([], title='Loading crawl ...', msg='Please wait while the data is being loaded ...')
    def load_crawl_to_outputtable(self, filters, table, columns=None):
        self.suspend_auto_scroll = True

        if not filters:
            self.master.title(
                self.master.title().replace(' (Filtered View)', ''))

        if not table:
            table = self.viewed_table

        self.clear_output_table()
        columns, items = self.crawler.get_crawl_data(
            filters, table, columns)
        self.populate_columns(columns=columns)

        self.add_items(items)

        self.suspend_auto_scroll = False
        self.treeview_table.yview_moveto(1)

    def update_progressbar(self):
        with self.lock:
            if self.crawler.urls_total > 0:
                self.percentage = int((self.crawler.urls_crawled /
                                  self.crawler.urls_total) * 100)
                self.progressbar["value"] = self.percentage
                if sys.platform == "win32":
                    self.style.configure('text.Horizontal.TProgressbar', text=f'{self.percentage} %')

    def update_bottom_stats(self):
        with self.lock:
            self.urls_string_var.set(f"Speed: {self.crawler.current_urls_per_second} URL/s")
            self.urls_crawled_string_var.set(f"URLs crawled/discovered: {'{:,}'.format(self.crawler.urls_crawled)}/{'{:,}'.format(self.crawler.urls_total)} ({self.percentage}%)")

    def update(self):
        self.button_crawl["text"] = "Resume"
        self.entry_url_input.entry['state'] = 'enabled'
        self.entry_url_input.entry.delete(0, 'end')
        self.entry_url_input.entry.insert(
            0, self.crawler.settings["STARTING_URL"])
        self.row_counter = self.crawler.urls_crawled
        self.populate_columns()
        self.update_progressbar()

    def reset(self, reset_url_input=True):
        self.entry_url_input.entry["state"] = "enabled"
        
        if reset_url_input:
            self.entry_url_input.entry.delete(0, 'end')
            self.entry_url_input.entry.insert(0, "Enter URL to crawl")
        
        self.progressbar["value"] = 0
        self.clear_output_table()
        self.populate_columns()
        self.button_crawl["text"] = "Start"
        self.suspend_auto_scroll = False
        self.filters = None
        self.reset_filter_window()
        self.crawler.reset_crawl()
        self.master.title(Defaults.window_title)

    def show_list_mode(self):
        self.reset()
        self.master.title(f'List Mode - {Defaults.window_title}')
        self.entry_url_input.entry.delete(0, 'end')
        self.entry_url_input.entry.insert(0, "List Mode ...")
        self.freeze_input()

    def freeze_input(self):
        self.entry_url_input.entry["state"] = "disabled"

    def assign_treeview_click(self, event):

        region = self.treeview_table.identify("region", event.x, event.y)

        if region == 'cell':

            iid = self.treeview_table.identify_row(event.y)

            if iid:
                self.treeview_table.selection_set(iid)
                item = self.treeview_table.selection()
                self.row_values = self.treeview_table.item(item)['values']

                try:
                    self.action_menu.tk_popup(
                        event.x_root, event.y_root + 20, 0)
                finally:
                    self.action_menu.grab_release()

        elif region == 'heading':
            col = self.treeview_table.identify_column(event.x)
            self.selected_column = self.treeview_table.heading(col)['text']

            try:
                self.popup_menu.tk_popup(event.x_root, event.y_root + 20, 0)
            finally:
                self.popup_menu.grab_release()

    def show_filter_window(self, label):
        columns = self.get_display_columns()

        if self.viewed_table != 'crawl':
            columns = self.get_display_columns(self.viewed_table)
        if 'Sort' in label:
            column = self.selected_column.lower().replace(' ', '_')
            print('Sorting column', column)
            
            # Remove previous sorting filters
            self.filters = [t for t in self.filters if 'Sort' not in t[1]]
            self.filters.append((column, label, ''))
            self.load_crawl_to_outputtable(self.filters, self.viewed_table, columns=columns)
            return

        # Window has never been initialised
        if not self.filter_window:
            self.filter_window = FilterWindow(self, label, self.selected_column, columns, table=self.viewed_table, title=f'Filter By {self.selected_column}')
        # window has been initialised but has been closed
        elif self.filter_window.winfo_exists() == 0:
            self.filter_window = FilterWindow(self, label, self.selected_column, columns, table=self.viewed_table, title=f'Filter By {self.selected_column}')
        else:
            self.filter_window.update()
            self.filter_window.deiconify()


    def show_action_window(self, label):
        url = ''

        if self.row_values:
            url = self.row_values[0]

        if label == 'Copy URL' and url:
            self.master.clipboard_clear()
            self.master.clipboard_append(url)
        elif label == 'Open URL in Browser' and url:
            open_in_browser(url, new=2)
        elif label == 'View Inlinks' and url:
            ViewInlinks(url, self.crawler.get_inlinks)

    def vertical_scrollbar_clicked(self, *args, **kwargs):
        self.treeview_table.yview(*args, **kwargs)
        if float(args[1]) < 0.95:
            self.suspend_auto_scroll = True
        else:
            self.suspend_auto_scroll = False

    def reset_filters(self):
        self.load_crawl_to_outputtable(None, self.viewed_table)

    def reset_filter_window(self):
        if not self.filter_window:
            return

        self.filter_window = None