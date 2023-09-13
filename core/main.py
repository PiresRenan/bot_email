import datetime
import os
import json
import math
from time import sleep

import openpyxl
import pandas as pd

from messenger import Email_getter, Postman
from ns_api import NS_Services


class Salesprogram:

    def check_email(self) -> str:
        self.clean_files()
        obj_email = Email_getter()
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
        return list_orders

    @staticmethod
    def retrieve_data_from_excel(path):
        df = pd.read_excel(path)
        pedido_atual = {}
        flag = 0
        pedidos: list = []
        for idx, row in df.iterrows():
            cnpj_sku, ordem_quantidade = str(row[0]), row[1]
            if len(str(cnpj_sku)) > 6:
                flag += 1
                pedido_atual = {"Pedido": [cnpj_sku, ordem_quantidade], "Items": []}
                pedidos.append(pedido_atual)
            else:
                item = {cnpj_sku: ordem_quantidade}
                pedido_atual['Items'].append(item)
        return pedidos

    @staticmethod
    def create_xlsx(cnpj=None, ordem_de_compra=None, lista_items=None):
        items = []
        for i in lista_items:
            item = (i['item']['externalId'], i['quantity'])
            items.append(item)
            data = [(cnpj, ordem_de_compra)] + items
            df = pd.DataFrame(data, columns=["CNPJ/SKU", "ORDEM DE COMPRA/QUANTIDADE"])
            with pd.ExcelWriter(f'./Erros/erro{cnpj}.xlsx', engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)

    def recover_client_data(self, eid_cliente=None, order_marker=None, name_order_maker=None, ordem_de_compra_e_desconto=None, lista_items=None):
        obj_api = NS_Services()
        err_send = Postman()
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
            now = datetime.datetime.now()
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
        err_send = Postman()
        obj_api = NS_Services()
        inactive_items = []
        payload = {}
        desconto = ""
        lista_items_formatada: list = []
        client_data = self.recover_client_data(eid_cliente, order_marker, name_order_maker, ordem_de_compra_e_desconto, lista_items)
        if client_data != 0:
            try:
                print(" 2.3.0 - Inicio da formatação do json para envio.")
                externalid_cliente = client_data['items'][0]['externalid']
                eid = {"externalid": externalid_cliente}
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
                        if math.isnan(float(key)):
                            key = 0
                        if key != "":
                            key = int(float(key))
                            key = str(key)
                        if math.isnan(float(value)):
                            value = 0
                            key = "error"
                        if self.consulting_isinactive(key):
                            inactive_items.append(key)
                        if desconto.upper() == 'N':
                            i = {"item": {"externalId": key}, "quantity": int(value)}
                        else:
                            promo = obj_api.get_promo(key)
                            if promo:
                                i = {"item": {"externalId": key}, "custcol_acs_aplc_prom": True, "quantity": int(value)}
                            else:
                                i = {"item": {"externalId": key}, "quantity": int(value)}
                    lista_items_formatada.append(i)
                payload.update({"item": {"items": lista_items_formatada}})
                print(" 2.3.10 - Lista de itens alocados com sucesso.")
            except Exception as e:
                pass
            if len(inactive_items) > 0:
                payload.update({"inactive_items": inactive_items})
            # print(" 2.3.11 - O json final é : \n{}".format(json.dumps(payload)))
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

    def order_with_inactive_items(self, json_to_absorve=None, itens_inativo=None, order_maker=None, order_maker_name=None):
        if json_to_absorve is not None:
            err_alert = Postman()
            now = datetime.datetime.now()
            time_now = now.strftime("%d/%m/%Y às %H:%M:%S")
            str_itens = ""
            if len(itens_inativo) == 1:
                str_itens = itens_inativo[0]
            else:
                for i, item in enumerate(itens_inativo):
                    str_itens += item
                    if i < len(itens_inativo) - 1:
                        str_itens += ", "
            cnpj = json_to_absorve['entity']['externalid']
            ordem_compra = json_to_absorve['otherrefnum']
            list_item = json_to_absorve['item']['items']
            print(cnpj)
            self.create_xlsx(cnpj, ordem_compra, list_item)
            archive_name = f'./Erros/erro_no_pedido_{cnpj}.xlsx'
            conteudo = """
Olá {},
o pedido enviado no dia {}, não foi absorvido com êxito.

Os itens {} não estão disponiveis. Confira com o setor responsável(comercial@candide.com.br) e tome as medidas devidas enquanto a estes e então reencaminhe para pedidoscandide@outlook.com

Atenciosamente,
Candide Industria e Comercio ltda
            """.format(order_maker_name, time_now, str_itens)
            # err_alert.send_mail(recipient=order_maker, subject="Pedido não inserido, item inativo", attach=archive_name, content=conteudo)

    def send_order(self, json_to_insert=None, order_marker=None, name_order_maker=None) -> bool:
        obj_api = NS_Services()
        response = obj_api.insert_order(data_raw=json_to_insert)
        if response.status_code == 400:
            err_send = Postman()
            r = response.json()
            res = r['o:errorDetails'][0]['detail']
            if res.endswith('Saldo do cliente ultrapassa limite de crédito.'):
                json_ = json.loads(json_to_insert)
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
O pedido tem valor aproximado de {} (impostos e preços personalizados não inclusos), entre em contato com o setor responsável (comercial@candide.com.br) para que o ajuste seja feito e reenvie o mesmo para que seja absorvido corretamente.

Atensiosamente,
Candide Industria e Comercio ltda. 
                """.format(name_order_maker, total_order)
                # self.create_xlsx()
                # err_send.send_mail(recipient=order_marker, subject="Saldo do cliente abaixo do total do pedido.", )
            elif res != "":
                print(res)
        return True

    def calculate_total_of_order(self, values=None):
        total = 0.0
        for value in values:
            total += float(value)
        return round(total)

    def consulting_isinactive(self, upccode=None) -> bool:
        if upccode is not None:
            obj_api = NS_Services()
            if obj_api.is_inactive(upccode):
                return True
            else:
                return False
