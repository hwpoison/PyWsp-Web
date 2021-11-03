from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from dataclasses import dataclass
import autoit

import configparser
import time
import os
import re


from errors import SendMessageError, ChromedriverNotFoundError

CURRENT_PATH = os.getcwd()

# common names for automatic detection :TODO
commons_col_names = {
    'name': ['nombre','name', 'firstname'],
    'lastname': ['lastname', 'apellido'],
    'phone': ['phone', 'cellphone', 'teléfono', 'tel', 'whatsapp']
}

CONFIG = {
    # default values
   'FILEDIALOG_TITLE': 'Open',
   'NAME_COL_NAME': 'name',
   'LASTNAME_COL_NAME': 'lastname',
   'PHONE_COL_NAME': 'phone'
}


def load_configuration():
    # read config.ini
    config_load = configparser.ConfigParser()
    config_load.read('config.ini')
    if 'MISC' in config_load.sections():
        print("[+]reading config.ini")
        misc = config_load['MISC']
        if dialog_title := misc.get('DIALOGFILE_TITLE'):
            CONFIG['FILEDIALOG_TITLE'] = dialog_title
        # default col names
        if phone := misc.get('PHONE_COL'):
            CONFIG['PHONE_COL_NAME'] = phone
        if lastname := misc.get('LASTNAME_COL'):
            CONFIG['LASTNAME_COL_NAME'] = lastname
        if name := misc.get('NAME_COL'):
            CONFIG['NAME_COL_NAME'] = name
        return True
    else:
        return False


class Browser:
    """ handles the browser functions """

    def __init__(self) -> None:
        self.driver = None
        self.home_url = "https://web.whatsapp.com/"

    def open_whatsapp(self, headless=False):
        print("[+]Initializing driver...")
        chrome_options = Options()
        # chrome_options.add_argument('--user-data-dir=./User_Data')
        if headless:
            chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(
            executable_path=self.chromedriver_path(), options=chrome_options)

        wait = WebDriverWait(self.driver, 600)
        print('[+] Opening WhatsappWeb.')
        self.driver.get(self.home_url)
        self.driver.maximize_window()
        print('[+] Driver initialized.')

    def chromedriver_path(self):
        chrome_default_path = CURRENT_PATH + '/driver/chromedriver' + \
            ('.exe' if os.sys.platform == 'win32' else '')
        if os.path.exists(chrome_default_path):
            return chrome_default_path
        raise ChromedriverNotFoundError()


class Contacts:
    """ contact handle functions """
    def __init__(self) -> None:
        self.contacts = {}

    def sanitize_phone(self, phone: str):  # remove all non-numeric characters
        return phone.translate(str.maketrans({' ': '', '+': ''}))

    def format_message(self, message: str, keywords: dict):
        # Substitute special keys ocurrences ( $nombre => 'John')
        new_message = message
        keys = re.findall('.\$\((\w+)\)(?:.|$)', message)  # all $(\w+) ocurrences

        for key in keys:
            key = key.strip()  # to replace reference: $(value)
            new = keywords.get(key)  # new value
            if not new:
                raise Exception('[+]Problem to get column value.')
            else:
                new_message = new_message.replace(
                    '$('+key+')', new)
        return new_message

    def load(self, filename: str):
        # Load contacts from .csv and apply normalization
        print("[+]Loading contacts...")
        with open(filename, "r") as file:
            file = file.read().split('\n')
            delimiter = ','
            file_content = list(map(lambda c: c.split(delimiter), file))
            columns = file_content[0]
            for idx, row in enumerate(file_content[1:]):
                if row and len(row) == len(columns):
                    self.contacts[idx] = {}
                    self.contacts[idx].update({columns: info.strip() for columns, info in zip(columns, row)})
                    # normalize phone number
                    if phone := self.contacts[idx].get(CONFIG['PHONE_COL_NAME']):
                        phone = self.sanitize_phone(phone)
                        self.contacts[idx][CONFIG['PHONE_COL_NAME']] = self.sanitize_phone(phone)

        print(f"[+]{len(self.contacts)} contacts loaded.")
        return True

    def __dict__(self) -> dict:
        return self.contacts


