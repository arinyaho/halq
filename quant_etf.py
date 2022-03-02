from abc import abstractmethod
from enum import Enum

import pandas as pd


class RebalanceDay(Enum):
    FIRST_DAY = 1
    LAST_DAY = 2


class QuantETF:
    def __init__(self, name):
        self.name = name

    # Print choice for rebalancing and the 
    @abstractmethod
    def rebalance(self, date):
        pass
    
    # Get Pandas DataFrame of backtest data
    # containing column 'Growth' begining from 1 and 'MDD'
    @abstractmethod
    def backtest(self, begin, end, seed=1, monthly_installment=0, rebalance_date=RebalanceDay.LAST_DAY, rebalance_month=1):
        pass

    @abstractmethod
    def find_best_month(self, begin, end, rebalance_date=RebalanceDay.LAST_DAY):
        pass

    @classmethod
    def add_dd(cls, data) -> pd.DataFrame:
        data['dd'] = -1 * (data['Growth'].cummax() - data['Growth']) / data['Growth'].cummax()    
        return data

