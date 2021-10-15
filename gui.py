from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk
import pywsp
from threading import Thread
import pathlib
import time

main = Tk()

demo_text = "Hola $nombre, espero que esté todo bien! 😂 😂"

class Window:
	def __init__(self, master):
		self.main = master
		self.actual_selection = None
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
		self.load_contacts_from()
		self.populate_contact_list()
		
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
			nombre = f"{contact['nombre']} {contact['apellido']}"
			if len(nombre) < 20:
				nombre = nombre + ' '*(30-len(nombre))
			self.contacts_list_box.insert(END, f"{nombre} {contact['telefono']}")

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
			pywsp.load_contacts(self.contacts_filename)	

	def driver_is_opened(self):
		if not pywsp.browser:
			messagebox.showwarning(
				"Problema!", 
				"El navegador no se encuentra abierto o no ha terminado de inicializarse.")
			return False
		return True

	def reload_contacts_box(self):
		print("[UI] Reloading contacts list.")
		self.load_contacts_from()
		self.populate_contact_list()
	
	def on_select_contact(self, event):
	  selection = event.widget.curselection()
	  index = selection[0]
	  value = event.widget.get(index)
	  self.actual_selection = pywsp.contacts[index]
	  print("[UI]Selected:", index,' -> ',value, self.actual_selection)

	def get_msg_box_content(self):
		return self.message_box.get("1.0","end-1c")

	def send_to_selected(self):
		if not self.driver_is_opened():
			return False
		print("[+]Sending message to", self.actual_selection)
		pywsp.send_to(self.actual_selection, self.get_msg_box_content(), self.actual_attachment)

	def send_to_all(self):
		if not self.driver_is_opened():
			return False
		print("[UI]Starting send to all.")
		for idx, contact in pywsp.contacts.items():
			sent = pywsp.send_to(contact, self.get_msg_box_content(), self.actual_attachment)
			if sent:
				self.contacts_list_box.itemconfigure(idx, bg="#00aa00", fg="#fff")
			else:
				self.contacts_list_box.itemconfigure(idx, bg="#ff0000", fg="#fff")
		print("[UI]Massive sent Finished.")

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
			command=self.reload_contacts_box)

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
		self.message_box.pack()
		
		self.contacts_list_title.pack()

		self.contacts_list_box.bind('<<ListboxSelect>>', self.on_select_contact)
		
		self.scrollbar.config(command=self.contacts_list_box.yview)
		self.scrollbar.pack(side=RIGHT, fill=Y)
		self.contacts_list_box.pack()

		self.send_to_all.pack()
		self.send_to_selected_btn.pack()

print("Welcome :)")
app = Window(main)
app.init_window()