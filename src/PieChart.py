import os, json
import matplotlib.pyplot as plt
import arrow

data = []
for filename in os.listdir('../data/archive'):
    if filename.endswith("_crypto_values.json"):
        data.append(json.loads(open('../data/archive/' + filename).read()))
        continue

arrow_timestamps = []
totals = []
for item in data:
    arrow_timestamps.append(arrow.get(item['timestamp']))
    totals.append(float(item['total_value'].replace(',', '')))

datetimes = [a.datetime for a in arrow_timestamps]
date_labels = [a.format('MM-DD HH:MM') for a in arrow_timestamps]

# Get PIE Data
crypto_data = json.loads(open('../data/crypto_values.json').read())
crypto_values = crypto_data['values']

# sort the data by value - there must be a better way!
tuples = crypto_values.items()
sorted_data = sorted(zip([y for _, y in tuples], [x for x, _ in tuples]), reverse=True)

# Data to plot
labels = []
values = []

for value, label in sorted_data:
    if value > 1:
        labels.append(label)
        values.append(int(value))

with plt.xkcd():
    plt.rcParams.update({'font.size': 12})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 13))
    # fig.set_size_inches(8,6)

    # ax = fig.add_axes((0, 0, .9, .9))
    ax1.set_title('Total Value: ' + crypto_data['total_value'])  # , bbox={'facecolor': '0.8', 'pad': 3})
    # plt.rcParams.update({'font.size': 14}) #adjust font size; not really needed

    ax1.pie(values,
            labels=labels,
            autopct='%1.1f%%',
            pctdistance=0.8,
            startangle=0)

    ax1.axis('equal')  # ensure pie is round

    ax2.plot(datetimes, totals)
    ax2.set_title('Total Value Over Time')
    #ax2.set_xticklabels(date_labels, rotation=90)

    plt.xticks(rotation=90)
    plt.show()

    plt.savefig('../data/crypto_pie.jpg', bbox_inches='tight')

    #short term hack so i can see it!
    plt.savefig('../../../../Google Drive/crypto_pie.jpg', bbox_inches='tight')
    #plt.show()
