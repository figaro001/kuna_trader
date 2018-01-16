import os
from time import sleep

import kuna_api as api
import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer


class RequestHandler(BaseHTTPRequestHandler):

    DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'historical.csv')

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        data = pd.read_csv(self.DATA_FILE_PATH, index_col=0)
        data = data.set_index('timestamp')
        data = data.to_json(orient='index')
        self.wfile.write(bytes(data, "utf8"))
        return


class KunaChronicler(object):

    DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'historical.csv')

    def __init__(self):

        if os.path.exists(self.DATA_FILE_PATH):
            self.historical_data = pd.read_csv(self.DATA_FILE_PATH, index_col=0)
        else:
            columns = ['timestamp', 'buy', 'sell', 'low', 'high', 'last', 'vol']
            self.historical_data = pd.DataFrame(columns=columns)

    def log_data(self):
        data = api.get_tick()
        pd1 = pd.DataFrame({'timestamp': data['at'],
                            'buy': data['ticker']['buy'],
                            'sell': data['ticker']['sell'],
                            'low': data['ticker']['low'],
                            'high': data['ticker']['high'],
                            'last': data['ticker']['last'],
                            'vol': data['ticker']['vol']}, index=[0])
        self.historical_data = pd.concat([self.historical_data, pd1])
        self.historical_data.to_csv(self.DATA_FILE_PATH)

    def run_server(self):
        server_address = ('0.0.0.0', 8081)
        httpd = HTTPServer(server_address, RequestHandler)
        httpd.serve_forever()

    def start_main_loop(self):
        try:
            self.run_server()
            while True:
                try:
                    self.log_data()
                except Exception as e:
                    print(e)

                sleep(60 * 15)
        except KeyboardInterrupt:
            print('Exiting...')


if __name__ == "__main__":
    chronicler = KunaChronicler()
    chronicler.start_main_loop()
