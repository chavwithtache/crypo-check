import gdax
import json
import cryptolib
import urllib.request
import collections
import logging
import os

logger = logging.getLogger('crypto_toddlerTrading')
hdlr = logging.FileHandler('../logs/crypto_toddler_trading.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class ToddlerTrading(object):
    def __init__(self):
        cfg = cryptolib.Config()
        api_config = cfg.api_config()

        self.gdax_config = api_config['gdax_write']
        self.reconnect_client()
        self.reload_orders()

        self.Pair = collections.namedtuple('Pair', 'market size spread')

        self.trade_pairs = []
        self.counter = 0

    def reconnect_client(self):
        self.gdax_auth_client = gdax.AuthenticatedClient(self.gdax_config['api_key'], self.gdax_config['api_secret'], self.gdax_config['passphrase'])

    def reload_orders(self):
        self.orders = self.gdax_auth_client.get_orders()

    def add_pair(self, market, size, spread):
        self.trade_pairs.append(self.Pair(market=market, size=size, spread=spread))


    def check_products(self):
        try:
            self.reload_orders()
            for trade_pair in self.trade_pairs:
                self.check_product(trade_pair)
        except:
            print('some error...')
            logger.error('some error...')


    def do_trades(self, trade_pair, mid_price):

        # do trades
        sell_price = round(mid_price + trade_pair.spread / 2, 2)
        self.do_trade(trade_pair, 'sell', sell_price)

        buy_price = round(mid_price - trade_pair.spread / 2, 2)
        self.do_trade(trade_pair, 'buy', buy_price)



    def do_trade(self, trade_pair, side, price):
        market = trade_pair.market
        size = trade_pair.size

        print('{} {} {} @ {}'.format(side, size, market, price))
        if side == 'sell':
            result = self.gdax_auth_client.sell(product_id=market, type='limit', size=size, price=price)
        else:
            result = self.gdax_auth_client.buy(product_id=market, type='limit', size=size, price=price)

        logger.info(result)
        with open('../data/toddler_trading/{}/{}'.format(market, result['id']), 'w'):
            pass

    def check_product(self, trade_pair):
        market = trade_pair.market

        active_ids = [order['id'] for order in self.orders[0]]
        orders_left = 0
        for active_id in os.listdir('../data/toddler_trading/' + market):
            try:
                active_ids.index(active_id)
                # order still open.
                orders_left += 1
            except ValueError:
                # not in the list so delete the file. this means that has traded since last run
                os.remove('../data/toddler_trading/ETH-EUR/' + active_id)

        if orders_left == 0:
            print('{}: orders all hit - do another pair'.format(market))
            url = 'https://api.gdax.com/products/' + market + '/book?level=1'
            orderbook = json.loads(urllib.request.urlopen(url).read())
            mid = (float(orderbook['bids'][0][0]) + float(orderbook['asks'][0][0])) / 2

            self.do_trades(trade_pair,mid)

        else:
            self.counter += 1
            print('{} {}: waiting for orders to hit. {} order(s) outstanding'.format(self.counter, market, orders_left))



test = ToddlerTrading()
test.add_pair('ETH-EUR', 2.4, 2.0)
test.add_pair('LTC-EUR', 0.55, 2.0)
test.add_pair('BTC-EUR', 0.1, 10.0)

logger.info('started')
while True:
    test.check_products()



#my_market = 'ETH-EUR'
    #my_size = 1.0 #number of ETH per trade
    #my_spread = 1.0 #number of EUR wide spread