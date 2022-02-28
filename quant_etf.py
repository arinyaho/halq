from abc import abstractmethod
import pandas as pd


class QuantETF:
    def __init__(self, name):
        self.name = name

    # Print choice for rebalancing and the 
    @abstractmethod
    def rebalance(self, date):
        pass
    
    # Get Pandas DataFrame of backtest data
    @abstractmethod
    def backtest(self, begin, end, rebalance_month=1) -> pd.DataFrame:
        pass

    @classmethod
    def add_dd(cls, data) -> pd.DataFrame:
        data['dd'] = -1 * (data['Growth'].cummax() - data['Growth']) / data['Growth'].cummax()    
        return data
