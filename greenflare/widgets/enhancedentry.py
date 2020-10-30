from tkinter import ttk


class EnhancedEntry(ttk.Frame):

    def __init__(self, parent, default_text_):
        ttk.Frame.__init__(self, parent)
        self.default_text = default_text_

        self.style = ttk.Style()
        self.style.configure('Grey.TEntry', foreground='grey')
        self.style.configure('Black.TEntry', foreground='black')

        self.entry = ttk.Entry(parent, style='Grey.TEntry')
        self.entry.pack(side='left', padx=(0, 20), expand=True, fill='x')

        self.entry.insert(0, default_text_)
        self.entry.bind('<FocusIn>', self.handle_focus_in)
        self.entry.bind('<FocusOut>', self.handle_focus_out)

    def handle_focus_in(self, _):
        if self.entry.get() == self.default_text:
	        self.entry.delete(0, 'end')
	        self.entry.config(style='Black.TEntry')

    def handle_focus_out(self, _):
        if not self.entry.get().strip():
	        self.entry.delete(0, 'end')
	        self.entry.config(style='Grey.TEntry')
	        self.entry.insert(0, self.default_text)
