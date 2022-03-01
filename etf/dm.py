from quant_etf import QuantETF, RebalanceDay
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from fredapi import Fred

import os

yf.pdr_override()

class DualMomentum(QuantETF):
    def __init__(self):
        self.assets = ['SPY', 'EFA', 'BIL', 'AGG']


    @classmethod
    def profit(cls, ticker, date):
        e = date
        b = e + timedelta(days=-400)
        d = pdr.get_data_yahoo(ticker, start=b, end=e, progress=False)['Adj Close']

        f = d.iloc[-240]
        r = d.iloc[-1]
        return r/f - 1.


    def rebalance(self, date):
        spy = self.profit('SPY', date)
        efa = self.profit('EFA', date)
        bil = self.profit('BIL', date)
        agg = self.profit('AGG', date)

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

        print("Asset Allocation: %s 100%%" % ticker)


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
