import requests
import time
import oauth2 as oauth
from .sign_sha256 import SignatureMethod_HMAC_SHA256


class NS_Services:
    def __init__(self, _environment=None, where=None, payload=None):
        if _environment is not None:
            _environment = int(_environment)
            if _environment == 1:
                # PRODUCTION
                self.consumer_key = "0bb156a24a337d8d2d6323d76dc655aa3e682839111e01f096ea6ded6e0f6ffa"
                self.consumer_secret = "f06f8e9a8611eb9aa0ae1c5e7ed6b20ed742f25c9e33afa46eaab06bf38abfc9"
                self.token_key = "c39621762979221db09e697c341be870d69cbf9dfb0b319668201429e833b487"
                self.token_secret = "ab6fbcedb4bc3ee2473aa273fafa9179b1139752516f8fe92c21e6d143398276"
                self.url = f"https://7586908.suitetalk.api.netsuite.com/services/rest/"
                self.realm = '7586908'
            elif _environment == 2:
                # SANDBOX
                self.consumer_key = "9b6410f3cc08ffddde74606bcffe25f09744438d65588c1f1884368f0c6664ae"
                self.consumer_secret = "46555a11b49191e9f3af95405cdad0b931fa4861fd8a26a80403d42eb6ef72fa"
                self.token_key = "cb38dbeea1075a85610e2cb7f2191f396feda6065308695f1e4e4f2f0900d555"
                self.token_secret = "ba20c9979714b030d98ba0b1fc92418e2c209828db2d1cb596b91b791d2b427d"
                self.url = f"https://7586908-sb1.suitetalk.api.netsuite.com/services/rest/"
                self.realm = '7586908_SB1'
            self.consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_secret)
            self.token = oauth.Token(key=self.token_key, secret=self.token_secret)
            if where is None:
                self.url_ = f'{self.url}query/v1/suiteql?limit=1000'
            else:
                self.url_ = f'{self.url}{where}'
            if payload is None:
                self.payload = {}
            else:
                self.payload = payload
        else:
            print("Corrija o endpoint, não possui a especificação para o ambiente.")

    def get_results(self, _environment=None, where=None, payload=None, http_method=None):
        if where is None:
            where = self.url_
        else:
            where = "{}{}".format(self.url, where)

        if payload is None:
            payload = self.payload

        if http_method is not None:
            params = {
                'oauth_version': "1.0",
                'oauth_nonce': oauth.generate_nonce(),
                'oauth_timestamp': str(int(time.time())),
                'oauth_token': self.token.key,
                'oauth_consumer_key': self.consumer.key
            }
            request = oauth.Request(method=http_method, url=where, parameters=params)
            signature_method = SignatureMethod_HMAC_SHA256()
            request.sign_request(signature_method, self.consumer, self.token)
            header = request.to_header(self.realm)
            auth = header['Authorization'].encode('ascii', 'ignore')
            headerx = {'Authorization': auth, "Content-Type": "application/json", 'prefer': 'transient',
                       'Cookie': 'NS_ROUTING_VERSION=LAGGING', 'expandSubResources': 'true'}

            if http_method == "POST":
                return self.get_results_POST(where, headerx, payload)
            elif http_method == "GET":
                return self.get_results_GET(where, headerx)
            elif http_method == "DELETE":
                return self.get_results_DELETE(where, headerx)
            elif http_method == "PATCH":
                return self.get_results_PATCH(where, headerx)
            else:
                return f"O metodo '{http_method}' não existe."
        else:
            return "Metodo HTTP não está definido."

    def get_results_POST(self, where, headerx, payload):
        if self.url_.endswith("services/rest/record/v1/salesorder"):
            response = requests.request("POST", where, headers=headerx, data=self.payload)
            return response
        else:
            with requests.post(url=where, headers=headerx, json=payload) as connection:
                results = connection
            return results

    def get_results_GET(self, where, headerx):
        results = ""
        try:
            with requests.get(url=where, headers=headerx) as connection:
                results = connection
        except requests.exceptions.ConnectionError as e:
            results = f"Ocorreu um erro de conexão: {e}"
        except requests.exceptions.Timeout as e:
            results = f"A requisição excedeu o tempo limite: {e}"
        except requests.exceptions.RequestException as e:
            results = f"Ocorreu um erro na requisição: {e}"
        finally:
            return results

    def get_results_PATCH(self, where, headerx):
        response = requests.request("PATCH", where, headers=headerx, data=self.payload)
        results = response
        response.close()
        return results

    def get_results_DELETE(self, where, headerx):
        with requests.delete(url=where, headers=headerx, json=self.payload) as results:
            return results
