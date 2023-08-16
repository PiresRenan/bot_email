import os
import openpyxl
import pandas as pd

from messenger import Email_getter


class Salesprogram:

    def get_data(self):
        if self.check_email():
            self.format_data()
            # self.clean_files()
        return "Funcionando"

    def check_email(self):
        teste = Email_getter()
        if teste.email_catch():
            return True
        else:
            return False

    def format_data(self):
        print(self.search_for_files())
        pass

    def search_for_files(self):
        path_to_file = "./Pedidos"
        lista_pedidos_final = []

        arquivos = os.listdir(path_to_file)
        for arquivo in arquivos:
            if arquivo.endswith('.xlsx'):
                caminho_arquivo = os.path.join(path_to_file, arquivo)
                lista_pedidos_final.append(self.get_data_xlsx(caminho_arquivo))

        return lista_pedidos_final

    def get_data_xlsx(self, path=None):
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
    def clean_files():
        path_to_file = ["./Erros", "./Pedidos"]
        for file in path_to_file:
            print(file)
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
