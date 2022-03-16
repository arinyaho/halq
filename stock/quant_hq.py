from abc import abstractmethod
from enum import Enum

import pandas as pd


class QuantStock:
    def __init__(self):
        pass

    # Print choices
    @abstractmethod
    def choice(self, date, numbers=20):
        pass
    
    # Get Pandas DataFrame of backtest data
    # containing column 'Growth' begining from 1 and 'MDD'
    @abstractmethod
    def backtest(self, begin, end):
        pass

    @classmethod
    def add_dd(cls, data) -> pd.DataFrame:
        data['dd'] = -1 * (data['Growth'].cummax() - data['Growth']) / data['Growth'].cummax()    
        return data

