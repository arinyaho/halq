from enum import Enum


class Market(Enum):
    KOSPI = 1
    KOSDAQ = 2


class Corp:
    def __init__(self, name:str, stock:str, market:Market):
        self.name = name
        self.stock = stock
        self.market = market
        self.sales = None
        self.net_income = None
        self.profit = None
        self.cash_flow = None
        self.book_value = None
        self.price = None
        self.shares = None
        self.capex = None


    def per(self):
        return self.price * self.shares / self.net_income

    
    def pbr(self):
        return self.price * self.shares / self.book_value
    

    def psr(self):
        return self.price * self.shares / self.sales


    def fcf(self):
        return self.cash_flow - self.capex

    
    def pfcr(self):
        return self.price * self.shares / self.fcf()
   