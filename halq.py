import FinanceDataReader as fdr
import dart_fss as dart
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
from fredapi import Fred

from etf.vaa_a import VAA_A
from etf.laa import LAA

import abc
import argparse
import os
import sys
import math
from datetime import datetime, timedelta

yf.pdr_override()


def dispaly_figure(data, title):
    capr = plt.figure(1)
    capr.suptitle(f"{title} Growth")    
    data['Growth'].plot.line()

    mdd = plt.figure(2)
    mdd.suptitle(f"{title} MDD")
    (data['dd'] * 100).plot.line(color='red')

    plt.show()


def parse():
    parser = argparse.ArgumentParser(description="Hal-To Quant")
    parser.add_argument('--strategy', '-s', type=str, help='Strategy')
    parser.add_argument('--date', '-d', type=str, help='Rebalancing base date in YYYYMMDD format')
    parser.add_argument('--backtest', action='store_true', help='Backtest')
    parser.add_argument('--begin', type=str, help='Backtest begin date in YYYYMMDD format')
    parser.add_argument('--end', type=str, help='Backtest end date in YYYYMMDD format')
    parser.add_argument('--rebalance-month', type=int, default=1, choices=range(1, 13), help='Month for rebalancing asset allocation')
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


def dual_momentum_original_backtest(begin, end, rebalance_month=1):
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
    dmo['dd'] = -1 * (dmo['Profit_acc'].cummax() - dmo['Profit_acc']) / dmo['Profit_acc'].cummax()
    print('Start: %s' % dmo.index[0].strftime('%Y-%m-%d'))
    print('End  : %s' % dmo.index[-1].strftime('%Y-%m-%d'))
    print('CAPR: %.3f' % (((dmo['Profit_acc'][-1] ** (1. / (len(dmo) / 12)) - 1)) * 100))
    print('MDD: %.3f' % (dmo['dd'].min() * 100))

    dmo.to_excel('dmo_backtest.xlsx')

    capr = plt.figure(1)
    capr.suptitle("Original Dual Momentum Growth")    
    dmo['Profit_acc'].plot.line()

    mdd = plt.figure(2)
    mdd.suptitle("Original Dual Momentum MDD")
    (dmo['dd'] * 100).plot.line(color='red')

    plt.show()

def hq_ultra():
    if not os.path.exists('dart.api'):
        print('DART API Key file not found: dart.api')
        sys.exit(1)

    with open('dart.api', 'r') as fin:
        apikey = fin.read()
    
    print(apikey)
    dart.set_api_key(api_key=apikey)
    clist = dart.get_corp_list()
    print(clist)

def list_strategies():
    print('List of Strategies')
    print('  laa       Lethargic Asset Allocation')
    print('  vaa-a     Vigilant Asset Allocation Aggresive')
    print('  dmo       Original Dual Momentum')


def main():
    # hq_ultra()
    # sys.exit(2)

    args = parse()
    
    fundic = {
        ('dmo', False): dual_momentum_original,
        ('dmo', True): dual_momentum_original_backtest
    }

    clsdic = {
        'laa': LAA,
        'vaa-a': VAA_A
    }

    sfullname = {
        'laa': 'Lethargic Asset Allocation',
        'vaa-a': 'Vigilant Asset Allocation Aggresive'
    }

    if (args.list):
        list_strategies()
        sys.exit(0)

    sname = args.strategy.lower()

    if (sname, args.backtest) not in fundic and sname not in clsdic:
        print('Strategy not supported: %s' % args.strategy)
        sys.exit(1)

    if sname in clsdic:
        q = clsdic[sname]()
        if args.backtest:
            b = datetime.strptime(args.begin, '%Y%m%d')
            e = datetime.strptime(args.end, '%Y%m%d')            
            data = q.backtest(b, e, rebalance_month=args.rebalance_month)
            days = (e - b).days
            growth = data['Growth'][-1]
            print('Start: %s' % data.index[0].strftime('%Y-%m-%d'))
            print('End  : %s' % data.index[-1].strftime('%Y-%m-%d'))
            print('CAPR: %.3f' % (((growth ** (1. / (days / 365)) - 1)) * 100))
            print('MDD: %.3f' % (data['dd'].min() * 100))

            print(data.tail())
            data.to_excel(f'{sname}.xlsx')
            dispaly_figure(data, sfullname[sname])
        else:
            date = datetime.now() if args.date is None else datetime.strptime(args.date, '%Y%m%d')
            q.rebalance(date)
    else:
        if args.backtest:
            b = datetime.strptime(args.begin, '%Y%m%d')
            e = datetime.strptime(args.end, '%Y%m%d')            
            fundic[(args.strategy.lower(), True)](b, e, args.rebalance_month)
        else:
            date = datetime.now() if args.date is None else datetime.strptime(args.date, '%Y%m%d')
            fundic[(args.strategy.lower(), False)](date)

if __name__ == '__main__':
    main()
