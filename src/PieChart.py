import matplotlib.pyplot as plt
import json

crypto_data = json.loads(open('../data/crypto_values.json').read())
crypto_values = crypto_data['values']

#sort the data by value - there must be a better way!
tuples = crypto_values.items()
sorted_data = sorted(zip([y for _,y in tuples],[x for x,_ in tuples]), reverse=True)

# Data to plot
labels = []
values = []

for value, label in sorted_data:
    if value > 1:
        labels.append(label)
        values.append(int(value))
with plt.xkcd():
    fig = plt.figure(figsize=(11,6))
    ax = fig.add_axes((0, 0, .9, .9))
    ax.set_title('Total Value: ' + crypto_data['total_value'],
                 bbox={'facecolor': '0.8', 'pad': 3})
    plt.rcParams.update({'font.size': 14}) #adjust font size; not really needed

    plt.pie(values,
            labels=labels,
            autopct='%1.1f%%',
            pctdistance = 0.8,
            startangle=0)

    plt.axis('equal') #ensure pie is round
    plt.savefig('../data/crypto_pie.jpg', bbox_inches='tight')

    #short term hack so i can see it!
    plt.savefig('../../../../Google Drive/crypto_pie.jpg', bbox_inches='tight')
    #plt.show()
    