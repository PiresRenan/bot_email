import re
import email
import base64
from time import sleep

import imapclient
import urllib.parse
from googletrans import Translator

from mail_sender import Postman

from email.header import decode_header


class Email_getter:
    def __init__(self) -> None:
        self.imap_server = 'outlook.office365.com'
        self.user = 'pedidoscandide@outlook.com'
        self.password = '13579Can'

    def email_catch(self) -> bool:
        try:
            server = imapclient.IMAPClient(self.imap_server, ssl=True)
            server.login(self.user, self.password)
            inbox_folder = 'INBOX'
            server.select_folder(inbox_folder)
            messages = server.search()
            for uid, message_data in server.fetch(messages, 'RFC822').items():
                email_message = email.message_from_bytes(message_data[b'RFC822'])
                for part in email_message.walk():
                    filename = part.get_filename()
                    if filename is not None:
                        if filename.startswith("=?iso"):
                            temporary_name = filename.split("?")
                            temporary_name = temporary_name[3]
                            filename = temporary_name.replace("=E0", "a").replace("=E1", "a").replace("=E2", "a").replace("=E3", "a").replace("=E4", "a").replace("=E5", "a").replace("=E6", "a").replace("=E7", "a").replace("=E8", "a").replace("=E9", "a").replace("=AA", "a").replace("=BA", "a")

                        if filename.startswith("=?UTF"):
                            filename = filename.split("?")[3]
                            decoded_bytes = base64.b64decode(filename)
                            decoded_text = decoded_bytes.decode("utf-8")
                            translator = Translator()
                            filename = translator.translate(decoded_text, src="pt", dest="pt").text

                        sender_email = email_message['From']
                        print(sender_email)
                        # if filename.endswith(('.xlsx')):
                        #     file_data = part.get_payload(decode=True)
                        #     with open(f'./Pedidos/{filename}', 'wb') as f:
                        #         f.write(file_data)
                        #     server.move(uid, 'Absorvidos')
                        # else:
                        #     sender_email = email_message['From']
                        #     print(sender_email)
            server.logout()
            sleep(45)
            return True
        except Exception as e:
            print("Caiu nesta exceção! {}".format(e))

    def extension_err(self, sender):
        pass