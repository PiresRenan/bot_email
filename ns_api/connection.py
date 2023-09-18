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

    def build_header(self, env=None, http_mtd=None, url=None):
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
                     f"WHERE   LIKE %'{cnpj}'%"
            }
            with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
                result = r.json()
            return result

    def all_inactive_itens(self) -> str:
        url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT upccode FROM item WHERE isinactive='T'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        itens = result['items']
        filtered_items = []
        for item in itens:
            upccode = item.get('upccode', '')
            if not upccode.startswith('C') and upccode.isdigit():
                filtered_items.append(int(upccode))
        final_str = '\n'.join(map(str, filtered_items))
        return final_str

    def get_price(self, eid=None):
        url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT custitem13 FROM item WHERE upccode='{eid}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        price = result['items'][0]['custitem13']
        return price

    def is_inactive(self, eid=None):
        url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT isinactive FROM item WHERE upccode='{eid}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        inactive = result['items'][0]['isinactive']
        if inactive == "F":
            return False
        else:
            return True

    def insert_order(self, data_raw=None):
        _url = "https://7586908.suitetalk.api.netsuite.com/services/rest/record/v1/salesorder"
        data_raw = json.dumps(data_raw)
        response = requests.request("POST", _url, headers=self.build_header(env=1, url=_url), data=data_raw)
        return response

    def get_promo(self, eid=None) -> bool:
        url = "https://7586908.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT custitem_acs_promo FROM item WHERE externalid='{eid}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        try:
            promocao = float(result['items'][0]['custitem_acs_promo'])
        except:
            promocao = 0
        try:
            if promocao > 0:
                return True
            else:
                return False
        except Exception as e:
            print(" 2.3.9 [Error] - Erro na captura da promoção. Erro: {}".format(e))
            return False
