from .quant_etf import QuantETF, RebalanceDay
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from fredapi import Fred

import sys
import os

yf.pdr_override()

class DualMomentum(QuantETF):
    assets = ['SPY', 'EFA', 'BIL', 'AGG']

    def __init__(self):
        pass
        

    @classmethod
    def profit_month(cls, ticker, date):
        e = date
        b = e + timedelta(days=-400)
        d = pdr.get_data_yahoo(ticker, start=b, end=e, progress=False)['Adj Close']

        f = d.iloc[-240]    # price before 1 year (240 business days)
        r = d.iloc[-1]
        return r/f - 1.


    @classmethod
    def profits_month(cls, date):
        ret = {}
        for ticker in cls.assets:
            ret[ticker] = cls.profit_month(ticker, date)
        return ret


    @classmethod
    def select(cls, profits):
        if profits['SPY'] > profits['BIL']:
            return 'SPY' if profits['SPY'] > profits['BIL'] else 'EFA'
        else:
            return 'AGG'
    

    def rebalance(self, date):
        profits = self.profits_month(date)
        profits_before = self.profits_month(date + timedelta(days=-30))

        choice = self.select(profits)
        choice_before = self.select(profits_before)

        print("Original Dual Momentum: Monthly Rebalancing")
        print("Yearly Profit (%s)" % date)
        print("  SPY: %f" % profits['SPY'])
        print("  EFA: %f" % profits['EFA'])
        print("  BIL: %f" % profits['BIL'])
        print("  AGG: %f" % profits['AGG'])

        print("Asset Allocation: %s 100%%" % choice)
        print(f"1-Month Growth: {100 * (self.profit_month(choice_before, date)):.3f}%")

    @classmethod
    def select_dmo(cls, x):
        asset = pd.Series([0], index=['Choice'])
        if x['SPY_YoY'] > x['BIL_YoY']:
            asset['Choice'] = 'SPY' if x['SPY_YoY'] > x['EFA_YoY'] else 'EFA'        
        else:
            asset['Choice'] = 'AGG'
        return asset


    def backtest(self, begin, end, seed=1, monthly_installment=0, rebalance_date=RebalanceDay.LAST_DAY, rebalance_month=1):
        begin = begin + timedelta(days=-365)
        spy = pdr.get_data_yahoo('SPY', start=begin, end=end, progress=False)['Adj Close']
        efa = pdr.get_data_yahoo('EFA', start=begin, end=end, progress=False)['Adj Close']
        bil = pdr.get_data_yahoo('BIL', start=begin, end=end, progress=False)['Adj Close']
        agg = pdr.get_data_yahoo('AGG', start=begin, end=end, progress=False)['Adj Close']

        dmo = pd.concat([spy, efa, bil, agg], axis=1).dropna()
        dmo.columns = ['SPY', 'EFA', 'BIL', 'AGG']

        # Takes only first or last day of each month
        if rebalance_date == RebalanceDay.LAST_DAY:
            dmo = dmo.dropna().resample(rule='M').apply(lambda x: x[-1])
        else:
            dmo = dmo.dropna().resample('BMS').first()

        # Calculate YoY
        dmo_12m = dmo.shift(12)
        dmo_yoy = dmo / dmo_12m - 1.
        dmo[['SPY_YoY', 'EFA_YoY', 'BIL_YoY', 'AGG_YoY']] = dmo_yoy
        dmo = dmo.dropna()
        
        dmo['Growth'] = seed        
        dmo['Choice'] = dmo.apply(lambda x: self.select_dmo(x), axis=1)
        dmo['Hold'] = 0
        dmo.loc[dmo.index[0], 'Hold'] = seed / dmo.iloc[0][dmo.iloc[0]['Choice']]

        for i in range(1, len(dmo)):
            asset_before = dmo.iloc[i-1]['Choice']
            asset_now = dmo.iloc[i]['Choice']
            val = dmo.iloc[i-1]['Hold'] * dmo.iloc[i][asset_before] + monthly_installment           
            dmo.loc[dmo.index[i], ['Hold']] = val / dmo.iloc[i][asset_now]
            dmo.loc[dmo.index[i], ['Growth']] = val

        dmo = self.add_dd(dmo)
        return dmo