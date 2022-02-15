import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from fredapi import Fred


import argparse
import os
import sys
import math
from datetime import datetime, timedelta



yf.pdr_override()

def parse():
    parser = argparse.ArgumentParser(description="Hal-To Quant")
    parser.add_argument('--strategy', '-s', type=str, help='Strategy')
    parser.add_argument('--date', '-d', type=str, help='Rebalancing base date')
    parser.add_argument('--backtest', action='store_true', help='Backtest')
    parser.add_argument('--begin', type=str, help='Backtest begin')
    parser.add_argument('--end', type=str, help='Backtest end')
    parser.add_argument('--list', action='store_true', help='List strategies')
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

def laa(date):
    # 200 days moving average of S&P500 index
    begin = date + timedelta(days=-365)
    spy = pdr.get_data_yahoo('^GSPC', start=begin, end=date, progress=False)['Adj Close']
    spy_ma200 = spy.rolling(window=200).mean()

    if not os.path.exists('fred.api'):
        print('FRED API Key file not found: fred.api')
        sys.exit(1)

    with open('fred.api', 'r') as fin:
        apikey = fin.read()
    
    fred = Fred(api_key=apikey)
    unrate = fred.get_series('UNRATE').tail(15)
    unrate_ma12m = unrate.rolling(window=12).mean()

    choose_shy = spy[-2] < spy_ma200[-2] and unrate[-1] > unrate_ma12m[-1]
    choice = 'SHY' if choose_shy else 'QQQ'

    print("LAA")
    print("  Monthly Rebalancing: QQQ or SHY")
    print("  Yearly Rebalancing: GLD, IWD, IEF, (QQQ or SHY)")
    print("Indicators (%s)" % date)
    print("  S&P500,       MA200: %.2f, %.2f" % (spy[-2], spy_ma200[-2]))
    print("  Unemployment, MA12m: %.2f, %.2f" % (unrate[-1], unrate_ma12m[-1]))
    print("Asset to buy:")
    print("  GLD: 25%")
    print("  IWD: 25%")
    print("  IEF: 25%")
    print("  %s: 25%%" % choice)


def dual_momentum_original(date):
    spy = profit('SPY', date, 365)
    efa = profit('EFA', date, 365)
    bil = profit('BIL', date, 365)
    agg = profit('AGG', date, 365)

    print("Original Dual Momentum: Monthly Rebalancing")
    print("Yearly Profit (%s)" % date)
    print("  SPY: %f" % spy)
    print("  EFA: %f" % efa)
    print("  BIL: %f" % bil)
    print("  AGG: %f" % agg)

    if spy > bil:
        ticker = 'SPY' if spy > efa else 'EFA'
    else:
        ticker = 'AGG'

    print("Asset to buy: %s 100%%" % ticker)


def select_dmo(x):
    asset = pd.Series([0,0], index=['ASSET', 'PRICE'])
    if x['SPY_YoY'] > x['BIL_YoY']:
        asset['ASSET'] = 'SPY' if x['SPY_YoY'] > x['EFA_YoY'] else 'EFA'        
    else:
        asset['ASSET'] = 'AGG'
    asset['PRICE'] = x[asset['ASSET']]
    return asset


def dual_momentum_original_backtest(begin, end):
    begin = begin + timedelta(days=-365)
    spy = pdr.get_data_yahoo('SPY', start=begin, end=end, progress=False)['Adj Close']
    efa = pdr.get_data_yahoo('EFA', start=begin, end=end, progress=False)['Adj Close']
    bil = pdr.get_data_yahoo('BIL', start=begin, end=end, progress=False)['Adj Close']
    agg = pdr.get_data_yahoo('AGG', start=begin, end=end, progress=False)['Adj Close']

    dmo = pd.concat([spy, efa, bil, agg], axis=1).dropna()
    dmo.columns = ['SPY', 'EFA', 'BIL', 'AGG']

    # Takes only last day of each month
    dmo = dmo.resample(rule='M').apply(lambda x: x[-1])
    dmo_after = dmo.shift(periods=-12, axis=0)
    
    # YoY
    dmo_yoy = dmo_after / dmo - 1.
    dmo_yoy = dmo_yoy.shift(periods=12, axis=0).dropna()
    dmo[['SPY_YoY', 'EFA_YoY', 'BIL_YoY', 'AGG_YoY']] = dmo_yoy
    dmo[['Asset', 'Price']] = dmo.apply(lambda x: select_dmo(x), axis=1)
    dmo = dmo.dropna()
    
    dmo['Profit'] = 0
    dmo['Profit_acc'] = 1

    for i in range(len(dmo)):
        profit = 0
        if i != 0:
            asset_before = dmo.iloc[i-1]['Asset']
            profit_acc_before = dmo.iloc[i-1]['Profit_acc']
            profit = dmo.iloc[i][asset_before] / dmo.iloc[i-1][asset_before] - 1.
            dmo.loc[dmo.index[i], 'Profit'] = profit
            dmo.loc[dmo.index[i], 'Profit_acc'] = profit_acc_before * (1 + profit)
    
    ## MDD
    dmo['dd'] = (dmo['Profit_acc'].cummax() - dmo['Profit_acc']) / dmo['Profit_acc'].cummax()
    dmo.to_csv('test.csv')
    print(len(dmo))
    print('Start: %s' % dmo.index[0].strftime('%Y-%m-%d'))
    print('End  : %s' % dmo.index[-1].strftime('%Y-%m-%d'))
    print('APR: %.3f' % (dmo['Profit_acc'][-1] ** (1. / (len(dmo) / 12)) - 1))
    print('MDD: %.3f' % dmo['dd'].max())

def main():
    args = parse()
    
    fundic = {
        ('dmo', False): dual_momentum_original,
        ('dmo', True): dual_momentum_original_backtest,
        ('laa', False): laa
    }

    try:
        if args.backtest:
            b = datetime.strptime(args.begin, '%Y%m%d')
            e = datetime.strptime(args.end, '%Y%m%d')
            fundic[(args.strategy.lower(), True)](b, e)
        else:
            date = datetime.now() if args.date is None else args.date
            fundic[(args.strategy.lower(), False)](date)
    except KeyError:
        print('Strategy not supported: %s' % args.strategy)

if __name__ == '__main__':
    main()
