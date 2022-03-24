import sqlite3
import requests
import os


_db_url = 'https://github.com/arinyaho/fin-data/raw/main/krx.db'
_db_path = 'krx.db'
_tbl_name = 'krx'


class KRX:    
    def __init__(self):
        if not os.path.exists(_db_path):
            self.__download_db()
        self.conn = sqlite3.connect(_db_path)
        self.cursor = self.conn.cursor()


    def __download_db(self):
        with open(_db_path, "wb") as fout:
            file = requests.get(_db_url, stream = True)
            for chunk in file.iter_content(chunk_size=1024):  
                if chunk:
                    fout.write(chunk)


    def get_corps(self, year: int, quarter: int):
        if quarter < 1 or quarter > 4:
            return None
        
        sql = f'SELECT * FROM {_tbl_name} WHERE year={year} AND quarter={quarter}'
        self.cursor.execute(sql)
        return self.cursor.fetchall()
        

        
        
        
        
    

        