import json
import datetime


class Config(object):

    def __init__(self):
        self.config = json.loads(open('../config/config.json').read())

    def starting_balances(self): return self.config['starting_balances']

    def api_config(self): return self.config['api_config']

    def coin_config(self):  return self.config['coins']

    def wallet_config(self): return self.config['wallets']


class Balances(object):

    def __init__(self, starting_balances={}):
        self.coins = starting_balances

    def add_balance(self, coin, balance, description):
        if self.coins.get(coin) is None:
            self.coins[coin] = {'balances': []}
        self.coins[coin]['balances'].append({'balance': balance, 'description': description})

    def add_balances(self, new_balances):
        for coin, balances in new_balances.items():
            for balance in balances['balances']:
                if balance['balance'] != 0.0:
                    if self.coins.get(coin) is None:
                        self.coins[coin] = {'balances': []}
                    self.coins[coin]['balances'].append(balance)

    def get_aggregated_balances(self, coin_config):
        simple_balances = {"crypto": {}, "fiat": {}, "iconomi_fund": {}}
        for coin, balances in self.coins.items():
            if coin_config.get(coin):
                _type = coin_config[coin]['type']
            else:
                _type = 'crypto'

            simple_balances[_type][coin] = sum(
                [x['balance'] for x in balances['balances']])


        return simple_balances

    def write_balances(self, filename='crypto_balances'):
        write_dictionary_as_json_file(filename, self.coins)

    def write_aggregated_balances(self, coin_config):
        write_dictionary_as_json_file('crypto_balances_aggregated', self.get_aggregated_balances(coin_config))

    def load_aggregated_balances(self):
        # this doesn't belong here...
        return json.loads(open('../data/crypto_balances_aggregated.json').read())['data']


class Valuation(object):

    def __init__(self, display_ccy=''):
        self.balances = {}
        self.prices = {}
        self.values = {}
        self.missing_coins = []
        self.display_ccy = display_ccy
        self.iconomi_value = 0.0

    def add_result(self, coin, balance, price):
        self.balances[coin] = balance
        self.prices[coin] = price
        self.values[coin] = price * balance

    def add_missing_coin(self, coin):
        self.missing_coins.append(coin)

    def total_value(self):
        return sum([self.values[x] for x in self.values])

    def set_display_ccy(self, display_ccy):
        self.display_ccy = display_ccy

    def set_iconomi_value(self, iconomi_value):
        self.iconomi_value = iconomi_value

    def valuation(self):
        return {'balances': self.balances,
                            'prices': self.prices,
                            'values': self.values,
                            'total_value': '{:0,.2f}'.format(self.total_value()),
                            'display_ccy': self.display_ccy,
                            'iconomi_value': self.iconomi_value,
                            'missing_coins': self.missing_coins}

    def write_valuation(self):
        write_dictionary_as_json_file('crypto_values', self.valuation(), True)
        # temp hack to get online..
        write_dictionary_as_json_file('../../../../Google Drive/crypto_values', self.valuation())


def write_dictionary_as_json_file(filename, dictionary, archive=False):
    output_dictionary = {'data': dictionary}
    output_dictionary['timestamp'] = datetime.datetime.now().isoformat()
    with open('../data/' + filename + '.json', 'w') as f:
        f.write(json.dumps(output_dictionary, indent=4))
    if archive:
        archive_filename = '../data/archive/' + filename + '/' + output_dictionary['timestamp'][0:19].replace(':', '') + '_' + filename + '.json'
        with open(archive_filename, 'w') as fa:
            fa.write(json.dumps(output_dictionary, indent=4))
