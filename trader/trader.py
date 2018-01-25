
from time import sleep

import kuna_api as api
import strategies

from log import logger


class KunaTrader(object):

    TRADING_UAH_AMOUNT = 6000

    def process_latest_signal(self):

        strategy = strategies.RollingMeanStrategy(1, 32)
        signals = strategy.fill_signals()
        signal = signals.tail(1).signals.item()

        logger.info('signal: {}'.format(signal))

        if signal == -1:  # sell
            volume = api.get_eth_amount()[:8]
            rate = api.get_eth_sell_rate()
            api.sell_eth(volume, rate)

        elif signal == 1:  # buy
            rate = api.get_eth_buy_rate()
            volume = str(float(self.TRADING_UAH_AMOUNT) / rate)[:8]
            logger.info('Buying. Amount: {} Rate: {} Cash Spent: {}'.format(volume, rate, self.TRADING_UAH_AMOUNT))
            api.buy_eth(volume, rate)

    def start_main_loop(self):
        while True:
            try:
                self.process_latest_signal()
            except Exception as e:
                logger.error(e)

            sleep(60*15)



if __name__ == "__main__":
    trader = KunaTrader()
    trader.start_main_loop()
