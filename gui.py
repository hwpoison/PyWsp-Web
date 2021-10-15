from tkinter import *
from tkinter import filedialog
from tkinter import ttk
import pywsp
from threading import Thread
import pathlib
import time
main = Tk()
main.title("Whattasap!")
main.geometry("300x550+600+100")


init_driver_btn = None
reload_contacts_btn = None
contacts_list_box = None
actual_attach = []
amount_files = StringVar()
amount_files.set('Ninguno')
actual_selected = None
message_box = None

def check_driver():
	print("cheking browser status")
	while True:
		time.sleep(1)
		if pywsp.browser:		
			init_driver_btn.config(state=DISABLED)
		else:
			init_driver_btn.config(state=ACTIVE)

def init_driver():
	print("init_driver()")
	browser_thread = Thread(target=pywsp.whatsapp_login)
	browser_thread.start()
	
def close_driver():
	print("closing driver.")
	pywsp.browser.close()
	pywsp.browser = None

def add_files():
	global actual_attach, amount_files
	print("add_files()")
	files = filedialog.askopenfiles(title="Seleccionar archivos (Mantener presionado Ctrl mientras se seleccionan)", multiple=True)
	actual_attach = list(map(lambda f: pathlib.Path(f.name), files))
	file_names = [file.name for file in actual_attach]
	amount_files.set(", ".join(file_names))
	print("attachs:", actual_attach)

def load_contacts_box():
	pywsp.load_contacts()
	for contact in pywsp.contacts.values():
		nombre = f"{contact['nombre']} {contact['apellido']}"
		if len(nombre) < 20:
			nombre = nombre + ' '*(30-len(nombre))
		contacts_list_box.insert(END, f"{nombre} {contact['telefono']}")

def recargar():
	print("recargar()")
	pywsp.load_contacts()
	load_contacts_box()

def onclickList(event):
  global actual_selected
  selection = event.widget.curselection()
  index = selection[0]
  value = event.widget.get(index)
  actual_selected = pywsp.contacts[index+1]
  print("selected:", index,' -> ',value, actual_selected)

def send_to_selected():
	print("sending to...")
	message = message_box.get("1.0","end-1c")
	print(actual_selected)
	pywsp.send_to(actual_selected, message, actual_attach)


# menu
init_driver_btn = Button(text='🔛 Iniciar WhatsappWeb', width=50, command=init_driver)
init_driver_btn.pack()

reload_contacts_btn = Button(text="❌ Cerrar Whatsapp", width=50, command=close_driver)
reload_contacts_btn.pack()

reload_contacts_btn = Button(text="📓 Recargar lista de Contactos", width=50, command=recargar)
reload_contacts_btn.pack()

files_attach = Button(text="📎 Seleccionar adjuntos", width=50, command=add_files)
files_attach.pack()

added_files_title = Label(main, text="Archivos adjuntos:").pack()

added_files = Entry(main, textvar=amount_files, width=50, state='readonly').pack()
# message input
message_box_title = Label(main, text='Contenido del mensaje:').pack()
demo_text = "Hola $nombre, espero que esté todo bien! 😂 😂"
message_box = Text(main, font = ('calibre',12,'normal'), height=8)
message_box.pack()

# contact box handle
contacts_list_title = Label(main, text='Contactos:').pack()

scrollbar = ttk.Scrollbar(main, orient=VERTICAL)
contacts_list_box = Listbox(
	main, width=50, 
	yscrollcommand=scrollbar.set,
	selectforeground="#ffffff",
    selectbackground="#00aa00"
)
#contact click event


contacts_list_box.bind('<<ListboxSelect>>', onclickList)


scrollbar.config(command=contacts_list_box.yview)
scrollbar.pack(side=RIGHT, fill=Y)
contacts_list_box.pack()


# send buttons
send_to_all = Button(text="✈️ Enviar a todos los contactos", width=50, command=close_driver)
send_to_all.pack()
send_to_selected_btn = Button(text="👤 Enviar a seleccionado", width=50, command=send_to_selected)
send_to_selected_btn.pack()

# 
browser_check = Thread(target=check_driver)
browser_check.start()
load_contacts_box()

main.mainloop()