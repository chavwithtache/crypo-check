# Price Manager
import json
import requests
import cryptolib
import asyncio
from aiohttp import ClientSession
import time

val = cryptolib.Valuation()
bal = cryptolib.Balances()

# config
cfg = cryptolib.Config()
wallet_config = cfg.wallet_config()
api_config = cfg.api_config()
#coin_config = cfg.coin_config()

# crypto_balances = json.loads(open('../data/crypto_balances.json').read())['coins']
simple_balances = bal.load_aggregated_balances()

# get crypto prices from coin market cap
cmc_config = api_config['coinmarketcap']
display_ccy = cmc_config['display_ccy']
val.set_display_ccy(display_ccy)

print('start cmc')


class CoinMarketCap(object):
    def __init__(self, base_url: str, display_ccy: str):
        self._base_url = base_url
        self._display_ccy = display_ccy
        self.get_listings()

    def get_listings(self):
        full_url = self._base_url + 'listings/'
        print('{}'.format(full_url))
        listings = requests.get(full_url).json()['data']
        self._coin_lookup = {item['symbol']: item['id'] for item in listings}

    async def get_price(self, session, coin):
        if self._coin_lookup.get(coin):
            full_url = '{}ticker/{}?convert={}'.format(self._base_url, self._coin_lookup[coin], self._display_ccy)
            print('{}: {}'.format(coin, full_url))
            async with session.get(full_url) as response:
                return await response.read()

    def get_lookup(self):
        return self._coin_lookup


class CoinMarketCapOld(object):
    def __init__(self, base_url: str, display_ccy: str):
        self._base_url = base_url
        self._display_ccy = display_ccy
        self._coin_lookup = {}

    async def get_price(self, session, cmc_id, coin):
        self._coin_lookup[cmc_id] = coin
        full_url = self._base_url + cmc_id + '?convert=' + self._display_ccy
        print('{}: {}'.format(coin, full_url))
        async with session.get(full_url) as response:
            return await response.read()

    def get_lookup(self):
        return self._coin_lookup


# cmc = CoinMarketCapOld(cmc_config['url_old'], display_ccy)
cmc = CoinMarketCap(cmc_config['url'], display_ccy)


async def get_multi_prices(cmc, coins):
    tasks = []
    async with ClientSession() as session:
        for coin in coins:
            tasks.append(asyncio.ensure_future(cmc.get_price(session, coin)))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses


coins = [coin for coin in simple_balances['crypto']]
#coins = coins[0:15]
chunk_size = 15
wait_seconds = int(60 / 30 * chunk_size)-1
cmc_coin_chunks_list = [coins[i:i + chunk_size] for i in range(0, len(coins), chunk_size)]

loop = asyncio.get_event_loop()
results = []
print("chunking cmc requests into {} every {}s to make sure I don't get banned for requesting > 30 in 1 minute".format(
    chunk_size, wait_seconds))

for index, cmc_coin_chunk in enumerate(cmc_coin_chunks_list):
    print('getting chunk {} out of {}'.format(index + 1, len(cmc_coin_chunks_list)))
    future = asyncio.ensure_future(get_multi_prices(cmc, cmc_coin_chunk))
    results_raw = loop.run_until_complete(future)
    results_valid = [result for result in results_raw if result]
    print('{} loaded'.format(len(results_valid)))
    results += [json.loads(result)['data'] for result in results_valid]
    if (index + 1) < len(cmc_coin_chunks_list):
        print('waiting {} seconds'.format(wait_seconds))
        time.sleep(wait_seconds)

prices = {item['symbol']: item['quotes'][display_ccy.upper()]['price'] for item in results}
for coin in simple_balances['crypto']:
    price = prices.get(coin, None)
    if price:
        val.add_result(coin, simple_balances['crypto'][coin], float(price))
    else:
        val.add_missing_coin(coin)

print('end cmc')

# get fiat prices from fixer.io
print('start fixer.io')
fixer_config = api_config['fixerio']
base_ccy = fixer_config['base_ccy']
api_key = fixer_config['api_key']
url = fixer_config['url'] + '?symbols={}&access_key={}'.format(
    ','.join(set(list(simple_balances['fiat']) + [base_ccy])), api_key)
print(url)
fxrates_raw = requests.get(url).json()
fixer_base_rate = fxrates_raw['rates'][base_ccy]
fxrates = {key: value / fixer_base_rate for key, value in fxrates_raw['rates'].items()}

for coin, balance in simple_balances['fiat'].items():
    val.add_result(coin, balance, 1 / fxrates[coin])
print('end fixer.io')

# Try BLX using some dodgy hack
print('start iconomi')
iconomi_config = api_config['iconomi_blx']
usdrate = fxrates['USD']
iconomi_value = 0.0
for coin, balance in simple_balances['iconomi_fund'].items():
    print(iconomi_config['url'] + coin + '-chart')
    data = requests.get(iconomi_config['url'] + coin + '-chart').json()['chartData'].pop()['y'][
        'tokenPrice']
    print(data)
    price_usd = float(data)
    iconomi_value += balance * price_usd / usdrate
    val.add_result(coin, balance, price_usd / usdrate)
val.set_iconomi_value(iconomi_value)
print('end iconomi')

print('£' + '{:0,.2f}'.format(val.total_value()))
val.write_valuation()
