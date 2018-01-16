
import logging
import os
from time import sleep

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

    def main_loop(self):

        decision = strategies.RollingMeanStrategy(8, 10).decide()

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
