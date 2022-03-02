import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
from fredapi import Fred

from etf.vaa_a import VAA_A
from etf.laa import LAA
from etf.dm import DualMomentum

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
    
    fundic = {}

    clsdic = {
        'dm': DualMomentum,
        'laa': LAA,
        'vaa-a': VAA_A
    }

    sfullname = {
        'dm': 'Dual Momentum',
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
            data.to_csv(f'{sname}.csv')
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
