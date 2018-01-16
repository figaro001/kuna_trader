import pandas as pd
import numpy as np

class RollingMeanStrategy(object):

    SHORT_WINDOW = 4
    LONG_WINDOW = 40

    def decide(self, datas):
        datas['timestamp'] = pd.to_datetime(datas['timestamp'], unit='s')
        datas = datas.set_index('timestamp')

        datas['position'] = 0.0
        datas['short_mavg'] = datas['sell'].rolling(window=self.SHORT_WINDOW, min_periods=1, center=False).mean()
        datas['long_mavg'] = datas['sell'].rolling(window=self.LONG_WINDOW, min_periods=1, center=False).mean()
        datas['position'][self.SHORT_WINDOW:] = np.where(datas['short_mavg'][self.SHORT_WINDOW:] > datas['long_mavg'][self.SHORT_WINDOW:], 1.0, 0.0)
        datas['signals'] = datas['position'].diff()
        signal = datas.tail(1).signals.item()

        if signal == 0:
            return 'wait'
        elif signal == 1:
            return 'buy'
        elif signal == -1:
            return 'sell'

    def backtest(self, datas):

        datas['timestamp'] = pd.to_datetime(datas['timestamp'], unit='s')
        datas = datas.set_index('timestamp')

        signals = pd.DataFrame(index=datas.index)

        signals['short_mavg'] = datas['sell'].rolling(window=self.SHORT_WINDOW, min_periods=1, center=False).mean()
        signals['long_mavg'] = datas['sell'].rolling(window=self.LONG_WINDOW, min_periods=1, center=False).mean()
        signals['signal'] = 0.0
        signals['signal'][self.SHORT_WINDOW:] = np.where(
            signals['short_mavg'][self.SHORT_WINDOW:] > signals['long_mavg'][self.SHORT_WINDOW:], 1.0, 0.0
        )
        signals['positions'] = signals['signal'].diff()


        initial_capital = float(6000)
        positions = pd.DataFrame(index=signals.index).fillna(0.0)
        positions['ETH'] = 0.15 * signals['signal']

        portfolio = positions.multiply(datas['sell'], axis=0)
        pos_diff = positions.diff()
        portfolio['holdings'] = (positions.multiply(datas['sell'], axis=0)).sum(axis=1)
        portfolio['cash'] = initial_capital - (pos_diff.multiply(datas['sell'], axis=0)).sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()
        print(portfolio)




