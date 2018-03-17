import os
import sqlite3
from datetime import datetime

from celery import Celery, chain
from celery.schedules import crontab
from flask import Flask, Response, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from bot.trader import JOURNAL_DB_PATH, KunaTrader, Log
from kuna_api import KunaApiClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DATA_FILE_PATH = os.path.join(BASE_DIR, 'data', 'historical.csv')
DB_DATA_FILE_PATH = os.path.join(BASE_DIR, 'data', 'historical.db')
#DATA_URL = 'http://192.168.0.105:5000/data'
DATA_URL = 'http://localhost:5000/data'
LOG_FILE_PATH = os.path.join(BASE_DIR, 'logs', 'celery_supervisor_err.log')

engine = create_engine('sqlite:///{}'.format(JOURNAL_DB_PATH), echo=False)
Session = sessionmaker(bind=engine)

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://myuser:mypassword@localhost:5672/myvhost'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
celery.conf.beat_schedule = {
    'each-15-minutes': {
        'task': 'main.tick',
        'schedule': crontab(minute='*/15'),
    },
}

@app.template_filter('currency')
def format_currency(value):
    value = float(value)
    return "{:,.2f}".format(value)

@app.template_filter('shortdate')
def shortdate(value):
    try:
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        value = value.strftime('%d/%m %H:%M')
    except:
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S+02:00')
        value = value.strftime('%d/%m %H:%M')
        pass
    return value

@app.template_filter('logdate')
def logdate(value):
    return value.strftime('%d/%m %H:%M')


@app.route('/', methods=['GET', 'POST'])
def main():
    client = KunaApiClient()
    if request.method == 'GET':
        eth_tick = client.get_tick()
        actives = client.get_balance()
        at = datetime.fromtimestamp(eth_tick['at'])
        orders = client.get_active_orders()
        deals = client.get_trades_history()
        deals = [x for x in deals if x['market']=='ethuah'][:5]

        session = Session()
        logs = []
        for log in session.query(Log).order_by(Log.date.desc())[:5]:
            logs.append({'date':log.date,
                         'side': log.side,
                         'status': log.status,
                         'comment': log.comment,
                         'volume': log.volume,
                         'rate': log.rate,
                        })

        data = pd.read_csv(CSV_DATA_FILE_PATH, index_col=0)
        data['short_mavg'] = data['sell'].rolling(window=93, min_periods=1, center=False).mean()
        data['long_mavg'] = data['sell'].rolling(window=104, min_periods=1, center=False).mean()
        data.index = pd.to_datetime(data.index)
        data_long =  [[x[0].timestamp()*1000, round(x[1],0)] for x in data['long_mavg'].items()]
        data_short = [[x[0].timestamp()*1000, round(x[1],0)] for x in data['short_mavg'].items()]
        data =       [[x[0].timestamp()*1000, round(x[1],0)] for x in data['sell'].items() ]

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
        return redirect(url_for('main'))


@app.route('/data')
def historical():
    data = pd.read_csv(CSV_DATA_FILE_PATH, index_col=0)
    data = data.to_json(orient='index')
    return Response(response=data, status=200, mimetype='application/json')


@celery.task()
def process_signals(_):
    pass
    #KunaTrader(data_url=DATA_URL).process_latest_signal()


@celery.task
def save_history():
    if not os.path.exists(CSV_DATA_FILE_PATH):
        columns = ['timestamp', 'buy', 'sell', 'low', 'high', 'last', 'vol']
        historical_data = pd.DataFrame(columns=columns)
        historical_data = historical_data.set_index('timestamp')
        historical_data.to_csv(CSV_DATA_FILE_PATH)

    data = KunaApiClient().get_tick()
    df = pd.DataFrame({'timestamp': datetime.fromtimestamp(int(data['at'])),
                       'buy': float(data['ticker']['buy']),
                       'sell': float(data['ticker']['sell']),
                       'low': float(data['ticker']['low']),
                       'high': float(data['ticker']['high']),
                       'last': float(data['ticker']['last']),
                       'vol': float(data['ticker']['vol'])}, index=[0])
    df = df.set_index('timestamp')
    df.to_csv(CSV_DATA_FILE_PATH, mode='a', header=False)

    conn = sqlite3.connect(DB_DATA_FILE_PATH)
    df.to_sql(name='signals', con=conn, if_exists='append')


@celery.task()
def tick():
    chain(save_history.s(), process_signals.s())()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
