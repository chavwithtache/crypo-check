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
#coin_config = cfg.coin_config()

bal = cryptolib.Balances(cfg.starting_balances())

# add in blockchain balances
blockchain_balances = json.loads(open('../data/blockchain_balances.json').read())['data']
bal.add_balances(blockchain_balances)

# Coinbase
# pip install coinbase
print('start coinbase')
coinbase_config = api_config['coinbase']

client = cbClient(coinbase_config['api_key'], coinbase_config['api_secret'])
accounts = client.get_accounts()
for account in accounts.data:
    coin = cfg.resolve_coin(account['currency'].upper())
    bal.add_balance(coin, float(account['balance']['amount']),
                    'from Coinbase {addr}'.format(addr=account['name']))
print('end coinbase')

# GDAX
# pip install gdax

if True:
    print('start GDAX')
    gdax_config = api_config['gdax']

    gdax_auth_client = gdax.AuthenticatedClient(gdax_config['api_key'], gdax_config['api_secret'],
                                                gdax_config['passphrase'])
    for account in gdax_auth_client.get_accounts():
        print(account)
        coin = cfg.resolve_coin(account['currency'].upper())
        bal.add_balance(coin, float(account['balance']),
                        'from GDAX {addr}'.format(addr=account['id']))
    print('end GDAX')

# Binance

# pip install python-binance
# also requires Visual C++ Build Tools.. from here http://landinghub.visualstudio.com/visual-cpp-build-tools

#print('BINANCE DISABLED - CHECK AND REENABLE')
if True:
    print('start binance')
    binance_config = api_config['binance']

    bnb_client = bnbClient(binance_config['api_key'], binance_config['api_secret'])
    recvWindow = 10000 #This may need to be increased if local and server times go out of sync
    bnb_balances = bnb_client.get_account(recvWindow=recvWindow)['balances']#
    print(bnb_balances)
    nonEmpty = [bnbbal for bnbbal in bnb_balances if float(bnbbal['free']) != 0 or float(bnbbal['locked']) != 0]
    for bnbbal in nonEmpty:
        coin = cfg.resolve_coin(bnbbal['asset'].upper())
        bal.add_balance(coin, float(bnbbal['free']) + float(bnbbal['locked']), 'from Binance')
    print('end binance')

# Bitfinex
# pip install bitfinex NB the current prod version didn't have the TradeClient class so needed to manually download the bitfinex-develop version
print('start Bitfinex')
bfx_config = api_config['bitfinex']
bfx_auth_client = bfxClient(bfx_config['api_key'], bfx_config['api_secret'])
for account in bfx_auth_client.balances():
    coin = cfg.resolve_coin(account['currency'].upper())
    bal.add_balance(coin, float(account['amount']),
                    'from Bitfinex')
print('end Bitfinex')

# Write data files
bal.write_balances()

# simplify balances from detail
bal.write_aggregated_balances(cfg)
