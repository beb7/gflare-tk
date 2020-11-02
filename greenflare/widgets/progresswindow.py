from tkinter import ttk, Toplevel, TOP
center_on_parent(self.master, self)


class ProgressWindow(Toplevel):

    def __init__(self, title=None, msg=None):
        Toplevel.__init__(self)

        self.topframe = ttk.Frame(self)
        self.topframe.pack(anchor='center', padx=20, pady=20, fill="x")

        if title:
            self.title(title)
        if msg:
            self.lbl = ttk.Label(self.topframe, text=msg)
            self.lbl.pack(padx=20, pady=20, side=TOP, expand=True)

        self.pb = ttk.Progressbar(
            self.topframe, orient='horizontal', mode='indeterminate')
        self.pb.pack(fill="x", pady=(0, 20), padx=20, side=TOP, expand=True)
        self.pb.start(50)

        center_on_parent(self.master, self)

        self.lift()
