import os
import json
import math
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
    def create_xlsx(cnpj, ordem_de_compra, lista_items):
        items = []
        for i in lista_items:
            item = (i['item']['externalId'], i['quantity'])
            items.append(item)

        data = [(cnpj, ordem_de_compra)] + items
        df = pd.DataFrame(data, columns=["CNPJ/SKU", "ORDEM DE COMPRA/QUANTIDADE"])

        with pd.ExcelWriter(f'./Erros/erro{cnpj}.xlsx', engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)

    def format_json(self, eid_cliente=None, ordem_de_compra_e_desconto=None, lista_items=None, memo=None):

        err_send = Postman()

        payload = {}
        desconto = ""
        lista_items_formatada: list = []
        obj_api = NS_Services()
        try:
            client_data = obj_api.retrieve_client_data(cnpj=eid_cliente)
        except Exception as e:
            print("Não pode recuperar os dados do CNPJ digitado, CNPJ: {}. Certifique-se se está digitado corretamente e/ou o cadastro está correto. Exceção capturada: {}".format(eid_cliente, e))
            err_send.send_mail()
        try:
            externalid_cliente = client_data['items'][0]['externalid']
            eid = {"externalid": externalid_cliente}
            cliente = {"entity": eid}
            payload.update(cliente)
        except Exception as e:
            pass
        print(payload)
        # if ordem_de_compra_e_desconto != "":
        #
        #     try:
        #         desconto = str(ordem_de_compra_e_desconto).split(':')[1].strip()
        #     except Exception as a:
        #         desconto = str(ordem_de_compra_e_desconto).strip()
        #
        #     try:
        #         ordem_de_compra = str(ordem_de_compra_e_desconto).split(':')[0]
        #     except:
        #         ordem_de_compra = str(ordem_de_compra_e_desconto)
        #
        #     try:
        #         if math.isnan(float(ordem_de_compra)):
        #             ordem_de_compra = ""
        #     except:
        #         pass
        #
        #     ordem_de_compra = ''.join(ordem_de_compra.split())
        #
        #     if ordem_de_compra.upper() == "N":
        #         ordem_de_compra = ""
        #
        #     ord_c = {"otherrefnum": ordem_de_compra}
        #     payload.update(ord_c)
        #
        # try:
        #     transportadora_padrao = client_data[1]
        #     t_padrao = {"custbody_enl_carrierid": transportadora_padrao}
        #     payload.update(t_padrao)
        # except Exception as e:
        #     pass
        #
        # try:
        #     tipo_de_frete = client_data[2]
        #     frete_padrao = {"custentity_cand_tipofrete_cli": tipo_de_frete}
        #     payload.update(frete_padrao)
        # except Exception as e:
        #     pass
        #
        # try:
        #     prazo_padrao = client_data[3]
        #     p_padrao = {"terms": prazo_padrao}
        #     payload.update(p_padrao)
        # except Exception as e:
        #     pass
        #
        # try:
        #     banco_padrao = client_data[4]
        #     b_padrao = {"custbody_acs_cfx_bllngbnk_ls": banco_padrao}
        #     payload.update(b_padrao)
        # except Exception as e:
        #     pass
        #
        # payload.update({
        #     "custbody_enl_order_documenttype": 9,
        #     "custbody_enl_operationtypeid": 222,
        #     "taxdetailsoverride": False
        # })
        #
        # if memo is not None:
        #     payload.update({
        #         "memo": "O pedido é continuação do pedido anterior."
        #     })
        #
        # for item in lista_items:
        #     for key, value in item.items():
        #
        #         if math.isnan(float(key)):
        #             key = 0
        #
        #         if key != "":
        #             key = int(float(key))
        #             key = str(key)
        #
        #         if math.isnan(float(value)):
        #             value = 0
        #             key = "error"
        #
        #         if desconto.upper() == 'N':
        #             i = {"item": {"externalId": key}, "quantity": int(value)}
        #
        #         else:
        #             promo = self.o_ns.get_promo(key)
        #             if promo > 0:
        #                 i = {"item": {"externalId": key}, "custcol_acs_aplc_prom": True, "quantity": int(value)}
        #             else:
        #                 i = {"item": {"externalId": key}, "quantity": int(value)}
        #         lista_items_formatada.append(i)
        #
        # payload.update({"item": {"items": lista_items_formatada}})
        #
        # return json.dumps(payload)

    # def warning_error(self):


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
