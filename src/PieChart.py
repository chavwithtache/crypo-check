import os, json
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import matplotlib.dates as dates
import arrow
import seaborn as sns
import cryptolib
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import math

# config
cfg = cryptolib.Config()
coin_config = cfg.coin_config()


# lookback_days = 30
# chart_points = 400
def get_chart_timeseries(root, period='1M', chart_points=400):
    timestamps = []
    totals = []
    # arrow_timestamps = []
    s_files = cryptolib.get_file_series(root).last(period)
    s_files = s_files.iloc[::math.trunc(len(s_files) / chart_points)]
    for datestamp in s_files.index:
        data = json.loads(open(root + '/' + s_files[datestamp]).read())
        # arrow_timestamps.append(arrow.get(datestamp))
        timestamps.append(datestamp)
        totals.append(float(data['data']['total_value'].replace(',', '')))

    # datetimes = [a.datetime for a in arrow_timestamps]
    date_labels = [dt.strftime('%m-%d %H:%M') for dt in timestamps]
    return timestamps, totals, date_labels


def get_value_data_series(data_file, name):
    # Get PIE Data
    crypto_data = json.loads(open(data_file).read())
    crypto_values_raw = crypto_data['data']['values']
    total_value_str = crypto_data['data']['total_value']
    crypto_values = {}

    # Make all Iconomi Funds into a single wedge
    iconomi_value = 0.0
    for coin in crypto_values_raw:
        if coin in coin_config:
            if coin_config.get(coin)['type'] == 'iconomi_fund':
                iconomi_value += crypto_values_raw[coin]
            else:
                crypto_values[coin] = crypto_values_raw[coin]
    crypto_values['ICONOMI'] = iconomi_value
    s = pd.Series(crypto_values)
    s.name = name
    return s, total_value_str, iconomi_value


def get_piechart_data_and_diff(root, period='1D'):
    sFiles = cryptolib.get_file_series(root).last(period)
    from_file = sFiles.iloc[0]
    to_file = sFiles.iloc[-1]
    to_date = sFiles.index[-1]

    s_from, _,_ = get_value_data_series(root + '/' + from_file, 'from')
    s_to, total_value_str,iconomi_value = get_value_data_series(root + '/' + to_file, 'value')
    df = pd.concat([s_from, s_to], axis=1)
    df['change'] = (df['value'] - df['from']) / df['from']
    df.sort_values(by='value', ascending=False, inplace=True)
    df.reset_index(inplace=True)
    df['label'] = df['index'] + str(df['change'])
    df['label'] = df.apply(lambda row: row['index'] + ' ({:.2f}%)'.format(row['change'] * 100), axis=1)
    return df[['label', 'value']].to_dict(orient='records'), total_value_str, iconomi_value, to_date.strftime('%Y-%m-%d %H:%M')


datetimes, totals, date_labels = get_chart_timeseries('../data/archive/crypto_values', '30D')
sorted_data, total_value_str, iconomi_value, timestamp = get_piechart_data_and_diff('../data/archive/crypto_values', '1D')

# Data to plot
labels = []
values = []
gravel_value = 0.0
gravel_labels = []
gravel_values = []
dust_value = 0.0
gravel_max = 4000.0
dust_max = 200.00
for dic in sorted_data:
    value = dic['value']
    label = dic['label']
    if value > gravel_max:
        labels.append(label)
        values.append(int(value))
    elif value > dust_max:
        gravel_value += value
        gravel_labels.append(label)
        gravel_values.append(int(value))
    else:
        dust_value += value

# if gravel_value + dust_value > gravel_max:
labels.append('ALTCOINS')
values.append(int(gravel_value + dust_value))

# if dust_value > 5:
gravel_labels.append('SHITCOINS')
gravel_values.append(int(dust_value))

sns.set_palette("Pastel1", 20)

# with plt.xkcd():
if True:  # below to retain indent
    # plt.rcParams.update({'font.size': 15})
    fig = plt.figure(figsize=(6, 8))
    fig.autofmt_xdate()
    # gs = grd.GridSpec(2, 1, height_ratios=[2, 1])
    # ax1 = plt.subplot(gs[0])
    # ax2 = plt.subplot(gs[1])
    ax1 = fig.add_axes([0.1, 0.44, 0.9, 0.9])  # big pie
    ax2 = fig.add_axes([0.1, 0.1, 0.9, 0.4])
    axMini = fig.add_axes([0.53, 0.89, 0.45, 0.4])

    # ax1.set_title('Total Value: ' + crypto_data['data']['total_value'])  # , bbox={'facecolor': '0.8', 'pad': 3})
    # plt.rcParams.update({'font.size': 14}) #adjust font size; not really needed

    ax1.pie(values,
            labels=labels,
            autopct='%1.1f%%',
            pctdistance=0.8,
            startangle=0)

    ax1.axis('equal')  # ensure pie is round

    axMini.pie(gravel_values,
               labels=gravel_labels,
               autopct='%1.1f%%',
               pctdistance=0.8,
               startangle=0)
    axMini.axis('equal')  # ensure pie is round

    ax2.plot(datetimes, totals, 'royalblue')
    # ax2.set_title('Total Value Over Time (kGBP)')
    ax2.set_title(
        'Total Value: {}   :   Iconomi: {:,.0f}   :   {}'.format(total_value_str, iconomi_value,
                                                                 timestamp), fontdict={'fontsize': 12})
    ax2.get_yaxis().set_major_formatter(tck.FuncFormatter(lambda x, p: format(x / 1000, ',')))

    ax2.xaxis.set_major_formatter(dates.DateFormatter('%d-%b'))

    plt.savefig('../data/crypto_pie.jpg', bbox_inches='tight')

    # short term hack so i can see it!
    plt.savefig('../../../../Google Drive/crypto_pie.jpg', bbox_inches='tight')
    #plt.show()

