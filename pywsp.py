# selenium dependencies
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

# load autoit
try:
    import autoit
except ModuleNotFoundError:
    pass

import time
import os
import re

chrome_default_path = os.getcwd() + '/driver/chromedriver' + \
    ('.exe' if os.sys.platform == 'win32' else '')  # xD

HOME_URL = "https://web.whatsapp.com/"

browser = None
contacts = {}


def sanitize_phone(phone):
    return phone.translate(str.maketrans({' ': '', '+': ''}))


def open_chat(number):
    js_open_chat = f"""
        var wsp_msg_url = "https://web.whatsapp.com/send?phone={sanitize_phone(number)}&text="
        const msj = document.createElement('a')
        msj.id = 'envio'
        msj.href = wsp_msg_url
        document.body.appendChild(msj)
        msj.click() // TODO: clear input box before write a message
    """
    print(f"[+] Opening chat with {number}.")
    browser.execute_script(js_open_chat)


def write_message(number, message_text):
    js_populate_messagebox = f"""
        var wsp_msg_url = "https://web.whatsapp.com/send?phone={sanitize_phone(number)}&text={message_text}"
        const msj = document.createElement('a')
        msj.id = 'envio'
        msj.href = wsp_msg_url
        document.body.appendChild(msj)
        msj.click() // TODO: clear input box before write a message
    """
    print(f"[+]Sending message to {number} with the text:{message_text}!")
    browser.execute_script(js_populate_messagebox)


def confirm_send():
    js_send = """
        var btn_send = document.querySelector('[data-testid="send"]')
        btn_send.click()
    """
    browser.execute_script(js_send)


def load_file(attachment=[]):
    files = list(map(lambda f: f"\"{f}\"", attachment))
    print("[+]Prepared for send ", files)

    attach_btn_click = """
        boton_adjuntar_imagen = document.querySelector(
            '[data-testid="attach-image"]')
        boton_adjuntar = document.querySelector('[aria-label="Adjuntar"]')
        boton_adjuntar.click()
    """
    browser.execute_script(attach_btn_click)
    upping = ActionChains(browser)\
        .send_keys(Keys.ARROW_DOWN)\
        .send_keys(Keys.ENTER)\
        .perform()
    time.sleep(1.5)
    try:
        autoit.control_focus("Open", "Edit1")
        autoit.control_set_text("Open", "Edit1", " ".join(files))
        autoit.control_click("Open", "Button1")
        return False
    except:
        return True


def test_message():
    write_message(5493463443291, "Este es un mensaje de prueba.")


def test_image():
    load_file(
        ["C:\\Users\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png"])


class ModalHandle:

    def getElement():
        # return modal (confirmation, error, etc) content like str
        js_modal = """
            const app = document.getElementById('app');
            return app.childNodes[0].childNodes[1]
        """
        return browser.execute_script(js_modal)

    def getContent():
        return ModalHandle.getElement().text

    def confirm():
        # click on button
        js_modal_click = """
            const app = document.getElementById('app')
            const modal = app.childNodes[0].childNodes[1]
            modal.querySelector("[role='button']").click()
        """
        browser.execute_script(js_modal_click)
        return not ModalHandle.isOpened()

    def isOpened():
        # return modal (confirmation, loading_statues(?, error, etc) content like str
        js_modal = """
            const app = document.getElementById('app');
            if(app.childNodes[0].childNodes[1].innerHTML != ''){
                return true
            }
            return false
        """
        return browser.execute_script(js_modal)

    def invalidPhone():
        msg_invalid_phone = "teléfono compartido a través de la dirección URL es inválido"
        if msg_invalid_phone in str(ModalHandle.getContent()):
            return True
        return False


def test_images():
    load_file(["C:\\Users\\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png",
               "C:\\Users\Guille\\Desktop\\whatsapp\\2.jpg"])


def test_case():
    send_to_all("Hola señor *$apellido* , espero que te encuentres bien, este es un mensaje automático de prueba! Por cierto, conozco tu nombre, es $nombre 😊.",
                ["C:\\Users\\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png", "C:\\Users\Guille\\Desktop\\whatsapp\\2.jpg"])


def whatsapp_login(headless=False):
    global browser
    print("[+]Initializing driver...")
    chrome_options = Options()
    # chrome_options.add_argument('--user-data-dir=./User_Data')
    if headless == True:
        chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(
        executable_path=chrome_default_path, options=chrome_options)

    wait = WebDriverWait(browser, 600)
    browser.get(HOME_URL)
    browser.maximize_window()
    print('[+]Driver initialized...')


def filter_keywords(message):
    keywords = re.findall('.(\$\w+)(?:.|$)', message)  # all $\w+ ocurrences
    return keywords

def send_to(contact, message, attachment):
    if not contact:
        return False
    try:
        phone = contact['telefono']
        new_message = message
        print("="*30)
        print("\n[+] Sending message to ", phone)
        # Substitute special keys ocurrences
        for key in filter_keywords(message):
            key = key.strip()
            new = contact.get(key[1:])
            # replace key $... for contact[key without $]
            new_message = new_message.replace(
                key, new if new else '<error>')
        if browser:
            write_message(phone, new_message)
            time.sleep(1)
            if ModalHandle.invalidPhone():
                ModalHandle.confirm()
                raise Exception("[x] Teléfono invalido! :(")
            time.sleep(1.5)
            if not ModalHandle.isOpened():
                if attachment:
                    load_files = load_file(attachment)
                    time.sleep(1.5)
                confirm_send()
            else:
                raise Exception("Problem to send message after load files")

        print("[+]Message sent!")
        return True
    except:
        print("[x]Error to send message:")
        print(os.sys.exc_info())
        return False

def send_to_all(message, attachment=None):
    print("[+] Starting send...")
    # prepare files
    # prepare contacts
    for contact in contacts.values():
        send_to(contact, message, attachment)
    print("[+] Send_to_all finished...")

def load_contacts():
    # Load contacts from .csv
    print("[+]Loading contacts...")
    with open("telefonos.csv", "r") as file:
        file = file.read().split('\n')
        delimiter = ','

        file_content = list(map(lambda c: c.split(delimiter), file))
        header = file_content[0]
        for data in file_content[1:]:
            if len(data)-1 == len(header):
                cid = int(data[0])
                contacts[cid] = {}
                for idx, col in enumerate(data[1:]):
                    contacts[cid].update({header[idx]: col})
    print("[+]Ready")


if __name__ == '__main__':
    load_contacts()
    whatsapp_login(headless=False)
   
    while True:
        try:
            eval(input("Debug console:"))
        except:
            print(os.sys.exc_info())
