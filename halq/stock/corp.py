from __future__ import annotations
from enum import Enum


class Market(str, Enum):
    KOSPI = 'KOSPI'
    KOSDAQ = 'KOSDAQ'


class Corp:
    def __init__(self, name:str, stock:str, market:Market, year:int, quarter:int):
        self.name = name
        self.stock = stock
        self.market = market
        self.year = year
        self.quarter = quarter

        self.sales = None
        self.sales_cost = None
        self.net_income = None
        self.profit = None
        self.cash_flow = None
        self.assets = None
        self.equity = None
        self.liabilities = None
        self.price = None
        self.shares = None
        self.capex = None
        self.equity_issue = 0

        self.market_cap = None
        self.sales_profit = None
        self.book_value = None

        self.pbr = None
        self.per = None
        self.psr = None
        self.fcf = None
        self.pfcr = None
        self.roa = None
        self.roe = None
        self.gpa = None

        self.ipbr = None
        self.iper= None
        self.ipsr = None
        self.ipfcr = None

        self.profit_growth_qoq = None
        self.profit_growth_yoy = None
        self.net_income_growth_qoq = None
        self.net_income_growth_yoy = None
        self.bool_value_grwoth_qoq = None
        self.assets_growth_qoq = None
        self.fscore_k = None
