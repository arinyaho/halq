import yaml
import sys
import math
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

yf.pdr_override()


def main():
    if len(sys.argv) != 3:
        print('Usage: port.py [dollar] [port yaml]')
        sys.exit(1)

    cash = int(sys.argv[1])
    f = sys.argv[2]
    with open(f, 'r') as fin:
        try:
            port = yaml.safe_load(fin)
        except yaml.YAMLError as ex:
            print(ex)
            exit(2)
    
    today = datetime.today()

    prices = {}

    strats = port['portfolio']['strategies']
    for sname in strats:
        strat = strats[sname]
        portion = float(strat['Portion']) / 100
        scash = cash * portion
        print(sname + ": " + "$" + str(scash))
        res = {}
        tickers = strat['Tickers']
        for ticker in tickers:
            tportion = float(tickers[ticker]) / 100
            tcash = scash * tportion
            if tportion == 0:
                pass
            if ticker not in prices:
                data = pdr.get_data_yahoo(ticker, start=today, end=today, progress=False)['Close']
                price = data.iloc[0]
                prices[ticker] = price
            else:
                price = prices[ticker]
            tcount = math.floor(tcash / price)
            if tcount != 0:
                print('\t', ticker, tcount)



if __name__ == '__main__':
    main()