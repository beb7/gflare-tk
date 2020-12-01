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

import tkinter as tk
from tkinter import ttk, Menu, filedialog as fd, messagebox, TclError
from greenflare.core.gflarecrawler import GFlareCrawler
from greenflare.core.defaults import Defaults
from greenflare.widgets.crawltab import CrawlTab
from greenflare.widgets.settingstab import SettingsTab
from greenflare.widgets.exclusionstab import ExclusionsTab
from greenflare.widgets.extractionstab import ExtractionsTab
from greenflare.widgets.listcrawl import ListModeWindow
from greenflare.widgets.progresswindow import ProgressWindow
from greenflare.widgets.aboutwindow import AboutWindow
from greenflare.widgets.menuhelper import generate_menu
from concurrent import futures
from csv import writer as csvwriter
import functools
from threading import Lock
from os import path, remove
from pathlib import Path
import sys
import argparse


class mainWindow(ttk.Frame):

    def __init__(self, root, crawler=None):
        ttk.Frame.__init__(self)

        self.root = root
        self.crawler = crawler
        self.executor = futures.ThreadPoolExecutor(max_workers=1)
        self.tab_parent = ttk.Notebook()
        self.tab_crawl = CrawlTab(self, crawler, freeze_tabs=self.freeze_tabs, unfreeze_tabs=self.unfreeze_tabs)
        self.tab_settings = SettingsTab(crawler)
        self.tab_exclusions = ExclusionsTab(crawler)
        self.tab_extractions = ExtractionsTab(crawler)

        self.tab_parent.add(self.tab_crawl, text="Crawl")
        self.tab_parent.add(self.tab_settings, text="Settings")
        self.tab_parent.add(self.tab_exclusions, text="Exclusions")
        self.tab_parent.add(self.tab_extractions, text="Extractions")
        self.tab_parent.pack(expand=1, fill="both")
        self.master.title(Defaults.window_title)

        self.menubar = Menu(self)

        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="New", command=self.new_crawl)
        self.filemenu.add_command(label="Load Crawl", command=self.load_crawl)
        self.filemenu.add_separator()
        self.filemenu.add_command(
            label="Export View", command=self.export_view)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.modemenu = Menu(self.menubar, tearoff=0)
        self.modemenu.add_command(label="Spider", command=self.spider_mode)
        self.modemenu.add_command(label="List", command=self.list_mode)
        self.menubar.add_cascade(label="Mode", menu=self.modemenu)

        self.viewmenu = Menu(self.menubar, tearoff=0)
        self.viewmenu.add_command(
            label='All Crawl Data', command=self.show_crawl_output)

        self.inlinks_menu = Menu(self.viewmenu, tearoff=0)
        self.status_codes_menu = Menu(self.viewmenu, tearoff=0)
        self.content_types_menu = Menu(self.viewmenu, tearoff=0)
        self.crawl_status_menu = Menu(self.viewmenu, tearoff=0)

        self.viewmenu.add_cascade(
            label='Internal Links', menu=self.inlinks_menu)
        self.viewmenu.add_cascade(
            label='Status Codes', menu=self.status_codes_menu)
        self.viewmenu.add_cascade(
            label='Content Types', menu=self.content_types_menu)
        self.viewmenu.add_cascade(
            label='Crawl Status', menu=self.crawl_status_menu)
        self.menubar.add_cascade(label='View', menu=self.viewmenu)

        self.aboutmenu = Menu(self.menubar, tearoff=0)
        self.aboutmenu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=self.aboutmenu)

        inlinks_labels = [
            'Redirects (3xx)', 'Client Error (4xx)', 'Server Error (5xx)']
        generate_menu(self.inlinks_menu, inlinks_labels,
                      self.view_broken_inlinks)

        status_codes_labels = [
            'OK (200)', 'Redirects (3xx)', 'Client Error (4xx)', 'Server Error (5xx)']
        generate_menu(self.status_codes_menu,
                      status_codes_labels, self.view_status_codes)

        content_types_labels = ['HTML', 'Image',
                                'CSS', 'Font', 'JSON', 'XML', 'JavaScript']
        generate_menu(self.content_types_menu,
                      content_types_labels, self.view_content_types)

        crawl_status_labels = ['OK', 'Not OK',
                               'Canonicalised', 'Blocked By Robots', 'Noindex']
        generate_menu(self.crawl_status_menu,
                      crawl_status_labels, self.view_crawl_status)

        self.about_window = None
        self.root.config(menu=self.menubar)

    def daemonize(title=None, msg=None, callbacks=None):
        def decorator(target):
            @functools.wraps(target)
            def wrapper(*args, **kwargs):

                args[0].win_progress = ProgressWindow(title=title, msg=msg)
                args[0].win_progress.focus_force()
                args[0].win_progress.grab_set()

                result = args[0].executor.submit(target, *args, **kwargs)
                result.add_done_callback(args[0].daemon_call_back)

                if callbacks:
                    for func in callbacks:
                        result.add_done_callback(func)
                return result

            return wrapper

        return decorator

    def daemon_call_back(self, future):
        self.win_progress.grab_release()
        self.win_progress.destroy()
        exception = future.exception()
        if exception:
            raise exception

    def show_crawl_output(self):
        self.tab_crawl.load_crawl_to_outputtable(None, 'crawl')
        self.tab_crawl.viewed_table = 'crawl'
        self.tab_crawl.filters = []

    def load_crawl(self, db_file=None):
        files = [('Greenflare DB', f'*{Defaults.file_extension}'), ('All files', '.*')]

        if not db_file:
            db_file = fd.askopenfilename(filetypes=files)
        # Don't do anything if user does not select a file
        if not db_file:
            return

        try:
            self.crawler.load_crawl(db_file)

            if self.crawler.settings["MODE"] == "Spider":
                self.master.title(f"{self.crawler.settings['ROOT_DOMAIN']} - {Defaults.window_title}")
            elif self.crawler.settings["MODE"] == "List":
                self.tab_crawl.show_list_mode()

            self.update_gui()
            self.tab_crawl.freeze_input()
            self.tab_crawl.button_clear['state'] = 'enabled'
            self.show_crawl_output()
            self.tab_crawl.update_bottom_stats()
        except Exception as e:
            messagebox.showerror(title='Error - Invalid database',
                                 message=f'Could not load {db_file} as it is invalid!')
            print(e)

    def new_crawl(self):
        self.crawler.reset_crawl()
        self.crawler.settings = Defaults.settings.copy()
        self.tab_crawl.reset()

    def export_view(self):
        files = [('CSV files', '*.csv')]
        export_file = fd.asksaveasfilename(filetypes=files)

        if not export_file:
            return

        if not export_file.endswith(".csv"):
            export_file += ".csv"
        if path.isfile(export_file):
            remove(export_file)

        data = [self.tab_crawl.treeview_table.item(
            child)['values'] for child in self.tab_crawl.treeview_table.get_children()]

        self.export_to_csv(
            export_file, self.tab_crawl.treeview_table['columns'], data)

    def show_export_completed_msg(self):
        messagebox.showinfo(title='Export completed', message=f'All data has been successfully exported!')

    @daemonize(title="Exporting view ...", msg="Exporting to CSV, that might take a while ...", callbacks=[show_export_completed_msg])
    def export_to_csv(self, csv_file, columns, data):

        with open(csv_file, "w", newline='', encoding='utf-8-sig') as csv_file:
            csv_writer = csvwriter(csv_file, delimiter=",", dialect='excel')
            csv_writer.writerow([i for i in columns])
            csv_writer.writerows(data)

    def spider_mode(self):
        self.crawler.settings['MODE'] = 'Spider'
        self.tab_crawl.reset()

    def list_mode(self):
        lm_wnd = ListModeWindow(crawler=self.crawler,
                                crawl_tab=self.tab_crawl, root=self.root)

    def show_about(self):
        if not self.about_window:
            self.about_window = AboutWindow()
        elif self.about_window.winfo_exists() == 0:
            self.about_window = AboutWindow()
        else:
            pass

    def view_broken_inlinks(self, label):
        if '3xx' in label:
            table = 'broken_inlinks_3xx'
        elif '4xx' in label:
            table = 'broken_inlinks_4xx'
        elif '5xx' in label:
            table = 'broken_inlinks_5xx'

        try:
            self.tab_crawl.viewed_table = table
            self.tab_crawl.filters = []
            self.tab_crawl.load_crawl_to_outputtable(None, table)
        except Exception as e:
            print('ERROR: view_broken_inlinks failed!')
            print(e)

    def view_status_codes(self, label):
        if '200' in label:
            table = 'status_codes_200'
        elif '3xx' in label:
            table = 'status_codes_3xx'
        elif '4xx' in label:
            table = 'status_codes_4xx'
        elif '5xx' in label:
            table = 'status_codes_5xx'

        try:
            self.tab_crawl.viewed_table = table
            self.tab_crawl.filters = []
            self.tab_crawl.load_crawl_to_outputtable(None, table)
            self.tab_crawl.reset_filter_window()
        except Exception as e:
            print('ERROR: view_status_codes failed!')
            print(e)

    def view_content_types(self, label):
        content_type = label.lower()
        table = 'content_type_' + content_type

        try:
            self.tab_crawl.viewed_table = table
            self.tab_crawl.filters = []
            self.tab_crawl.load_crawl_to_outputtable(None, table)
        except Exception as e:
            print('ERROR: view_content_types failed!')
            print(e)

    def view_crawl_status(self, label):
        table_mapping = {
            'OK': 'crawl_status_ok',
            'Not OK': 'crawl_status_not_ok',
            'Canonicalised': 'crawl_status_canonicalised',
            'Blocked By Robots': 'crawl_status_blocked_by_robots',
            'Noindex': 'crawl_status_noindex'
        }

        table = table_mapping[label]

        try:
            self.tab_crawl.viewed_table = table
            self.tab_crawl.filters = []
            self.tab_crawl.load_crawl_to_outputtable(None, table)
        except Exception as e:
            print('ERROR: view_crawl_status failed!')
            print(e)

    def update_gui(self):
        self.tab_crawl.update()
        self.tab_settings.update()
        self.tab_exclusions.update()
        self.tab_extractions.update()

    def freeze_tabs(self):
        self.tab_parent.tab(self.tab_settings, state='disabled')
        self.tab_parent.tab(self.tab_exclusions, state='disabled')
        self.tab_parent.tab(self.tab_extractions, state='disabled')

    def unfreeze_tabs(self):
        self.tab_parent.tab(self.tab_settings, state='normal')
        self.tab_parent.tab(self.tab_exclusions, state='normal')
        self.tab_parent.tab(self.tab_extractions, state='normal')

    def on_closing(self):
        self.crawler.end_crawl_gracefully()
        self.master.destroy()

    def open_file_on_macos(self, *args):
        for f in args:
            if f.endswith(Defaults.file_extension):
                self.load_crawl(db_file=f)
            break

