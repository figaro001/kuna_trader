from celery import Celery, chain
import sqlite3
import os
import pandas as pd
from api_client import KunaApiClient
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DATA_FILE_PATH = os.path.join(BASE_DIR, 'database.db')
CONN = conn = sqlite3.connect(DB_DATA_FILE_PATH)

celery = Celery('tasks', broker='redis://localhost:6379/0')
celery.conf.beat_schedule = {
    'each-15-minutes': {
        'task': 'tasks.tick',
        'schedule': timedelta(seconds=10)  # timedelta(minutes=15)
    },
}


@celery.task()
def process_signal(_):
    # KunaTrader(db_connection=CONN).process_latest_signal()
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
    df.to_sql(name='historical', con=CONN, if_exists='append')


@celery.task()
def tick():
    chain(save_history.s(), process_signal.s())()
