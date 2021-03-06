from .quant_etf import QuantETF, RebalanceDay
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from fredapi import Fred

import os, sys
import multiprocessing
from functools import partial


yf.pdr_override()

class LAA(QuantETF):    
    def __init__(self):
        self.assets = ['GLD', 'IWD', 'IEF', 'QQQ', 'SHY']


    def rebalance(self, date):
        # 200 days moving average of S&P500 index
        begin = date + timedelta(days=-365)
        spy = pdr.get_data_yahoo('^GSPC', start=begin, end=date, progress=False)['Adj Close']
        spy_ma200 = spy.rolling(window=200).mean()

        api_filename = 'api/fred.api'
        if not os.path.exists(api_filename):
            print('FRED API Key file not found: fred.api')
            sys.exit(1)

        with open(api_filename, 'r') as fin:
            apikey = fin.read()
        
        fred = Fred(api_key=apikey)
        unrate = fred.get_series('UNRATE').tail(15)
        unrate_ma12m = unrate.rolling(window=12).mean()

        choose_shy = spy[-1] < spy_ma200[-1] and unrate[-1] > unrate_ma12m[-1]
        choice = 'SHY' if choose_shy else 'QQQ'
        
        begin = date + timedelta(days=-35)
        gld = pdr.get_data_yahoo('GLD', start=begin, end=date, progress=False)['Adj Close']
        iwd = pdr.get_data_yahoo('IWD', start=begin, end=date, progress=False)['Adj Close']
        ief = pdr.get_data_yahoo('IEF', start=begin, end=date, progress=False)['Adj Close']
        choice_data = pdr.get_data_yahoo(choice, start=begin, end=date, progress=False)['Adj Close']

        data = pd.concat([gld, iwd, ief, choice_data], axis=1)
        data.columns = [self.assets[:-2] + [choice]]
        growth = 0
        for ticker in data.columns:
            growth += 0.25 * (data.iloc[-1][ticker] / data.iloc[-20][ticker])

        print("LAA")
        print("  Monthly Rebalancing: QQQ or SHY")
        print("  Yearly Rebalancing: GLD, IWD, IEF, (QQQ or SHY)")
        print("Indicators (%s)" % date)
        print("  S&P500,       MA200: %.2f, %.2f" % (spy[-1], spy_ma200[-1]))
        print("  Unemployment, MA12m: %.2f, %.2f" % (unrate[-1], unrate_ma12m[-1]))
        print("Asset Allocation:")
        print("  GLD: 25%")
        print("  IWD: 25%")
        print("  IEF: 25%")
        print("  %s: 25%%" % choice)
        print(f"1-Month Growth: {100 * (growth - 1):.3f}%")


    @classmethod
    def select_laa(cls, x):
        choice = pd.Series([0], index=['Choice'])
        choose_shy = x['S&P500'] < x['S&P500_MA200'] and x['UNRATE'] > x['UNRATE_MA12M']
        choice['Choice'] = 'SHY' if choose_shy else 'QQQ'
        return choice


    def backtest(self, begin, end, seed=1, monthly_installment=0, rebalance_date=RebalanceDay.LAST_DAY, rebalance_month=1):
        api_filename = 'api/fred.api'
        if not os.path.exists(api_filename):
            print('FRED API Key file not found: fred.api')
            sys.exit(1)

        with open(api_filename, 'r') as fin:
            apikey = fin.read()

        fred = Fred(api_key=apikey)

        begin = begin + timedelta(days=-365)

        with multiprocessing.Pool(processes=4) as pools:
            get_data = partial(pdr.get_data_yahoo, start=begin, end=end, progress=False)
            data = pools.map(get_data, self.assets + ['^GSPC'])
        for i in range(len(data)):
            data[i] = data[i]['Adj Close']
        
        '''
        gld = pdr.get_data_yahoo('GLD', start=begin, end=end, progress=False)['Adj Close']
        iwd = pdr.get_data_yahoo('IWD', start=begin, end=end, progress=False)['Adj Close']
        ief = pdr.get_data_yahoo('IEF', start=begin, end=end, progress=False)['Adj Close']
        qqq = pdr.get_data_yahoo('QQQ', start=begin, end=end, progress=False)['Adj Close']
        shy = pdr.get_data_yahoo('SHY', start=begin, end=end, progress=False)['Adj Close']
        snp = pdr.get_data_yahoo('^GSPC', start=begin, end=end, progress=False)['Adj Close']
        '''
        une = fred.get_series('UNRATE')
        une.name = 'UNRATE'

        # snp_ma200 = snp.rolling(window=200).mean()
        snp_ma200 = data[5].rolling(window=200).mean()
        une_ma12m = une.rolling(window=12).mean()
        une_ma12m.name = 'UNRATE_MA12M'

        # laa = pd.concat([gld, iwd, ief, qqq, shy, snp, snp_ma200], axis=1)
        laa = pd.concat(data + [snp_ma200], axis=1)
        laa.columns = ['GLD', 'IWD', 'IEF', 'QQQ', 'SHY', 'S&P500', 'S&P500_MA200']

        laa = laa.merge(une, how="outer", left_index=True, right_index=True)        
        laa['UNRATE'] = laa['UNRATE'].fillna(method='ffill')

        laa = laa.merge(une_ma12m, how='outer', left_index=True, right_index=True)
        laa['UNRATE_MA12M'] = laa['UNRATE_MA12M'].fillna(method='ffill')
        
        if rebalance_date == RebalanceDay.LAST_DAY:
            laa = laa.dropna().resample(rule='M').apply(lambda x: x[-1])
        else:
            laa = laa.dropna().resample('BMS').first()

        laa['Choice'] = laa.apply(lambda x: self.select_laa(x), axis=1)
        laa.loc[laa.index[0], ['GLD_HOLD']] = (seed / 4.) / laa.iloc[0]['GLD']
        laa.loc[laa.index[0], ['IWD_HOLD']] = (seed / 4.) / laa.iloc[0]['IWD']
        laa.loc[laa.index[0], ['IEF_HOLD']] = (seed / 4.) / laa.iloc[0]['IEF']
        laa[['QQQ_HOLD', 'SHY_HOLD']] = 0
        if laa.iloc[0]['Choice'] == 'QQQ':
            laa.loc[laa.index[0], ['QQQ_HOLD']] = (seed / 4.) / laa.iloc[0]['QQQ']
        else:
            laa.loc[laa.index[0], ['SHY_HOLD']] = (seed / 4.) / laa.iloc[0]['SHY']
   
        for i in range(1, len(laa)):
            laa.loc[laa.index[i], 'GLD_HOLD'] = laa.iloc[i-1]['GLD_HOLD'] + (monthly_installment / 4.) / laa.iloc[i]['GLD']
            laa.loc[laa.index[i], 'IWD_HOLD'] = laa.iloc[i-1]['IWD_HOLD'] + (monthly_installment / 4.) / laa.iloc[i]['IWD']
            laa.loc[laa.index[i], 'IEF_HOLD'] = laa.iloc[i-1]['IEF_HOLD'] + (monthly_installment / 4.) / laa.iloc[i]['IEF']
            
            if laa.iloc[i-1]['Choice'] == 'QQQ':
                laa.loc[laa.index[i], 'QQQ_HOLD'] = laa.iloc[i-1]['QQQ_HOLD'] + (monthly_installment / 4.) / laa.iloc[i]['QQQ']
                if laa.iloc[i]['Choice'] == 'SHY':                    
                    val = laa.iloc[i]['QQQ_HOLD'] * laa.iloc[i]['QQQ']
                    laa.loc[laa.index[i], 'QQQ_HOLD'] = 0
                    laa.loc[laa.index[i], 'SHY_HOLD'] = val / laa.iloc[i]['SHY']

            else:
                laa.loc[laa.index[i], 'SHY_HOLD'] = laa.iloc[i-1]['SHY_HOLD'] + (monthly_installment / 4.) / laa.iloc[i]['SHY']
                if laa.iloc[i]['Choice'] == 'QQQ':                    
                    val = laa.iloc[i]['SHY_HOLD'] * laa.iloc[i]['SHY']        
                    laa.loc[laa.index[i], 'SHY_HOLD'] = 0
                    laa.loc[laa.index[i], 'QQQ_HOLD'] = val / laa.iloc[i]['QQQ']

            # Yearly rebalancing
            if i > 12 and laa.index[i].month == rebalance_month:
                sum = (laa.loc[laa.index[i], 'GLD_HOLD'] * laa.iloc[i]['GLD'] 
                     + laa.loc[laa.index[i], 'IWD_HOLD'] * laa.iloc[i]['IWD'] 
                     + laa.loc[laa.index[i], 'IEF_HOLD'] * laa.iloc[i]['IEF'] 
                     + laa.loc[laa.index[i], 'QQQ_HOLD'] * laa.iloc[i]['QQQ'] 
                     + laa.loc[laa.index[i], 'SHY_HOLD'] * laa.iloc[i]['SHY'])
                laa.loc[laa.index[i], 'GLD_HOLD'] = (sum / 4.) / laa.iloc[i]['GLD']
                laa.loc[laa.index[i], 'IWD_HOLD'] = (sum / 4.) / laa.iloc[i]['IWD']
                laa.loc[laa.index[i], 'IEF_HOLD'] = (sum / 4.) / laa.iloc[i]['IEF']
                laa.loc[laa.index[i], 'QQQ_HOLD'] = 0
                laa.loc[laa.index[i], 'SHY_HOLD'] = 0
                if laa.iloc[i]['Choice'] == 'QQQ':
                    laa.loc[laa.index[i], 'QQQ_HOLD'] = (sum / 4.) / laa.iloc[i]['QQQ']
                else:
                    laa.loc[laa.index[i], 'SHY_HOLD'] = (sum / 4.) / laa.iloc[i]['SHY']

        laa['Growth'] = laa['GLD_HOLD'] * laa['GLD'] + laa['IWD_HOLD'] * laa['IWD'] + laa['IEF_HOLD'] * laa['IEF'] + laa['QQQ_HOLD'] + laa['SHY_HOLD']        
        laa = self.add_dd(laa)

        return laa