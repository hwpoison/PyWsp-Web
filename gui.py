from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk
import pywsp
from threading import Thread
import pathlib
import time

main = Tk()

DEMO_TEXT = "Hola *$nombre*, espero que esté todo bien! Este es un mensaje automático de prueba. 😁🤖"

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

		self.load_gui()
		self.init_gui()
		self.check_driver_thread()


	def init_window(self):
		self.main.title("Whattasap! (by:hwpoison)")
		self.main.geometry("300x550+600+100")
		self.main.resizable(False, False)
		self.load_contact_box()
		self.main.mainloop()
	
	def init_driver(self):
		print("[UI]Initializing driver...")
		messagebox.showinfo(
			"Atención!", 
			"A continuación se va a abrir Whatsapp Web, escaneá el código QR antes de efectuar alguna acción!")
		Thread(target=pywsp.whatsapp_login).start()

	def quit_driver(self):
		print("[UI]Quitting driver...")
		if not self.driver_is_opened():
			return False
		pywsp.browser.close()
		pywsp.browser = None

	def load_attach_files(self):
		title = "Seleccionar archivos (Mantener presionado Ctrl mientras se seleccionan)"
		print("[UI]Loading attached files.")
		files = filedialog.askopenfiles(title=title, multiple=True)
		self.actual_attachment = list(map(lambda f: pathlib.Path(f.name), files))
		file_names = [file.name for file in self.actual_attachment]
		self.amount_files.set(", ".join(file_names))
		print("attachs:", self.actual_attachment)

	def populate_contact_list(self):
		self.contacts_list_box.delete(0, END)
		for contact in pywsp.contacts.values():
			name = f"{contact[pywsp.config['NAME_COL_NAME']]} {contact[pywsp.config['LASTNAME_COL_NAME']]}"
			if len(name) < 20:
				name = name + ' '*(30-len(name))
			self.contacts_list_box.insert(END, f"{name} {contact[pywsp.config['PHONE_COL_NAME']]}")

	def check_driver_thread(self):
		Thread(target=self.check_driver_loop).start()

	def check_driver_loop(self):
		print("[GUI]Checking driver status...")
		while True:
			time.sleep(1)
			if pywsp.browser:		
				self.init_driver_btn.config(state=DISABLED)
			else:
				self.init_driver_btn.config(state=ACTIVE)

	def load_contacts_from(self):
			pywsp.contacts = {}
			return pywsp.load_contacts(self.contacts_filename)

	def driver_is_opened(self):
		if not pywsp.browser:
			messagebox.showwarning(
				"Problema!", 
				"El navegador no se encuentra abierto o no ha terminado de inicializarse.")
			return False
		return True

	def load_contact_box(self):
		print("[UI] Loading contacts list.")
		try:
			self.load_contacts_from()
			self.populate_contact_list()
		except:
			messagebox.showerror('Error', 'Problema al cargar los contactos del .csv, por favor revise la configuración.')

	def on_select_contact(self, event):
	  selection = event.widget.curselection()
	  index = selection[0]
	  value = event.widget.get(index)
	  self.actual_selection = pywsp.contacts[index]
	  self.actual_selection_idx = index
	  print("[UI]Selected:", index,' -> ',value, self.actual_selection)

	def get_msg_box_content(self):
		return self.message_box.get("1.0","end-1c")

	def format_message(self, contact):
		try:
			message = pywsp.format_message(self.get_msg_box_content(), contact)
			return message
		except:
			messagebox.showerror('Oops!', 
				'Problema al formatear el mensaje, revisa que las palabras claves coincidan con el nombre de alguna columna.')
			return False		

	def send_to(self, contact : dict, attachment : list):
		print("[+]Sending message to", contact)
		message = self.format_message(contact)
		if not message:
			return False

		return pywsp.send_to(contact, message, attachment)


	def send_to_selected(self):
		if not self.driver_is_opened():
			return False
		sent = self.send_to(self.actual_selection, self.actual_attachment)
		if sent:
			self.set_contact_color(self.actual_selection_idx)		
		else:
			self.set_contact_color(self.actual_selection_idx, color='red')

		return sent

	def set_contact_color(self, index, color='green'):
		if color == 'green':
			self.contacts_list_box.itemconfigure(index, bg="#00aa00", fg="#fff")
		else:
			self.contacts_list_box.itemconfigure(index, bg="#ff0000", fg="#fff")

	def send_to_all(self):
		if not self.driver_is_opened():
			return False
		print("[UI]Starting send to all.")
		for idx, contact in pywsp.contacts.items():
			message = self.format_message(contact)
			if not message:
				break
			sent = pywsp.send_to(contact, message, self.actual_attachment)
			if sent:
				self.set_contact_color(idx)
			else:
				self.set_contact_color(idx, color='red')
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

		self.reload_contacts_btn = Button(
			text="📓 Recargar lista de Contactos", 
			width=50, 
			command=self.load_contact_box)

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
		self.message_box_title = Label(self.main, text='Contenido del mensaje:')
		self.message_box = Text(font = ('calibre',12,'normal'), height=8)
		
		# contact box handle
		self.contacts_list_title = Label(text='Contactos disponibles:')
		self.scrollbar = ttk.Scrollbar(orient=VERTICAL)
		self.contacts_list_box = Listbox(
			main, width=50, 
			yscrollcommand=self.scrollbar.set)
		

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
		self.reload_contacts_btn.pack()
		self.files_attach.pack()

		self.added_files_title.pack()
		self.added_files.pack()

		self.message_box_title.pack()
		self.message_box.insert(END, DEMO_TEXT)
		self.message_box.pack()
		
		self.contacts_list_title.pack()

		self.contacts_list_box.bind('<<ListboxSelect>>', self.on_select_contact)
		
		self.scrollbar.config(command=self.contacts_list_box.yview)
		self.scrollbar.pack(side=RIGHT, fill=Y)
		self.contacts_list_box.pack()

		self.send_to_all.pack()
		self.send_to_selected_btn.pack()

print("Holis! :)")
app = Window(main)

app.init_window()