import os
from datetime import datetime
import sqlite3

import pandas as pd
from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from trader.trader import KunaTrader, Log
from kuna_client.client import KunaApiClient
from credentials import API_KEY, API_SECRET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORICAL_DB_PATH = os.path.join(BASE_DIR, 'database.db')
JOURNAL_DB_PATH = os.path.join(BASE_DIR, 'database.db')
LOG_FILE_PATH = os.path.join(BASE_DIR, 'logs', 'celery_supervisor_err.log')

engine = create_engine('sqlite:///{}'.format(JOURNAL_DB_PATH), echo=False)
Session = sessionmaker(bind=engine)

app = Flask(__name__, static_url_path='')


@app.route('/web/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@app.route('/', methods=['GET', 'POST'])
def main():
    client = KunaApiClient(API_KEY, API_SECRET)
    if request.method == 'GET':
        eth_tick = client.get_tick()
        actives = client.get_balance()
        at = datetime.fromtimestamp(eth_tick['at'])
        orders = client.get_active_orders()
        deals = client.get_trades_history()
        deals = [x for x in deals if x['market'] == 'ethuah'][:5]

        session = Session()
        logs = []
        for log in session.query(Log).order_by(Log.date.desc())[:5]:
            logs.append({'date': log.date,
                         'side': log.side,
                         'status': log.status,
                         'comment': log.comment,
                         'volume': log.volume,
                         'rate': log.rate,
                         })

        cnx = sqlite3.connect('database.db')
        data = pd.read_sql_query("SELECT * FROM historical", cnx)
        data['short_mavg'] = data['sell'].rolling(window=93, min_periods=1, center=False).mean()
        data['long_mavg'] = data['sell'].rolling(window=104, min_periods=1, center=False).mean()
        data.index = pd.to_datetime(data.index)
        data_long = [[x[0].timestamp() * 1000, round(x[1], 0)] for x in data['long_mavg'].items() if not pd.isnull(x[0])]
        data_short = [[x[0].timestamp() * 1000, round(x[1], 0)] for x in data['short_mavg'].items() if not pd.isnull(x[0])]
        data = [[x[0].timestamp() * 1000, round(x[1], 0)] for x in data['sell'].items() if not pd.isnull(x[0])]

        return render_template('index.html',
                               at=at,
                               eth_tick=eth_tick,
                               actives=actives,
                               orders=orders,
                               logs=logs,
                               deals=deals,
                               data=data,
                               data_s=data_short,
                               data_l=data_long,
                               )
    if request.method == 'POST':
        bid = request.form['action']
        if bid == 'sell':
            KunaTrader(DATA_URL).sell()
        if bid == 'buy':
            KunaTrader(DATA_URL).buy()
        if bid == 'cancel-order':
            client.cancel_order(request.form['order-id'])
        return redirect(url_for('main'))
