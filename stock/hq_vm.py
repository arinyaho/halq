from quant_hq import QuantStock
import krx
import sys
import pandas as pd

class HQ_VM(QuantStock):
    def choice(self, date):
        year = date.year
        if date.month < 4:   quarter = 4
        elif date.month < 7:   quarter = 1
        elif date.month < 10:  quarter = 2
        else: quarter = 3

        print(year, quarter)
        corps_py = krx.load_corps(year-1, quarter)
        corps_pq = krx.load_corps(year-1 if quarter == 1 else year, 4 if quarter == 1 else quarter-1)
        corps = krx.load_corps(year, quarter)

        if corps_py == None or corps_pq == None or corps == None:
            print('Insufficient past data')
            sys.exit(1)

        stocks = list(map(lambda c: c.stock, corps)) 

        ipbr  = pd.Series(list(map(lambda c: 1. / c.pbr(),  corps)), index=stocks)
        iper  = pd.Series(list(map(lambda c: 1. / c.per(),  corps)), index=stocks)
        ipsr  = pd.Series(list(map(lambda c: 1. / c.psr(),  corps)), index=stocks)
        ipfcr = pd.Series(list(map(lambda c: 1. / c.pfcr(), corps)), index=stocks)

        ipbr_py  = pd.Series(list(map(lambda c: 1. / c.pbr(),  corps_py)), index=stocks)
        iper_py  = pd.Series(list(map(lambda c: 1. / c.per(),  corps_py)), index=stocks)
        ipsr_py  = pd.Series(list(map(lambda c: 1. / c.psr(),  corps_py)), index=stocks)
        ipfcr_py = pd.Series(list(map(lambda c: 1. / c.pfcr(), corps_py)), index=stocks)



        data = pd.concat([ipbr, iper, ipsr, ipfcr], axis=1)
        data.columns = ['IPBR', 'IPER', 'IPSR', 'IPFCR']

        print(len(corps_pq))
        print(len(corps_py))
        print(len(corps))

        print(data.tail())



from datetime import datetime
q = HQ_VM()
q.choice(datetime.strptime('20210401', '%Y%m%d'))
