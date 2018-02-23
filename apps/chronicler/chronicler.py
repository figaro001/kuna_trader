import threading
from time import sleep
import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer

import sys
sys.path.append('..')
from service import mixins


class RequestHandler(BaseHTTPRequestHandler, mixins.LocalDataAccessMixin):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        data = pd.read_csv(self.DATA_FILE_PATH, index_col=0)
        data = data.set_index('timestamp')
        data = data.to_json(orient='index')
        self.wfile.write(bytes(data, "utf8"))
        return


class KunaChronicler(mixins.LocalDataAccessMixin, mixins.ApiAccessMixin):

    def log_data(self):
        data = self.api_client.get_tick()
        df = pd.DataFrame({'timestamp': data['at'],
                           'buy': data['ticker']['buy'],
                           'sell': data['ticker']['sell'],
                           'low': data['ticker']['low'],
                           'high': data['ticker']['high'],
                           'last': data['ticker']['last'],
                           'vol': data['ticker']['vol']}, index=[0])
        self.historical_data = pd.concat([self.historical_data, df])
        self.historical_data.to_csv(self.DATA_FILE_PATH)

    def run_server(self):
        server_address = ('0.0.0.0', 8081)
        httpd = HTTPServer(server_address, RequestHandler)
        httpd.serve_forever()

    def start_chronicler(self):
        while True:
            try:
                self.log_data()
            except Exception:
                print('exception')

            sleep(60*15)


if __name__ == "__main__":
    chronicler = KunaChronicler()
    thread1 = threading.Thread(target=chronicler.run_server).start()
    thread2 = threading.Thread(target=chronicler.start_chronicler).start()
