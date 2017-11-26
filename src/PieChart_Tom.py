import os, json
#import matplotlib.pyplot as plt
#import matplotlib.ticker as tck
#import matplotlib.dates as dates
import arrow
import seaborn as sns
import pandas as pd

arrow_timestamps = []
totals = []
#lookback_days = 4
chart_points = 400

# get appropriate number of points for chart for date range
'2017-11-23T142908_crypto_values.json'

start_time = arrow.get('2017-11-23T14:29:00')

files_to_process = [filename for filename in
                    os.listdir('../data/archive/crypto_values')
                    if filename.endswith("_crypto_values.json")
                    and (arrow.get(filename[0:13]+':'+filename[13:15]+':'+filename[15:17])) >= start_time]

files_to_process.sort()
files_to_process = files_to_process[::-max(1, int(round(len(files_to_process) / chart_points, 0)))]
files_to_process.sort()

timeseries_data = {}

# def testthis(myRow):


for filename in files_to_process:
    data = json.loads(open('../data/archive/crypto_values/' + filename).read())
    data_date = arrow.get(data['timestamp']).datetime  # data['timestamp']#
    timeseries_data[data_date] = data['data']['values']

df = pd.DataFrame(timeseries_data) * 0.022
# df = df.transpose()
df.sort_values(by=df.columns.max(), inplace=True, axis=0, ascending=False)
df['row'] = range(0, len(df))
df['ccy'] = df.index
# Add column for groupBy
df['group'] = df.apply(lambda x: x['ccy'] if x['row'] < 5 else 'OTHER', axis=1)
df.drop(['ccy', 'row'], axis=1, inplace=True)
df = df.groupby(by='group', sort=False, group_keys=True).sum().transpose()

# df['Total']=df.sum(axis=1)
# df
# DataFrame.sort_values(by, axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')

# df.columns()
current_value = df.iloc[-1:].sum().sum()
plt = df.plot.area(figsize=(12, 8))
plt.set_title('Current value: £{:,.0f}                 {}'.format(current_value,df.iloc[-1:].index[0].strftime('%Y-%m-%d %H:%M:%S')),fontdict ={'fontsize':18})
plt.tick_params(axis='both', which='major', labelsize=14)
plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))

fig = plt.get_figure()
fig.savefig('../data/crypto_chart_tom.jpg', bbox_inches='tight')
fig.savefig('../../../../Google Drive/Tom/crypto_chart_tom.jpg', bbox_inches='tight')