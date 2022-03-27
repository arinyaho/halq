import sqlite3
import requests
import os
from typing import List, Dict

from .corp import Corp


_db_url = 'https://github.com/arinyaho/fin-data/raw/main/krx.db'
_db_path = 'krx.db'
_tbl_name = 'krx'


class KRX_Reader:
    def __init__(self):
        if not os.path.exists(_db_path):
            self.__download_db()
        self.__conn = sqlite3.connect(_db_path)
        self.__conn.row_factory = sqlite3.Row


    def __download_db(self):
        with open(_db_path, "wb") as fout:
            file = requests.get(_db_url, stream = True)
            for chunk in file.iter_content(chunk_size=1024):  
                if chunk:
                    fout.write(chunk)


    def get_corps(self, year: int, quarter: int) -> List[Corp]:
        if quarter < 1 or quarter > 4:
            return None
        
        cursor = self.__conn.cursor()
        sql = f'SELECT * FROM {_tbl_name} WHERE year={year} AND quarter={quarter}'
        cursor.execute(sql)
        ret = [Corp(row) for row in cursor.fetchall()]
        return ret
        
