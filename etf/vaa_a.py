from quant_etf import QuantETF, RebalanceDay
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta

yf.pdr_override()

class VAA_A(QuantETF):
    def __init__(self):
        self.assets_a = ['SPY', 'EFA', 'EEM', 'AGG']     # Aggresive
        self.assets_d = ['LQD', 'IEF', 'SHY']            # Defensive    


    @classmethod
    def __momentum(cls, data):
        ds20  = (data / data.shift(20)  - 1) * 12   # 1-Month
        ds60  = (data / data.shift(60)  - 1) * 4    # 3-Month
        ds120 = (data / data.shift(120) - 1) * 2    # 6-Month
        ds240 = (data / data.shift(240) - 1)        # 12-Month
        m = ds20 + ds60 + ds120 + ds240        
        return m


    @classmethod
    def __calculate(cls, tickers, begin, end):
        data = []
        momentum = []
        
        for ticker in tickers:
            d = pdr.get_data_yahoo(ticker, start=begin, end=end, progress=False)['Adj Close']
            # d = laa.dropna().resample('BMS').last()

            data.append(d)
            m = cls.__momentum(d)
            momentum.append(m)

        a = pd.concat(data + momentum, axis=1)
        a.columns = tickers + [s + '_M' for s in tickers]       

        return a


    def rebalance(self, date):
        begin = date + timedelta(days=-400)
        a = self.__calculate(self.assets_a, begin, date)
        d = self.__calculate(self.assets_d, begin, date)
        v = pd.concat([a])
        v = v.merge(d, how="outer", left_index=True, right_index=True)
        
        # Set asset choice
        v['Choice'] = v.apply(lambda x: self.__select(x), axis=1)

        # Check momentum score
        aggresive = True
        for ticker in self.assets_a:
            aggresive = aggresive and a.iloc[-1][ticker + '_M'] >= 0  
        print("VAA-Aggresive: Monthly rebalancing")
        print("Momentum score for aggresive assets")
        for ticker in self.assets_a:
            print(f"    {ticker}: {a.iloc[-1][ticker + '_M']:.3f}")
        print("Momentum score for defensive assets")
        for ticker in self.assets_d:
            print(f"    {ticker}: {d.iloc[-1][ticker + '_M']:.3f}")
        print("Asset choice: " + v.iloc[-1]['Choice'])

        choice_before = v.iloc[-2]['Choice']
        growth = v.iloc[-1][choice_before] / v.iloc[-2][choice_before] - 1
        print(f"1-Month Growth: {growth:.3f}")
    

    def backtest(self, begin, end, seed=1, monthly_installment=0, rebalance_date=RebalanceDay.LAST_DAY, rebalance_month=1):
        start = begin + timedelta(days=-400)
        a = self.__calculate(self.assets_a, start, end)
        d = self.__calculate(self.assets_d, start, end)

        vaa = pd.concat([a])
        vaa = vaa.merge(d, how="outer", left_index=True, right_index=True).dropna()     
        # Rebalance every last day of each month

        if rebalance_date == RebalanceDay.LAST_DAY:
            vaa = vaa.dropna().resample(rule='M').apply(lambda x: x[-1])
        else:
            vaa = vaa.dropna().resample('BMS').first()

        vaa['Growth'] = seed
        vaa['Choice'] = vaa.apply(lambda x: self.__select(x), axis=1)

        for i in range(1, len(vaa)):
            asset_before = vaa.iloc[i-1]['Choice']
            profit = vaa.iloc[i][asset_before] / vaa.iloc[i-1][asset_before]
            vaa.loc[vaa.index[i], 'Growth'] = vaa.iloc[i-1]['Growth'] * profit
        
        vaa = self.add_dd(vaa)

        return vaa


    @classmethod
    def __get_max_momentum_ticker(cls, tickers, row):
        max_ticker = ''
        max_value = float('-inf')
        for ticker in tickers:
            if row[ticker + '_M'] > max_value:
                max_ticker = ticker
                max_value = row[ticker + '_M']
        return max_ticker
    

    def __select(self, row):
        choice = pd.Series([0], index=['Choice'])
        aggresive = True
        for ticker in self.assets_a:
            aggresive = aggresive and (row[ticker + '_M'] >= 0)
        
        choice = self.__get_max_momentum_ticker(self.assets_a, row) if aggresive else self.__get_max_momentum_ticker(self.assets_d, row)
        return choice
        

if __name__ == '__main__':
    q = VAA_A()
    q.rebalance(datetime.strptime('20220201', '%Y%m%d'))