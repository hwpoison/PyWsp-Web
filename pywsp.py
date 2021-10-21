from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

import autoit

import configparser
import time
import os
import re

browser = None
contacts = {}

# common names for automatic detection :TODO
commons_col_names = {
    'name':['nombre','name', 'firstname'],
    'lastname':['lastname', 'apellido'],
    'phone':['phone', 'cellphone', 'teléfono', 'tel', 'whatsapp']
}


HOME_URL = "https://web.whatsapp.com/"

config = {
    # default values
   'FILEDIALOG_TITLE': 'Open',
   'NAME_COL_NAME': 'name',
   'LASTNAME_COL_NAME': 'lastname',
   'PHONE_COL_NAME': 'phone' 
}

# read config.ini
config_load = configparser.ConfigParser()
config_load.read('config.ini')
if 'MISC' in config_load.sections():
    print("[+]reading config.ini")
    misc = config_load['MISC']
    if dialog_title:= misc.get('DIALOGFILE_TITLE'):
        config['FILEDIALOG_TITLE'] = dialog_title
    # default col names
    if phone:= misc.get('PHONE_COL'):
        config['PHONE_COL_NAME'] = phone
    if lastname:= misc.get('LASTNAME_COL'):
        config['LASTNAME_COL_NAME'] = lastname
    if name:= misc.get('NAME_COL'):
        config['NAME_COL_NAME'] = name

# load driver path 
chrome_default_path = os.getcwd() + '/driver/chromedriver' + \
    ('.exe' if os.sys.platform == 'win32' else '')  # xD


def sanitize_phone(phone):
    return phone.translate(str.maketrans({' ': '', '+': ''}))

class ChatBoxHandle:
    """ Functions to handle whatsapp web chat box 
    """
    def confirm_send():
        js = """
            var btn_send = document.querySelector('[data-testid="send"]')
            btn_send.click()
        """
        try:
            browser.execute_script(js)
            return True
        except:
            return False

    def is_loading_mode():
        js = """
            const loading_svg = document.querySelector("[viewBox='0 0 44 44']")
            return loading_svg?loading_svg.innerHTML!='':false
        """
        return browser.execute_script(js)

    def is_media_editor_mode():
        js = """
            return document.querySelector("[data-testid='media-editor-sticker']")?true:false;
        """
        return browser.execute_script(js)

    def attach_file(attachment=[]):
        files = list(map(lambda f: f"\"{f}\"", attachment))
        print("[+]Prepared for send ", files)

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
        try:
            # focus dialog file to write dirs.
            autoit.control_focus(config['FILEDIALOG_TITLE'], "Edit1")
            autoit.control_set_text(config['FILEDIALOG_TITLE'], "Edit1", " ".join(files))
            autoit.control_click(config['FILEDIALOG_TITLE'], "Button1")
            return True
        except:
            # if fails, close filedialog and attach dropdown pressing esc * 2
            autoit.send("{ESC}")
            autoit.send("{ESC}")
            return False

    def write_message(number, message_text):
        print(f"[+]Sending message to {number} with the text:{message_text}!")
        js = """
            // Open chat and write something to a phone number
            const openChat = (phone_number, message='') => {
                var wsp_msg_url = `https://web.whatsapp.com/send?phone=${ phone_number }&text=${ message }`
                const open_chat = document.createElement('a')
                open_chat.id = 'wsp_chat_'
                open_chat.href = wsp_msg_url
                document.body.appendChild(open_chat)
                open_chat.click()
            };""" f"openChat('{sanitize_phone(number)}', '{message_text}')"
        browser.execute_script(js)

class NotificationTasteHandle:
    """ Functions to handle taste notifications 
    """

    def is_showing():
        js = """
            return app.childNodes[0].childNodes[0].textContent != ''
        """
        return browser.execute_script(js)

    def get_text():
        js = """
            return app.childNodes[0].childNodes[0].textContent
        """
        return browser.execute_script(js)

