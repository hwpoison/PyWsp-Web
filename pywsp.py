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
    ('.exe' if os.sys.platform == 'win32' else '')

HOME_URL = "https://web.whatsapp.com/"

browser = None
contacts = {}


def sanitize_phone(phone):
    return phone.translate(str.maketrans({' ': '', '+': ''}))


def send_message(number, message_text):
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
    print("Prepared for send ", files)

    attach_btn_click = """
    boton_adjuntar_imagen = document.querySelector('[data-testid="attach-image"]')
    boton_adjuntar = document.querySelector('[aria-label="Adjuntar"]')
    boton_adjuntar.click()
    """
    browser.execute_script(attach_btn_click)
    upping = ActionChains(browser)\
        .send_keys(Keys.ARROW_DOWN)\
        .send_keys(Keys.ENTER)\
        .perform()
    time.sleep(1.5)
    autoit.control_focus("Open", "Edit1")
    autoit.control_set_text("Open", "Edit1", " ".join(files))
    autoit.control_click("Open", "Button1")


def test_message():
    send_message(5493463443291, "Este es un mensaje de prueba.")


def test_image():
    load_file(
        ["C:\\Users\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png"])


def test_images():
    load_file(["C:\\Users\\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png",
               "C:\\Users\Guille\\Desktop\\whatsapp\\2.jpg"])

def test_case():
    send_to_all("Hola * $nombre * , espero que te encuentres bien!", ["C:\\Users\\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png","C:\\Users\Guille\\Desktop\\whatsapp\\2.jpg"])

def whatsapp_login(chrome_path, headless):
    global browser
    print("[+]Initializing driver...")
    chrome_options = Options()
    # chrome_options.add_argument('--user-data-dir=./User_Data')
    if headless == 'True':
        chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(
        executable_path=chrome_path, options=chrome_options)

    wait = WebDriverWait(browser, 600)
    browser.get(HOME_URL)
    browser.maximize_window()
    print('[+]Driver initialized...')


def send_to_all(message, attachment=None):
    print("Sending...")
    # prepare files
    # prepare contacts
    keyworkds = re.findall('(\$.+?)\s', message)  # all $(..) ocurrences
    for contact in contacts.values():
        new_message = message
        try:
            if contact:
                phone = contact['telefono']

                # Substitute special keys ocurrences
                for key in keyworkds:
                    new = contact.get(key[1:])
                    # replace key $... for contact[key without $]
                    new_message = new_message.replace(
                        key, new if new else '<error>')
                # load_file(attachment)
                send_message(phone, new_message)
                time.sleep(1.5)
                load_file(attachment)
                time.sleep(2)
                confirm_send()
                
            print("[+]Message sent!")
        except:
            print("[-]Error to send message.")


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
                contacts[data[0]] = {}
                for idx, col in enumerate(data[1:]):
                    contacts[data[0]].update({header[idx]: col})
    print("[+]Ready")


if __name__ == '__main__':
    whatsapp_login('driver/chromedriver.exe', headless=False)

    load_contacts()
    #send_to_all("Hola * $nombre * , espero que te encuentres bien!", ["C:\\Users\\Guille\\Desktop\\whatsapp\\WebWhatsapp-Wrapper\\webwhatsapi\\js\\imagen.png","C:\\Users\Guille\\Desktop\\whatsapp\\2.jpg"])

    while True:
        try:
            eval(input("debug:"))
        except:
            print(os.sys.exc_info())
