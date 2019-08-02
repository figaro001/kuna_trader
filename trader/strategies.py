import numpy as np
import pandas as pd


class RollingMeanStrategy(object):

    def __init__(self, data_url, short_window=8, long_window=10):
        self.short_window = short_window
        self.long_window = long_window
        self.data_url = data_url

    def get_data(self):
        return pd.read_json(self.data_url, orient='index')

    def fill_signals(self):
        data = self.get_data()
        data['position'] = 0.0
        data['short_mavg'] = data['sell'].rolling(window=self.short_window, min_periods=1, center=False).mean()
        data['long_mavg'] = data['sell'].rolling(window=self.long_window, min_periods=1, center=False).mean()
        data['position'][self.short_window:] = np.where(
            data['short_mavg'][self.short_window:] > data['long_mavg'][self.short_window:], 1.0, 0.0)
        data['signals'] = data['position'].diff()
        return data

    def backtest(self, data):
        signals = pd.DataFrame(index=data.index)
        signals['short_mavg'] = data['sell'].rolling(window=self.short_window, min_periods=1, center=False).mean()
        signals['long_mavg'] = data['sell'].rolling(window=self.long_window, min_periods=1, center=False).mean()
        signals['signal'] = 0.0
        signals['signal'][self.short_window:] = np.where(
            signals['short_mavg'][self.short_window:] > signals['long_mavg'][self.short_window:], 1.0, 0.0
        )
        signals['positions'] = signals['signal'].diff()

        initial_capital = float(6000)
        positions = pd.DataFrame(index=signals.index).fillna(0.0)

        positions['ETH'] = 0.15 * signals['signal']

        portfolio = positions.multiply(data['sell'], axis=0)
        pos_diff = positions.diff()
        portfolio['holdings'] = (positions.multiply(data['sell'], axis=0)).sum(axis=1)
        portfolio['cash'] = initial_capital - (pos_diff.multiply(data['sell'], axis=0)).sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()

        return portfolio
