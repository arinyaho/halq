from quant_hq import QuantHQ
import krx

class HQ_VM(QuantHQ):
    def choice(self, date):
        year = date.year
        if date.month < 4:   quarter = 1
        elif date.month < 7:   quarter = 2
        elif date.month < 10:  quarter = 3
        else: quarter = 4

        print(year, quarter)
        corps = krx.load_corps(year, quarter)
        print(len(corps))



from datetime import datetime
q = HQ_VM()
q.choice(datetime.strptime('20210401', '%Y%m%d'))
