from datetime import datetime

from flask import Flask
from flask import render_template
from ..kuna_api import KunaApiClient
from ..credentials import API_KEY, API_SECRET

app = Flask(__name__)

@app.route('/')
def hello_world():
    client = KunaApiClient(API_KEY, API_SECRET)
    eth_tick = client.get_tick()
    actives = client.get_balance()
    at = datetime.fromtimestamp(eth_tick['at'])
    orders = client.get_active_orders()
    with open('../../logs/trader.log', 'r') as f:
        logs = f.read()
    logs = '\n'.join(logs.splitlines()[-5:])

    return render_template('index.html',
                           at=at,
                           eth_tick=eth_tick,
                           actives=actives,
                           orders=orders,
                           logs=logs,
                           )