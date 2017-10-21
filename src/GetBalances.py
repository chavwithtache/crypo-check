import urllib.request
from etherscan.tokens import Tokens
from etherscan.accounts import Account
from coinbase.wallet.client import Client as cbClient
from bitfinex.client import TradeClient as bfxClient
from binance.client import Client as bnbClient
import gdax
import json
import cryptolib


# config
cfg = cryptolib.Config()
wallet_config = cfg.wallet_config()
api_config = cfg.api_config()
coin_config = cfg.coin_config()

bal = cryptolib.Balances(cfg.starting_balances())

# Ethereum Manager
# pip install etherscan


eth_config = wallet_config['ethereum']
api_key = api_config['etherscan']['api_key']

# get the simple ETH balances for each address
print('start etherscan')
api = Account(address=eth_config['addresses'], api_key=api_key)
for address in api.get_balance_multiple():
    bal.add_balance('ETH', int(address['balance']) / coin_config['ETH']['etherscan_units'],
                                 'from ETH address {addr}'.format(addr=address['account']))

# Now add the tokens from each address

for token in coin_config:
    contract_address = coin_config[token].get('erc20_token_contract_address')
    if contract_address != None:
        api = Tokens(contractaddress=contract_address, api_key=api_key)
        balance = 0
        for address in eth_config['addresses']:
            bal.add_balance(token, int(api.get_token_balance(address=address)) / coin_config[token][
                                             'etherscan_units'], 'from ETH address {addr}'.format(addr=address))
print('end etherscan')
# Coinbase
# pip install coinbase
print('start coinbase')
coinbase_config = api_config['coinbase']

client = cbClient(coinbase_config['api_key'], coinbase_config['api_secret'])
accounts = client.get_accounts()
for account in accounts.data:
    bal.add_balance(account['currency'], float(account['balance']['amount']),
                                 'from Coinbase {addr}'.format(addr=account['name']))
print('end coinbase')
# GDAX
# pip install gdax
print('start GDAX')
gdax_config = api_config['gdax']

gdax_auth_client = gdax.AuthenticatedClient(gdax_config['api_key'], gdax_config['api_secret'], gdax_config['passphrase'])
for account in gdax_auth_client.get_accounts():
    bal.add_balance(account['currency'], float(account['balance']),
                                 'from GDAX {addr}'.format(addr=account['id']))
print('end GDAX')
#Binance
# pip install python-binance
# also requires Visual C++ Build Tools.. from here http://landinghub.visualstudio.com/visual-cpp-build-tools
print('start binance')
binance_config = api_config['binance']

bnb_client = bnbClient(binance_config['api_key'], binance_config['api_secret'])
nonEmpty = [bnbbal for bnbbal in bnb_client.get_account()['balances'] if float(bnbbal['free']) != 0 or  float(bnbbal['locked']) != 0]
for bnbbal in nonEmpty:
    bal.add_balance(bnbbal['asset'], float(bnbbal['free']) + float(bnbbal['locked']), 'from Binance')
print('end binance')


#Bitfinex
# pip install bitfinex NB the current prod version didn't have the TradeClient class so needed to manually download the bitfinex-develop version
print('start Bitfinex')
bfx_config = api_config['bitfinex']
bfx_auth_client = bfxClient(bfx_config['api_key'], bfx_config['api_secret'])
for account in bfx_auth_client.balances():
    bal.add_balance(account['currency'].upper(), float(account['amount']),
                                 'from Bitfinex')
print('end Bitfinex')

#Get BCH from Blockchair
print('start blockchair')
bch_config = wallet_config['bitcoin-cash']
for address in bch_config['addresses']:
    bch_url = api_config['blockchair']['url'] + '?q=recipient({addr})'.format(addr=address)
    blockchair_result = json.loads(urllib.request.urlopen(bch_url).read())
    bal.add_balance('BCH', int(blockchair_result['data'][0]['value']) / coin_config['BCH']['blockchair_units'],
                                 'from BCH address {addr}'.format(addr=address))
print('end blockchair')

#Write data files
bal.write_balances()

# simplify balances from detail
bal.write_aggregated_balances(coin_config)
