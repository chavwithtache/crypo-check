import os
import json

root = 'C:/Users/Ben/dev/python/crypo-check/'


def calc_value(balances, prices):
    # missing coin in value just adds zero
    total_value = 0.0
    for coin in balances:
        total_value += balances[coin] * prices.get(coin, 0)
    return total_value


def output_data(comment, from_file, currentData, latest_value):
    prevData = json.loads(open(root + from_file).read())['data']
    start_value = calc_value(prevData['balances'], prevData['prices'])
    nontrad_value = calc_value(prevData['balances'], currentData['prices'])
    tradepl = latest_value - nontrad_value
    print(comment)
    print('value at start          : £{:,.2f}'.format(start_value))
    print('value now if no trading : £{:,.2f}'.format(nontrad_value))
    print('trading p&l             : £{:,.2f}\n'.format(tradepl))


from_dec = 'data/archive/crypto_values/2017-12-01T060200_crypto_values.json'
from_jan = 'data/archive/crypto_values/2018-01-01T060016_crypto_values.json'
from_feb = 'data/archive/crypto_values/2018-02-01T060018_crypto_values.json'

currentData = json.loads(open(root + 'data/crypto_values.json').read())['data']
latest_value = calc_value(currentData['balances'], currentData['prices'])
print('Current value           : £{:,.2f}\n'.format(latest_value))

output_data('from Dec', from_dec, currentData, latest_value)
output_data('from Jan', from_jan, currentData, latest_value)
output_data('from Feb', from_feb, currentData, latest_value)
