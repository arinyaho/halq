import FinanceDataReader as fdr
import dart_fss as dart
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
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

def vaa_a_momentum(data):
    ds20  = (data / data.shift(20)  - 1) * 12
    ds60  = (data / data.shift(60)  - 1) * 4
    ds120 = (data / data.shift(120) - 1) * 2
    ds240 = (data / data.shift(240) - 1)
    m = ds20 + ds60 + ds120 + ds240
    
    return m

def vaa_a(date):    
    assets_a = ['SPY', 'EFA', 'EEM', 'AGG']     # Aggresive
    assets_d = ['LQD', 'IEF', 'SHY']            # Defensive    

    a, amax = vaa_a_calculate(assets_a, date)
    d, dmax = vaa_a_calculate(assets_d, date)

    a.to_excel('a.xlsx')
    
    # Check momentum score
    aggresive = True
    for ticker in assets_a:
        aggresive = aggresive and a.iloc[-1][ticker + '_M'] >= 0
    
    print("LAA")
    print("Momentum score for aggresive assets")
    for ticker in assets_a:
        print(f"    {ticker}: {a.iloc[-1][ticker + '_M']:.3f}")
    print("Momentum score for defensive assets")
    for ticker in assets_d:
        print(f"    {ticker}: {d.iloc[-1][ticker + '_M']:.3f}")
    print("Asset choice: " + (amax if aggresive else dmax))
    

def vaa_a_calculate(tickers, date):
    data = []
    momentum = []
    begin = date + timedelta(days=-400)
    for ticker in tickers:
        d = pdr.get_data_yahoo(ticker, start=begin, end=date, progress=False)['Adj Close']
        data.append(d)
        m = vaa_a_momentum(d)
        momentum.append(m)

    a = pd.concat(data + momentum, axis=1)
    a.columns = tickers + [s + '_M' for s in tickers]

    max_ticker = ''
    max_value = float('-inf')
    for ticker in tickers:
        if a.iloc[-1][ticker + '_M'] > max_value:
            max_ticker = ticker
            max_value = a.iloc[-1][ticker + '_M']

    return a, max_ticker


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

    choose_shy = spy[-1] < spy_ma200[-1] and unrate[-1] > unrate_ma12m[-1]
    choice = 'SHY' if choose_shy else 'QQQ'

    print("LAA")
    print("  Monthly Rebalancing: QQQ or SHY")
    print("  Yearly Rebalancing: GLD, IWD, IEF, (QQQ or SHY)")
    print("Indicators (%s)" % date)
    print("  S&P500,       MA200: %.2f, %.2f" % (spy[-1], spy_ma200[-1]))
    print("  Unemployment, MA12m: %.2f, %.2f" % (unrate[-1], unrate_ma12m[-1]))
    print("Asset to buy:")
    print("  GLD: 25%")
    print("  IWD: 25%")
    print("  IEF: 25%")
    print("  %s: 25%%" % choice)


def select_laa(x):
    choice = pd.Series([0], index=['Choice'])
    choose_shy = x['S&P500'] < x['S&P500_MA200'] and x['UNRATE'] > x['UNRATE_MA12M']
    choice['Choice'] = 'SHY' if choose_shy else 'QQQ'
    return choice


