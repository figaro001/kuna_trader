from datetime import datetime

from flask import Flask
from flask import render_template
from ..kuna_api import KunaApiClient
from ..credentials import API_KEY, API_SECRET

app = Flask(__name__)

@app.template_filter('currency')
def format_currency(value):
    value = float(value)
    return "{:,.2f}".format(value)

@app.template_filter('shortdate')
def shortdate(value):
    try:
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        value = value.strftime('%y-%m-%d %H:%M')
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

    with open('../../logs/trader.log', 'r') as f:
        logs = f.read()

    logs = logs.splitlines()[-10:]

    return render_template('index.html',
                           at=at,
                           eth_tick=eth_tick,
                           actives=actives,
                           orders=orders,
                           logs=logs,
                           deals=deals,
                           )