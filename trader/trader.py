
import os
import logging
from time import sleep
import pandas as pd

import kuna_api as api
import strategies


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fhandler = logging.FileHandler('../logs/trader.log')
shandler = logging.StreamHandler()
fhandler.setLevel(logging.INFO)
shandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s  %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
fhandler.setFormatter(formatter)
shandler.setFormatter(formatter)
logger.addHandler(fhandler)
logger.addHandler(shandler)


class KunaTrader(object):

    TRADING_UAH_AMOUNT = 6000
    DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'historical.csv')

    def __init__(self):
        self.load_historical_data()

    def load_historical_data(self):
        if os.path.exists(self.DATA_FILE_PATH):
            self.historical_data = pd.read_csv(self.DATA_FILE_PATH, index_col=0)
        else:
            columns = ['timestamp', 'buy', 'sell', 'low', 'high', 'last', 'vol']
            self.historical_data = pd.DataFrame(columns=columns)

    def save_historical_data(self):
        self.historical_data.to_csv(self.DATA_FILE_PATH)

    def update_historical_datas(self):
        data = api.get_tick()
        pd1 = pd.DataFrame({'timestamp': data['at'],
                            'buy': data['ticker']['buy'],
                            'sell': data['ticker']['sell'],
                            'low': data['ticker']['low'],
                            'high': data['ticker']['high'],
                            'last': data['ticker']['last'],
                            'vol': data['ticker']['vol']}, index=[0])

        self.historical_data = pd.concat([self.historical_data, pd1])
        self.save_historical_data()

    def main_loop(self):

        decision = strategies.RollingMeanStrategy().decide(self.historical_data)

        if decision == 'sell':
            api.sell_eth()
        elif decision == 'buy':
            api.buy_eth()
        elif decision == 'wait':
            pass


    def start_main_loop(self):
        try:
            while True:
                try:
                    self.main_loop()
                except Exception as e:
                    logger.error(e)

                sleep(60*15)

        except KeyboardInterrupt:
            print('Exiting...')


if __name__ == "__main__":
    trader = KunaTrader()
    trader.start_main_loop()
