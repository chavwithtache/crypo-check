import json
import urllib.request
import asyncio
from datetime import datetime
import arrow
import os
import pandas as pd


def get_file_series(root):
    df = pd.DataFrame([(filename[0:17], filename) for filename in
                       os.listdir(root)
                       if filename.endswith("_crypto_values.json")], columns=['Date', 'Filename'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df['Filename']


def get_diff_df(root, period):
    s_files = get_file_series(root)
    last_day = s_files.last(period)

    current_time_stamp, current_file = (arrow.get(last_day.index[-1]), last_day.iloc[-1])
    previous_time_stamp, previous_file = (arrow.get(last_day.index[0]), last_day.iloc[0])

    print('from {} to {}'.format(previous_time_stamp.humanize(), current_time_stamp.humanize()))

    s_current = pd.Series(
        json.loads(open('../data/archive/crypto_values/{}'.format(current_file)).read())['data']['values'])
    s_current.name = 'values_new'

    print('../data/archive/crypto_values/{}'.format(previous_file))
    s_previous = pd.Series(
        json.loads(open('../data/archive/crypto_values/{}'.format(previous_file)).read())['data']['values'])
    s_previous.name = 'values_prev'

    df_all = pd.concat([s_current, s_previous], axis=1)
    df_all['diff'] = df_all['values_new'] - df_all['values_prev']
    df_all['diff_pc'] = (df_all['values_new'] - df_all['values_prev']) / df_all['values_prev']
    df_all.sort_values(by='diff_pc', inplace=True, ascending=False)
    return df_all





class Config(object):
    default_path = '../config/config.json'

    def __init__(self, path=default_path):
        self.config = json.loads(open(path).read())

    def starting_balances(self):
        return self.config['starting_balances']

    def api_config(self):
        return self.config['api_config']

    def wallet_config(self):
        return self.config['wallets']

    def coin_config(self):
        return self.config['coins']

    def resolve_coin(self, coin):
        c = self.config['coins'].get(coin)
        if c:
            if c['type'] == 'link':
                return c['parent']
        return coin


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

    def get_all_balances(self):
        return self.coins

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


class CoinMarketCap(object):
    def __init__(self, base_url: str, display_ccy: str):
        self._base_url = base_url
        self._display_ccy = display_ccy

    def get_price(self, coin):
        full_url = self._base_url + coin + '?convert=' + self._display_ccy
        print(full_url)
        res = json.loads(urllib.request.urlopen(full_url).read())
        return res[0]['price_' + self._display_ccy.lower()]


def write_dictionary_as_json_file(filename, dictionary, archive=False):
    output_dictionary = {'data': dictionary}
    output_dictionary['timestamp'] = datetime.now().isoformat()
    with open('../data/' + filename + '.json', 'w') as f:
        f.write(json.dumps(output_dictionary, indent=4))
    if archive:
        archive_filename = '../data/archive/' + filename + '/' + output_dictionary['timestamp'][0:19].replace(':',
                                                                                                              '') + '_' + filename + '.json'
        with open(archive_filename, 'w') as fa:
            fa.write(json.dumps(output_dictionary, indent=4))
