
from time import sleep

import kuna_api as api
import strategies

from log import logger


class KunaTrader(object):

    TRADING_UAH_AMOUNT = 6000

    def sell(self):
        orders = api.get_active_orders()
        available_volume = api.get_currency_balance('eth')[:8]
        rate = api.get_eth_sell_rate()
        err = None

        logger.info('Sell initiated. Volume:{} Price:{}'.format(available_volume, rate))

        if orders:
            err = 'There are active orders. {}'.format(orders)
        if float(available_volume) < 0.01:
            err = 'To low eth amount. {}'.format(available_volume)
        if err:
            logger.info('Sell canceled. Error: {}'.format(err))
            return

        result = api.sell_eth(available_volume, rate)

        if result.status_code == 201:
            logger.info('Sell order placed succesfully')
        else:
            logger.error('Failed. Status Code: {}'.format(result.status_code))
            logger.error('{}'.format(result.content))

    def buy(self):
        available_cash = api.get_currency_balance('uah')[:8]
        orders = api.get_active_orders()
        rate = api.get_eth_buy_rate()
        volume = str(float(self.TRADING_UAH_AMOUNT) / rate)[:8]

        logger.info('Buy initiated. Amount: {} Rate: {} Cash Spent: {}'.format(volume, rate, float(volume)*rate))
        err = None
        if float(available_cash) < float(volume) * rate:
            err = 'Not enough cash for deal. Needed: {}  Actual:{}'.format(rate*float(volume), available_cash)
        if orders:
            err = 'There are active orders. {}'.format(orders)
        if err:
            logger.info('Buy canceled. Error: {}'.format(err))
            return

        result = api.buy_eth(volume, rate)

        if result.status_code == 201:
            logger.info('Buy order placed succesfully')
        else:
            logger.error('Failed. Status Code: {}'.format(result.status_code))
            logger.error('{}'.format(result.content))

    def process_latest_signal(self):

        strategy = strategies.RollingMeanStrategy(93, 104)
        signals = strategy.fill_signals()
        signal = signals.tail(1).signals.item()

        logger.info('signal: {}'.format(signal))

        if signal == -1:  # sell
            self.sell()

        elif signal == 1:  # buy
            self.buy()


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
