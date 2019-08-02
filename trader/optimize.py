import random
from operator import add, sub

from .strategies import RollingMeanStrategy


class Optimizer(object):

    def __init__(self):
        data = self.get_data()
        self.data_length = len(data)
        self.known_nodes = []

    def get_random_node(self):
        short_window = random.randint(1, self.data_length)
        long_window = random.randint(short_window + 1, self.data_length + 1)
        node = {'short_window': short_window,
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
            if 1 <= value <= self.data_length:
                return value
            else:
                return self.mutate_value(incoming_value, value_type)

        if value_type == 'long':
            if short_value < value <= self.data_length:
                return value
            else:
                return self.mutate_value(incoming_value, 'long', short_value)

    def mutate_node(self, node):
        return {'short_window': self.mutate_value(node['short_window'], 'short'),
                'long_window': self.mutate_value(node['long_window'], 'long', node['short_window']),
                'last_total': 0}

    def optimize_windows(self):

        population_count = 100
        generation_cycles = 100
        nodes = [self.get_random_node() for _ in range(population_count)]

        data = self.get_data()

        for generation in range(generation_cycles):
            for node in nodes:
                strategy = RollingMeanStrategy(short_window=node['short_window'], long_window=node['long_window'])
                portfolio = strategy.backtest(data=data)
                node['last_total'] = portfolio.tail(1).total.item()
            nodes = sorted(nodes, key=lambda x: x['last_total'], reverse=True)

            nodes = [x for x in nodes[:35]]
            mutants = [self.mutate_node(x) for x in nodes[:]]
            randoms = [self.get_random_node() for x in range(30)]
            nodes = nodes + mutants + randoms

            print(nodes[0])
