
import hashlib
import hmac
import json
import time
from collections import OrderedDict
from urllib.parse import urlencode

import requests

from .credentials import API_KEY, API_SECRET

API_DOMAIN = 'https://kuna.io/api/v2'
TICKERS_URL = '{}/tickers/ethuah'.format(API_DOMAIN)
ORDERS_URL =  '{}/orders'.format(API_DOMAIN)
ME_URL = '{}/members/me'.format(API_DOMAIN)


def _build_personal_url(url, method, params):
    tonce = int(round(time.time() * 1000))
    params['tonce'] = tonce
    params['access_key'] = API_KEY
    params = OrderedDict(sorted(params.items(), key=lambda t: t[0]))
    msg = '{0}|{1}|{2}'.format(method.upper(), url.replace('https://kuna.io', ''), urlencode(params))
    signature = hmac.new(API_SECRET.encode('utf-8'), msg=msg.encode('utf-8'), digestmod=hashlib.sha256)
    signature = signature.hexdigest()
    return '{0}?access_key={1}&tonce={2}&signature={3}'.format(url, API_KEY, tonce, signature)


def sell_eth(volume, price):
    #logger.info('Selling {} ETH for {} UAH to get {} UAH'.format(volume, price, volume * price))
    params = {'side': 'sell',
              'volume': volume,
              'market': 'ethuah',
              'price': price}
    url = _build_personal_url(ORDERS_URL, 'POST', params)
    r = requests.post(url, params)
    r.raise_for_status()
    return r.status_code


def buy_eth(volume, price):

    params = {'side': 'buy',
              'volume': volume,
              'market': 'ethuah',
              'price': price}
    url = _build_personal_url(ORDERS_URL, 'POST', params)
    r = requests.post(url, params)
    r.raise_for_status()
    return r.status_code


def get_eth_amount():
    r = requests.get(_build_personal_url(ME_URL, 'GET', {}))
    r.raise_for_status()
    r = json.loads(r.content.decode('utf-8'))
    return float([x for x in r['accounts'] if x['currency']=='eth'][0]['balance'])


def get_eth_sell_rate():
    r = requests.get(TICKERS_URL)
    return float(json.loads(r.content.decode())['ticker']['sell'])


def get_eth_buy_rate():
    r = requests.get(TICKERS_URL)
    return float(json.loads(r.content.decode())['ticker']['buy'])


def get_tick():
    r = requests.get(TICKERS_URL)
    r.raise_for_status()
    return json.loads(r.content.decode())

def get_active_orders(side):
    params = {'market': 'ethuah'}
    url = _build_personal_url(ORDERS_URL, 'GET', params)
    r = requests.get(url, params)
    r.raise_for_status()
    r = json.loads(r.content.decode('utf-8'))
    return [x for x in r if x['side'] == side]
