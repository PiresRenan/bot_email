import os
import openpyxl
import pandas as pd

from messenger import Email_getter


class Salesprogram:

    def check_email(self) -> bool:
        self.clean_files()
        obj_email = Email_getter()
        if obj_email.email_catch():
            return True
        else:
            return False

    def get_data_from_excel(self) -> list:
        list_orders = []
        files = os.listdir("Pedidos")
        if len(files) > 0:
            for file in files:
                if file.endswith(".xlsx"):
                    path_to_file = os.path.join(".Pedidos", file)
                    list_orders.append(self.retrieve_data_from_excel(path_to_file))
        print(list_orders)
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
