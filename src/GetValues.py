# Price Manager
import json
import datetime
import urllib.request



def write_dictionary_as_json_file(filename, dictionary):
    dictionary['timestamp'] = datetime.datetime.now().isoformat()
    with open('../data/' + filename, 'w') as f:
        f.write(json.dumps(dictionary, indent=4))


crypto_data = {'balances': {}, 'prices': {}, 'values': {}}
crypto_prices = crypto_data['prices']
crypto_values = crypto_data['values']

# config
config = json.loads(open('config.json').read())
crypto_balances = json.loads(open('crypto_balances.json').read())['coins']
simple_balances = json.loads(open('crypto_balances_aggregated.json').read())['coins']




cmc_config = config['api_config']['coinmarketcap']
fixer_config = config['api_config']['fixerio']
coin_config = config['coins']

# get crypto prices from coin market cap
display_ccy = cmc_config['display_ccy']
for coin, balance in simple_balances['crypto'].items():
    cmc_id = coin_config[coin]['coinmarketcap_id']
    url = cmc_config['url'] + cmc_id + '?convert=' + display_ccy
    crypto_prices[coin] = float(json.loads(urllib.request.urlopen(url).read())[0]['price_' + display_ccy.lower()])
    crypto_values[coin] = crypto_prices[coin] * balance
    #also write the balance into the output file
    crypto_data['balances'][coin] = balance


# get fiat prices from fixer.io
base_ccy = fixer_config['base_ccy']
url = fixer_config['url'] + '?symbols=' + ','.join([coin for coin in simple_balances['fiat']]) + '&base=' + base_ccy
fxrates = json.loads(urllib.request.urlopen(url).read())

for coin, balance in simple_balances['fiat'].items():
    if coin == base_ccy:
        crypto_prices[coin] = 1
        crypto_values[coin] = balance
    else:
        crypto_prices[coin] = 1 / fxrates['rates'][coin]
        crypto_values[coin] = crypto_prices[coin] * balance
    # also write the balance into the output file
    crypto_data['balances'][coin] = balance


#Try BLX using some dodgy hack
iconomi_config = config['api_config']['iconomi_blx']
usdrate = fxrates['rates']['USD']
for coin, balance in simple_balances['iconomi_fund'].items():
    price_usd = float(json.loads(urllib.request.urlopen(iconomi_config['url']+coin+'-chart').read())['chartData'].pop()['y']['tokenPrice'])
    crypto_prices[coin] = price_usd / usdrate
    crypto_values[coin] = crypto_prices[coin] * balance
    crypto_data['balances'][coin] = balance

values = [crypto_values[x] for x in crypto_values]
total = '{:0,.2f}'.format(sum(values))
print('£' + total)
crypto_data['total_value'] = total
crypto_data['display_ccy'] = display_ccy
write_dictionary_as_json_file('crypto_values.json', crypto_data)

