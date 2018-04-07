import requests
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
api_key = api_config['ethplorer']['api_key']
url_root = api_config['ethplorer']['url']
# get the simple ETH balances for each address
print('start ethplorer')
for eth_address in eth_config['addresses']:
    req = requests.get('{}getAddressInfo/{}?apiKey={}'.format(url_root, eth_address, api_key))
    if req.ok:
        data = req.json()
        bal.add_balance('ETH', data['ETH']['balance'],
                        'from ETH address {}'.format(eth_address))
        for token in data['tokens']:
            token_info = token['tokenInfo']
            if token_info['symbol'] != '':
                bal.add_balance(token_info['symbol'], token['balance'] / (10 ** int(token_info['decimals'])),
                                'from ETH address {}'.format(eth_address))
            elif token_info['name'] != '':
                bal.add_balance(token_info['name'], token['balance'] / (10 ** int(token_info['decimals'])),
                                'from ETH address {}. NO SYMBOL. DODGY.'.format(eth_address))
print('end ethplorer')

#Get BCH from Blockchair
print('start blockchair')
bch_config = wallet_config['bitcoin-cash']
for address in bch_config['addresses']:
    bch_url = api_config['blockchair']['url'] + '?q=recipient({addr})'.format(addr=address)
    print(bch_url)
    blockchair_result = requests.get(bch_url).json()
    print(blockchair_result)
    bal.add_balance('BCH', int(blockchair_result['data'][0]['value']) / coin_config['BCH']['blockchair_units'],
                                 'from BCH address {addr}'.format(addr=address))
print('end blockchair')

#Write data files
bal.write_balances('blockchain_balances')

