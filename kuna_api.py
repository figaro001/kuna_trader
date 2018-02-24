
import hashlib
import hmac
import json
import time
from collections import OrderedDict
from urllib.parse import urlencode

import requests
import credentials


class KunaApiClient(object):

    API_DOMAIN = 'https://kuna.io/api/v2'
    TICKERS_URL = '{}/tickers/ethuah'.format(API_DOMAIN)
    ORDERS_URL = '{}/orders'.format(API_DOMAIN)
    TRADES_URL = '{}/trades/my'.format(API_DOMAIN)
    ME_URL = '{}/members/me'.format(API_DOMAIN)

    def __init__(self, api_key=credentials.API_KEY, api_secret=credentials.API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret

    def _build_personal_url(self, url, method, params):
        tonce = int(round(time.time() * 1000))
        params['tonce'] = tonce
        params['access_key'] = self.api_key
        params = OrderedDict(sorted(params.items(), key=lambda t: t[0]))
        msg = '{0}|{1}|{2}'.format(method.upper(), url.replace('https://kuna.io', ''), urlencode(params))
        signature = hmac.new(self.api_secret.encode('utf-8'), msg=msg.encode('utf-8'), digestmod=hashlib.sha256)
        signature = signature.hexdigest()
        return '{0}?access_key={1}&tonce={2}&signature={3}'.format(url, self.api_key, tonce, signature)

    def sell_eth(self, volume, price):
        params = {'side': 'sell',
                  'volume': volume,
                  'market': 'ethuah',
                  'price': price}
        url = self._build_personal_url(self.ORDERS_URL, 'POST', params)
        r = requests.post(url, params)
        return r

    def buy_eth(self, volume, price):
        params = {'side': 'buy',
                  'volume': volume,
                  'market': 'ethuah',
                  'price': price}
        url = self._build_personal_url(self.ORDERS_URL, 'POST', params)
        r = requests.post(url, params)
        return r

    def get_currency_balance(self, currency_name):
        r = requests.get(self._build_personal_url(self.ME_URL, 'GET', {}))
        r.raise_for_status()
        r = json.loads(r.content.decode('utf-8'))
        return [x for x in r['accounts'] if x['currency']==currency_name][0]['balance']

    def get_balance(self):
        r = requests.get(self._build_personal_url(self.ME_URL, 'GET', {}))
        r.raise_for_status()
        r = json.loads(r.content.decode('utf-8'))
        return r['accounts']

    def get_eth_sell_rate(self):
        r = requests.get(self.TICKERS_URL)
        return float(json.loads(r.content.decode())['ticker']['sell'])

    def get_eth_buy_rate(self):
        r = requests.get(self.TICKERS_URL)
        return float(json.loads(r.content.decode())['ticker']['buy'])

    def get_tick(self):
        r = requests.get(self.TICKERS_URL)
        r.raise_for_status()
        return json.loads(r.content.decode())

    def get_active_orders(self, side=None):
        params = {'market': 'ethuah'}
        url = self._build_personal_url(self.ORDERS_URL, 'GET', params)
        r = requests.get(url, params)
        r.raise_for_status()
        r = json.loads(r.content.decode('utf-8'))
        if side:
            r = [x for x in r if x['side'] == side]
        return r

    def get_trades_history(self):
        params = {'market': 'ethuah'}
        url = self._build_personal_url(self.TRADES_URL, 'GET', params)
        r = requests.get(url, params)
        r.raise_for_status()
        r = json.loads(r.content.decode('utf-8'))
        return r
