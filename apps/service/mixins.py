import os

import pandas as pd

import sys
sys.path.append('..')

from service.kuna_api import KunaApiClient


class RemoteDataAccessMixin(object):

    DATA_URL = 'http://192.168.0.105:8081'

    def get_data(self):
        datas = pd.read_json(self.DATA_URL, orient='index')
        return datas


class LocalDataAccessMixin(object):
    DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'historical.csv')

    def __init__(self):

        self.api_client = KunaApiClient()

        if os.path.exists(self.DATA_FILE_PATH):
            self.historical_data = pd.read_csv(self.DATA_FILE_PATH, index_col=0)
        else:
            columns = ['timestamp', 'buy', 'sell', 'low', 'high', 'last', 'vol']
            self.historical_data = pd.DataFrame(columns=columns)


class ApiAccessMixin(object):

    def __init__(self):
        self.api_client = KunaApiClient()
