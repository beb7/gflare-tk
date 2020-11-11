# Code obtained from https://github.com/jarikmarwede/center-tk-window/
# MIT License

# Copyright (c) 2019 Jarik Marwede

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import tkinter
from typing import Union


def center_on_screen(window: Union[tkinter.Tk, tkinter.Toplevel]):
    """Center a window on the screen."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x_coordinate = int(window.winfo_screenwidth() / 2 - width / 2)
    y_coordinate = int(window.winfo_screenheight() / 2 - height / 2)

    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


def center_on_parent(root: tkinter.Tk, window: tkinter.Toplevel):
    """Center a window on its parent."""
    window.update_idletasks()
    height = window.winfo_height()
    width = window.winfo_width()
    parent = root.nametowidget(window.winfo_parent())
    x_coordinate = int(parent.winfo_x() +
                       (parent.winfo_width() / 2 - width / 2))
    y_coordinate = int(parent.winfo_y() +
                       (parent.winfo_height() / 2 - height / 2))

    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


def center(root: tkinter.Tk, window: Union[tkinter.Tk, tkinter.Toplevel]):
    """Center a window on its parent or the screen if there is no parent."""
    if window.winfo_parent():
        center_on_parent(root, window)
    else:
        center_on_screen(window)
