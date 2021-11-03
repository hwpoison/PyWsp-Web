from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.ttk as ttk

from threading import Thread
import pathlib
import time

import pywsp

class MultiColumnListbox:
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, col_headers, row_data):
        self.tree = None
        self.container = None
        self.col_headers = col_headers
        self.row_data = row_data
        self._setup_widgets()
        self._build_tree()

    def _setup_widgets(self):
        # set up the treeview
        self.container = ttk.Frame()
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(columns=self.col_headers, show="headings")
        # set treeview font size
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Monospace", 11))
        # set treeview row font size
        style.configure("Treeview", font=("Monospace", 11))

        vsb = ttk.Scrollbar(orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self.container)
        vsb.grid(column=1, row=0, sticky='ns', in_=self.container)
        hsb.grid(column=0, row=1, sticky='ew', in_=self.container)

        # set the frame resizing priorities
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def _build_tree(self):
        for col in self.col_headers:
            self.tree.heading(col, text=col.title(),
                              command=lambda c=col: self.sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col,
                             width=tkFont.Font().measure(col.title())+15)

        for ix, item in enumerate(self.row_data):

            self.tree.insert('', 'end', values=item, tags=str(ix))
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkFont.Font().measure(val)
                if self.tree.column(self.col_headers[ix], width=None) < col_w:
                    self.tree.column(self.col_headers[ix], width=col_w)

    def sortby(self, tree, col, descending):
        """ sort tree contents when a column header is clicked on """
        # grab values to sort
        data = [(tree.set(child, col), child)
                for child in tree.get_children('')]
        # if the data to be sorted is numeric change to float
        #data =  change_numeric(data)

        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        # switch the heading so it will sort in the opposite direction
        tree.heading(col, command=lambda col=col: self.sortby(tree, col,
                                                              int(not descending)))


