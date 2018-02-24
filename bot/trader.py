import logging

from . import strategies
from kuna_api import KunaApiClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fhandler = logging.FileHandler('trader.log')
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
    STOP_LOSS = 300

    def __init__(self, data_url):
        self.api_client = KunaApiClient()
        self.data_url = data_url

    def sell(self):
        orders = self.api_client.get_active_orders()
        available_volume = self.api_client.get_currency_balance('eth')[:8]
        rate = self.api_client.get_eth_sell_rate()
        err = None

        logger.info('Sell initiated. Volume:{} Price:{}'.format(available_volume, rate))

        if orders:
            err = 'There are active orders. {}'.format(orders)
        if float(available_volume) < 0.01:
            err = 'To low eth amount. {}'.format(available_volume)
        if err:
            logger.info('Sell canceled. Error: {}'.format(err))
            return

        result = self.api_client.sell_eth(available_volume, rate)

        if result.status_code == 201:
            logger.info('Sell order placed succesfully')
        else:
            logger.error('Failed. Status Code: {}'.format(result.status_code))
            logger.error('{}'.format(result.content))

    def buy(self):
        available_cash = self.api_client.get_currency_balance('uah')[:8]
        orders = self.api_client.get_active_orders()
        rate = self.api_client.get_eth_buy_rate()
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

        result = self.api_client.buy_eth(volume, rate)

        if result.status_code == 201:
            logger.info('Buy order placed succesfully')
        else:
            logger.error('Failed. Status Code: {}'.format(result.status_code))
            logger.error('{}'.format(result.content))

    def stop_loss(self):
        available_volume = float(self.api_client.get_currency_balance('eth'))

        if available_volume > 0.001:
            rate = self.api_client.get_eth_sell_rate()
            potential_income = float(self.api_client.get_currency_balance('eth')) * rate

            deals = self.api_client.get_trades_history()
            buy_deals = list(filter(lambda x: x['side']=='bid', deals))
            latest_spending = buy_deals[0]['fund']

            if (latest_spending - potential_income) < self.STOP_LOSS:
                msg = 'STOP LOSS triggered. rate: {} latest_spending: {} potential_income: {}'
                msg = msg.format(rate, latest_spending, potential_income)
                logger.info(msg)
                self.sell()

    def process_latest_signal(self):

        strategy = strategies.RollingMeanStrategy(self.data_url, 93, 104)
        signals = strategy.fill_signals()
        signal = signals.tail(1).signals.item()

        logger.info('signal: {}'.format(signal))

        self.stop_loss()

        if signal == -1:  # sell
            self.sell()

        elif signal == 1:  # buy
            self.buy()
