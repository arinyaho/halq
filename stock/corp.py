from enum import Enum


class Market(str, Enum):
    KOSPI = 'KOSPI'
    KOSDAQ = 'KOSDAQ'


class Corp:
    def __init__(self, name:str, stock:str, market:Market):
        self.name = name
        self.stock = stock
        self.market = market
        self.sales = None
        self.net_income = None
        self.profit = None
        self.cash_flow = None
        #self.book_value = None
        self.assets = None
        self.liabilities = None
        self.price = None
        self.shares = None
        self.capex = None


    def per(self):
        try:
            return self.price * self.shares / self.net_income
        except ZeroDivisionError:
            return float('inf')

    
    def pbr(self):
        try:
            return self.price * self.shares / (self.assets - self.liabilities)
        except ZeroDivisionError:
            return float('inf')
    

    def psr(self):
        try:
            return self.price * self.shares / self.sales
        except ZeroDivisionError:
            return float('inf')


    def fcf(self):
        return self.cash_flow - self.capex

    
    def pfcr(self):
        try:
            return self.price * self.shares / self.fcf()
        except ZeroDivisionError:
            return float('inf')
   