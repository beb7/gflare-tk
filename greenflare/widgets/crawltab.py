from tkinter import LEFT, RIGHT, ttk, W, NO, filedialog as fd, messagebox, StringVar, Menu
from widgets.progresswindow import ProgressWindow
from widgets.filterwindow import FilterWindow
from widgets.enhancedentry import EnhancedEntry
from core.defaults import Defaults
from concurrent import futures
import functools
from functools import partial
from os import path, remove
from webbrowser import open as open_in_browser
import queue
import sys


class CrawlTab(ttk.Frame):

    def __init__(self, root, crawler=None):
        ttk.Frame.__init__(self)
        self.root = root
        self.crawler = crawler
        self.lock = crawler.lock

        self.executor = futures.ThreadPoolExecutor(max_workers=1)
        self.win_progress = None

        self.topframe = ttk.Frame(self)
        self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

        self.entry_url_input = EnhancedEntry(
            self.topframe, 'Enter URL to crawl')
        self.entry_url_input.entry.bind('<Return>', self.enter_hit)

        self.button_crawl = ttk.Button(
            self.topframe, text="Start", command=self.btn_crawl_pushed)
        self.button_crawl.pack(side=LEFT, padx=(0, 20))

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
            self.middle_frame, selectmode="browse")

        # Capture right clicks on table
        right_click = '<Button-3>'

        if sys.platform == 'darwin':
            right_click = '<Button-2>'

        self.treeview_table.bind(right_click, self.assign_treeview_click)

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
        self.urls_crawled_string_var.set("URLs crawled/discovered: 0/0")
        self.label_urls_crawled = ttk.Label(
            self.bottom_frame, textvariable=self.urls_crawled_string_var)
        self.label_urls_crawled.pack(side=RIGHT)

        self.populate_columns()
        self.row_counter = 1

        # pop up menu for treeview header items
        self.popup_menu = Menu(self, tearoff=0)
        self.popup_menu.add_command(
            label='Reset Filters', command=self.load_crawl_to_outputtable)
        self.popup_menu.add_separator()
        labels = Defaults.popup_menu_labels
        self.generate_menu(self.popup_menu, labels, self.show_filter_window)
        self.selected_column = ''

        self.filter_window = None

        # action menu for treeview row items
        self.action_menu = Menu(self, tearoff=0)
        #labels = ['Copy URL', 'Open URL in Browser', '_', 'Inspect']
        labels = ['Copy URL', 'Open URL in Browser']
        self.generate_menu(self.action_menu, labels, self.show_action_window)
        self.row_values = []
        self.suspend_auto_scroll = False

    def daemonize(title=None, msg=None):
        def decorator(target):
            @functools.wraps(target)
            def wrapper(*args, **kwargs):
                args[0].win_progress = ProgressWindow(title=title, msg=msg)
                args[0].win_progress.focus_force()
                args[0].win_progress.grab_set()
                result = args[0].executor.submit(target, *args, **kwargs)
                result.add_done_callback(args[0].daemon_call_back)
                return result

            return wrapper

        return decorator

    def daemon_call_back(self, future):
        self.win_progress.grab_release()
        self.win_progress.destroy()
        exception = future.exception()
        if exception:
            raise exception

    def clear_output_table(self):
        # Clear table
        self.treeview_table.delete(*self.treeview_table.get_children())
        self.row_counter = 1

    def populate_columns(self):
        columns = Defaults.display_columns.copy()
        if self.crawler.columns:
            columns = self.crawler.columns.copy()
            # if 'unique_inlinks' in columns: columns.remove('unique_inlinks')

        items = [i.title().replace("_", " ") for i in columns]
        items[items.index("Url")] = "URL"
        items[items.index("Redirect Url")] = "Redirect URL"

        self.treeview_table["columns"] = tuple(items)
        self.treeview_table.heading("#0", text="id", anchor=W)
        self.treeview_table.column("#0", width=50, stretch=False)
        self.treeview_table.heading("URL", text="URL", anchor=W)
        self.treeview_table.column("URL", width=750, stretch=False)

        # Set width and stretch for all other columns
        for e in self.treeview_table["columns"][1:]:
            self.treeview_table.heading(e, text=e, anchor=W)
            self.treeview_table.column(e, width=85, stretch=False)

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
            self.after(10, self.change_btn_text)

    @daemonize(title="Stopping crawl ...", msg="Waiting for crawl to finish ...")
    def stop_crawl(self):
        self.crawler.end_crawl_gracefully()
        self.after(10, self.change_btn_text)

    def btn_crawl_pushed(self):
        url = self.entry_url_input.entry.get().strip()
        if self.button_crawl["text"] == "Start":
            # Validate input url
            url_components = self.crawler.gf.parse_url(url)

            if self.crawler.settings.get('MODE', '') == 'Spider':

                if url_components['scheme'] == '':
                    url = 'http://' + url
                    url_components = self.crawler.gf.parse_url(url)
                    print(url_components, url)

                if url_components['netloc'] == '' or ' ' in url_components['netloc']:
                    messagebox.showerror(
                        title='Invalid URL', message='Please enter a valid URL!')
                    return

            url = self.crawler.gf.url_components_to_str(url_components)

            self.entry_url_input.entry.delete(0, 'end')
            self.entry_url_input.entry.insert(0, url)

            self.start_new_crawl(url)

        elif self.button_crawl["text"] == "Pause":
            self.stop_crawl()

        elif self.button_crawl["text"] == "Resume":
            self.populate_columns()
            self.crawler.resume_crawl()
            self.after(10, self.add_to_outputtable)
            self.after(10, self.change_btn_text)

        elif self.button_crawl["text"] == "Restart":
            self.start_new_crawl(url)

        print(self.crawler.settings)

    def change_btn_text(self):
        btn_txt = self.button_crawl["text"]
        if btn_txt == "Start":
            self.button_crawl["text"] = "Pause"
        elif btn_txt == "Pause":
            self.button_crawl["text"] = "Resume"
        elif btn_txt == "Resume":
            self.button_crawl["text"] = "Pause"
        elif btn_txt == "Restart":
            self.button_crawl["text"] = "Pause"

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
                self.add_item_to_outputtable(item)

            self.update_progressbar()
            self.update_bottom_stats()

        if self.crawler.crawl_completed.is_set():
            self.button_crawl["text"] = "Restart"
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
            self.update_bottom_stats()
            return
        if self.crawler.crawl_running.is_set():
            self.update_bottom_stats()
            return

        self.after(250, self.add_to_outputtable)

    # @daemonize(title="Loading crawl ...", msg="Please wait while the crawl is loading ...")
    def load_crawl_to_outputtable(self, filters=None):
        if not filters:
            self.master.title(
                self.master.title().replace(' (Filtered View)', ''))

        items = self.crawler.get_crawl_data(filters=filters)
        self.clear_output_table()
        for item in items:
            self.add_item_to_outputtable(item)

    def update_progressbar(self):
        with self.lock:
            if self.crawler.urls_total > 0:
                percentage = int((self.crawler.urls_crawled /
                                  self.crawler.urls_total) * 100)
                self.progressbar["value"] = percentage
                if sys.platform == "win32":
                    self.style.configure('text.Horizontal.TProgressbar', text=f'{percentage} %')

    def update_bottom_stats(self):
        with self.lock:
            self.urls_string_var.set(f"Speed: {self.crawler.current_urls_per_second} URL/s")
            self.urls_crawled_string_var.set(f"URLs crawled/discovered: {self.crawler.urls_crawled}/{self.crawler.urls_total}")

    def update(self):
        self.button_crawl["text"] = "Resume"
        self.entry_url_input.entry['state'] = 'enabled'
        self.entry_url_input.entry.delete(0, 'end')
        self.entry_url_input.entry.insert(
            0, self.crawler.settings["STARTING_URL"])
        self.row_counter = self.crawler.urls_crawled
        self.populate_columns()
        self.update_progressbar()

    def reset(self):
        self.entry_url_input.entry["state"] = "enabled"
        self.entry_url_input.entry.delete(0, 'end')
        self.entry_url_input.entry.insert(0, "Enter URL to crawl")
        self.progressbar["value"] = 0
        self.clear_output_table()
        self.populate_columns()
        self.button_crawl["text"] = "Start"
        self.suspend_auto_scroll = False

    def show_list_mode(self):
        self.reset()
        self.master.title(f'List Mode - {Defaults.window_title}')
        self.entry_url_input.entry.delete(0, 'end')
        self.entry_url_input.entry.insert(0, "List Mode ...")
        self.freeze_input()

    def freeze_input(self):
        self.entry_url_input.entry["state"] = "disabled"

    def generate_menu(self, menu, labels, func):
        for label in labels:
            if label != '_':
                action_with_arg = partial(func, label)
                menu.add_command(label=label, command=action_with_arg)
            else:
                menu.add_separator()

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
        columns = Defaults.display_columns.copy()
        if self.crawler and self.crawler.columns:
            columns = self.crawler.columns.copy()
        if 'Sort' in label:
            print('>>>', label)
            self.load_crawl_to_outputtable(
                filters=([(self.selected_column.lower().replace(' ', '_'), label, '')]))
            return
        if not self.filter_window:
            self.filter_window = FilterWindow(self, label, self.selected_column, columns, title=f'Filter By {self.selected_column}')
        elif self.filter_window.winfo_exists() == 0:
            self.filter_window = FilterWindow(self, label, self.selected_column, columns, title=f'Filter By {self.selected_column}')
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
        elif label == 'Inspect' and url:
            print(self.row_values)
            self.root.add_url_tab(
                dict(zip(self.crawler.columns, self.row_values)))

    def vertical_scrollbar_clicked(self, *args, **kwargs):
        self.treeview_table.yview(*args, **kwargs)
        if float(args[1]) < 0.95:
            self.suspend_auto_scroll = True
        else:
            self.suspend_auto_scroll = False
