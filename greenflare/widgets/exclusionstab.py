from tkinter import ttk
from re import escape


class ExclusionsTab(ttk.Frame):

    def __init__(self, crawler=None):
        ttk.Frame.__init__(self)
        self.crawler = crawler
        self.widgets = []
        self.bind('<FocusOut>', self.save_inexes)

        self.center_frame = ttk.Frame(self, width=700)
        self.center_frame.pack(side='top', anchor='center',
                               fill='both', padx=20, pady=20)

        self.topframe = ttk.Frame(self.center_frame)
        self.topframe.pack(anchor='center', fill='x')

        self.lbl_description = ttk.Label(
            self.topframe, text='Exclude URLs that:')
        self.lbl_description.pack(side='left', padx=20)

        self.button_add = ttk.Button(
            self.topframe, text='+', command=self.add_inex_widget)
        self.button_add.pack(side='right', padx=20)
        self.button_remove = ttk.Button(
            self.topframe, text='-', command=self.remove_inex_widget)
        self.button_remove['state'] = 'disabled'
        self.button_remove.pack(side='right')

        self.add_inex_widget()

    def add_inex_widget(self):

        pad_x = (0, 10)

        self.widgets.append(ttk.Frame(self.center_frame))
        self.widgets[-1].pack(anchor='center', padx=20, pady=20, fill='x')

        self.operators = [
            'Contain', 'Equal to (=)', 'Start with', 'End with', 'Regex match']
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

    def remove_inex_widget(self):
        self.widgets[-1].pack_forget()
        self.widgets[-1].destroy()
        self.widgets.pop()

        if len(self.widgets) < 2:
            self.button_remove['state'] = 'disabled'
        if len(self.widgets) < 10:
            self.button_add['state'] = 'enabled'

    def save_inexes(self, event):

        if len(self.widgets) == 1 and self.widgets[0].winfo_children()[1] == '':
            self.crawler.settings['EXCLUSIONS'] = []

        exclusions = []

        for w in self.widgets:
            children = w.winfo_children()
            operator = children[0].get()
            value = children[1].get()

            exclusions.append((operator, value))

        self.crawler.settings['EXCLUSIONS'] = exclusions

        print(exclusions)

    def update(self):

        children = self.widgets[-1].winfo_children()
        children[-2].current(4)
        children[3].insert(0, self.crawler.settings.get('EXCLUSIONS', ''))
