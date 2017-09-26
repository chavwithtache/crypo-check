import urllib.request
from etherscan.tokens import Tokens
from etherscan.accounts import Account
from coinbase.wallet.client import Client as cbClient
from bitfinex.client import TradeClient as bfxClient
import gdax
import json
import crypto_globals as cg


# config


# Ethereum Manager
# pip install etherscan

eth_config = cg.config['wallets']['ethereum']
api_key = cg.config['api_config']['etherscan']['api_key']

# get the simple ETH balances for each address
api = Account(address=eth_config['addresses'], api_key=api_key)
for address in api.get_balance_multiple():
    cg.add_balance('ETH', int(address['balance']) / cg.coin_config['ETH']['etherscan_units'],
                                 'from ETH address {addr}'.format(addr=address['account']))

# Now add the tokens from each address

for token in cg.coin_config:
    contract_address = cg.coin_config[token].get('erc20_token_contract_address')
    if contract_address != None:
        api = Tokens(contractaddress=contract_address, api_key=api_key)
        balance = 0
        for address in eth_config['addresses']:
            cg.add_balance(token, int(api.get_token_balance(address=address)) / cg.coin_config[token][
                                             'etherscan_units'], 'from ETH address {addr}'.format(addr=address))

# Coinbase
# pip install coinbase

coinbase_config = cg.config['api_config']['coinbase']

client = cbClient(coinbase_config['api_key'], coinbase_config['api_secret'])
accounts = client.get_accounts()
for account in accounts.data:
    cg.add_balance(account['currency'], float(account['balance']['amount']),
                                 'from Coinbase {addr}'.format(addr=account['name']))

# GDAX
# pip install gdax

gdax_config = cg.config['api_config']['gdax']

gdax_auth_client = gdax.AuthenticatedClient(gdax_config['api_key'], gdax_config['api_secret'], gdax_config['passphrase'])
for account in gdax_auth_client.get_accounts():
    cg.add_balance(account['currency'], float(account['balance']),
                                 'from GDAX {addr}'.format(addr=account['id']))


#Bitfinex
# pip install bitfinex NB the current prod version didn't have the TradeClient class so needed to manually download the bitfinex-develop version

bfx_config = cg.config['api_config']['bitfinex']
bfx_auth_client = bfxClient(bfx_config['api_key'], bfx_config['api_secret'])
for account in bfx_auth_client.balances():
    cg.add_balance(account['currency'].upper(), float(account['amount']),
                                 'from Bitfinex')


#Get BCH from Blockchair
bch_config = cg.config['wallets']['bitcoin-cash']
for address in bch_config['addresses']:
    bch_url = cg.config['api_config']['blockchair']['url'] + '?q=recipient({addr})'.format(addr=address)
    blockchair_result = json.loads(urllib.request.urlopen(bch_url).read())
    cg.add_balance('BCH', int(blockchair_result['data'][0]['value']) / cg.coin_config['BCH']['blockchair_units'],
                                 'from BCH address {addr}'.format(addr=address))

#Write data files
cg.write_dictionary_as_json_file('crypto_balances.json', cg.crypto_balances)

# simplify balances from detail
cg.write_dictionary_as_json_file('crypto_balances_aggregated.json', cg.simplify_balances())
