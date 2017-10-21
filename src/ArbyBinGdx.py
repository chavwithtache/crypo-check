import json
import urllib.request
import logging
import gdax
from binance.client import Client as binanceClient
from binance.enums import *
import cryptolib
from math import floor
import sys
from collections import defaultdict

logger = logging.getLogger('crypto_bingdx')
hdlr = logging.FileHandler('../logs/crypto_bingdx.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

# config
cfg = cryptolib.Config()
api_config = cfg.api_config()

gdax_config = api_config['gdax_write']
binance_config = api_config['binance']

class ArbBinGdx(object):
    def __init__(self, coin1, coin2):
        self.gdaxfees = defaultdict(lambda: 0.003)
        self.gdaxfees['ETHBTC'] = 0.003 #can override individually here
        self.binancefees = defaultdict(lambda: 0.001)
        self.binancefees['ETHBTC'] = 0.001  # can override individually here

        #self.max_trades = {'ETHBTC': 0.5, 'LTCBTC': 2}

        self.binance_client = binanceClient(binance_config['api_key'], binance_config['api_secret'])
        self.gdax_client = gdax.AuthenticatedClient(gdax_config['api_key'], gdax_config['api_secret'],
                                                    gdax_config['passphrase'])
        self.orderbook={}
        self.balances={}

        self.coin1 = coin1
        self.coin2 = coin2

    def load_orderbook(self):
        market = self.coin1 + self.coin2
        try:
            url = 'https://api.gdax.com/products/' + self.coin1 + '-' + self.coin2 + '/book?level=1'
            self.orderbook['GDAX'] = json.loads(
                urllib.request.urlopen(url).read())

        except:
            logger.error('Error loading gdax orderbook: ' + url)

        try:
            self.orderbook['Binance'] = self.binance_client.get_order_book(symbol=market, limit=5)

        except:
            logger.error('Error loading Binance orderbook: ' + market)

        self.gdax_fee = self.gdaxfees[market]
        self.binance_fee = self.binancefees[market]

    def load_balances(self):
        binance_balances = self.binance_client.get_account()['balances']
        self.balances['Binance'] ={}
        for account in binance_balances:
            if account['asset'] == self.coin1:
                self.balances['Binance'][self.coin1] = float(account['free'])
            elif account['asset'] == self.coin2:
                self.balances['Binance'][self.coin2] = float(account['free'])
            elif account['asset'] == 'BNB': #for record keeping..
                self.balances['Binance']['BNB'] = float(account['free'])

        gdax_balances = self.gdax_client.get_accounts()
        self.balances['GDAX'] = {}
        for account in gdax_balances:
            if account['currency'] == self.coin1:
                self.balances['GDAX'][self.coin1] = float(account['available'])
            elif account['currency'] == self.coin2:
                self.balances['GDAX'][self.coin2] = float(account['available'])
        print(self.balances)
        logger.info(self.balances)

    def calc_1(self):

            traded = False
            asset1 = 0.0
            asset2 = 0.0
            # see if we buy on gdax and sell on binance
            gdax_bid = float(self.orderbook['GDAX']['bids'][0][0])
            gdax_bid_size = float(self.orderbook['GDAX']['bids'][0][1])
            gdax_ask = float(self.orderbook['GDAX']['asks'][0][0])
            gdax_ask_size = float(self.orderbook['GDAX']['asks'][0][1])

            binance_bid = float(self.orderbook['Binance']['bids'][0][0])
            binance_bid_size = float(self.orderbook['Binance']['bids'][0][1])
            binance_ask = float(self.orderbook['Binance']['asks'][0][0])
            binance_ask_size = float(self.orderbook['Binance']['asks'][0][1])

            print('GDAX:    bid{}, size{}, ask{}, size{}, fee{}'.format(gdax_bid,gdax_bid_size,gdax_ask,gdax_ask_size,self.gdax_fee))
            print('Binance: bid{}, size{}, ask{}, size{}, fee{}'.format(binance_bid,binance_bid_size,binance_ask,binance_ask_size,self.binance_fee))
            #max_trade = self.max_trades[self.coin1 + self.coin2]
            max_trade = min(self.balances['Binance'][self.coin1], self.balances['GDAX'][self.coin1])

            #try sell on Binance and buyback on GDAX
            # sell on Binance at the bid price and buy on dgax at the ask
            size = floor(min(binance_bid_size, gdax_ask_size, max_trade)*1000.0)/1000.0 # round to 3 dp

            #Only proceed if there are enough funds
            if self.balances['Binance'][self.coin1] >= size and self.balances['GDAX'][self.coin2] >= size * gdax_ask:
                #binance trade: sell {size} {asset1} @ {binance_bid}
                asset1 -= size
                asset2 += (size * binance_bid) * (1-self.binance_fee)

                # GDAX trade: buy {size} {asset1} @ {gdax_ask}
                asset1 += size
                asset2 -= (size * gdax_ask) * (1 + self.gdax_fee)

                print('Buy GDAX, Sell Binance PL: {} {}'.format(asset2, self.coin2))

                if asset2 > 0.0001:

                    binance_order = self.binance_client.create_order(
                        symbol=self.coin1 + self.coin2,
                        side=SIDE_SELL,
                        type=ORDER_TYPE_MARKET,
                        quantity=size) #,disable_validation=True)
                    logger.info(binance_order)

                    logger.info(
                        self.gdax_client.buy(product_id=self.coin1 + '-' + self.coin2, type='market', size=size))

                    traded = True
            else:
                print('not enough funds')

            #try sell on GDAX and buyback on Binance
            # sell on GDAX at the bid price and buy on Binance at the ask
            size = floor(min(gdax_bid_size, binance_ask_size, max_trade)*1000.0)/1000.0 #1 ETH max

            # Only proceed if there are enough funds ...
            if self.balances['GDAX'][self.coin1] >= size and self.balances['Binance'][self.coin2] >= size * binance_ask:
                # GDAX trade: sell {size} {asset1} @ {binance_bid}
                asset1 -= size
                asset2 += (size * gdax_bid) * (1-self.gdax_fee)

                # Binance trade: buy {size} {asset1} @ {gdax_ask}
                asset1 += size
                asset2 -= (size * binance_ask) * (1 + self.binance_fee)

                print('Buy Binance, Sell GDAX PL: {} {}'.format(asset2, self.coin2))
                if asset2 > 0.0001:

                    binance_order = self.binance_client.create_order(
                        symbol=self.coin1 + self.coin2,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_MARKET,
                        quantity=size) #,disable_validation=True)
                    logger.info(binance_order)

                    logger.info(
                        self.gdax_client.sell(product_id=self.coin1 + '-' + self.coin2, type='market', size=size))

                    traded = True
            else:
                print('not enough funds')

            return traded

    def runonce(self):
        self.load_orderbook()
        if self.calc_1():
            self.load_balances()

    def run(self):
        self.load_balances()
        traded = False
        while not traded:
            self.load_orderbook()
            traded = self.calc_1()
        self.load_balances()


testETH = ArbBinGdx('ETH', 'BTC')
testLTC = ArbBinGdx('LTC', 'BTC')

testETH.load_balances()
testLTC.load_balances()

while True:
    testETH.runonce()
    testLTC.runonce()


#test = ArbBinGdx('LTC', 'BTC')
#test.run()
