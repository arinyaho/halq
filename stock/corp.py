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
    