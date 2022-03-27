from enum import Enum
import sqlite3

class Market(str, Enum):
    KOSPI = 'KOSPI'
    KOSDAQ = 'KOSDAQ'


class Corp:
    def __init__(self, r: sqlite3.Row):
        for k in r.keys():
            setattr(self, k, r[k])

    def __str__(self):
        return self.stock