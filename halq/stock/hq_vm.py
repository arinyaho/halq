from quant_hq import QuantStock
from datetime import datetime
import krx
import sys, json
import pandas as pd
import numpy as np


class HQ_VM(QuantStock):
    @classmethod
    def get_year_and_quarter(cls, date):
        year = date.year
        if date.month < 4:      quarter = 1
        elif date.month < 7:    quarter = 2
        elif date.month < 10:   quarter = 3
        else: quarter = 4
        return year, quarter

    @classmethod
    def get_prev_year_and_quarter(cls, date):
        year = date.year
        if date.month < 4:
            quarter = 4
            year -= 1
        elif date.month < 7:   quarter = 1
        elif date.month < 10:  quarter = 2
        else: quarter = 3
        return year, quarter


    @classmethod
    def _choice(self, corps_prev_year, corps_prev_quarter, corps, year, quarter, num):
        stocks = list(map(lambda c: c.stock, corps))
        qstocks = list(map(lambda c: c.stock, corps_prev_quarter))
        ystocks = list(map(lambda c: c.stock, corps_prev_year)) 

        name  = pd.Series(list(map(lambda c: c.name,        corps)), index=stocks, dtype=str)
        ipbr  = pd.Series(list(map(lambda c: 1. / c.pbr(),  corps)), index=stocks, dtype=np.float64)
        iper  = pd.Series(list(map(lambda c: 1. / c.per(),  corps)), index=stocks, dtype=np.float64)
        ipsr  = pd.Series(list(map(lambda c: 1. / c.psr(),  corps)), index=stocks, dtype=np.float64)
        ipfcr = pd.Series(list(map(lambda c: 1. / c.pfcr(), corps)), index=stocks, dtype=np.float64)
        sales = pd.Series(list(map(lambda c: c.sales,       corps)), index=stocks, dtype=np.int64)
        net   = pd.Series(list(map(lambda c: c.net_income,  corps)), index=stocks, dtype=np.int64)

        qsale  = pd.Series(list(map(lambda c: c.sales,      corps_prev_quarter)), index=qstocks, dtype=np.int64)
        qnet   = pd.Series(list(map(lambda c: c.net_income, corps_prev_quarter)), index=qstocks, dtype=np.int64)
        ysale  = pd.Series(list(map(lambda c: c.sales,      corps_prev_year)),    index=ystocks, dtype=np.int64)
        ynet   = pd.Series(list(map(lambda c: c.net_income, corps_prev_year)),    index=ystocks, dtype=np.int64)

        data  = pd.concat([name, ipbr, iper, ipsr, ipfcr, sales, net], axis=1)
        qdata = pd.concat([qsale, qnet], axis=1)
        ydata = pd.concat([ysale, ynet], axis=1)

        data.columns  = ['Name', 'IPBR', 'IPER', 'IPSR', 'IPFCR', 'SALES', 'NET']
        qdata.columns = ['Q-SALES', 'Q-NET']
        ydata.columns = ['Y-SALES', 'Y-NET']
                
        vm = data.merge(qdata, how="outer", left_index=True, right_index=True).dropna()
        vm = vm.merge(ydata, how="outer", left_index=True, right_index=True).dropna()
        vm['Q-SALES-GROWTH'] = vm['SALES'] / vm['Q-SALES'] - 1
        vm['Y-SALES-GROWTH'] = vm['SALES'] / vm['Y-SALES'] - 1
        vm['Q-NET-GROWTH'] = vm['NET'] / vm['Q-NET'] - 1
        vm['Y-NET-GROWTH'] = vm['NET'] / vm['Y-NET'] - 1

        columns = ['IPBR', 'IPER', 'IPSR', 'IPFCR', 'Q-SALES-GROWTH', 'Y-SALES-GROWTH', 'Q-NET-GROWTH', 'Y-NET-GROWTH']
        
        # print(len(vm))
        # print(vm.tail())
        for col in columns:        
            vm = vm.sort_values(by=[col], ascending=False)
            vm[f'{col}-ORD'] = 0
            for i in range(len(vm)):
                vm.loc[vm.index[i], f'{col}-ORD'] = i + 1

        vm['Score'] = vm[list(map(lambda x: f'{x}-ORD', columns))].mean(axis=1)
        vm = vm.sort_values(by=['Score'])
        vm.index.name = 'Stock'
        # print(vm.head())
        # vm.to_excel(f'hqvm-{year}-{quarter}.xlsx')
        # vm.to_csv(f'hqvm-{year}-{quarter}.csv')

        # print(len(corps_pq))
        # print(len(corps_py))
        # print(len(corps))
        # print(vm.head(numbers).index.tolist())
        corps_map = {}
        for c in corps:
            corps_map[c.stock] = c

        stocks = vm.head(num).index.tolist()
        return list(map(lambda s: corps_map[s], stocks))


    def choice(self, date, numbers=20):
        year, quarter = self.get_prev_year_and_quarter(date)

        corps_py = krx.load_corps(year-1, quarter)
        if corps_py is None:
            return None

        corps_pq = krx.load_corps(year-1 if quarter == 1 else year, 4 if quarter == 1 else quarter-1)
        if corps_pq is None:
            return None

        corps = krx.load_corps(year, quarter)
        if corps is None:
            return None

        if corps_py == None or corps_pq == None or corps == None:
            return None

        return self._choice(corps_py, corps_pq, corps, year, quarter, numbers)
        
        

    def backtest(self, begin, halloween=False, num=20, smallcap=0):
        begin_year, begin_quarter = self.get_year_and_quarter(begin)
        end_year, end_quarter = self.get_prev_year_and_quarter(datetime.now())

        year = begin_year
        quarter = begin_quarter

        timestamp = []
        corps_all_dict = []
        corps_all_list = []
        while year * 10 + quarter < end_year * 10 + end_quarter:
            # dt = datetime(year=year, month=(quarter-1)*3+1, day=1)
            # print(f'Checking {year}-{quarter}Q, {dt.strftime("%Y-%m-%d")}')            

            t = (year, quarter)
            c = krx.load_corps(year, quarter)            

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




q = HQ_VM()
# q.choice(datetime.strptime('20210401', '%Y%m%d'))
d = q.backtest(datetime.strptime('20100401', '%Y%m%d'), halloween=False)
print(d)
