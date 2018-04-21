import os, json
import arrow
import seaborn as sns
# import numpy as np
import pandas as pd
import cryptolib

cfg = cryptolib.Config()
coin_config = cfg.coin_config()

def generate_area_chart(files_to_process, multiplier=1.0, y_bottom=0.0):
    # arrow_timestamps = []
    # totals = []
    chart_points = 400

    files_to_process.sort()
    files_to_process = files_to_process[::-max(1, int(round(len(files_to_process) / chart_points, 0)))]
    files_to_process.sort()

    timeseries_data = {}

    for filename in files_to_process:
        data = json.loads(open('../data/archive/crypto_values/' + filename).read())
        data_date = arrow.get(data['timestamp']).datetime  # data['timestamp']#
        timeseries_data[data_date] = data['data']['values']

    df = pd.DataFrame(timeseries_data) * multiplier
    # df = df.transpose()
    # Add column for Iconomi
    is_iconomi=[]
    for coin in list(df.index):
        if coin in coin_config:
            is_iconomi.append(coin_config[coin]['type'] == 'iconomi_fund')
        else:
            is_iconomi.append(False)
    df['is_iconomi'] = is_iconomi

    s_iconomi = df[df['is_iconomi'] == True].sum(axis=0)
    s_iconomi.name = 'ICONOMI'
    df = df[df['is_iconomi'] == False].append(s_iconomi)
    del(df['is_iconomi'])
    df.sort_values(by=df.columns.max(), inplace=True, axis=0, ascending=False)
    df['row'] = range(0, len(df))
    df['ccy'] = df.index

    # Add column for groupBy
    df['group'] = df.apply(lambda x: x['ccy'] if x['row'] < 7 else 'OTHER', axis=1)
    df.drop(['ccy', 'row'], axis=1, inplace=True)
    df = df.groupby(by='group', sort=False, group_keys=True).sum().transpose()
    df.index = pd.to_datetime(df.index)
    df = df.resample(rule='12H').last().ffill()

    # df.columns()
    current_value = df.iloc[-1:].sum().sum()
    ts_yesterday = arrow.get(df.iloc[-1:].index[0]).shift(days=-1, minutes=10).datetime
    previous_value = df.loc[df.index.asof(ts_yesterday)].sum()
    move = (current_value - previous_value) / previous_value
    move_direction = 'up' if move > 0 else 'down'

    sns.set_palette("spectral", 8)
    plt = df.plot.area(figsize=(12, 8), alpha=0.4)
    plt.set_title('Current value: £{:,.2f} ({} {:0.4f}% in 24h)               {}'.format(current_value, move_direction,
                                                                                         move * 100,
                                                                                         df.iloc[-1:].index[0].strftime(
                                                                                             '%Y-%m-%d %H:%M:%S')),
                  fontdict={'fontsize': 18})
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.set_axisbelow(False)
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='lightgrey', alpha=0.6)
    plt.axes.set_ylim(bottom=y_bottom)
    return plt.get_figure()


# Do Toms & Doms & Mabel:
start_time = arrow.get('2017-11-23T14:29:00')
files_to_process = [filename for filename in
                    os.listdir('../data/archive/crypto_values')
                    if filename.endswith("_crypto_values.json")
                    and (arrow.get(filename[0:13] + ':' + filename[13:15] + ':' + filename[15:17])) >= start_time]
# Tom
fig = generate_area_chart(files_to_process, 0.00366, 0.0)
fig.savefig('../data/crypto_chart_tom.jpg', bbox_inches='tight')
fig.savefig('../../../../Google Drive/Tom/crypto_chart_tom.jpg', bbox_inches='tight')
# Dom
fig = generate_area_chart(files_to_process, 0.0000044, 0.0)
fig.savefig('../data/crypto_chart_dominic.jpg', bbox_inches='tight')
fig.savefig('../../../../Google Drive/Tom/crypto_chart_dominic.jpg', bbox_inches='tight')
# Mabel
fig = generate_area_chart(files_to_process, 0.00044, 0.0)
fig.savefig('../data/crypto_chart_mabel.jpg', bbox_inches='tight')
fig.savefig('../../../../Google Drive/Mabel/crypto_chart_mabel.jpg', bbox_inches='tight')
# Do Bens:
lookback_days = 90
files_to_process = [filename for filename in
                    os.listdir('../data/archive/crypto_values')
                    if filename.endswith("_crypto_values.json")
                    and (arrow.now() - arrow.get(filename[0:10])).days < lookback_days]

fig = generate_area_chart(files_to_process, 1.0, 0.0)
fig.savefig('../data/crypto_chart_ben.jpg', bbox_inches='tight')
fig.savefig('../../../../Google Drive/crypto_chart_ben.jpg', bbox_inches='tight')
