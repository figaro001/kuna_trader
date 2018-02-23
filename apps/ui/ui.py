import json
from datetime import datetime
import sys
sys.path.append('..')
from flask import Flask, render_template
import service
from service.credentials import API_KEY, API_SECRET
from service.kuna_api import KunaApiClient
from trader.strategies import RemoteDataAccessMixin

app = Flask(__name__)

@app.template_filter('currency')
def format_currency(value):
    value = float(value)
    return "{:,.2f}".format(value)

@app.template_filter('shortdate')
def shortdate(value):
    try:
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        value = value.strftime('%d-%m-%y %H:%M')
    except:
        pass
    return value


@app.route('/')
def hello_world():
    client = KunaApiClient(API_KEY, API_SECRET)
    eth_tick = client.get_tick()
    actives = client.get_balance()
    at = datetime.fromtimestamp(eth_tick['at'])
    orders = client.get_active_orders()
    deals = client.get_trades_history()
    deals = [x for x in deals if x['market']=='ethuah'][:10]

    with open('../trader/trader.log', 'r') as f:
        logs = f.read()

    logs = logs.splitlines()[-10:]
    data = RemoteDataAccessMixin().get_data().to_json()
    data = json.loads(data)
    data = [ [int(x[0]), x[1] ] for x in data['sell'].items() ]

    return render_template('index.html',
                           at=at,
                           eth_tick=eth_tick,
                           actives=actives,
                           orders=orders,
                           logs=logs,
                           deals=deals,
                           data=data,
                           )
