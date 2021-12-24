import FinanceDataReader as fdr
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
import argparse
from datetime import datetime, timedelta

yf.pdr_override()

def parse():
    parser = argparse.ArgumentParser(description="Hal-To Quant")
    parser.add_argument('--strategy', '-s', type=str, help='Strategy')
    parser.add_argument('--date', '-d', type=str, help='Rebalancing base date')
    parser.add_argument('--backtest', action='store_true', help='Backtest')
    parser.add_argument('--begin', type=str, help='Backtest begin')
    parser.add_argument('--end', type=str, help='Backtest end')
    return parser.parse_args()


def profit(ticker, date, dayOffset):
    e = date
    if type(e) == str:
        e = datetime.strptime(e, '%Y-%m-%d')
    b = e + timedelta(days=-dayOffset)
    spy = fdr.DataReader(ticker, b, e)
    f = spy.head(1).iloc[0]['Close']
    r = spy.tail(1).iloc[0]['Close']
    return r/f - 1.


def dual_momentum_original(date):
    spy = profit('SPY', date, 365)
    efa = profit('EFA', date, 365)
    bil = profit('BIL', date, 365)

    print("Original Dual Momentum: Monthly Rebalancing")
    print("Yearly Profit (%s)" % date)
    print("  SPY: %f" % spy)
    print("  EFA: %f" % efa)
    print("  BIL: %f" % bil)

    if spy > bil:
        ticker = 'SPY' if spy > efa else 'EFA'
    else:
        ticker = 'AGG'

    print("Asset to buy: %s 100%%" % ticker)


def select_dmo(x):
    asset = pd.Series([0,0], index=['ASSET', 'PRICE'])
    if x['SPY_YoY'] > x['BIL_YoY']:
        asset['ASSET'] = 'SPY' if x['SPY_YoY'] > x['EFA_YoY'] else 'EFA'
        asset['PRICE'] = x[asset['ASSET']]
    return asset


def dual_momentum_original_backtest(begin, end):
    begin = begin + timedelta(days=-365)
    spy = pdr.get_data_yahoo('SPY', start=begin, end=end, progress=False)['Adj Close']
    efa = pdr.get_data_yahoo('EFA', start=begin, end=end, progress=False)['Adj Close']
    bil = pdr.get_data_yahoo('BIL', start=begin, end=end, progress=False)['Adj Close']
    dmo = pd.concat([spy, efa, bil], axis=1).dropna()
    dmo.columns = ['SPY', 'EFA', 'BIL']

    # Takes only last day of each month
    dmo = dmo.resample(rule='M').apply(lambda x: x[-1])
    dmo_after = dmo.shift(periods=-12, axis=0)
    
    # YoY
    dmo_yoy = dmo_after / dmo - 1.
    dmo_yoy = dmo_yoy.shift(periods=12, axis=0).dropna()
    dmo[['SPY_YoY', 'EFA_YoY', 'BIL_YoY']] = dmo_yoy
    dmo[['ASSET', 'PRICE']] = dmo.apply(lambda x: select_dmo(x), axis=1)
    

def main():
    args = parse()
    if args.strategy == 'dmo':
        if args.backtest:
            b = datetime.strptime(args.begin, '%Y%m%d')
            e = datetime.strptime(args.end, '%Y%m%d')
            dual_momentum_original_backtest(b, e)
        else:
            if args.date is None:
                date = datetime.now()
            else:
                date = args.date
            dual_momentum_original(date)
    else:
        print('Strategy not supported: %s' % args.strategy)

if __name__ == '__main__':
    main()
