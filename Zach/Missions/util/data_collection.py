
import csv

def save_data(tx, ty, tz, obs, filename='data/data.csv'):
    data = [tx, ty, tz]
    for ob in obs:
        data.append(ob[1][0])
        data.append(ob[1][1])

    with open(filename, 'a', newline='') as f_data:
        wr = csv.writer(f_data, quoting=csv.QUOTE_ALL)
        wr.writerow(data)

def save_labels(pitch, yaw, f, filename='data/labels.csv'):
    with open(filename, 'a', newline='') as f_labels:
        wr = csv.writer(f_labels, quoting=csv.QUOTE_ALL)
        wr.writerow([pitch, yaw, f])
