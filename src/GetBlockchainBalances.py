import urllib.request
from etherscan.tokens import Tokens
from etherscan.accounts import Account
import json
import cryptolib


# config
cfg = cryptolib.Config()
wallet_config = cfg.wallet_config()
api_config = cfg.api_config()
coin_config = cfg.coin_config()

bal = cryptolib.Balances()

# Ethereum Manager
# pip install etherscan

eth_config = wallet_config['ethereum']
api_key = api_config['etherscan']['api_key']

# get the simple ETH balances for each address
print('start etherscan')
api = Account(address=eth_config['addresses'], api_key=api_key)
for address in api.get_balance_multiple():
    print(address)
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

#Get BCH from Blockchair
print('start blockchair')
bch_config = wallet_config['bitcoin-cash']
for address in bch_config['addresses']:
    bch_url = api_config['blockchair']['url'] + '?q=recipient({addr})'.format(addr=address)
    print(bch_url)
    blockchair_result = json.loads(urllib.request.urlopen(bch_url).read())
    print(blockchair_result)
    bal.add_balance('BCH', int(blockchair_result['data'][0]['value']) / coin_config['BCH']['blockchair_units'],
                                 'from BCH address {addr}'.format(addr=address))
print('end blockchair')

#Write data files
bal.write_balances('blockchain_balances')

