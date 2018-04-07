# Price Manager
import json
import urllib.request
import cryptolib



val = cryptolib.Valuation()
bal = cryptolib.Balances()

# config
cfg = cryptolib.Config()
wallet_config = cfg.wallet_config()
api_config = cfg.api_config()
coin_config = cfg.coin_config()

#crypto_balances = json.loads(open('../data/crypto_balances.json').read())['coins']
simple_balances = bal.load_aggregated_balances()

# get crypto prices from coin market cap
cmc_config = api_config['coinmarketcap']
display_ccy = cmc_config['display_ccy']
val.set_display_ccy(display_ccy)


print('start cmc')
cmc = cryptolib.CoinMarketCap(cmc_config['url'], display_ccy)
for coin, balance in simple_balances['crypto'].items():
    #if we have a coin thats not defined in config, add to missing coin section
    coin_config_coin = coin_config.get(coin)
    if coin_config_coin:
        cmc_id = coin_config_coin['coinmarketcap_id']
        price = cmc.get_price(cmc_id)
        val.add_result(coin, balance, float(price))
    else:
        val.add_missing_coin(coin)
print('end cmc')

# get fiat prices from fixer.io
print('start fixer.io')
fixer_config = api_config['fixerio']
base_ccy = fixer_config['base_ccy']
url = fixer_config['url'] + '?symbols=' + ','.join([coin for coin in simple_balances['fiat']]) + '&base=' + base_ccy
print(url)
fxrates = json.loads(urllib.request.urlopen(url).read())
fxrates['rates'][base_ccy] = 1
for coin, balance in simple_balances['fiat'].items():
    val.add_result(coin, balance, 1 / fxrates['rates'][coin])
print('end fixer.io')

#Try BLX using some dodgy hack
print('start iconomi')
iconomi_config = api_config['iconomi_blx']
usdrate = fxrates['rates']['USD']
iconomi_value = 0.0
for coin, balance in simple_balances['iconomi_fund'].items():
    print(iconomi_config['url']+coin+'-chart')
    data=json.loads(urllib.request.urlopen(iconomi_config['url']+coin+'-chart').read())['chartData'].pop()['y']['tokenPrice']
    print(data)
    price_usd = float(data)
    iconomi_value += balance * price_usd / usdrate
    val.add_result(coin, balance, price_usd / usdrate)
val.set_iconomi_value(iconomi_value)
print('end iconomi')

print('£' + '{:0,.2f}'.format(val.total_value()))
val.write_valuation()

