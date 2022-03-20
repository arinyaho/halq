import sqlite3
from typing import Dict
from corp import Corp

def load_corps(year: int, quarter: int) -> Dict[str, Corp]:
    sqlite_filename = 'krx.db'
    conn = sqlite3.connect(sqlite_filename)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    sql = f'SELECT * FROM fin WHERE year={year} AND quarter={quarter}'
    
    corps = {}
    for row in cursor.execute(sql):
        corp = Corp(row['name'], row['stock'], row['market'])
        corp.sales = row['sales']
        corp.net_income = row['net_income']
        corp.profit = row['profit']
        corp.cash_flow = row['cash_flow']
        corp.assets = row['assets']
        corp.liabilities = row['liabilities']
        corp.price = row['price']
        corp.shares = row['shares']
        corp.capex = row['capex']
        corps[corp.stock] = corp

    cursor.close()
    conn.close()
    return corps if len(corps) > 0 else None


if __name__ == '__main__':
    for year in range(2016, 2021):
        for quarter in range(1, 5):
            corps = load_corps(year, quarter)
            print(year, quarter, len(corps))
            print()
    
    year = 2021
    for quarter in range(1, 4):
        corps = load_corps(year, quarter)
        print(year, quarter, len(corps))
        print()
 