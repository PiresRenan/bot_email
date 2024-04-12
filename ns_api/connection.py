import json
import re

import requests
from time import time, sleep
import oauth2 as oauth

from .sign_sha256 import SignatureMethod_HMAC_SHA256


class NS_Services:
    def __init__(self):
        # Produção
        self.CONSUMER_ID = "123654"
        self.CONSUMER_SECRET = "123987"
        self.TOKEN_ID = "12345"
        self.TOKEN_SECRET = "0256"
        # Sandbox
        self.CONSUMER_ID_SB1 = "9784"
        self.CONSUMER_SECRET_SB1 = "6548"
        self.TOKEN_ID_SB1 = "120as"
        self.TOKEN_SECRET_SB1 = "asdf98"

    def build_header(self, env=None, http_mtd=None, url=None):
        if env is None:
            env = 2
        if http_mtd is None:
            http_mtd = "POST"
        if url is None:
            url = "https://envoionment.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        if env == 1:
            consumer = oauth.Consumer(key=self.CONSUMER_ID, secret=self.CONSUMER_SECRET)
            token = oauth.Token(key=self.TOKEN_ID, secret=self.TOKEN_SECRET)
            realm = "123"
        else:
            consumer = oauth.Consumer(key=self.CONSUMER_ID_SB1, secret=self.CONSUMER_SECRET_SB1)
            token = oauth.Token(key=self.TOKEN_ID_SB1, secret=self.TOKEN_SECRET_SB1)
            realm = "123_sb"
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
            url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
            data_raw = {
                "q": f"SELECT id, frete, tipo_bank, sld, externalid, transportadora, prazo "
                     f"FROM customer "
                     f"WHERE cnpj = '{cnpj}'"
            }
            with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
                result = r.json()
            return result

    def retrieve_client_data_retry(self, cnpj=None):
        if len(cnpj) < 14:
            cnpj = cnpj.zfill(14)
        elif len(cnpj) > 14:
            cnpj = cnpj[:14]
        url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT id, tipo_frete, conta, saldo, externalid, transportadora, prazo "
                 f"FROM customer "
                 f"WHERE cnpj='{cnpj}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        return result

    def retrieve_client_data_last_try(self, cnpj=None):
        if cnpj is not None:
            url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
            data_raw = {
                "q": f"SELECT id, tipo_frete, saldo, saldo2, externalid, transportadora, prazo "
                     f"FROM customer "
                     f"WHERE cnpj LIKE '{cnpj}'"
            }
            with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
                result = r.json()
            return result

    def find_item_id(self, key=None):
        if key is not None:
            url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
            data_raw = {
                "q": f"SELECT eid "
                     f"FROM item "
                     f"WHERE prod='{key}'"
            }
            with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
                result = r.json()
            eid = result['items'][0]['externalid']
            return eid

    def all_inactive_itens(self) -> str:
        url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT prod FROM item WHERE isinactive='T'"
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
        url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT item_inf FROM item WHERE codigo_item='{eid}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        price = result['items'][0]['custitem13']
        return price

    def search_for_inactive(self, internal_id=None):
        url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT eid FROM item WHERE id='{internal_id}'"
        }
        with requests.post(url=url, headers=self.build_header(env=1), json=data_raw) as r:
            result = r.json()
        eid = result['items'][0]['externalid']
        return eid

    def is_inactive(self, eid=None):
        url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
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
        _url = "https://env.suitetalk.api.netsuite.com/services/rest/record/v1/salesorder"
        data_raw = json.dumps(data_raw)
        response = requests.request("POST", _url, headers=self.build_header(env=1, url=_url), data=data_raw)
        return response

    def get_promo(self, eid=None) -> bool:
        url = "https://env.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql?limit=1000"
        data_raw = {
            "q": f"SELECT promocao FROM item WHERE eid='{eid}'"
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
