from tkinter import ttk, LEFT, RIGHT


class URLTab(ttk.Frame):

    def __init__(self, data):
        ttk.Frame.__init__(self)
        self.data = data

        self.lblframe_onpage = ttk.LabelFrame(self, text='On-Page Elements')
        self.lblframe_onpage.pack(side='left', padx=20, pady=20)

        self.onpage_elements = [
            ('URL:', self.data.get('url', '')),
            ('Page Title:', self.data.get('page_title', '')),
            ('Meta Description:', self.data.get('meta_description', ''))
         ]

        for name, text in self.onpage_elements:
            self.generate_label_group(self.lblframe_onpage, name, text)

        self.frame_bottom = ttk.Frame(self)
        self.frame_bottom.pack(anchor='w')

        self.btn_close = ttk.Button(
            self.frame_bottom, text='Close', command=self.destroy)
        self.btn_close.pack(anchor='e', padx=20, pady=20)

        print(data)


    def generate_label_group(self, lblframe, label_name, label_text):
        lbl_name = ttk.Label(lblframe, text=label_name, width=75)
        lbl_name.pack(anchor='w')

        lbl_text = ttk.Label(lblframe, text=label_text)
        lbl_text.pack()
