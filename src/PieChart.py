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


def get_series_from_data(data_file, data_item, name):
    crypto_data = json.loads(open(data_file).read())
    crypto_values_raw = crypto_data['data'][data_item]
    s = pd.Series(crypto_values_raw)
    s.name = name
    return s


# def get_value_data_series(data_file, name):
#     # Get PIE Data
#     crypto_data = json.loads(open(data_file).read())
#     crypto_values_raw = crypto_data['data']['values']
#     total_value_str = crypto_data['data']['total_value']
#     crypto_values = {}
#
#     # Make all Iconomi Funds into a single wedge
#     iconomi_value = 0.0
#     for coin in crypto_values_raw:
#         if coin in coin_config:
#             if coin_config.get(coin)['type'] == 'iconomi_fund':
#                 iconomi_value += crypto_values_raw[coin]
#             else:
#                 crypto_values[coin] = crypto_values_raw[coin]
#     crypto_values['ICONOMI'] = iconomi_value
#     s = pd.Series(crypto_values)
#     s.name = name
#     return s, total_value_str, iconomi_value


def get_piechart_data_and_diff(root, period='1D'):
    s_files = cryptolib.get_file_series(root).last(period)
    from_file = s_files.iloc[0]
    to_file = s_files.iloc[-1]
    to_date = s_files.index[-1]

    s_balances_t = get_series_from_data(root + '/' + to_file, 'balances', 'balances_t')
    s_prices_t = get_series_from_data(root + '/' + to_file, 'prices', 'prices_t')
    s_prices_t_1 = get_series_from_data(root + '/' + from_file, 'prices', 'prices_t_1')
    df = pd.concat([s_balances_t, s_prices_t, s_prices_t_1], axis=1)
    df['is_iconomi'] = [coin_config[coin]['type'] == 'iconomi_fund' for coin in list(df.index)]
    df['value'] = df['balances_t'] * df['prices_t']
    df['value_t1_prices'] = df['balances_t'] * df['prices_t_1']
    df['move_from_prices'] = df['value'] - df['value_t1_prices']
    total_value = df['value'].sum(axis=0)
    total_value_str = '{:0,.0f}'.format(total_value)
    # roll up iconomi funds
    s_iconomi = df[df['is_iconomi'] == True].sum(axis=0)
    s_iconomi.name = 'ICONOMI'
    iconomi_value = s_iconomi['value']
    df = df[df['is_iconomi'] == False].append(s_iconomi)
    # this is everything with iconomi rolled up to a single item.
    # next do a new df for ALTS
    gravel_max = total_value / 100
    dust_max = gravel_max / 10
    df['value_category'] = df.apply(
        lambda row: 'DUST' if row['value'] < dust_max else 'GRAVEL' if row['value'] < gravel_max else 'MAIN', axis=1)
    df_main = df[df['value_category'] == 'MAIN']
    df_gravel = df[df['value_category'] == 'GRAVEL']
    s_dust_total = df[df['value_category'] == 'DUST'].sum(axis=0)

    s_gravel_plus_dust_total = df_gravel.sum(axis=0) + s_dust_total
    s_gravel_plus_dust_total.name = 'ALTS'
    df_main = df_main.append(s_gravel_plus_dust_total)

    s_dust_total.name = 'DUST'
    df_gravel = df_gravel.append(s_dust_total)

    main_pie_data = finalise_chart_data(df_main, 'ALTS')
    gravel_pie_data = finalise_chart_data(df_gravel, 'DUST')
    return main_pie_data, gravel_pie_data, total_value_str, iconomi_value, to_date.strftime('%Y-%m-%d %H:%M')


def finalise_chart_data(df, last=None):
    df['change'] = df['move_from_prices'] / df['value_t1_prices']

    df.sort_values(by='value', ascending=False, inplace=True)
    if last:
        new_index = list(df.index)
        new_index.remove(last)
        new_index = new_index + [last]
        df = df.reindex(new_index)
    df.reset_index(inplace=True)
    df['label'] = df['index'] + str(df['change'])
    df['label'] = df.apply(lambda row: row['index'] + ' ({:.2f}%)'.format(row['change'] * 100), axis=1)
    return df[['label', 'value']].to_dict(orient='list')


datetimes, totals, date_labels = get_chart_timeseries('../data/archive/crypto_values', '30D')
main_pie_data, gravel_pie_data, total_value_str, iconomi_value, timestamp = get_piechart_data_and_diff(
    '../data/archive/crypto_values',
    '1D')

sns.set_palette("Pastel1", 20)

# with plt.xkcd():
if True:  # below to retain indent
    # plt.rcParams.update({'font.size': 15})
    fig = plt.figure(figsize=(6, 8))
    fig.autofmt_xdate()
    # gs = grd.GridSpec(2, 1, height_ratios=[2, 1])
    # ax1 = plt.subplot(gs[0])
    # ax2 = plt.subplot(gs[1])
    ax1 = fig.add_axes([0.05, 0.44, 0.9, 0.9])  # big pie
    ax2 = fig.add_axes([0.1, 0.1, 0.95, 0.4])
    axMini = fig.add_axes([0.53, 0.89, 0.45, 0.4])

    # ax1.set_title('Total Value: ' + crypto_data['data']['total_value'])  # , bbox={'facecolor': '0.8', 'pad': 3})
    # plt.rcParams.update({'font.size': 14}) #adjust font size; not really needed

    ax1.pie(main_pie_data['value'],
            labels=main_pie_data['label'],
            autopct='%1.1f%%',
            pctdistance=0.8,
            startangle=0)

    ax1.axis('equal')  # ensure pie is round

    axMini.pie(gravel_pie_data['value'],
               labels=gravel_pie_data['label'],
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
    # plt.show()
