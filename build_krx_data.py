
import sys
import numpy as np
import re
from enum import Enum

# http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101

class KRXMarket(Enum):
    KOSPI = 1
    KOSDAQ = 2


class krx:
    def __init__(self, name:str, stock:str, market:KRXMarket):
        self.name = name
        self.stock = stock
        self.market = market
        self.sales = None
        self.net_income = None
        self.profit = None
        self.cash_flow = None
        self.book_value = None
        self.price = None
        self.shares = None
    

year=  2021
quarter = 1
type = 'PL'

filename = f'{year}-{quarter}Q-{type}.txt'

dart_kospi_title = '유가증권시장상장법인'
dart_kosdaq_title = '코스닥시장상장법인'

corps = {}
corps_invalid = {}

# Sales, Net-Income
type = 'PL'
filename = f'{year}-{quarter}Q-{type}.txt'
with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:
    fields = fin.readline().split('\t')
    print(fields)
    
    recent_corp = None
    for line in fin:
        data = line.split('\t')
        type = data[3].strip()
        field = data[11].strip()
        field = re.sub('[^()가-힣]', '', field)
        value = data[12].strip()
        stock = data[1][1:-1]

        if stock in corps_invalid:
            continue

        if type == dart_kosdaq_title or type == dart_kospi_title:
            name = data[2].strip()
            market = KRXMarket.KOSDAQ if type == dart_kosdaq_title else KRXMarket.KOSPI
            
            if stock not in corps:
                corps[stock] = krx(name, stock, market)
                #if recent_corp is not None:
                    # print(f'{recent_corp.name}, {recent_corp.sales}, {recent_corp.net_income}')
                    #print(recent_corp.__dict__)
            
            c = corps[stock]
            recent_corp = c
            
            try:
                if field == '당기순이익' or field == '당기순이익(손실)' or field == '분기순이익' or field == '분기순이익(손실)':
                    if len(value.strip()) > 0:
                        net_income = int(value.replace(',', ''))
                        if c.net_income is not None and c.net_income != net_income:
                            print(name, stock, field)
                        c.net_income = net_income
                elif field == '매출액' or field == '수익(매출액)':
                    c.sales = int(value.replace(',', ''))
                elif field == '영업이익(손실)' or field == '영업이익':                
                    c.profit = int(value.replace(',', ''))
            except ValueError:
                print('Invalid', c.name, field, value)
                # del corps[stock]

# Cash-Flow
type = 'CF'
filename = f'{year}-{quarter}Q-{type}.txt'
with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
    recent_corp = None
    for line in fin:
        data = line.split('\t')
        type = data[3].strip()
        field = data[11].strip().replace("'", '').replace('"', '')
        field = re.sub('[^()가-힣]', '', field)
        stock = data[1][1:-1].strip()
        value = data[12].strip()

        if stock in corps_invalid:
            continue

        if type == dart_kosdaq_title or type == dart_kospi_title:            
            if stock not in corps:
                continue

            name = data[2].strip()            
            c = corps[stock]
            
            try:
                #if field.find('영업활동현금흐름') != -1 and field != '영업활동현금흐름':                    
                #     print(f'Debug: Unexpected field name: {field}')
                if field == '영업활동현금흐름' or field == '영업활동으로인한현금흐름':
                    c.cash_flow = int(value.replace(',', ''))                    
            except ValueError:
                print('Invalid', c.name, field, value)
                # del corps[stock]

# Book value
type = 'BS'
filename = f'{year}-{quarter}Q-{type}.txt'
with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
    recent_corp = None
    for line in fin:
        data = line.split('\t')
        type = data[3].strip()
        field = data[11].strip()
        stock = data[1][1:-1]
        value = data[12].strip()

        if stock in corps_invalid:
            continue

        if type == dart_kosdaq_title or type == dart_kospi_title:
            if stock not in corps:
                continue

            c = corps[stock]
            
            try:
                if field == '자본총계':
                    c.book_value = int(value.replace(',', ''))
            except ValueError:
                print('Invalid', c.name, field, value)
                # del corps[stock]

# Shares
filename = f'{year}-{1}Q-Stocks.csv'
with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
    fields = fin.readline().split(',')
    for line in fin:
        data = line.split(',')
        stock = data[0].strip().replace('"', '')
        market = data[2].strip().lower()

        if market != 'kospi' or market != 'kosdaq':
            continue

        if stock not in corps:
            continue

        c = corps[stock] 
        try:
            c.price = int(data[4].strip().replace('"', ''))
            c.shares = int(data[-1].strip().replace('"', ''))
        except ValueError:
            print('Invalid', c.name, data)
            continue


for corp in corps.values():
    asdict = corp.__dict__
    valid = True
    for v in asdict.values():
        if v is None:
            valid = False
    if not valid:
        print(corp.__dict__)
