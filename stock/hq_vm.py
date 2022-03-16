from quant_hq import QuantStock
import krx
import sys, json

import datetime
import pandas as pd

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



    def choice(self, date, numbers=20):
        year, quarter = self.get_prev_year_and_quarter(date)

        corps_py = krx.load_corps(year-1, quarter)
        print('PY Type' + type(corps_pq))
        if corps_py is None:
            return None

        corps_pq = krx.load_corps(year-1 if quarter == 1 else year, 4 if quarter == 1 else quarter-1)
        print('PQ Type' + type(corps_pq))
        if corps_pq is None:
            return None

        corps = krx.load_corps(year, quarter)
        print('Curr Type' + type(corps))
        if corps is None:
            return None

        print([ob.__dict__ for ob in corps_pq[:20]])
        if corps_py == None or corps_pq == None or corps == None:
            # print('Insufficient past data')
            return None

        stocks = list(map(lambda c: c.stock, corps)) 
        qstocks = list(map(lambda c: c.stock, corps_pq))
        ystocks = list(map(lambda c: c.stock, corps_py)) 

        name  = pd.Series(list(map(lambda c: c.name,        corps)), index=stocks)
        ipbr  = pd.Series(list(map(lambda c: 1. / c.pbr(),  corps)), index=stocks)
        iper  = pd.Series(list(map(lambda c: 1. / c.per(),  corps)), index=stocks)
        ipsr  = pd.Series(list(map(lambda c: 1. / c.psr(),  corps)), index=stocks)
        ipfcr = pd.Series(list(map(lambda c: 1. / c.pfcr(), corps)), index=stocks)
        sales = pd.Series(list(map(lambda c: c.sales,       corps)), index=stocks)
        net   = pd.Series(list(map(lambda c: c.net_income,  corps)), index=stocks)

        qsale  = pd.Series(list(map(lambda c: c.sales,      corps_pq)), index=qstocks)
        qnet   = pd.Series(list(map(lambda c: c.net_income, corps_pq)), index=qstocks)
        ysale  = pd.Series(list(map(lambda c: c.sales,      corps_py)), index=ystocks)
        ynet   = pd.Series(list(map(lambda c: c.net_income, corps_py)), index=ystocks)

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
        vm.to_excel(f'hqvm-{year}-{quarter}.xlsx')
        vm.to_csv(f'hqvm-{year}-{quarter}.csv')

        # print(len(corps_pq))
        # print(len(corps_py))
        # print(len(corps))
        # print(vm.head(numbers).index.tolist())
        return vm.head(numbers).index.tolist()
        

    def backtest(self, begin):        
        begin_year, begin_quarter = self.get_year_and_quarter(begin)
        end_year, end_quarter = self.get_prev_year_and_quarter(datetime.now())

        corps = None
        year = begin_year
        quarter = begin_quarter

        timestamp = []
        corps = []
        while year * 10 + quarter < end_year * 10 + end_quarter:
            dt = datetime(year=year, month=(quarter-1)*3+1, day=1)            
            print(f'Checking {year}-{quarter}Q, {dt.strftime("%Y-%m-%d")}')
            corp = self.choice(dt)
            corp = krx.load_corps(year, quarter)            

            quarter += 1
            if quarter == 5:
                quarter = 1
                year += 1

            if corp is None:
                continue
            
            timestamp.append((year, quarter))
            corps.append(corp)

        data = pd.DataFrame(pd.Series([0]), index=timestamp)
        
        if len(timestamp) > 1:
            for i in range(timestamp):
                t = timestamp[i]
                choices = corps[i]



        
        

        

        

from datetime import datetime
q = HQ_VM()
# q.choice(datetime.strptime('20210401', '%Y%m%d'))
q.backtest(datetime.strptime('20170401', '%Y%m%d'))
