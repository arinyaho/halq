from halq.etf.quant_etf import QuantETF, RebalanceDay
from datetime import datetime, timedelta
import pandas as pd
import pandas_datareader as pdr
import yfinance as yf



yf.pdr_override()


class MA(QuantETF):
    def __init__(self):
        self.ticker = 'SPY'
        self.top = 50
        self.bottom = 50
        QuantETF.__init__(self, 'Moving Average')


    def backtest(self, begin, end, seed=1, monthly_installment=0, rebalance_date=RebalanceDay.LAST_DAY, rebalance_month=1):
        d = pdr.get_data_yahoo(self.ticker, start=begin, end=end)
        
        d_ma_top = d['Adj Close'].rolling(window=self.top).mean()
        d_ma_bottom = d['Adj Close'].rolling(window=self.bottom).mean()
        d['ma_top'] = d_ma_top
        d['ma_bottom'] = d_ma_bottom
        d['value'] = seed
        d['hold'] = 0
        d['action'] = 'stay'
        d = d.dropna()        

        if d.iloc[0]['Adj Close'] > d.iloc[0]['ma_bottom']:
            d.loc[d.index[0], 'hold'] = seed / d.iloc[0]['Adj Close']
            d.loc[d.index[0], 'action'] = 'buy'
        d.loc[d.index[0], 'value'] = seed
        


        for i in range(1, len(d)):
            yesterday = d.iloc[i-1]['Adj Close']
            yesterday_above_top = yesterday > d.iloc[i-1]['ma_top']
            yesterday_between = d.iloc[i-1]['ma_bottom'] <= yesterday <= d.iloc[i-1]['ma_top']
            yesterday_under_bottom = yesterday < d.iloc[i-1]['ma_bottom']

            today = d.iloc[i]['Adj Close']
            today_above_top = today > d.iloc[i-1]['ma_top']
            today_between = d.iloc[i-1]['ma_bottom'] <= today <= d.iloc[i-1]['ma_top']
            today_under_bottom = today < d.iloc[i-1]['ma_bottom']

            hold_yesterday = d.iloc[i-1]['hold']
            value_yesterday = d.iloc[i-1]['value']

            # Sell
            if yesterday_above_top and (today_between or today_under_bottom) and hold_yesterday > 0:
                hold = 0
                value = today * hold_yesterday
                action = 'sell'
            # Buy
            elif yesterday_under_bottom and (today_between or today_above_top) and hold_yesterday == 0:                
                hold = value_yesterday / today
                value = value_yesterday
                action = 'buy'
            else:
                hold = hold_yesterday
                if hold == 0:
                    value = value_yesterday
                else:
                    value = hold * today
                action = 'stay'
            d.loc[d.index[i], 'hold'] = hold
            d.loc[d.index[i], 'value'] = value
            d.loc[d.index[i], 'action'] = action
        d = self.add_dd(d, 'value')
        return d
        
