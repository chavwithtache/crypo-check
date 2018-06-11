import gdax
import json
import cryptolib
import urllib.request
import collections
import logging
import os
import arrow
import numpy as np
import math

logger = logging.getLogger('crypto_toddlerTrading')
hdlr = logging.FileHandler('../logs/crypto_toddler_trading.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


def round_up(f, dp):
    return math.ceil(f * 10 ** dp) / 10 ** dp


class ToddlerTrading(object):
    def __init__(self):
        cfg = cryptolib.Config()
        api_config = cfg.api_config()

        self.gdax_config = api_config['gdax_write']
        self.reconnect_client()
        self.reload_orders()

        self.Pair = collections.namedtuple('Pair', 'market size spread accumulate_asset')

        self.trade_pairs = []
        self.error_markets = {}
        self.counter = 0
        self.sentiment_or = {}

    def reconnect_client(self):
        self.gdax_auth_client = gdax.AuthenticatedClient(self.gdax_config['api_key'], self.gdax_config['api_secret'],
                                                         self.gdax_config['passphrase'])

    def reload_orders(self):
        self.orders = self.gdax_auth_client.get_orders()

    def add_pair(self, market, size, spread, sentiment_or=-1.0, accumulate_asset=False):
        self.trade_pairs.append(self.Pair(market=market, size=size, spread=spread, accumulate_asset=accumulate_asset))
        self.error_markets[market] = False
        self.sentiment_or[market] = sentiment_or

    def check_products(self):
        try:
            self.reload_orders()
            for trade_pair in self.trade_pairs:
                self.check_product(trade_pair)
        except:
            print('some error...')
            logger.exception('some error...')

    def do_trades(self, trade_pair, mid_price):
        market = trade_pair.market
        sentiment = self.calc_sentiment(market) if self.sentiment_or[market] == -1.0 else self.sentiment_or[market]

        sell_price = round(mid_price + trade_pair.spread * sentiment, 2)
        sell_size = (
                            sell_price - trade_pair.spread) * trade_pair.size / sell_price if trade_pair.accumulate_asset else trade_pair.size
        sell_size = round_up(sell_size, 3)
        trade1_id = self.do_trade(market, 'sell', sell_price, sell_size)

        if trade1_id is not None:
            # first trade succeeded. Do second trade
            buy_price = round(mid_price - trade_pair.spread * (1 - sentiment), 2)
            trade2_id = self.do_trade(market, 'buy', buy_price, trade_pair.size)

            if trade2_id is not None:
                # Both trades executed successfully. Happy days
                pass
            else:
                # Trade1 succeeded but trade 2 failed. Need to cancel trade 1
                self.error_markets[market] = True
                logger.info(
                    'Second trade failed. Cancelling Trade1 id:{}. Trade_pair {} disabled'.format(trade1_id, market))
                logger.info(self.gdax_auth_client.cancel_order(trade1_id))
        else:
            self.error_markets[market] = True
            logger.info('First trade failed. Trade_pair {} disabled'.format(market))

    def do_trade(self, market, side, price, size):

        print('{} {} {} @ {}'.format(side, size, market, price))
        if side == 'sell':
            result = self.gdax_auth_client.sell(product_id=market, type='limit', size=size, price=price, post_only=True)
        else:
            result = self.gdax_auth_client.buy(product_id=market, type='limit', size=size, price=price, post_only=True)

        logger.info(result)

        # the success is if result is a dictionary with an id key AND 'status' != 'rejected'
        try:
            new_trade_id = result['id']
            if result['status'] == 'rejected':
                new_trade_id = None
            else:
                with open('../data/toddler_trading/{}/{}'.format(market, new_trade_id), 'w'):
                    pass
        except:
            new_trade_id = None

        return new_trade_id

    def check_product(self, trade_pair):
        market = trade_pair.market
        if self.error_markets[market]:
            print('{} temporarily suspended due to error'.format(market))
        else:
            active_ids = [order['id'] for order in self.orders[0]]
            orders_left = 0
            for active_id in os.listdir('../data/toddler_trading/' + market):
                try:
                    active_ids.index(active_id)
                    # order still open.
                    orders_left += 1
                except ValueError:
                    # not in the list so delete the file. this means that has traded since last run
                    os.remove('../data/toddler_trading/{}/{}'.format(market, active_id))

            if orders_left == 0:
                print('{}: orders all hit - do another pair'.format(market))
                url = 'https://api.gdax.com/products/' + market + '/book?level=1'
                orderbook = json.loads(urllib.request.urlopen(url).read())
                mid = (float(orderbook['bids'][0][0]) + float(orderbook['asks'][0][0])) / 2

                self.do_trades(trade_pair, mid)

            else:
                self.counter += 1
                print('{} {}: waiting for orders to hit. {} order(s) outstanding'.format(self.counter, market,
                                                                                         orders_left))

    @staticmethod
    def calc_sentiment(market):
        # sentiment is the ratio of the spread that is applied to the sell order
        # eg if 0.8 is specified then the orders will be:
        # sell_price =  mid + 0.8 * spread
        # buy_price =  mid - 0.2 * spread
        # eg. 0.2 is bearish, 0.5 neutral, 0.8 bullish

        granularity = 60  # number of seconds for the candle
        lookback_mins = 15  # number of minutes of data to go back
        max_move = 0.01  # highest move in a single candle
        min_move = -0.01  # lowest move in a single candle
        max_sentiment = 0.8  # max sentiment that maps to max_move
        min_sentiment = 0.2  # min sentiment that maps to min_move

        xp = np.array([min_move, max_move])
        fp = np.array([min_sentiment, max_sentiment])

        public_client = gdax.PublicClient()

        to_time = arrow.get(public_client.get_time()['iso']).shift(seconds=-5)
        from_time = to_time.shift(minutes=-lookback_mins)

        # if the market is vs EUR or GBP, check the USD market as it is much more liquid
        liq_market = market[0:4] + 'USD' if market[4:7] in ['EUR', 'GBP'] else market

        result = public_client.get_product_historic_rates(product_id=liq_market, start=from_time.isoformat()[:19],
                                                          end=to_time.isoformat()[:19], granularity=granularity)

        x = np.array([candle[0] for candle in result])
        _close = np.array([candle[4] for candle in result])

        future = x[0] + granularity
        p = np.poly1d(np.polyfit(x, _close, 2))

        _last = _close[0]
        _next = p(future)
        pc_move = (_next - _last) / _last
        sentiment = round(np.interp(pc_move, xp, fp), 2)
        # future close

        logger.info(
            'market {} (used {}), last {}, next {}. Going {} by {:5.4f}% Calculated sentiment:{}'.format(market,
                                                                                                         liq_market,
                                                                                                         _last, _next,
                                                                                                         'up' if _next > _last else 'down',
                                                                                                         100 * pc_move,
                                                                                                         sentiment))

        return sentiment


test = ToddlerTrading()
# test.add_pair('ETH-EUR', 10, 2.5)
# test.add_pair('ETH-EUR', 10, 6.0, sentiment_or=0.9, accumulate_asset=True)  # NB I AM FORCING SENTIMENT TO BE VERY BULLISH HERE
# test.add_pair('ETH-EUR', 5, 2.0)
# test.add_pair('ETH-EUR', 5, 20.0, sentiment_or=0.95, accumulate_asset=True)
test.add_pair('ETH-EUR', 4.3, 10.0, accumulate_asset=False, sentiment_or=0.8)
#test.add_pair('ETH-EUR', 0.5, 1.0, accumulate_asset=True)
test.add_pair('LTC-EUR', 1.2, 5, accumulate_asset=False, sentiment_or=0.8)
# test.add_pair('BCH-EUR', 1, 20.0, sentiment_or=0.8, accumulate_asset=True)
# test.add_pair('BTC-EUR', 0.1, 20.0)
# test.add_pair('BTC-GBP', 0.1, 18.0)

logger.info('started')
while True:
    test.check_products()
