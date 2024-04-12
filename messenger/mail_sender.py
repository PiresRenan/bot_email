import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders


class Postman:

    def __init__(self):
        self.username = "netsuite@email.com.br"
        self.password = "123456"
        self.smtp_server = "smtp-mail.outlook.com"

    def send_mail(self, recipient=None, copy_to=None, subject=None, attach=None, content=None, err=None) -> bool:

        if recipient is None:
            recipient = "suporte@email.com.br"

        if copy_to is None:
            copy_to = [
                "suporte@email.com.br",
                "cadastro@email.com.br",
                "decio@email.com.br",
                "cleo@email.com.br",
                "rosana@email.com.br",
                "rogerio@email.com.br",
                "wagner@email.com.br",
                "marcelogentil@email.com.br",
                "luiz@email.com.br"
                       ]

        if subject is None:
            subject = "Pedido com erro. Causa pendente."

        if content is None:
            if err is None:
                pass
            else:
                content = """
O pedido que acabara de gerar uma tentativa de absorção, não obteve êxito!\n
A causa do erro é desconhecido. Entrar em contato com Suporte.
                    
Causas comuns de erros:
    - Nome de arquivo com caractere inválido
    - Extensão do arquivo incorreta, deve ser <nome_do_arquivo>.xlsx
    - O arquivo está fora da formatação correta.
    - O arquivo está com algum item presente no pedido com irregularidade no SKU.
    - Existem células vazias.\n\n
Lembrete: o arquivo deve-se conter apenas duas colunas, na primeira linha deve conter o cabeçalho com a escrita imutável "CNPJ/SKU" na coluna um e na coluna dois "ORDEM DE COMPRA/QUANTIDADE", e então os dados referentes aos pedidos, sendo que cada pedido deve conter em sua primeira linha o cnpj do cliente, e ordem de compra se houver e marcação para aplicação de descontos "n", nas linhas subsequentes devem se conter sku e quantidade referente aos itens, podendo se digitar inumeros pedidos seguindo esta formatação.
                   
Atenciosamente,\n
Candide Industria e Comercio ltda. 
                        """
                content = """
O pedido que acabara de gerar uma tentativa de absorção, não obteve êxito!\n
Causa do erro pelo NetSuite: {}\n\n
Tome as devidas providencias quanto a esta problemática e então reenvie o pedido para pedidoscandide@outlook.com.
Atenciosamente,\n
Candide Industria e Comercio ltda.
                """.format(err)
        if attach is not None:
            complete_path = ""
            for arquivo in os.listdir("./Erros"):
                complete_path = os.path.join('./Erros', arquivo)
            with open(complete_path, 'rb') as binary_pdf:
                payload = MIMEBase('application', 'octate-stream', Name=complete_path)
                payload.set_payload((binary_pdf).read())
            encoders.encode_base64(payload)
            payload.add_header('Content-Decomposition',
                               'attachment', filename=complete_path)
            msg = MIMEMultipart()
            msg.attach(payload)
        else:
            msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = recipient
        msg['Cc'] = ', '.join(copy_to)
        msg['Subject'] = subject
        body = content
        msg.attach(MIMEText(body))
        try:
            server = smtplib.SMTP(self.smtp_server, 587)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.close()
            return True
        except Exception as e:
            print("O email não foi enviado pelo seguinte motivo: {}".format(e))
            return False