def laa_backtest(begin, end, rebalance_month=1):
    if not os.path.exists('fred.api'):
        print('FRED API Key file not found: fred.api')
        sys.exit(1)

    with open('fred.api', 'r') as fin:
        apikey = fin.read()

    fred = Fred(api_key=apikey)

    begin = begin + timedelta(days=-365)
    gld = pdr.get_data_yahoo('GLD', start=begin, end=end, progress=False)['Adj Close']
    iwd = pdr.get_data_yahoo('IWD', start=begin, end=end, progress=False)['Adj Close']
    ief = pdr.get_data_yahoo('IEF', start=begin, end=end, progress=False)['Adj Close']
    qqq = pdr.get_data_yahoo('QQQ', start=begin, end=end, progress=False)['Adj Close']
    shy = pdr.get_data_yahoo('SHY', start=begin, end=end, progress=False)['Adj Close']
    snp = pdr.get_data_yahoo('^GSPC', start=begin, end=end, progress=False)['Adj Close']
    une = fred.get_series('UNRATE')
    une.name = 'UNRATE'

    snp_ma200 = snp.rolling(window=200).mean()
    une_ma12m = une.rolling(window=12).mean()
    une_ma12m.name = 'UNRATE_MA12M'

    laa = pd.concat([gld, iwd, ief, qqq, shy, snp, snp_ma200], axis=1)
    laa.columns = ['GLD', 'IWD', 'IEF', 'QQQ', 'SHY', 'S&P500', 'S&P500_MA200']

    laa = laa.merge(une, how="outer", left_index=True, right_index=True)        
    laa['UNRATE'] = laa['UNRATE'].fillna(method='ffill')

    laa = laa.merge(une_ma12m, how='outer', left_index=True, right_index=True)
    laa['UNRATE_MA12M'] = laa['UNRATE_MA12M'].fillna(method='ffill')
    
    laa = laa.dropna().resample('BMS').first()

    laa['Choice'] = laa.apply(lambda x: select_laa(x), axis=1)    
    laa[['GLD_HOLD', 'IWD_HOLD', 'IEF_HOLD']] = 0.25
    laa[['QQQ_HOLD', 'SHY_HOLD']] = 0
    if laa.iloc[0]['Choice'] == 'QQQ':
        laa.loc[laa.index[0], ['QQQ_HOLD']] = 0.25
    else:
        laa.loc[laa.index[0], ['SHY_HOLD']] = 0.25

    for i in range(1, len(laa)):
        laa.loc[laa.index[i], 'GLD_HOLD'] = laa.iloc[i-1]['GLD_HOLD'] * laa.iloc[i]['GLD'] / laa.iloc[i-1]['GLD']
        laa.loc[laa.index[i], 'IWD_HOLD'] = laa.iloc[i-1]['IWD_HOLD'] * laa.iloc[i]['IWD'] / laa.iloc[i-1]['IWD']
        laa.loc[laa.index[i], 'IEF_HOLD'] = laa.iloc[i-1]['IEF_HOLD'] * laa.iloc[i]['IEF'] / laa.iloc[i-1]['IEF']
        laa.loc[laa.index[i], 'QQQ_HOLD'] = laa.iloc[i-1]['QQQ_HOLD'] * laa.iloc[i]['QQQ'] / laa.iloc[i-1]['QQQ']
        laa.loc[laa.index[i], 'SHY_HOLD'] = laa.iloc[i-1]['SHY_HOLD'] * laa.iloc[i]['SHY'] / laa.iloc[i-1]['SHY']
        
        if laa.iloc[i-1]['Choice'] == 'QQQ':
            if laa.iloc[i]['Choice'] == 'SHY':
                val = laa.iloc[i]['QQQ_HOLD'] * laa.iloc[i]['QQQ']
                laa.loc[laa.index[i], 'QQQ_HOLD'] = 0
                laa.loc[laa.index[i], 'SHY_HOLD'] = val / laa.iloc[i]['SHY']
        else:
            if laa.iloc[i]['Choice'] == 'QQQ':
                val = laa.iloc[i]['SHY_HOLD'] * laa.iloc[i]['SHY']        
                laa.loc[laa.index[i], 'SHY_HOLD'] = 0
                laa.loc[laa.index[i], 'QQQ_HOLD'] = val / laa.iloc[i]['QQQ']
            
            
        # Yearly rebalancing
        if i > 12 and laa.index[i].month == rebalance_month:
            sum = laa.loc[laa.index[i], 'GLD_HOLD'] + laa.loc[laa.index[i], 'IWD_HOLD'] + laa.loc[laa.index[i], 'IEF_HOLD'] + laa.loc[laa.index[i], 'QQQ_HOLD'] + laa.loc[laa.index[i], 'SHY_HOLD']
            laa.loc[laa.index[i], 'GLD_HOLD'] = sum / 4
            laa.loc[laa.index[i], 'IWD_HOLD'] = sum / 4
            laa.loc[laa.index[i], 'IEF_HOLD'] = sum / 4
            laa.loc[laa.index[i], 'QQQ_HOLD'] = 0
            laa.loc[laa.index[i], 'SHY_HOLD'] = 0
            if laa.iloc[i]['Choice'] == 'QQQ':
                laa.loc[laa.index[i], 'QQQ_HOLD'] = sum / 4
            else:
                laa.loc[laa.index[i], 'SHY_HOLD'] = sum / 4

    ## MDD
    laa['Profit'] = laa['GLD_HOLD'] + laa['IWD_HOLD'] + laa['IEF_HOLD'] + laa['QQQ_HOLD'] + laa['SHY_HOLD']
    laa['dd'] = -1 * (laa['Profit'].cummax() - laa['Profit']) / laa['Profit'].cummax()    
    print('Start: %s' % laa.index[0].strftime('%Y-%m-%d'))
    print('End  : %s' % laa.index[-1].strftime('%Y-%m-%d'))
    print('CAPR: %.3f' % (((laa['Profit'][-1] ** (1. / (len(laa) / 12)) - 1)) * 100))
    print('MDD: %.3f' % (laa['dd'].min() * 100))

    capr = plt.figure(1)
    capr.suptitle("LAA Growth")    
    laa['Profit'].plot.line()

    mdd = plt.figure(2)
    mdd.suptitle("LAA MDD")
    (laa['dd'] * 100).plot.line(color='red')
    plt.show()

    laa.to_excel('laa_backtest.xlsx')


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
        ('dmo', True): dual_momentum_original_backtest,
        ('laa', False): laa,
        ('laa', True): laa_backtest,
        ('vaa-a', False): vaa_a
    }

    if (args.list):
        list_strategies()
        sys.exit(0)


    if (args.strategy.lower(), args.backtest) not in fundic:
        print('Strategy not supported: %s' % args.strategy)
        sys.exit(1)

    if args.backtest:
        b = datetime.strptime(args.begin, '%Y%m%d')
        e = datetime.strptime(args.end, '%Y%m%d')            
        fundic[(args.strategy.lower(), True)](b, e, args.rebalance_month)
    else:
        date = datetime.now() if args.date is None else datetime.strptime(args.date, '%Y%m%d')
        fundic[(args.strategy.lower(), False)](date)

if __name__ == '__main__':
    main()
