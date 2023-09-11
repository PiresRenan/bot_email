import email
import base64
import datetime
import pytz

import imapclient
from googletrans import Translator

from .mail_sender import Postman


class Email_getter:
    def __init__(self) -> None:
        self.imap_server = 'outlook.office365.com'
        self.user = 'pedidoscandide@outlook.com'
        self.password = '13579Can'
        self.obj_email = Postman()

    def email_catch(self) -> list:
        captured_data = []
        sender_email = []
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
                        print(filename)
                        if filename.startswith("=?iso"):
                            temporary_name = filename.split("?")
                            temporary_name = temporary_name[3]
                            filename = temporary_name.replace("=E0", "a").replace("=E1", "a").replace("=E2", "a").replace("=E3", "a").replace("=E4", "a").replace("=E5", "a").replace("=E6", "a").replace("=E7", "a").replace("=E8", "a").replace("=E9", "a").replace("=AA", "a").replace("=BA", "a")

                        if filename.startswith("=?UTF-8"):
                            filename = filename.split("?")[3]
                            decoded_bytes = base64.b64decode(filename)
                            decoded_text = decoded_bytes.decode("utf-8")
                            translator = Translator()
                            filename = translator.translate(decoded_text, src="en", dest="pt").text

                        if filename.endswith(('.xlsx')):
                            sender_email.append(email_message['From'])
                            email_s = email_message['From'].split(" <")[1].replace(">", "")
                            print("Pedido recebido por {}".format(email_s))
                            file_data = part.get_payload(decode=True)
                            path_to_file = "./Pedidos/{}".format(filename)
                            try:
                                print("O arquivo está sendo baixado...")
                                with open(path_to_file, 'wb') as f:
                                    f.write(file_data)
                            except Exception as e:
                                print("O arquivo não obteve êxito ao ser baixado por: {}".format(e))
                            # server.move(uid, 'Absorvidos')
                        elif filename.endswith(('.jpg')) or filename.endswith(('.png')) or filename.endswith(('.jpeg')) or filename.endswith(('.gif')):
                            pass
                        else:
                            print("O arquivo {} não possui o formato compbinado, certifique-se de cumprir os requisitos necessários.".format(filename))
                            file_data = part.get_payload(decode=True)
                            path_to_file = "./Erros/{}".format(filename)
                            with open(path_to_file, 'wb') as f:
                                f.write(file_data)
                            # server.move(uid, 'Formato')
                            self.extension_err(sender=email_message['From'], err=path_to_file)
            server.logout()
            return sender_email
        except Exception as e:
            print("Não pode conectar ao email. Motivo: {}".format(e))
            return sender_email

    def extension_err(self, sender=None, err=None):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.datetime.now(brasilia_tz)
        hora_formatada = hora_atual.strftime('%H:%M')
        data_formatada = hora_atual.strftime('%d/%m/%Y')
        name_sender = sender.split("<")[0]
        try:
            name_sender = name_sender.replace("|", "")
        except Exception as e:
            pass
        problem_maker = sender.split("<")[1].replace(">", "")
        msg = """
Olá, {} | <{}>!

O pedido enviado às {} no dia {}, não pode ser absorvido de forma correta pelo motivo de: formato do arquivo inadequado.

Solução: abra novamente o arquivo e o salve novamente como "Microsoft Excel Worksheet"(<nome do arquivo>.xlsx).
Certifique-se de que não esteja enviando um link para uma pasta OneDrive/Exchange, pois serão aceitos e reconhecidos apenas arquivos anexados ao e-mail.
Feito esta alteração, reenvie o arquivo com o formato correto para pedidoscandide@outlook.com .

Atenciosamente,
Renan Pires.
        """.format(name_sender, problem_maker, hora_formatada, data_formatada)
        # warning_group = [
        #     "comercial@candide.com.br", "emerson.figueiredo@candide.com.br", "cleo@candide.com.br", "rosana@candide.com.br",
        #     "wagner@candide.com.br", "luiz@candide.com.br", "marcelo@candide.com.br", "decio@candide.com.br",
        #     "suporte@candide.com.br", "rogerio@candide.com.br", "suporte.renan@candide.com.br"
        # ]
        warning_group = ["suporte@candide.com.br", "suporte.renan@candide.com.br"]
        assunto = "Erro de pedido: Formato invalido"
        if err is not None:
            self.obj_email.send_mail(recipient=problem_maker, copy_to=warning_group, subject=assunto, attach=err, content=msg)
        else:
            self.obj_email.send_mail(recipient=problem_maker, copy_to=warning_group, subject=assunto, content=msg)
