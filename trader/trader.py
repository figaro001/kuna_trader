import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from api_client import KunaApiClient  # TODO: Fix

from . import strategies

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

engine = create_engine('sqlite:///{}'.format(DB_PATH), echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Log(Base):
    __tablename__ = 'journal'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    signal = Column(Integer)
    volume = Column(Float)
    rate = Column(Float)
    status = Column(String)
    comment = Column(String)

    def __repr__(self):
        return "{} at {}".format(self.signal, self.date)


Base.metadata.create_all(engine)


class KunaTrader(object):
    TRADING_UAH_AMOUNT = 6000
    STOP_LOSS = 300

    def __init__(self, db_connection):
        self.api_client = KunaApiClient()
        self.conn = db_connection
        self.session = Session()
        self.log = Log(date=datetime.now())

    def sell(self):
        orders = self.api_client.get_active_orders()
        available_volume = self.api_client.get_currency_balance('eth')[:8]
        rate = self.api_client.get_eth_sell_rate()

        self.log.volume = available_volume
        self.log.rate = rate
        self.log.side = 'sell'

        if orders:
            self.log.status = 'error'
            self.log.comment = 'There are active orders. {}'.format(orders)
            return

        if float(available_volume) < 0.01:
            self.log.status = 'error'
            self.log.comment = 'Not enough ETH: {}'.format(available_volume)
            return

        result = self.api_client.sell_eth(available_volume, rate)

        if result.status_code == 201:
            self.log.status = 'success'
        else:
            self.log.status = 'error'
            self.log.comment = 'Failed. Status Code: {}. Error: {}'.format(result.status_code, result.content)

        self.session.add(self.log)
        self.session.commit()

    def buy(self):
        available_cash = self.api_client.get_currency_balance('uah')[:8]
        orders = self.api_client.get_active_orders()
        rate = self.api_client.get_eth_buy_rate()
        volume = str(float(self.TRADING_UAH_AMOUNT) / rate)[:8]

        self.log.volume = volume
        self.log.rate = rate
        self.log.side = 'buy'

        if float(available_cash) < float(volume) * rate:
            self.log.status = 'error'
            self.log.comment = 'Not enough UAH. Needed:{}  Actual:{}'.format(rate * float(volume), available_cash)
            return
        if orders:
            self.log.status = 'error'
            self.log.comment = 'There are active orders. {}'.format(orders)
            return

        result = self.api_client.buy_eth(volume, rate)

        if result.status_code == 201:
            self.log.status = 'success'
        else:
            self.log.status = 'error'
            self.log.comment = 'Failed. Status Code: {}. Error: {}'.format(result.status_code, result.content)

        self.session.add(self.log)
        self.session.commit()

    def stop_loss(self):
        available_volume = float(self.api_client.get_currency_balance('eth'))

        if available_volume > 0.001:
            rate = self.api_client.get_eth_sell_rate()
            potential_income = float(self.api_client.get_currency_balance('eth')) * rate

            deals = self.api_client.get_trades_history()
            buy_deals = list(filter(lambda x: x['side'] == 'bid', deals))
            latest_spending = float(buy_deals[0]['funds'])

            if (latest_spending - potential_income) < self.STOP_LOSS:
                # msg = 'STOP LOSS triggered. rate: {} latest_spending: {} potential_income: {}'
                # msg = msg.format(rate, latest_spending, potential_income)
                self.sell()

    def process_latest_signal(self):

        strategy = strategies.RollingMeanStrategy(self.conn, 93, 104)
        signals = strategy.fill_signals()
        signal = signals.tail(1).signals.item()
        # self.stop_loss()

        if signal == -1:  # sell
            self.sell()

        elif signal == 1:  # buy
            self.buy()
