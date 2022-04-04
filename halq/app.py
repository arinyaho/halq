import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
from fredapi import Fred

from halq.etf import MA, VAA_A, LAA, DualMomentum


import abc
import argparse
import os
import sys
import math
from datetime import datetime, timedelta

yf.pdr_override()


def dispaly_figure(data, title, cols=[]):
    capr = plt.figure(1)
    capr.suptitle(f"{title} Growth")
    data['value'].plot.line()

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
    parser.add_argument('--seed', type=int, default=1, help='Seed for backtest')
    parser.add_argument('--installment', type=int, default=0, help='Montly installment for backtest')
    parser.add_argument('--rebalance-month', type=int, default=1, choices=range(1, 13), help='Month for rebalancing asset allocation')
    parser.add_argument('--list', action='store_true', default=False, help='List strategies')
    args = parser.parse_args()
    if args.seed < 0:
        print('Seed for backtest should be greater than 0.')
        sys.exit(1)
    if args.installment < 0:
        print('Monthly installment for backtest should be greater than 0.')
        sys.exit(1)
    return args


def list_strategies():
    print('List of Strategies')
    print('  laa       Lethargic Asset Allocation')
    print('  vaa-a     Vigilant Asset Allocation Aggresive')
    print('  dmo       Original Dual Momentum')
    print('  ma        Moving Average')


def main():
    # hq_ultra()
    # sys.exit(2)

    args = parse()
    
    fundic = {}

    clsdic = {
        'dm': DualMomentum,
        'laa': LAA,
        'vaa-a': VAA_A,
        'ma': MA
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
            if sname.lower() == 'ma':
                pass
            
            data = q.backtest(b, e, seed=args.seed, monthly_installment=args.installment, rebalance_month=args.rebalance_month)
            days = (e - b).days

            growth = data['value'][-1] / data['value'][0]
            cagr = math.pow(growth, 1 / (days/365)) - 1

            if args.seed != 1:
                print(f'Period : {days} days')
                print(f'Seed   : {args.seed}')
                print(f'Profit : {(data["value"][-1] - data["value"][0])}')

            print('Start : %s' % data.index[0].strftime('%Y-%m-%d'))
            print('End   : %s' % data.index[-1].strftime('%Y-%m-%d'))
            print(f'Growth: {growth:.3f}')
            print('CAGR  : %.3f' % (cagr))
            print('MDD   : %.3f' % (data['dd'].min() * 100))

            data.to_excel(f'{sname}.xlsx')
            data.to_csv(f'{sname}.csv')
            dispaly_figure(data, q.name, cols=['ma_top', 'ma_bottom'])
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
