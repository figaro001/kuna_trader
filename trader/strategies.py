import json
import random
from operator import add, sub

import requests

import numpy as np
import pandas as pd


class DataAccessMixin(object):

    DATA_URL = 'http://0.0.0.0:8081'

    def get_data(self):
        datas = pd.read_json(self.DATA_URL, orient='index')
        return datas


class RollingMeanStrategy(DataAccessMixin):

    def __init__(self, short_window=8, long_window=10):
        self.short_window = short_window
        self.long_window = long_window

    def decide(self):
        datas = self.get_data()
        datas['position'] = 0.0
        datas['short_mavg'] = datas['sell'].rolling(window=self.short_window, min_periods=1, center=False).mean()
        datas['long_mavg'] = datas['sell'].rolling(window=self.long_window, min_periods=1, center=False).mean()
        datas['position'][self.short_window:] = np.where(datas['short_mavg'][self.short_window:] > datas['long_mavg'][self.short_window:], 1.0, 0.0)
        datas['signals'] = datas['position'].diff()
        signal = datas.tail(1).signals.item()

        if signal == 0:
            return 'wait'
        elif signal == 1:
            return 'buy'
        elif signal == -1:
            return 'sell'

    def backtest(self):

        datas = self.get_data()

        signals = pd.DataFrame(index=datas.index)
        signals['short_mavg'] = datas['sell'].rolling(window=self.short_window, min_periods=1, center=False).mean()
        signals['long_mavg'] = datas['sell'].rolling(window=self.long_window, min_periods=1, center=False).mean()
        signals['signal'] = 0.0
        signals['signal'][self.short_window:] = np.where(
            signals['short_mavg'][self.short_window:] > signals['long_mavg'][self.short_window:], 1.0, 0.0
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

        return portfolio


class Optimizer(DataAccessMixin):

    def __init__(self):
        data = self.get_data()
        self.data_length = len(data)
        self.known_nodes = []

    def get_random_node(self):
        short_window = random.randint(1, self.data_length)
        long_window = random.randint(short_window+1, self.data_length+1)
        node = {'short_window':short_window,
                'long_window': long_window,
                'last_total': 0}
        if node not in self.known_nodes:
            return node
        else:
            return self.get_random_node()

    def mutate_value(self, incoming_value, value_type, short_value=None):
        operation = random.choice([add, sub])
        value = operation(incoming_value, random.randint(0, 5))

        if value_type == 'short':
            if 1<=value<=self.data_length:
                return value
            else:
                return self.mutate_value(incoming_value, value_type)

        if value_type == 'long':
            if short_value < value <= self.data_length:
                return value
            else:
                return self.mutate_value(incoming_value, 'long', short_value)

    def mutate_node(self, node):
        new_node = {}
        new_node['short_window'] = self.mutate_value(node['short_window'], 'short')
        new_node['long_window'] = self.mutate_value(node['long_window'], 'long', node['short_window'])
        new_node['last_total'] = 0
        return new_node

    def optimize_windows(self):

        population_count = 100
        generation_cycles = 100
        nodes = [self.get_random_node() for x in range(population_count)]

        for generation in range(generation_cycles):
            for node in nodes:
                strategy = RollingMeanStrategy(short_window=node['short_window'], long_window=node['long_window'])
                portfolio = strategy.backtest()
                node['last_total'] = portfolio.tail(1).total.item()
            nodes = sorted(nodes, key=lambda x: x['last_total'], reverse=True)

            nodes =   [x for x in nodes[:35]]
            mutants = [self.mutate_node(x) for x in nodes[:] ]
            randoms = [self.get_random_node() for x in range(30)]
            nodes = nodes + mutants + randoms

            print(nodes[0])
