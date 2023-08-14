import re
import email
import imapclient
import urllib.parse

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
                        if filename.startswith("=?"):
                            temporary_name = filename.split("?")
                            temporary_name = temporary_name[3]
                            decoded_name = temporary_name.replace("=E7=E3", "")
                            print(decoded_name)
                        print(filename)
        except Exception as e:
            print("Caiu nesta exceção! {}".format(e))

        # try:
        #     server = imapclient.IMAPClient(self.imap_server, ssl=True)
        #     server.login(self.user, self.password)
        #     inbox_folder = 'INBOX'
        #     server.select_folder(inbox_folder)
        #     messages = server.search()
        #     for uid, message_data in server.fetch(messages, 'RFC822').items():
        #         email_message = email.message_from_bytes(message_data[b'RFC822'])
        #         for part in email_message.walk():
        #             filename = part.get_filename()
        #             if filename:
        #                 # decodificando o nome do arquivo, se necessário
        #                 filename = decode_header(filename)[0][0]
        #                 if filename.endswith(('.xlsx', '.xls', '.csv')):
        #                     # baixando o arquivo
        #                     file_data = part.get_payload(decode=True)
        #                     with open(f'./Pedidos/{filename}', 'wb') as f:
        #                         f.write(file_data)
        #                     # movendo o email para a pasta "Absorvidos"
        #                     server.move(uid, 'Absorvidos')
        #
        #     server.logout()
        #     return True
        # except Exception as e:
        #     server = imapclient.IMAPClient(self.imap_server, ssl=True)
        #     server.login(self.user, self.password)
        #
        #     inbox_folder = 'INBOX'
        #     server.select_folder(inbox_folder)
        #
        #     messages = server.search()
        #     for uid, message_data in server.fetch(messages, 'RFC822').items():
        #         email_message = email.message_from_bytes(message_data[b'RFC822'])
        #         for part in email_message.walk():
        #             filename = part.get_filename()
        #             if filename:
        #                 # Obter o endereço de e-mail remetente
        #                 sender_email = email_message['From']
        #                 notificador = send_mail.OutlookMailSender()
        #                 notificador.send_error_email(sender_email, str(e))
        #                 server.move(uid, 'Erros')
        #
        #     server.logout()
        #     return False
