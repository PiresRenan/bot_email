import json
import re

import requests
from time import time, sleep
import oauth2 as oauth

from .sign_sha256 import SignatureMethod_HMAC_SHA256


class NS_Services:
    def __init__(self):
        # Produção
        self.CONSUMER_ID = "0bb156a24a337d8d2d6323d76dc655aa3e682839111e01f096ea6ded6e0f6ffa"
        self.CONSUMER_SECRET = "f06f8e9a8611eb9aa0ae1c5e7ed6b20ed742f25c9e33afa46eaab06bf38abfc9"
        self.TOKEN_ID = "c7d8d94074e6e1cfbef510e59d04b888b4d3439634a1c0c661f7060a65414840"
        self.TOKEN_SECRET = "bd27af00e8c691857ecdf26259edb8f50773f7f01fb564c771806709fe404120"
        # Sandbox
        self.CONSUMER_ID_SB1 = "9b6410f3cc08ffddde74606bcffe25f09744438d65588c1f1884368f0c6664ae"
        self.CONSUMER_SECRET_SB1 = "46555a11b49191e9f3af95405cdad0b931fa4861fd8a26a80403d42eb6ef72fa"
        self.TOKEN_ID_SB1 = "cb38dbeea1075a85610e2cb7f2191f396feda6065308695f1e4e4f2f0900d555"
        self.TOKEN_SECRET_SB1 = "ba20c9979714b030d98ba0b1fc92418e2c209828db2d1cb596b91b791d2b427d"

    def build_header(self, env=None,  http_mtd=None, url=None):
        if env is None:
            env = 2
        if http_mtd is None:
            http_mtd = "POST"
        if url is None:
            url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        if env == 1:
            consumer = oauth.Consumer(key=self.CONSUMER_ID, secret=self.CONSUMER_SECRET)
            token = oauth.Token(key=self.TOKEN_ID, secret=self.TOKEN_SECRET)
            realm = "7586908"
        else:
            consumer = oauth.Consumer(key=self.CONSUMER_ID_SB1, secret=self.CONSUMER_SECRET_SB1)
            token = oauth.Token(key=self.TOKEN_ID_SB1, secret=self.TOKEN_SECRET_SB1)
            realm = "7586908_SB1"
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': str(int(time())),
            'oauth_consumer_key': consumer.key,
            'oauth_token': token.key
        }
        request = oauth.Request(method=http_mtd, url=url, parameters=params)
        signature_method = SignatureMethod_HMAC_SHA256()
        request.sign_request(signature_method, consumer, token)
        header = request.to_header(realm)
        headery = header['Authorization'].encode('ascii', 'ignore')
        headerx = {'Authorization': headery, "Content-Type": "application/json", 'prefer': 'transient',
                   'Cookie': 'NS_ROUTING_VERSION=LAGGING'}
        return headerx

    def retrieve_client_data(self, cnpj=None):
        if cnpj is not None:
            url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
            data_raw = {
                "q": f"SELECT custentity_cand_tipofrete_cli, custentity_acs_cfx_c_dfltpymntbnk_ls, custentity_acs_carteira, externalid, custentity_acs_transp_cli, terms "
                     f"FROM customer "
                     f"WHERE custentity_enl_cnpjcpf = '{cnpj}'"
            }
            with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
                result = r.json()
            return result

    def retrieve_client_data_retry(self, cnpj=None):
        if len(cnpj) < 14:
            cnpj = cnpj.zfill(14)
        elif len(cnpj) > 14:
            cnpj = cnpj[:14]
        url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT custentity_cand_tipofrete_cli, custentity_acs_cfx_c_dfltpymntbnk_ls, custentity_acs_carteira, externalid, custentity_acs_transp_cli, terms "
                 f"FROM customer "
                 f"WHERE custentity_enl_cnpjcpf='{cnpj}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        return result

    def retrieve_client_data_last_try(self, cnpj=None):
        if cnpj is not None:
            url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
            data_raw = {
                "q": f"SELECT custentity_cand_tipofrete_cli, custentity_acs_cfx_c_dfltpymntbnk_ls, custentity_acs_carteira, externalid, custentity_acs_transp_cli, terms "
                     f"FROM customer "
                     f"WHERE custentity_enl_cnpjcpf LIKE %'{cnpj}'%"
            }
            with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
                result = r.json()
            return result

    def get_price(self, eid=None):
        url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT custitem13 FROM item WHERE upccode='{eid}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        price = result['items'][0]['custitem13']
        return price

    def notificar_erro(self, info: dict, error_detail: str):
        objeto_criador_xlsx = order_filter.VerificarPedidos('./Erros')
        items = [item for item in info['item']['items']]
        objeto_criador_xlsx.criar_xlsx(info['entity']['externalid'], info['otherrefnum'], items)
        obj_notificador = send_mail.OutlookMailSender()
        obj_notificador.send_mail(error_detail)

    def capturar_erros(self, erro, data_raw) -> bool:
        _url = "https://7586908-sb1.suitetalk.api.netsuite.com/services/rest/record/v1/salesorder"
        try:
            erro_detail = erro['o:errorDetails'][0]['detail']

            if erro_detail.endswith('[entity]'):

                try:
                    novo_data_raw = json.loads(data_raw)
                    cnpj = novo_data_raw['entity']['externalid']
                    id = self.get_id(cnpj)
                    novo_data_raw['entity'] = {'id': id}
                    novo_data_raw = json.dumps(novo_data_raw)
                    result = self.get_results("POST", _url, novo_data_raw)

                    if result.status_code != 204:
                        error = result.json()
                        error_detail = error['o:errorDetails'][0]['detail']

                        try:
                            error_detail = error_detail.replace("Error while accessing a resource. ", "")
                            self.notificar_erro(json.loads(data_raw), error_detail)
                        except:
                            self.notificar_erro(json.loads(data_raw), error_detail)
                    else:
                        return True
                except Exception as e:
                    self.notificar_erro(json.loads(data_raw), str(e))
                    return False
            elif erro_detail.startswith('The record instance for external ID') and erro_detail.endswith(
                    'Provide a valid record instance ID.'):
                padrao = r"The record instance for external ID '(.*?)' does not exist"
                resultado = re.search(padrao, erro_detail)
                valor = ''
                if resultado:
                    valor = str(resultado.group(1))
                descricao_erro = f'O seguinte sku está com alguma falha de integridade, verifique: {valor}'
                self.notificar_erro(json.loads(data_raw), descricao_erro)
            elif erro_detail.endswith('Você deve inserir ao menos um item de linha para esta transação.'):
                detalhes_erro = f'Existe algum item com valor de sku invalido, certifique.'
                self.notificar_erro(json.loads(data_raw), detalhes_erro)


            else:
                self.notificar_erro(json.loads(data_raw), erro_detail)

        except:

            return False

    def insert_order(self, data_raw) -> bool:
        _url = "https://7586908.suitetalk.api.netsuite.com/services/rest/record/v1/salesorder"
        response = requests.request("POST", _url, headers=self.build_header(env=1, url=_url), data=data_raw)
        return response

    def search_response(self, cod):
        data_raw = {
            "q": f"SELECT custentity_cand_tipofrete_cli, custentity_acs_cfx_c_dfltpymntbnk_ls, custentity_acs_carteira, externalid, custentity_acs_transp_cli, terms "
                 f"FROM customer "
                 f"WHERE custentity_enl_cnpjcpf='{cod}'"
        }
        result = self.get_results("POST", self.ENDPOINT, data_raw)
        response = result.json()
        return response

    def alternative_search_response(self, cod):
        data_raw = {
            "q": f"SELECT custentity_cand_tipofrete_cli, custentity_acs_cfx_c_dfltpymntbnk_ls, custentity_acs_carteira, externalid, custentity_acs_transp_cli, terms "
                 f"FROM customer "
                 f"WHERE custentity_enl_cnpjcpf LIKE '%{cod}%'"
        }
        result = self.get_results("POST", self.ENDPOINT, data_raw)
        response = result.json()
        return response

    def search_eid(self, cod):
        externalId, transportadora, t_frete, banco_padrao, prazo, flag, tentativas, cod_inicial = "", "", "", "", "", True, 0, cod
        while flag:
            resp = self.search_response(cod)
            if resp['totalResults'] > 0:
                flag = False
            elif tentativas < 5:
                cod = cod.zfill(len(cod) + 1)
                tentativas += 1
            else:
                flag = False
                resp = self.alternative_search_response(cod_inicial)
                if resp['totalResults'] == 0:
                    return f"{cod_inicial} não encontrado", "1045"

        try:
            carteira: str = resp['items'][0]['custentity_acs_carteira']
        except:
            carteira: str = 'F'

        if carteira == 'F':
            try:
                banco_padrao: str = resp['items'][0]['custentity_acs_cfx_c_dfltpymntbnk_ls']
            except:
                banco_padrao: str = '2'

        try:
            t_frete: str = resp['items'][0]['custentity_cand_tipofrete_cli']
        except:
            t_frete: str = '2'

        try:
            externalId: str = resp['items'][0]['externalid']
        except:
            externalId: str = cod
        try:
            transportadora: str = resp['items'][0]['custentity_acs_transp_cli']
        except:
            transportadora: str = '1049'

        try:
            prazo = int(resp['items'][0]['terms'])
        except:
            prazo = 35

        if banco_padrao != "":
            return externalId, transportadora, t_frete, prazo, banco_padrao
        else:
            return externalId, transportadora, t_frete, prazo

    def get_promo(self, eid) -> float:
        data_raw = {
            "q": f"SELECT custitem_acs_promo FROM item WHERE externalid='{eid}'"
        }
        result = self.get_results("POST", self.ENDPOINT, data_raw)
        result_ = result.json()
        try:
            promocao = float(result_['items'][0]['custitem_acs_promo'])
            return promocao
        except Exception as e:
            return 0

    def get_id(self, cnpj: str):
        data_raw = {
            "q": f"SELECT id FROM customer WHERE custentity_enl_cnpjcpf='{cnpj}'"
        }
        result = self.get_results("POST", self.ENDPOINT, data_raw)
        result_ = result.json()
        return result_['items'][0]['id']