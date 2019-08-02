from celery import Celery, chain
import sqlite3
import os
import pandas as pd
from api_client import KunaApiClient
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DATA_FILE_PATH = os.path.join(BASE_DIR, 'data', 'historical_data.db')
celery = Celery('tasks', broker='redis://localhost:6379/0')
celery.conf.beat_schedule = {
    'each-15-minutes': {
        'task': 'tasks.tick',
        'schedule': timedelta(minutes=15)
    },
}


@celery.task()
def process_signal(_):
    # KunaTrader(data_url=DATA_URL).process_latest_signal()
    pass


@celery.task
def save_history():
    data = KunaApiClient().get_tick()
    df = pd.DataFrame({'timestamp': datetime.fromtimestamp(int(data['at'])),
                       'buy': float(data['ticker']['buy']),
                       'sell': float(data['ticker']['sell']),
                       'low': float(data['ticker']['low']),
                       'high': float(data['ticker']['high']),
                       'last': float(data['ticker']['last']),
                       'vol': float(data['ticker']['vol'])}, index=[0])
    df = df.set_index('timestamp')
    conn = sqlite3.connect(DB_DATA_FILE_PATH)
    df.to_sql(name='tick', con=conn, if_exists='append')


@celery.task()
def tick():
    chain(save_history.s(), process_signal.s())()
