import json
import datetime

#Define global variables
config = json.loads(open('../config/config.json').read())
coin_config = config['coins']

crypto_balances = {'coins': config["starting_balances"]}

def add_balance(coin, balance, description):
    global crypto_balances
    if crypto_balances['coins'].get(coin) is None:
        crypto_balances['coins'][coin] = {'balances': []}

    crypto_balances['coins'][coin]['balances'].append({'balance': balance, 'description': description})



def simplify_balances():
    simple_balances = {'coins': {"crypto": {}, "fiat": {}, "iconomi_fund": {}}}

    for coin, balances in crypto_balances['coins'].items():
        simple_balances['coins'][coin_config[coin]['type']][coin] = sum(
            [x['balance'] for x in balances['balances']])

    return simple_balances


def write_dictionary_as_json_file(filename, dictionary):
    dictionary['timestamp'] = datetime.datetime.now().isoformat()
    with open('../data/' + filename, 'w') as f:
        f.write(json.dumps(dictionary, indent=4))


def add_result(crypto_data, coin, balance, price):
    crypto_data['balances'][coin] = balance
    crypto_data['prices'][coin] = price
    crypto_data['values'][coin] = price * balance
    return crypto_data


def add_result_bycoin(crypto_data, coin, balance, price):
    crypto_data_coins = crypto_data['coins']
    crypto_data_coins[coin] = {}
    crypto_data_coins[coin]['balance'] = balance
    crypto_data_coins[coin]['price'] = price
    crypto_data_coins[coin]['value'] = price * balance
    return crypto_data
