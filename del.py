import csv

with open("sample.csv") as f:
    x = csv.DictReader(f)

    for i in x:
        print(i)