class Window:
    def __init__(self, master):
        self.main = master
        self.actual_selection = None
        self.actual_selection_idx = None
        self.contacts_filename = "contacts.csv"
        # vars
        self.amount_files = StringVar()
        self.amount_files.set('Ninguno')
        self.actual_attachment = []

        pywsp.load_configuration()
        self.load_gui()
        self.init_gui()

        self.check_driver_thread()

    def init_window(self):
        self.main.title("Whattasap! (by:hwpoison)")
        self.main.geometry("350x650+700+20")
        self.main.resizable(False, False)
        # set window icon from .ico
        self.main.iconbitmap(r'icon.ico')
        self.load_contacts_list()
        self.main.mainloop()

    def init_driver(self):
        print("[UI]Initializing driver...")
        messagebox.showinfo(
            "Atención!",
            "A continuación se va a abrir Whatsapp Web, escaneá el código QR antes de efectuar alguna acción!")
        Thread(target=pywsp.browser.open_whatsapp).start()

    def quit_driver(self):
        print("[UI]Quitting driver...")
        if not self.driver_is_opened():
            return False
        pywsp.browser.driver.close()
        pywsp.browser.driver = None

    def load_attach_files(self):
        title = "Seleccionar archivos (Mantener presionado Ctrl mientras se seleccionan)"
        print("[UI]Loading attached files.")
        files = filedialog.askopenfiles(title=title, multiple=True)
        self.actual_attachment = list(
            map(lambda f: pathlib.Path(f.name), files))
        file_names = [file.name for file in self.actual_attachment]
        self.amount_files.set(", ".join(file_names))
        print("attachs:", self.actual_attachment)

    def populate_contact_list(self):
        # delete all elements of listbox
        self.listbox.tree.delete(*self.listbox.tree.get_children())
        def get_by_keys(tuple, keys):
            def lambda_func(key): return [item[key] for item in tuple]
            return [[item[k] for k in keys] for item in tuple]

        name = pywsp.CONFIG['NAME_COL_NAME']
        lastname = pywsp.CONFIG['LASTNAME_COL_NAME']
        phone = pywsp.CONFIG['PHONE_COL_NAME']

        self.listbox.col_headers = [name, lastname, phone]
        self.listbox.row_data = get_by_keys(
            list(pywsp.contacts.contacts.values()), [name, lastname, phone])
        self.listbox._build_tree()

    def check_driver_thread(self):
        Thread(target=self.check_driver_loop).start()

    def check_driver_loop(self):
        print("[GUI]Checking driver status...")
        while True:
            time.sleep(1)
            if pywsp.browser.driver:
                self.init_driver_btn.config(state=DISABLED)
            else:
                self.init_driver_btn.config(state=ACTIVE)

    def driver_is_opened(self):
        if not pywsp.browser.driver:
            messagebox.showwarning(
                "Problema!",
                "El navegador no se encuentra abierto o no ha terminado de inicializarse.")
            return False
        return True

    def is_selected_contact(self):
        print(self.actual_selection, self.actual_selection_idx)
        if not self.actual_selection:
            messagebox.showwarning(
                "Ops!",
                "No ha un contacto seleccionado.")
            return False
        return True

    def load_contacts_list(self):
        print("[UI] Loading contacts list.")
        try:
            pywsp.contacts.contacts = {}
            pywsp.contacts.load(self.contacts_filename)
            self.populate_contact_list()
        except:
            messagebox.showerror(
                'Error', 'Problema al cargar los contactos del .csv, por favor revise la configuración.')

    def load_contacts_from_file(self):
        file = filedialog.askopenfilename(
        	initialdir='.', 
        	title="Seleccionar archivo", 
        	filetypes=(
            	("csv files", "*.csv"), ("all files", "*.*")))
        if file:
            self.contacts_filename = file
            self.load_contacts_list()

    def on_select_contact(self, event):
        item = self.listbox.tree.identify('item', event.x, event.y)
        idx = self.listbox.tree.index(item)
        # get all items from listbox

        self.actual_selection = pywsp.contacts.contacts[idx]
        self.actual_selection_idx = idx
        print("Actual selection:", self.actual_selection)

    def get_msg_box_content(self):
        return self.message_box.get("1.0", "end-1c")

    def format_message(self, contact):
        try:
            message = pywsp.contacts.format_message(
                self.get_msg_box_content(), contact)
            return message
        except:
            messagebox.showerror(
            	'Oops!',
                'Problema al formatear el mensaje, revisa que las palabras claves coincidan con el nombre de alguna columna.')
            return False

    def send_to(self, contact: dict, attachment: list):
        if not self.driver_is_opened():
            return False
        print("[+]Sending message to", contact)
        message = self.format_message(contact)

        items = self.listbox.tree.get_children()
        value = list(self.listbox.tree.item(
            items[self.actual_selection_idx], "values"))
        if not message:
            return False
        try:
            pywsp.Sender(pywsp.browser).send_to(contact, message, attachment)
            value[0] = "☑" + value[0]
        except:
            value[0] = "☒" + value[0]

        self.listbox.tree.item(
            items[self.actual_selection_idx], value=value, tags=('selected',))

    def send_to_selected(self):
        if not self.driver_is_opened():
            return False
        if not self.is_selected_contact():
            return False
        sent = self.send_to(self.actual_selection, self.actual_attachment)
        return sent

    def send_to_all(self):
        if not self.driver_is_opened():
            return False
        ask = messagebox.askyesno(
            "Enviar a todos", "¿Está seguro de enviar el mensaje a todos los contactos?")
        if not ask:
            return False
        print("[UI]Starting send to all.")
        for idx, contact in pywsp.contacts.contacts.items():
            self.actual_selection_idx = idx
            self.actual_selection = contact
            try:
                sent = self.send_to(contact, self.actual_attachment)
            except:
                print("[UI]Error sending message to", contact)

        messagebox.showinfo("Listo!", "Finalizó el envío masivo.")
        print("[UI]Massive sent Finished.")
        return True

    def load_gui(self):
        # Buttons
        self.init_driver_btn = Button(
            text='🔛 Iniciar WhatsappWeb',
            width=50,
            command=self.init_driver)

        self.quit_driver_btn = Button(
            text="❌ Cerrar Whatsapp",
            width=50,
            command=self.quit_driver)

        self.load_contacts_from_btn = Button(
            text="📓 Cargar contactos desde una archivo",
            width=50,
            command=self.load_contacts_from_file)

        self.reload_contacts_btn = Button(
            text="🔃 Recargar lista de Contactos",
            width=50,
            command=self.load_contacts_list)

        self.files_attach = Button(
            text="📎 Seleccionar adjuntos",
            width=50,
            command=self.load_attach_files)

        self.added_files_title = Label(text="Archivos adjuntos actuales:")
        self.added_files = Entry(
            textvar=self.amount_files,
            width=50,
            state='readonly')

        # message input
        self.message_box_title = Label(
            self.main, text='Contenido del mensaje:')
        self.message_box = Text(font=('calibre', 12, 'normal'), height=8)

        # contact box handle
        self.contacts_list_title = Label(text='Contactos disponibles:')

        name = pywsp.CONFIG['NAME_COL_NAME']
        lastname = pywsp.CONFIG['LASTNAME_COL_NAME']
        phone = pywsp.CONFIG['PHONE_COL_NAME']

        self.listbox = MultiColumnListbox([name, lastname, phone], [])

        self.send_to_all = Button(
            text="👥 Enviar a todos los contactos",
            width=50,
            command=self.send_to_all)

        self.send_to_selected_btn = Button(
            text="👤 Enviar solo a seleccionado",
            width=50,
            command=self.send_to_selected)

    def init_gui(self):
        self.init_driver_btn.pack()
        self.quit_driver_btn.pack()
        self.load_contacts_from_btn.pack()
        self.reload_contacts_btn.pack()
        self.files_attach.pack()

        self.added_files_title.pack()
        self.added_files.pack()

        self.message_box_title.pack()
        self.message_box.insert(END, DEMO_TEXT)
        self.message_box.pack()

        self.contacts_list_title.pack()

        self.listbox.tree.bind("<Button-1>", self.on_select_contact)
        self.listbox.container.pack(fill=BOTH, expand=True)

        self.send_to_all.pack()
        self.send_to_selected_btn.pack()


DEMO_TEXT = "Hola *$(nombre)*, espero que esté todo bien!\nEste es un _mensaje automático_ de prueba. \
	😁🤖\nSaludos!\n\nPD: ```Recordá que podés darle estilo a tus mensajes.```"

if __name__ == "__main__":
    main = Tk()
    app = Window(main)
    app.init_window()