class ModalHandle:
    """ Functions to handle modal 
    """

    def getElement():
        # return modal (confirmation, error, etc) content like str
        js_modal = """
            return app.childNodes[0].childNodes[1]
        """
        return browser.execute_script(js_modal)

    def getContent():
        return ModalHandle.getElement().text

    def confirm():
        # click on button
        js = """
            // Confirm Modal
            const confirmModal = () => {
                const modal = app.childNodes[0].childNodes[1]
                modal.querySelector("[role='button']").click()
            }
            confirmModal()
        """
        browser.execute_script(js)
        return not ModalHandle.isOpened()

    def isOpened():
        # return modal (confirmation, loading_statues(?, error, etc) content like str
        js = """
            // Verify if a modal is actually opened ( Invalid Phone or any other)
            const isModalOpened = () => {
                modal = app.childNodes[0].childNodes[1].innerHTML != ''
                if(modal){
                    return true
                }
                return false  
            }
            isModalOpened()
        """
        return browser.execute_script(js)

    def invalidPhone():
        msg_invalid_phone = "teléfono compartido a través de la dirección URL es inválido"
        if msg_invalid_phone in str(ModalHandle.getContent()):
            return True
        return False

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

def format_message(message : str , keywords : dict):
    # Substitute special keys ocurrences
    new_message = message
    keys = re.findall('.(\$\w+)(?:.|$)', message)  # all $\w+ ocurrences
    for key in keys:
        key = key.strip() # to replace reference: $(value)
        new = keywords.get(key[1:]) # new value
        # replace key $... for contact[key without $]
        if not new:
            raise Exception('[+]Problem to get column value.')
        else:
            new_message = new_message.replace(
                key, new)
    return new_message

def send_to(contact, message, attachment):
    if not contact or not browser:
        return False
    try:
        phone = contact[config['PHONE_COL_NAME']]
        new_message = message
        print("="*30)
        print("\n[+] Sending message to ", phone)

        #new_message = format_message(new_message)

        # write the message
        ChatBoxHandle.write_message(phone, new_message)
        # wait 1 sec 
        time.sleep(1)
        # verify if is a invalidPhone
        if ModalHandle.invalidPhone():
            # confirm modal and cancel send
            ModalHandle.confirm()
            raise Exception("[x] Invalid Phone!")

        # if modal is not open
        if not ModalHandle.isOpened():
            # procced to attach file
            if attachment:
                    time.sleep(1.5)
                    load_files = ChatBoxHandle.attach_file(attachment)
                    # wait to finish -auto it- interaction
                    time.sleep(2)
                    if not load_files:
                        raise Exception("[x] Problem to send file attach. Aborting message.")

                    # if after of 5 attempts is even loading, cancel send.
                    for attempt in range(0, 5):
                        if not ChatBoxHandle.is_loading_mode():
                            break
                        print("[-] Trying to send...", attempt)
                        time.sleep(5)
                        if attempt  == 5:
                            raise Exception('[x] Error to attach file.')

            ChatBoxHandle.confirm_send()
            time.sleep(1)
            ChatBoxHandle.confirm_send() # provisory send for files that not support comments. (videos)
        else:
            raise Exception("[x] Problem to send message after load files")
        print("[+]Message sent!")
        return True
    except:
        print("[Aborted!] Error to send message:")
        print(os.sys.exc_info())
        return False

def send_to_all(message, attachment=None):
    print("[+] Starting send...")
    # prepare files
    # prepare contacts
    for contact in contacts.values():
        send_to(contact, message, attachment)
    print("[+] Send_to_all finished...")

def load_contacts(filename):
    # Load contacts from .csv and apply normalization
    print("[+]Loading contacts...")
    with open(filename, "r") as file:
        file = file.read().split('\n')
        delimiter = ','
        file_content = list(map(lambda c: c.split(delimiter), file))
        columns = file_content[0]
        for idx, row in enumerate(file_content[1:]):
            if row and len(row) == len(columns):
                contacts[idx] = {}
                contacts[idx].update({columns:info.strip() for columns, info in zip(columns, row)})

    print(f"[+]{len(contacts)} contacts loaded.")
    return True

if __name__ == '__main__':
    load_contacts("contacts.csv")
    #whatsapp_login(headless=False)
    while True:
        try:
            eval(input("Debug console:"))
        except:
            print(os.sys.exc_info())
else:
    pass