@dataclass
class ChatBoxHandle:
    """ Functions to handle whatsapp web chat box """
    browser: Browser

    def confirm_send(self):
        js = """
            var btn_send = document.querySelector('[data-testid="send"]')
            btn_send.click()
        """
        try:
            self.browser.driver.execute_script(js)
            return True
        except:
            return False

    def is_loading_mode(self):
        js = """
            const loading_svg = document.querySelector("[viewBox='0 0 44 44']")
            return loading_svg?loading_svg.innerHTML!='':false
        """
        return self.browser.driver.execute_script(js)

    def is_media_editor_mode(self):
        js = """
            return document.querySelector("[data-testid='media-editor-sticker']")?true:false;
        """
        return self.browser.driver.execute_script(js)

    def attach_file(self, attachment=[]):
        files = list(map(lambda f: f"\"{f}\"", attachment))
        print("[+]Prepared for send ", files)

        attach_btn_click = """
            boton_adjuntar_imagen = document.querySelector('[data-testid="attach-image"]')
            boton_adjuntar = document.querySelector('[aria-label="Adjuntar"]')
            boton_adjuntar.click()
        """
        self.browser.driver.execute_script(attach_btn_click)
        upping = ActionChains(self.browser.driver)\
            .send_keys(Keys.ARROW_DOWN)\
            .send_keys(Keys.ENTER)\
            .perform()
        time.sleep(1.5)
        try:
            # focus dialog file to write dirs.
            autoit.control_focus(CONFIG['FILEDIALOG_TITLE'], "Edit1")
            autoit.control_set_text(CONFIG['FILEDIALOG_TITLE'], "Edit1", " ".join(files))
            autoit.control_click(CONFIG['FILEDIALOG_TITLE'], "Button1")
            print("ready!")
            return True
        except:
            print(os.sys.exc_info())
            # if fails, close filedialog and attach dropdown pressing esc * 2
            autoit.send("{ESC}")
            autoit.send("{ESC}")
            print("fails!")
            return False

    def write_message(self, number, message_text):
        # replace new line with %0
        message_text = message_text.replace('\n', '%0a')

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
            };""" f"openChat('{number}', '{message_text}')"

        self.browser.driver.execute_script(js)


@dataclass
class NotificationTasteHandle:
    """ Functions to handle taste notifications """
    browser: Browser

    def is_showing(self):
        js = """
            return app.childNodes[0].childNodes[0].textContent != ''
        """
        return self.browser.driver.execute_script(js)

    def get_text(self):
        js = """
            return app.childNodes[0].childNodes[0].textContent
        """
        return self.browser.driver.execute_script(js)


@dataclass
class ModalHandle:
    """ Functions to handle modal """
    browser: Browser

    def getElement(self):
        # return modal (confirmation, error, etc) content like str
        js_modal = """
            return app.childNodes[0].childNodes[1]
        """
        return self.browser.driver.execute_script(js_modal)

    def getContent(self):
        return self.getElement().text

    def confirm(self):
        # click on button
        js = """
            // Confirm Modal
            const confirmModal = () => {
                const modal = app.childNodes[0].childNodes[1]
                modal.querySelector("[role='button']").click()
            }
            confirmModal()
        """
        self.browser.driver.execute_script(js)
        return not self.isOpened()

    def isOpened(self):
        js = """
            // Verify if a modal is actually opened (Invalid Phone or any other)
            const isModalOpened = () => {
                modal = app.childNodes[0].childNodes[1].innerHTML != ''
                if(modal){
                    return true
                }
                return false
            }
            isModalOpened()
        """
        return self.browser.driver.execute_script(js)

    def invalidPhone(self):
        msg_invalid_phone = "teléfono compartido a través de la dirección URL es inválido"
        if msg_invalid_phone in str(self.getContent()):
            return True
        return False


@dataclass
class Sender:
    browser: Browser

    def send_to(self, contact: dict, message: str, attachment: list):
        """ Send message to a contact """

        if not contact or not self.browser:
            return False
        try:
            phone = contact[CONFIG['PHONE_COL_NAME']]
            new_message = message
            print("="*30)
            print("\n[+] Sending message to ", phone)

            ChatBoxHandle(self.browser).write_message(phone, new_message)
            # wait 1 sec
            time.sleep(1)
            # verify if is a invalidPhone
            if ModalHandle(self.browser).invalidPhone():
                # confirm modal and cancel send
                ModalHandle(self.browser).confirm()
                ModalHandle(self.browser).confirm()
                raise SendMessageError("Invalid Phone!")

            # if modal is not open
            if not ModalHandle(self.browser).isOpened():
                # procced to attach file
                if attachment:
                    time.sleep(1.5)
                    load_files = ChatBoxHandle(self.browser).attach_file(attachment)
                    # wait to finish -auto it- interaction
                    time.sleep(2)
                    if not load_files:
                        raise SendMessageError("Problem to send file attach. Aborting message.")

                    # if after of 5 attempts is even loading, cancel send.
                    for attempt in range(0, 5):
                        if not ChatBoxHandle(self.browser).is_loading_mode():
                            break
                        print("[-] Trying to send...", attempt)
                        time.sleep(5)
                        if attempt == 5:
                            raise SendMessageError('Error to attach file.')

                ChatBoxHandle(self.browser).confirm_send()
                time.sleep(1)
                # provisory send for files that not support comments. (videos)
                ChatBoxHandle(self.browser).confirm_send()
            else:
                raise SendMessageError("Problem to send message after load files")
            print("[+]Message sent!")
            return True
        except:
            raise SendMessageError(f"Error to send message to {phone}. [Aborted]")
            print(os.sys.exc_info())
            return False

    def send_to_all(self, message, attachment=None):
        """ Send message to all contacts """

        print("[+] Starting send...")
        # prepare files
        # prepare contacts
        for contact in self.contacts.values():
            Sender(self.browser).send_to(contact, message, attachment)
        print("[+] Send_to_all finished...")


if __name__ == '__main__':
    contacts = Contacts()
    browser = Browser()
    load_configuration()

    contacts.load(CURRENT_PATH + "\\contacts.csv")

    print(contacts.contacts)
    browser.open_whatsapp(headless=False)
    while True:
        try:
            eval(input("Debug console:"))
        except:
            print(os.sys.exc_info())
else:
    contacts = Contacts()
    browser = Browser()
