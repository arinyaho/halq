from quant_hq import QuantStock
import krx
import sys
import pandas as pd

class HQ_VM(QuantStock):
    @classmethod
    def get_year_and_quarter(cls, date):
        year = date.year
        if date.month < 4:   quarter = 4
        elif date.month < 7:   quarter = 1
        elif date.month < 10:  quarter = 2
        else: quarter = 3
        return year, quarter


    def choice(self, date, numbers=20):
        year, quarter = self.get_year_and_quarter(date)

        print(year, quarter)
        corps_py = krx.load_corps(year-1, quarter)
        corps_pq = krx.load_corps(year-1 if quarter == 1 else year, 4 if quarter == 1 else quarter-1)
        corps = krx.load_corps(year, quarter)

        if corps_py == None or corps_pq == None or corps == None:
            print('Insufficient past data')
            sys.exit(1)

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
        pass

        



from datetime import datetime
q = HQ_VM()
q.choice(datetime.strptime('20210401', '%Y%m%d'))
