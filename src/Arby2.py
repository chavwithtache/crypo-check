import json
import urllib.request
import logging
import gdax
import cryptolib
import sys

logger = logging.getLogger('crypto_arby2')
hdlr = logging.FileHandler('../logs/crypto_arby2.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

# config
cfg = cryptolib.Config()
api_config = cfg.api_config()

gdax_config = api_config['gdax_write']
class Arby2(object):
    def __init__(self):
        self.fees = {'ETHEUR': 0.003,
                    'ETHBTC': 0.003,
                    'BTCEUR': 0.003,
                    'LTCBTC': 0.003,
                    'LTCEUR': 0.003}
        self.gdax_auth_client = gdax.AuthenticatedClient(gdax_config['api_key'], gdax_config['api_secret'],
                                                         gdax_config['passphrase'])
    def load_single_orderbook(self, market):
        try:
            url = 'https://api.gdax.com/products/' + market[0:3] + '-' + market[3:6] + '/book?level=1'
            self.orderbook[market] = json.loads(
                urllib.request.urlopen(url).read())

        except:
            logger.error('Error loading: ' + url)

    def reload_orderbook(self, coin='all'):
        self.orderbook = {}
        if coin == 'all':
            self.load_single_orderbook('ETHEUR')
            self.load_single_orderbook('LTCEUR')
            self.load_single_orderbook('BTCEUR')
            self.load_single_orderbook('ETHBTC')
            self.load_single_orderbook('LTCBTC')
        else:
            self.load_single_orderbook(coin + 'EUR')
            self.load_single_orderbook('BTCEUR')
            self.load_single_orderbook(coin + 'BTC')

    def calc_1(self, starting_coin):
        """
        This method does the following path:
        1) Buy {starting_coin} with EUR
        2) Sell {starting_coin} for BTC
        3) Sell BTC for EUR
        if these 3 trades yield a positive EUR balance then send the trades to GDAX to execute
        :return:
        """
        try:
                                # buy {starting_coin} with EUR
                entry_price = float(self.orderbook[starting_coin + 'EUR']['asks'][0][0])
                entry_size = float(self.orderbook[starting_coin + 'EUR']['asks'][0][1])
                entry_fee = self.fees[starting_coin + 'EUR']

                # sell {starting_coin} for BTC
                switch_price = float(self.orderbook[starting_coin + 'BTC']['bids'][0][0])
                switch_size = float(self.orderbook[starting_coin + 'BTC']['bids'][0][1])
                switch_fee = self.fees[starting_coin + 'BTC']

                # sell BTC for EUR
                exit_price = float(self.orderbook['BTCEUR']['bids'][0][0])
                exit_size = float(self.orderbook['BTCEUR']['bids'][0][1])
                exit_fee = self.fees['BTCEUR']

                # first get the min of entry_size and switch_size as they are both in {starting_coin}
                size1 = min(entry_size, switch_size, (1 if starting_coin == 'ETH' else 5))

                potential_exit_size = size1 * switch_price * (1 - switch_fee)
                if exit_size > potential_exit_size:
                    # good to go with size1
                    pass
                else:
                    size1 = exit_size / (switch_price * (1 - switch_fee))

                size2 = size1 * switch_price * (1 - switch_fee)

                # round both to 8dp

                size1 = round(size1, 8)
                size2 = round(size2, 8)

                # quick eval - this will show the EUR profit of these trades

                EUR_PL = -(size1 * entry_price * (1 + entry_fee)) + size2 * exit_price * (1 - exit_fee)

                if EUR_PL < 0.5:
                    msg = 'PL: %f EUR. No Trade. (%s-BTC)' % (EUR_PL, starting_coin)
                    logger.debug(msg)
                    print(msg)
                else:
                    # looks good..
                    logger.info(self.orderbook)

                    self.balances = {'EUR': 0, 'ETH': 0, 'BTC': 0, 'LTC': 0}

                    logger.info('I buy %f %s @ %f %s' % (size1, starting_coin, entry_price, 'EUR'))
                    self.balances[starting_coin] += size1
                    self.balances['EUR'] -= size1 * entry_price * (1 + entry_fee)
                    logger.info(self.balances)

                    logger.info('I sell %f %s @ %f %s' % (size1, starting_coin, switch_price, 'BTC'))
                    self.balances[starting_coin] -= size1
                    self.balances['BTC'] += size2
                    logger.info(self.balances)

                    logger.info('I sell %f %s @ %f %s' % (size2, 'BTC', exit_price, 'EUR'))
                    self.balances['BTC'] -= size2
                    self.balances['EUR'] += size2 * exit_price * (1 - exit_fee)
                    logger.info(self.balances)

                    if self.balances['EUR'] > 0.5 and self.balances['ETH'] == 0 and self.balances['BTC'] == 0 and \
                                    self.balances['LTC'] == 0 and size2 > 0.01 and size1 > 0.01:
                        print('trading...')
                        # here we go.....
                        logger.info('holy shit Im doing it!!')

                        logger.info(self.gdax_auth_client.buy(product_id=starting_coin + '-EUR', type='market', size=size1))
                        logger.info(self.gdax_auth_client.sell(product_id=starting_coin + '-BTC', type='market', size=size1))
                        logger.info(self.gdax_auth_client.sell(product_id='BTC-EUR', type='market', size=size2))
        except Exception:
            logger.exception('Error running calc_1: ' + starting_coin)

    def calc_2(self, switch_coin):
        """
        This method does the following path:
        1) Buy BTC with EUR
        2) Buy {switch_coin} with BTC
        3) Sell {switch_coin} for EUR
        if these 3 trades yield a positive EUR balance then send the trades to GDAX to execute
        :return:
        """

        try:
            # buy BTC with EUR
            entry_price = float(self.orderbook['BTCEUR']['asks'][0][0])
            entry_size = float(self.orderbook['BTCEUR']['asks'][0][1])
            entry_fee = self.fees['BTCEUR']

            # buy {switch_coin} with BTC
            switch_price = float(self.orderbook[switch_coin + 'BTC']['asks'][0][0])
            switch_size = float(self.orderbook[switch_coin + 'BTC']['asks'][0][1])
            switch_fee = self.fees[switch_coin + 'BTC']

            # sell {switch_coin} for EUR
            exit_price = float(self.orderbook[switch_coin + 'EUR']['bids'][0][0])
            exit_size = float(self.orderbook[switch_coin + 'EUR']['bids'][0][1])
            exit_fee = self.fees[switch_coin + 'EUR']

            # first get the min of exit_size and switch_size as they are both in {switch_coin}
            logger.debug(self.orderbook)

            size2 = min(exit_size, switch_size, (1 if switch_coin == 'ETH' else 5))
            logger.debug('size2:%f' % size2)
            potential_entry_size = size2 * switch_price * (1 + switch_fee)
            logger.debug('potential_entry_size:%f' % potential_entry_size)

            if entry_size > potential_entry_size:
                # good to go with size2
                pass
            else:
                size2 = entry_size / (switch_price * (1 + switch_fee))
                logger.debug('resetting size2 to :%f' % size2)

            size1 = size2 * switch_price * (1 + switch_fee)
            logger.debug('size1:%f' % size1)

            #round both to 8dp

            size1 = round(size1, 8)
            size2 = round(size2, 8)

            #quick eval - this will show the EUR profit of these trades

            EUR_PL = -(size1 * entry_price * (1 + entry_fee)) + size2 * exit_price * (1 - exit_fee)

            if EUR_PL < 0.5:
                msg = 'PL: %f EUR. No Trade. (BTC-%s)' % (EUR_PL, switch_coin)
                logger.debug(msg)
                print(msg)
            else:
                #looks good..
                logger.info(self.orderbook)

                self.balances = {'EUR': 0, 'ETH': 0, 'BTC': 0, 'LTC': 0}

                logger.info('I buy %f %s @ %f %s' % (size1, 'BTC', entry_price, 'EUR'))
                self.balances['BTC'] += size1
                self.balances['EUR'] -= size1 * entry_price * (1 + entry_fee)
                logger.info(self.balances)

                logger.info('I buy %f %s @ %f %s' % (size2, switch_coin, switch_price, 'BTC'))
                self.balances[switch_coin] += size2
                self.balances['BTC'] -= size1
                logger.info(self.balances)

                logger.info('I sell %f %s @ %f %s' % (size2, switch_coin, exit_price, 'EUR'))
                self.balances[switch_coin] -= size2
                self.balances['EUR'] += size2 * exit_price * (1 - exit_fee)
                logger.info(self.balances)

                if self.balances['EUR'] >= 0.5 and self.balances['ETH'] == 0 and self.balances['BTC'] == 0 and \
                                self.balances['LTC'] == 0 and size2 > 0.01 and size1 > 0.01:
                    print('trading...see logs for info')
                    #here we go.....
                    logger.info('fingers crossed..!!')


                    logger.info(self.gdax_auth_client.buy(product_id='BTC-EUR', type='market', size=size1))
                    logger.info(self.gdax_auth_client.buy(product_id=switch_coin + '-BTC', type='market', size=size2))
                    logger.info(self.gdax_auth_client.sell(product_id=switch_coin + '-EUR', type='market', size=size2))
        except:
            logger.error('Error running calc_2: ' + switch_coin)

test = Arby2()
counter = 0

if len(sys.argv) == 1:
    while True:
        counter += 1
        print(counter)
        test.reload_orderbook()
        test.calc_1('ETH')
        test.calc_1('LTC')
        test.calc_2('ETH')
        test.calc_2('LTC')
elif len(sys.argv) == 2:
    logger.info('Starting Process: {}'.format(sys.argv[1]))
    while True:
        counter += 1
        print(counter)
        test.reload_orderbook(sys.argv[1])
        test.calc_1(sys.argv[1])
        test.calc_2(sys.argv[1])

