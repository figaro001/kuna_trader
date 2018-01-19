
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

        signal = strategies.RollingMeanStrategy(1, 32).check_signal()
        logger.info('signal: {}'.format(signal))
        if signal == -1: #sell
            volume = api.get_eth_amount()
            rate = api.get_eth_sell_rate()
            logger.info('SELL received. Selling {} ETH for {} uah'.format(volume, rate))
            api.sell_eth(volume, rate)
        elif signal == 1: # buy
            rate = api.get_eth_buy_rate()
            volume = rate / self.TRADING_UAH_AMOUNT
            logger.info('BUY signal. Buying {} ETH for {} uah'.format(volume, rate))
            api.buy_eth(rate, volume)

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
