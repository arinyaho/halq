from abc import abstractmethod

import pandas as pd


class QuantStock:
    def __init__(self, name):
        self.name = name

    # Print choices
    @abstractmethod
    def choice(self, year, quarter, decile=0, numbers=20):
        pass
    
    # Get Pandas DataFrame of backtest data
    # containing column 'Growth' begining from 1 and 'MDD'
    @abstractmethod
    def backtest(self, begin, num=20):
        pass

    @classmethod
    def add_dd(cls, data) -> pd.DataFrame:
        data['dd'] = -1 * (data['Growth'].cummax() - data['Growth']) / data['Growth'].cummax()    
        return data

