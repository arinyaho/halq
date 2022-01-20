import yaml
import sys
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

yf.pdr_override()


def main():
    if len(sys.argv) != 2:
        print('Usage: port.py [yml file]')
        sys.exit(1)

    f = sys.argv[1]
    with open(f, 'r') as fin:
        try:
            port = yaml.safe_load(fin)
        except yaml.YAMLError as ex:
            print(ex)
            exit(2)
    prices = {}
    ssum = {}
    strats = port['portfolio']['strategies']
    today = datetime.today()
    for sname, sport in strats.items():
        if sname not in ssum:
            ssum[sname] = 0
        print(sname, sport)
        for ticker, count in sport.items():
            if ticker not in prices:
                data = pdr.get_data_yahoo(ticker, start=today, end=today, progress=False)['Close']
                price = data.iloc[0]
                prices[ticker] = price
            else:
                price = prices[ticker]
            value = price * count
            ssum[sname] += value
    total = sum(list(ssum.values()))

    sportion = {}
    for sname in strats:
        sportion[sname] = 100. * ssum[sname] / total
    print(sportion)

    val = list(sportion.values())
    label = list(sportion.keys())
    plt.pie(val, labels=label, autopct='%.1f%%')
    plt.show() 


if __name__ == '__main__':
    main()