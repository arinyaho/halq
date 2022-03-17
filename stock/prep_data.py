import pandas as pd
import sqlite3
import krx
import sys, os


def prep(begin_year, begin_quarter, end_year, end_quarter):
    corps = None
    year = begin_year
    quarter = begin_quarter
    sqlite_filename = 'krx.db'

    if os.path.exists(sqlite_filename):
        os.remove(sqlite_filename)

    conn = sqlite3.connect(sqlite_filename)
    while year * 10 + quarter < end_year * 10 + end_quarter:    
        print(f'Processing {year}-{quarter}Q')
        corps = krx.load_corps(year, quarter)
        if corps is not None:
            d = pd.DataFrame([c.__dict__ for c in corps], index=[c.stock for c in corps])
            d = d.drop(['stock'], axis=1)
            d.index.name = 'stock'
            d['year'] = year
            d['quarter'] = quarter
            d.to_sql('fin', conn, if_exists='append')
        
        quarter += 1
        if quarter == 5:
            quarter = 1
            year += 1
    
    cur = conn.cursor()
    cur.execute('CREATE INDEX index_year_quarter_stock on fin(year, quarter, stock)')
    cur.execute('CREATE INDEX index_year_quarter on fin(year, quarter)')
    conn.close()




if __name__ == '__main__':
    prep(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))