def main():
    # Check if Greenflare has been launched as part of a binary bundle as this
    # impacts the working_dir
    if getattr(sys, 'frozen', False):
        Defaults.set_working_dir(path.dirname(sys.executable))
    else:
        Defaults.set_working_dir(path.dirname(path.realpath(__file__)))

    # Linux specific settings
    if sys.platform == 'linux':

        import importlib
        check = importlib.util.find_spec("ttkthemes")

        # Use arc theme if available
        if check:
            from ttkthemes import ThemedTk
            root = ThemedTk(theme=Defaults.linux_theme)
        else:
            root = tk.Tk()

        # This ugly step is needed to initialise the filemanager variables we
        # are setting below
        try:
            root.tk.call('tk_getOpenFile', '-foobarbaz')
        except TclError:
            pass

        # Disable hidden files in file dialogues by default but show option to
        # show them
        root.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
        root.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')

    else:
        root = tk.Tk()

    root.geometry("1024x768")
    # macOS tkinter cannot handle iconphotos at the time being, disabling it
    # for now
    if sys.platform != "darwin":
        root.iconphoto(False, tk.PhotoImage(file=Defaults.root_icon()))

    globalLock = Lock()
    crawl_items = Defaults.crawl_items
    Settings = Defaults.settings.copy()
    Crawler = GFlareCrawler(settings=Settings, gui_mode=True, lock=globalLock)

    app = mainWindow(root, crawler=Crawler)

    # running on macOS
    if sys.platform == "darwin":
        # Use TK's Apple Event Handler to react to clicked/open documents
        root.createcommand("::tk::mac::OpenDocument", app.open_file_on_macos)

    # Parse and load db file if provided
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=Path, nargs='*')

    p = parser.parse_args()

    if p.file_path and p.file_path[0].exists():
        app.load_crawl(db_file=p.file_path[0])

    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()