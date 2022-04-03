from typing import List
from datetime import datetime
import pandas as pd
import numpy as np

from halq.stock.corp import Corp
from halq.stock.krx import KRX_Reader
from halq.stock.quant_hq import QuantStock

class HQ_VM(QuantStock):
    def __init__(self):
        QuantStock.__init__(self, 'Haltoo Value-Momentum')


    @classmethod
    def get_year_and_quarter(cls, date: datetime):
        year = date.year
        if date.month < 4:      quarter = 1
        elif date.month < 7:    quarter = 2
        elif date.month < 10:   quarter = 3
        else: quarter = 4
        return year, quarter


    @classmethod
    def get_prev_year_and_quarter(cls, date: datetime):
        year, quarter = cls.get_year_and_quarter(date)
        if quarter == 1:
            quarter = 4
            year -= 1
        else:
            quarter -= 1
        return year, quarter


    @classmethod
    def _choice(self, corps: List[Corp], num: int):
        stocks = list(map(lambda c: c.stock, corps))

        data = pd.DataFrame([c.__dict__ for c in corps], index=stocks)
        data = data.drop(['stock'], axis=1)
        data.index.name = 'stock'

        columns = {
            'ord_ipbr': 'int64', 
            'ord_iper': 'int64', 
            'ord_ipsr': 'int64', 
            'ord_ipfcr': 'int64', 
            'ord_profit_growth_qoq': 'int64',  
            'ord_profit_growth_yoy': 'int64', 
            'ord_net_income_growth_qoq': 'int64', 
            'ord_net_income_growth_yoy': 'int64'
        }
        
        # data['score'] = data[list(map(lambda x: f'{x}', columns.keys()))].mean(axis=1)
        data = data.astype(columns)
        data['score'] = 0
        for k in columns.keys():
            data['score'] += data[k]
        data['score'] /= 8
        data = data.sort_values(by=['score'])
        data.index.name = 'Stock'
        data.to_csv('test.csv')

        corps_map = {}
        for c in corps:
            corps_map[c.stock] = c

        stocks = data.head(num).index.tolist()
        return list(map(lambda s: corps_map[s], stocks))


    def choice(self, year: int, quarter: int, decile: int = 0, numbers: int = 20):
        reader = KRX_Reader()
        
        corps = reader.get_corps(year, quarter)
        if corps is None:
            return None

        corps = list(filter(lambda c: c.market_cap is not None, corps))

        if decile != 0:
            corps.sort(key=lambda c: c.market_cap)
            decile_size = len(corps) // 10
            start_offset = decile_size * (decile - 1)
            if decile == 10:
                end_offset = len(corps)
            else:
                end_offset = start_offset + decile_size
            corps = corps[start_offset:end_offset]
        
        return self._choice(corps, numbers)
        
        

    def backtest(self, begin, halloween=False, num=20, smallcap=0):
        begin_year, begin_quarter = self.get_year_and_quarter(begin)
        end_year, end_quarter = self.get_prev_year_and_quarter(datetime.now())

        year = begin_year
        quarter = begin_quarter

        reader = KRX_Reader()

        timestamp = []
        corps_all_dict = []
        corps_all_list = []
        while year * 10 + quarter < end_year * 10 + end_quarter:
            # dt = datetime(year=year, month=(quarter-1)*3+1, day=1)
            # print(f'Checking {year}-{quarter}Q, {dt.strftime("%Y-%m-%d")}')            

            t = (year, quarter)
            c = reader.get_corps(year, quarter)            

            quarter += 1
            if quarter == 5:
                quarter = 1
                year += 1

            if c is None:
                continue
            
            timestamp.append(t)
            corps_all_dict.append(c)
            corps_all_list.append(list(c.values()))

        if not halloween:
            print('Rebalance at each quarter')
        else:
            print('Rebalance on October and April')
        
        hold = {}
        hold_index = 0
        value = 1
        # Skip first 1 year since YoY is required for stock choice
        if len(timestamp) > 4:
            data = pd.DataFrame(pd.Series(timestamp[4:], name='Timestamp'))

            for i in range(4, len(timestamp)):
                corps_py = corps_all_list[i-4]
                corps_pq = corps_all_list[i-1]
                clist    = corps_all_list[i]
                cdict    = corps_all_dict[i]
                
                t = timestamp[i]
                choices = self._choice(corps_py, corps_pq, clist, t[0], t[1], num)


                value = 1
                if i != 4:
                    value = 0                    
                    # Addup current price of previous chocies
                    for s, h in hold.items():
                        try:
                            value += h * cdict[s].price
                        except KeyError as ex:
                            print(timestamp[hold_index], timestamp[i], corps_all_dict[hold_index][s].name)
                
                year = t[0]
                quarter = t[1]

                y = year
                m = quarter*3 + 1
                if m > 12:
                    m = 1
                    year += 1
                    
                print(f'Value at {y}-{m:02d}-01: {value}', end='')
                data.loc[i-4, ['Growth']] = value

                if (i == 4 or not halloween) or (halloween and (quarter == 1 or quarter == 3)):
                    y = year
                    m = quarter*3 + 1
                    if m > 12:
                        m = 1
                        year += 1
                    print(f', Rebalance based on {year}-{quarter}Q data', end='')
                    hold.clear()
                    for c in choices:
                        hold[c.stock] = value / len(choices) / cdict[c.stock].price
                        hold_index = i
                print()
        
            data = self.add_dd(data)
            return data
        else:
            return None




# q = HQ_VM()
# chocies = q.choice(datetime.strptime('20210401', '%Y%m%d'))
# print(len(choices))
#d = q.backtest(datetime.strptime('20100401', '%Y%m%d'), halloween=False)
#print(d)
