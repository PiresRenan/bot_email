import datetime
import os
import json
import quopri
import math
import pytz

import pandas as pd

from messenger import mail_sender, email_interpreter
from ns_api import connection


class Salesprogram:

    def check_email(self) -> str:
        try:
            self.clean_files()
        except Exception as e:
            print(" 1.0.1 - Não foi necessário limpar as pastas.")
            if not os.path.exists("Erros"):
                os.mkdir("Erros")
                print(" 1.0.1 [Contenção de erros] - A pasta 'Erros' foi criada.")
            if not os.path.exists("Pedidos"):
                os.mkdir("Pedidos")
                print(" 1.0.1 [Contenção de erros] - A pasta 'Pedidos' foi criada.")
        obj_email = email_interpreter.Email_getter()
        result = obj_email.email_catch()
        if result != "":
            return result
        else:
            return ""

    def get_data_from_excel(self) -> list:
        list_orders = []
        files = os.listdir("Pedidos")
        if len(files) > 0:
            for file in files:
                if file.endswith(".xlsx"):
                    path_to_file = os.path.join("Pedidos", file)
                    list_orders.append(self.retrieve_data_from_excel(path_to_file))
        try:
            list_orders = list_orders[0]
        except:
            list_orders = []
        return list_orders

    @staticmethod
    def retrieve_data_from_excel(path):
        df = pd.read_excel(path)
        pedido_atual = {}
        flag = 0
        pedidos: list = []
        for idx, row in df.iterrows():
            cnpj_sku, ordem_quantidade = str(row.iloc[0]), row.iloc[1]
            if len(str(cnpj_sku)) > 6:
                flag += 1
                pedido_atual = {"Pedido": [cnpj_sku, ordem_quantidade], "Items": []}
                pedidos.append(pedido_atual)
            else:
                item = {cnpj_sku: ordem_quantidade}
                pedido_atual['Items'].append(item)
        return pedidos

    @staticmethod
    def create_xlsx(cnpj=None, ordem_de_compra=None, lista_items=None) -> str:
        items = []
        for i in lista_items:
            item = (i['item']['externalId'], i['quantity'])
            items.append(item)
            data = [(cnpj, ordem_de_compra)] + items
            df = pd.DataFrame(data, columns=["CNPJ/SKU", "ORDEM DE COMPRA/QUANTIDADE"])
            try:
                with pd.ExcelWriter(f'./Erros/erro{cnpj}.xlsx', engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
            except Exception as e:
                print(e)
        arc_name = f'./Erros/erro{cnpj}.xlsx'
        return arc_name

    def recover_client_data(self, eid_cliente=None, order_marker=None, name_order_maker=None, ordem_de_compra_e_desconto=None, lista_items=None):
        obj_api = connection.NS_Services()
        err_send = mail_sender.Postman()
        try:
            client_data = obj_api.retrieve_client_data(cnpj=eid_cliente)
            if client_data['count'] == 0:
                client_data = obj_api.retrieve_client_data_retry(cnpj=eid_cliente)
                if client_data['count'] == 0:
                    client_data = obj_api.retrieve_client_data_last_try(cnpj=eid_cliente)
            return client_data
        except Exception as e:
            print(
                " 2.2.0 [Error] - Não pode recuperar os dados do CNPJ digitado, CNPJ: {}. Certifique-se se está digitado corretamente e/ou o cadastro está correto. Exceção capturada: {}".format(
                    eid_cliente, e))
            self.create_xlsx(cnpj=eid_cliente, ordem_de_compra=ordem_de_compra_e_desconto, lista_items=lista_items)
            brasilia_timezone = pytz.timezone('America/Sao_Paulo')
            now = datetime.datetime.now(brasilia_timezone)
            time_now = now.strftime("%d/%m/%Y às %H:%M:%S")
            corpo_email = """
        O pedido inserido {}, por {} <{}>, não pode ser absorvido.
        O motivo: CNPJ digitado no corpo do arquivo não foi encontrado nos registros do Oracle NetSuite da Candide Industria e Comercio ltda., certifique-se de ter digitado corretamente, ou se o cliente desejado foi previamente cadastrado no sistema.

        No caso do CNPJ não estar registrado, entre em contato com o setor de cadastros através do endereço cadastro@candide.com.br.
        Caso existam irregularidades com o CNPJ, entre em contato com comercial@candide.com.br.

        Atensiosamente,
        Candide Industria e Comércio ltda.
                    """.format(time_now, name_order_maker, order_marker)
            err_send.send_mail(recipient=order_marker, subject="CNPJ para o pedido inválido.",
                               attach='./Erros/erro_no_pedido_{}.xlsx'.format(eid_cliente))
            return 0

    def format_json(self, eid_cliente=None, ordem_de_compra_e_desconto=None, lista_items=None, memo=None,
                    order_marker=None, name_order_maker=None):
        global client_data
        err_send = mail_sender.Postman()
        obj_api = connection.NS_Services()
        inactive_items = []
        payload = {}
        erros = []
        desconto = ""
        lista_items_formatada: list = []
        client_data = self.recover_client_data(eid_cliente, order_marker, name_order_maker, ordem_de_compra_e_desconto, lista_items)
        if client_data != 0:
            try:
                print(" 2.3.0 - Inicio da formatação do json para envio.")
                try:
                    externalid_cliente = client_data['items'][0]['externalid']
                    eid = {"externalid": externalid_cliente}
                except:
                    externalid_cliente = client_data['items'][0]['id']
                    eid = {"id": externalid_cliente}
                cliente = {"entity": eid}
                payload.update(cliente)
                print(" 2.3.1 - ExternalId alocado com sucesso.")
                if ordem_de_compra_e_desconto != "":
                    try:
                        desconto = str(ordem_de_compra_e_desconto).split(':')[1].strip()
                    except Exception as a:
                        desconto = str(ordem_de_compra_e_desconto).strip()
                    try:
                        ordem_de_compra = str(ordem_de_compra_e_desconto).split(':')[0]
                    except:
                        ordem_de_compra = str(ordem_de_compra_e_desconto)
                    try:
                        if math.isnan(float(ordem_de_compra)):
                            ordem_de_compra = ""
                    except:
                        pass
                    ordem_de_compra = ''.join(ordem_de_compra.split())
                    if ordem_de_compra.upper() == "N":
                        ordem_de_compra = ""
                    ord_c = {"otherrefnum": ordem_de_compra}
                    payload.update(ord_c)
                    print(" 2.3.2 - Ordem de Compra alocado com sucesso.")
                try:
                    transportadora_padrao = client_data['items'][0]['custentity_acs_transp_cli']
                    t_padrao = {"custbody_enl_carrierid": transportadora_padrao}
                    payload.update(t_padrao)
                    print(" 2.3.3 - Transportadora padrão alocada com sucesso.")
                except Exception as e:
                    pass
                try:
                    tipo_de_frete = client_data['items'][0]['custentity_cand_tipofrete_cli']
                    frete_padrao = {"custentity_cand_tipofrete_cli": tipo_de_frete}
                    payload.update(frete_padrao)
                    print(" 2.3.4 - Tipo de frete padrão do cliente alocado com sucesso.")
                except Exception as e:
                    pass
                try:
                    prazo_padrao = client_data['items'][0]['terms']
                    p_padrao = {"terms": prazo_padrao}
                    payload.update(p_padrao)
                    print(" 2.3.5 - Prazo padrão do cliente alocado com sucesso.")
                except Exception as e:
                    pass
                try:
                    banco_padrao = client_data['items'][0]['custentity_acs_cfx_c_dfltpymntbnk_ls']
                    b_padrao = {"custbody_acs_cfx_bllngbnk_ls": banco_padrao}
                    payload.update(b_padrao)
                    print(" 2.3.6 - Banco Padrão do Cliente alocado com sucesso.")
                except Exception as e:
                    pass
                payload.update({
                    "custbody_enl_order_documenttype": 9,
                    "custbody_enl_operationtypeid": 222,
                    "taxdetailsoverride": False
                })
                print(" 2.3.7 - Tipo de documento, tipo de operação e sobreescrita de impostos alocados com sucesso.")
                if memo is not None:
                    payload.update({
                        "memo": "O pedido é continuação do pedido anterior."
                    })
                print(" 2.3.8 - Inicio da formatação de itens.")
                if desconto.upper() == 'N':
                    print(" 2.3.9 - Não foi solicitado os descontos.")
                else:
                    print(" 2.3.9 - Será aplicado as promoções para cada item de acordo com o sistema.")
                for item in lista_items:
                    for key, value in item.items():
                        try:
                            if math.isnan(float(key)):
                                key = 0
                            if key != "":
                                key = int(float(key))
                                key = str(key)
                            if math.isnan(float(value)):
                                value = 0
                                key = "error"
                            if len(key) < 4:
                                key = key.zfill(4)
                            try:
                                inativo = self.consulting_isinactive(key)
                            except:
                                key = int(key)
                                inativo = self.consulting_isinactive(key)

                            key = self.find_item_eid(key)
                            print(key)
                            if desconto.upper() == 'N':
                                i = {"item": {"externalId": key}, "quantity": int(value)}
                            else:
                                promo = obj_api.get_promo(key)
                                if promo:
                                    i = {"item": {"externalId": key}, "custcol_acs_aplc_prom": True, "quantity": int(value)}
                                else:
                                    i = {"item": {"externalId": key}, "quantity": int(value)}
                        except Exception as e:
                            error = e
                            if 'list index out of range' in str(e):
                                error = 'Item não encontrado!'
                            erros.append({"key": key})
                            i = {"item": {"externalId": key}, "quantity": "Item com erro: {}".format(e)}
                    lista_items_formatada.append(i)
                payload.update({"item": {"items": lista_items_formatada}})
                print(" 2.3.10 - Lista de itens alocados com sucesso.")
            except Exception as e:
                pass
            if len(inactive_items) > 0:
                payload.update({"inactive_items": inactive_items})
            if len(erros) > 0:
                payload.update({"Erros": erros})
                print(" 2.3.10a [Erro] - Existe um ou mais itens com erro.")
            print(" 2.3.11 - O json final é : \n{}".format(json.dumps(payload)))
            return payload
        else:
            return 0

    @staticmethod
    def clean_files() -> bool:
        path_to_file = ["./Erros", "./Pedidos"]
        for file in path_to_file:
            for item in os.listdir(file):
                item_path = os.path.join(file, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    try:
                        os.rmdir(item_path)
                    except OSError:
                        import shutil
                        shutil.rmtree(item_path)
        return True

    def special_chars_prevent(self, s=None):
        decoded_text = ''
        if s.startswith('=?iso-8859-1'):
            parts = s.split("?")
            if len(parts) >= 4:
                charset = parts[1]
                encoding = parts[2]
                encoded_text = parts[3]
                try:
                    decoded_text = quopri.decodestring(encoded_text).decode(charset)
                    decoded_text = decoded_text.replace("_", " ").replace("-", " ")
                except (quopri.Error, UnicodeDecodeError) as e:
                    print(f"Erro ao decodificar a string: {e}")
        else:
            decoded_text = s
        return decoded_text

    def order_with_inactive_items(self, json_to_absorve=None, itens_inativo=None, order_maker=None, order_maker_name=None):
        if json_to_absorve is not None:
            err_alert = mail_sender.Postman()
            brasilia_timezone = pytz.timezone('America/Sao_Paulo')
            now = datetime.datetime.now(brasilia_timezone)
            time_now = now.strftime("%d/%m/%Y às %H:%M:%S")
            str_itens = ""
            if len(itens_inativo) == 1:
                str_itens = itens_inativo[0]
                print(str_itens)
            else:
                for i, item in enumerate(itens_inativo):
                    str_itens += item
                    if i < len(itens_inativo) - 1:
                        str_itens += ", "
            cnpj = json_to_absorve['entity']['externalid']
            ordem_compra = json_to_absorve['otherrefnum']
            list_item = json_to_absorve['item']['items']
            arch_name = self.create_xlsx(cnpj, ordem_compra, list_item)
            non_itens = self.get_inactive_itens_list()
            conteudo = """
Olá {},
o pedido enviado no dia {}, não foi absorvido com êxito.

Os itens [{}] não estão disponiveis. Confira com o setor responsável(comercial@candide.com.br) e tome as medidas devidas enquanto a estes e então reencaminhe novamente o pedido para pedidoscandide@outlook.com.

Segue a lista completa de itens inativos:
{}

Atenciosamente,
Candide Industria e Comercio ltda
            """.format(order_maker_name, time_now, str_itens, non_itens)
            err_alert.send_mail(recipient=order_maker, subject="Pedido não inserido, item inativo", attach=arch_name, content=conteudo)
            print(" 2.3.13 - Alerta criado e enviado com sucesso para os emails de cópia padrão e {}".format(order_maker))
            return True

    def send_order(self, json_to_insert=None, order_marker=None, name_order_maker=None) -> bool:
        obj_api = connection.NS_Services()
        response = obj_api.insert_order(data_raw=json_to_insert)
        print(response.json())
        if response.status_code == 400:
            err_send = mail_sender.Postman()
            r = response.json()
            res = r['o:errorDetails'][0]['detail']
            if res.endswith('Saldo do cliente ultrapassa limite de crédito.'):
                json_ = json_to_insert
                values = []
                for item in json_['item']['items']:
                    externalId = item['item']['externalId']
                    item_value = obj_api.get_price(externalId)
                    qtd = item['quantity']
                    values.append(float(item_value)*qtd)
                total_order = self.calculate_total_of_order(values)
                email_content = """
Olá, {}
Houve um problema ao inserir o pedido.

Motivo: O saldo do cliente está abaixo do valor total do pedido a ser inserido. 
O pedido tem valor aproximado de R${},00 (impostos e preços personalizados não inclusos), entre em contato com o setor responsável (comercial@candide.com.br) para que o ajuste seja feito e reenvie o mesmo para que seja absorvido corretamente.

Atensiosamente,
Candide Industria e Comercio ltda. 
                """.format(name_order_maker, total_order)
                cnpj = json_['entity']['externalid']
                ordem_compra = json_['otherrefnum']
                list_item = json_['item']['items']
                arch_name = self.create_xlsx(cnpj, ordem_compra, list_item)
                print(" 2.3.15 - Pedido NÃO inserido - Cliente com saldo insuficiente.")
                err_send.send_mail(recipient=order_marker, subject="Saldo do cliente abaixo do total do pedido.", attach=arch_name, content=email_content)
            elif res.endswith('Prazo.'):
                json_ = json_to_insert
                cnpj = json_['entity']['externalid']
                ordem_compra = json_['otherrefnum']
                list_item = json_['item']['items']
                email_content = """
Olá, {}
Houve um problema ao inserir o pedido.

Motivo: O cadastro do cliente está incompleto. Campo "Prazo" está pendente.
O pedido poderá ser inserido assim que o setor responsável atualizar os dados cadastrais, sendo necessário encaminhar este email para cadastro@candide.com.br, solicitando que os dados do cliente do CNPJ {} sejam alinhados. 
Caso existam necessidades especiais e/ou prazos dedicados a este CNPJ em questão, reencaminhe o e-mail para comercial@candide.com.br. 

Atensiosamente,
Candide Industria e Comercio ltda. 
                                """.format(name_order_maker, cnpj)
                arch_name = self.create_xlsx(cnpj, ordem_compra, list_item)
                print(" 2.3.15 - Pedido NÃO inserido - Erro no prazo cadastrado do cliente.")
                copy_to = ["suporte.renan@candide.com.br", "suporte@candide.com.br", "comercial@candide.com.br", "rogerio@candide.com.br", "cadastro@candide.com.br",
                           "wagner@candide.com.br", "marcelogentil@candide.com.br", "luiz@candide.com.br"]
                err_send.send_mail(recipient=order_marker, copy_to=copy_to, subject="Dados cadastrais incompletos: Prazo", attach=arch_name, content=email_content)
            elif res != "":
                json_ = json_to_insert
                cnpj = json_['entity']['externalid']
                ordem_compra = json_['otherrefnum']
                list_item = json_['item']['items']
                arch_name = self.create_xlsx(cnpj, ordem_compra, list_item)
                err_send.send_mail(recipient=order_marker, err=res, attach=arch_name)
            return True
        elif response.status_code == 204:
            brasilia_timezone = pytz.timezone('America/Sao_Paulo')
            now = datetime.datetime.now(brasilia_timezone)
            time_now = now.strftime("%d/%m/%Y às %H:%M:%S")
            email_content = """
Olá, {}
O pedido feito no dia {}, foi inserido com êxito.

Confira no sistema NetSuite na barra de funções deixe o ponteiro do mouse sobre "Clientes", então entre as opções deixe o ponteiro do mouse sobre "Transações" e então clique em "Pedidos de vendas", fazendo isto aparecerá todos os pedidos que foram feitos e vinculados ao seu código de representante.

Atensiosamente,
Candide Industria e Comercio ltda. 
                            """.format(name_order_maker, time_now)
            insert_warning = mail_sender.Postman()
            insert_warning.send_mail(recipient=order_marker, subject="Pedido inserido com sucesso.", content=email_content)
            print(" 2.3.13 - Pedido inserido com sucesso!")
            return True

    def item_com_erro(self, json_to_insert=None, erros=None, name_order_maker=None, order_maker=None):
        json_ = json_to_insert
        err_send = mail_sender.Postman()
        cnpj = json_['entity']['externalid']
        ordem_compra = json_['otherrefnum']
        list_item = json_['item']['items']
        str_itens = ""
        if len(erros) == 1:
            str_itens = erros[0]['key']
        else:
            for i, item in enumerate(erros):
                str_itens += item['key']
                if i < len(erros) - 1:
                    str_itens += ", "
        email_content = """
Olá, {}
Houve um problema ao inserir o pedido.

Motivo: O item ou itens {} está/estão com erro, por favor revise o pedido. 
Deverá ser retirado ou tratado os itens em questão apontados no arquivo em anexo, caso permaneça o erro, entre em contato com comercial@candide.com.br. 

Atensiosamente,
Candide Industria e Comercio ltda. 
                        """.format(name_order_maker, str_itens)
        arch_name = self.create_xlsx(cnpj, ordem_compra, list_item)
        err_send.send_mail(recipient=order_maker, subject="Pedido com item com erro", content=email_content, attach=arch_name)
        print(" 2.3.13 - Pedido com item errado, emitido aviso para que seja tomada as devidas providencias. ")

    def get_inactive_itens_list(self) -> str:
        obj_api = connection.NS_Services()
        return obj_api.all_inactive_itens()

    def calculate_total_of_order(self, values=None):
        total = 0.0
        for value in values:
            total += float(value)
        return round(total/2)

    def consulting_isinactive(self, upccode=None) -> bool:
        if upccode is not None:
            obj_api = connection.NS_Services()
            if obj_api.is_inactive(upccode):
                return True
            else:
                return False

    def find_item_eid(self, key=None):
        if key is not None:
            obj_api = connection.NS_Services()
            key = obj_api.find_item_id(key)
        return key