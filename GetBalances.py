import urllib.request
import json
import datetime
from etherscan.tokens import Tokens
from etherscan.accounts import Account
from coinbase.wallet.client import Client
import gdax


def add_balance(balances_dict, coin, balance, description):
    if balances_dict['coins'].get(coin) is None:
        balances_dict['coins'][coin] = {'balances': []}

    balances_dict['coins'][coin]['balances'].append({'balance': balance, 'description': description})
    return balances_dict


def simplify_balances(coin_config, crypto_balances):
    simple_balances = {'coins': {"crypto": {}, "fiat": {}}}

    for coin, balances in crypto_balances['coins'].items():
        simple_balances['coins'][coin_config[coin]['type']][coin] = sum(
            [x['balance'] for x in balances['balances']])

    return simple_balances


def write_dictionary_as_json_file(filename, dictionary):
    dictionary['timestamp'] = datetime.datetime.now().isoformat()
    with open(filename, 'w') as f:
        f.write(json.dumps(dictionary, indent=4))


# config
config = json.loads(open('config.json').read())
crypto_balances = {'coins': config["starting_balances"]}

# Ethereum Manager
# pip install etherscan


eth_config = config['wallets']['ethereum']
coin_config = config['coins']
api_key = config['api_config']['etherscan']['api_key']

# get the simple ETH balances for each address
api = Account(address=eth_config['addresses'], api_key=api_key)
for address in api.get_balance_multiple():
    crypto_balances = add_balance(crypto_balances, 'ETH',
                                  int(address['balance']) / coin_config['ETH']['etherscan_units'],
                                 'from ETH address {addr}'.format(addr=address['account']))

# Now add the tokens from each address

for token in coin_config:
    contract_address = coin_config[token].get('erc20_token_contract_address')
    if contract_address != None:
        api = Tokens(contractaddress=contract_address, api_key=api_key)
        balance = 0
        for address in eth_config['addresses']:
            crypto_balances = add_balance(crypto_balances, token,
                                          int(api.get_token_balance(address=address)) / coin_config[token][
                                             'etherscan_units'], "from ETH address {addr}".format(addr=address))

# Coinbase
# pip install coinbase


coinbase_config = config['api_config']['coinbase']

client = Client(coinbase_config['api_key'], coinbase_config['api_secret'])
accounts = client.get_accounts()
for account in accounts.data:
    crypto_balances = add_balance(crypto_balances, account['currency'], float(account['balance']['amount']),
                                 "from Coinbase {addr}".format(addr=account['name']))

# GDAX
# pip install gdax

gdax_config = config['api_config']['gdax']

auth_client = gdax.AuthenticatedClient(gdax_config['api_key'], gdax_config['api_secret'], gdax_config['passphrase'])
for account in auth_client.get_accounts():
    crypto_balances = add_balance(crypto_balances, account['currency'], float(account['balance']),
                                 "from GDAX {addr}".format(addr=account['id']))


#Get BCH from Blockchair
bch_config = config['wallets']['bitcoin-cash']
for address in bch_config['addresses']:
    bch_url = config['api_config']['blockchair']['url'] + '?q=recipient({addr})'.format(addr=address)
    blockchair_result = json.loads(urllib.request.urlopen(bch_url).read())
    crypto_balances = add_balance(crypto_balances, 'BCH', int(blockchair_result['data'][0]['value']) / coin_config['BCH'][
                                             'blockchair_units'],
                                 "from BCH address {addr}".format(addr=address))

#Write data files
write_dictionary_as_json_file('crypto_balances.json', crypto_balances)

# simplify balances from detail
simple_balances = simplify_balances(coin_config, crypto_balances)
write_dictionary_as_json_file('crypto_balances_aggregated.json', simple_balances)
