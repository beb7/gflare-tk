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

from functools import partial, wraps
from csv import writer as csvwriter


def generate_menu(menu, labels, func):
    for label in labels:
        if label != '_':
            action_with_arg = partial(func, label)
            menu.add_command(label=label, command=action_with_arg)
        else:
            menu.add_separator()

def tk_after(target):
    @wraps(target)
    def wrapper(self, *args, **kwargs):
        args = (self,) + args
        self.after(0, target, *args, **kwargs)
 
    return wrapper

def _background_function(func, *args, event=None, **kwargs):
    func(*args, **kwargs)
    event.set()

def _callback_functions(funcs, *args, event=None, instance=None, **kwargs):
    event.wait()
    
    for func in funcs:
        func(instance)

def _spawn_progress_window(title=None, msg=None):
     from greenflare.widgets.progresswindow import ProgressWindow

     progress_window = ProgressWindow(title=title, msg=msg)
     progress_window.focus_force()
     progress_window.grab_set()
     return progress_window

def _close_progress_window(*args, wnd=None, **kwargs):
    if wnd:
        wnd.grab_release()
        wnd.destroy()
    else:
        from time import sleep
        print('Sleeping ...')
        sleep(0.5)
        close_progress_window(*args, wnd=wnd, **kwargs)

def run_in_background_with_window(callbacks, title=None, msg=None):
    from threading import Thread, Event

    def decorator(target):
        @wraps(target)
        def wrapper(*args, **kwargs):

            self = args[0]
            event = Event()
            wnd = _spawn_progress_window(title=title, msg=msg)
            main_func = partial(_background_function, target, *args,  event=event, **kwargs,)
            # callbacks.insert(0, partial(_close_progress_window, wnd=wnd))
            callbacks.append(partial(_close_progress_window, wnd=wnd))
            callback_func = partial(_callback_functions, callbacks, instance=self, event=event)

            Thread(target=callback_func).start()
            Thread(target=main_func).start()

        return wrapper
    return decorator


def _show_export_completed_msg(*args, **kwargs):
    from tkinter import messagebox
    messagebox.showinfo(title='Export completed', message=f'All data has been successfully exported!')

@run_in_background_with_window([], title='Exporting View ...', msg='Exporting to CSV, that might take a while ...')
def export_to_csv(csv_file, columns, data):

    with open(csv_file, "w", newline='', encoding='utf-8-sig') as csv_file:
        csv_writer = csvwriter(csv_file, delimiter=",", dialect='excel')
        csv_writer.writerow([i for i in columns])
        csv_writer.writerows(data)
