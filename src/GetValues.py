# Price Manager
import json
import urllib.request
import crypto_globals

crypto_data = {'balances': {}, 'prices': {}, 'values': {}}

# config
config = json.loads(open('../config/config.json').read())
coin_config = config['coins']

crypto_balances = json.loads(open('../data/crypto_balances.json').read())['coins']
simple_balances = json.loads(open('../data/crypto_balances_aggregated.json').read())['coins']

# get crypto prices from coin market cap
cmc_config = config['api_config']['coinmarketcap']
display_ccy = cmc_config['display_ccy']
for coin, balance in simple_balances['crypto'].items():
    cmc_id = coin_config[coin]['coinmarketcap_id']
    url = cmc_config['url'] + cmc_id + '?convert=' + display_ccy
    crypto_data = crypto_globals.add_result(crypto_data, coin, balance, float(json.loads(urllib.request.urlopen(url).read())[0]['price_' + display_ccy.lower()]))


# get fiat prices from fixer.io
fixer_config = config['api_config']['fixerio']
base_ccy = fixer_config['base_ccy']
url = fixer_config['url'] + '?symbols=' + ','.join([coin for coin in simple_balances['fiat']]) + '&base=' + base_ccy
fxrates = json.loads(urllib.request.urlopen(url).read())
fxrates['rates'][base_ccy] = 1
for coin, balance in simple_balances['fiat'].items():
    crypto_data = crypto_globals.add_result(crypto_data, coin, balance, 1 / fxrates['rates'][coin])


#Try BLX using some dodgy hack
iconomi_config = config['api_config']['iconomi_blx']
usdrate = fxrates['rates']['USD']
for coin, balance in simple_balances['iconomi_fund'].items():
    price_usd = float(json.loads(urllib.request.urlopen(iconomi_config['url']+coin+'-chart').read())['chartData'].pop()['y']['tokenPrice'])
    crypto_data = crypto_globals.add_result(crypto_data, coin, balance, price_usd / usdrate)


values = [crypto_data['values'][x] for x in crypto_data['values']]
total = '{:0,.2f}'.format(sum(values))
print('£' + total)
crypto_data['total_value'] = total
crypto_data['display_ccy'] = display_ccy
crypto_globals.write_dictionary_as_json_file('crypto_values.json', crypto_data)

