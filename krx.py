from pykrx import stock
from pykrx import bond

# import dart_fss as dart
 
import pandas as pd
 
from datetime import datetime, timedelta
from enum import Enum
import sys
import xml.etree.ElementTree as et
import zipfile
import io
import json
import requests
import os

# Read DART API Key
print('Seeting DART API Key')
dart_api_key = ''
with open('api/dart.api', 'r') as fin:
    dart_api_key = fin.read()
print(dart_api_key) 
 



class KRXMarket(Enum):
    KOSPI = 1
    KOSDAQ = 2

class krx:
    def __init__(self, name, stock_code, dart_code):
        self.name = name
        self.stock_code = stock_code
        self.dart_code = dart_code
        self.per = None
        self.psr = None
        self.pfcr = None
        self.pbr = None
        self.market = None



def info(corp_code):
    url = 'https://opendart.fss.or.kr/api/company.json'
    params = {
        'crtfc_key': dart_api_key,
        'corp_code': corp_code
    }
    response = requests.get(url, params)
    if response.status_code != 200:
        return None
    return json.loads(response.content)
 

def fs(corp_code, year):
    url = 'https://opendart.fss.or.kr/api/fnlttMultiAcnt.json'
    params = {
        'crtfc_key': dart_api_key,
        'corp_code': corp_code,
        'bsns_year': str(year),
        'reprt_code': '11011'
    }
    response = requests.get(url, params)    
    if response.status_code == 200:
        return response.text
    return None

 
# dart.set_api_key(dart_api_key)
now = datetime.today()

'''
begin_date = (now + timedelta(days=-180)).strftime('%Y%m%d')
print(begin_date)

# Read all corp codes
corp_list = dart.corp.get_corp_list().find_by

total_count = 0
corps = []

for corp in corp_list:
    total_count += 1
    if corp.stock_code is not None and len(corp.stock_code.strip()) > 0:
        corps.append(corp)
        print(f'{corp.corp_name}: {corp.stock_code}, {corp.corp_code}')

        report = corp.extract_fs(bgn_de=begin_date, report_tp='quarter')

        print(report)
        sys.exit(1)
        
        # PER

 
print(f'Corporations: {total_count}')
print(f'Stocks      : {len(corps)}') 
 
'''
print('Loading KOSPI/KOSDAQ Tickers')
kospi_tickers = set(stock.get_market_ticker_list(now.strftime('%Y%m%d'), market='KOSPI'))
kosdaq_tickers = set(stock.get_market_ticker_list(now.strftime('%Y%m%d'), market='KOSDAQ'))
print(f'KOSPI       : {len(kospi_tickers)}')
print(f'KOSDAQ      : {len(kosdaq_tickers)}')

if os.path.exists('corp_codes.xml'):
    print('Reading corporation list')
    xml = et.parse('corp_codes.xml')
else:
    print('Loading corporation list')
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    params = {'crtfc_key': dart_api_key}
    corps = requests.get(url, params)

    if corps.status_code != 200:
        print(corps.message)
        sys.exit(1)
    
    zf = zipfile.ZipFile(io.BytesIO(corps.content), "r")
    xml = ''
    for f in zf.infolist():
        xml += zf.read(f).decode('utf_8')
    with open('corp_codes.xml', 'w', encoding='utf_8') as fout:
        fout.write(xml)
    xml = et.fromstring(xml)
 
corps = []

# Collect KOSPI and KOSDAQ    
total = len(xml.getroot())
processed = 0
for c in xml.getroot():
    processed += 1
    if processed % 100 == 0:
        rate = processed*100/total
        print(f'\r{processed}/{total} ({rate:.1f} %)', end='')
    
    stock = c.find('stock_code').text.strip()
    if len(stock) == 0:
        continue

    name = c.find('corp_name').text.strip()
    code = c.find('corp_code').text.strip()

    is_kospi = stock in kospi_tickers
    is_kosdaq = stock in kosdaq_tickers

    if is_kospi or is_kosdaq:                                
        corp = krx(name, stock, code)
        corp.market = KRXMarket.KOSPI if is_kospi else KRXMarket.KOSDAQ
        corps.append(corp)
print(f'\rCorporations: {len(xml.getroot())}')

for c in corps:
    print(c.dart_code)
    ret = fs(c.dart_code, now.year)
    if ret is not None:
        fs_json = json.loads(ret)
        if fs_json['status'] == '000':
            ret = fs(c.dart_code, now.year-1)
            print(fs_json)
            sys.exit(1)

verbose = True
 
#kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
#print(kospi_tickers)
 
#kosdaq_tickers = stock.get_market_ticker_list(market="KODAQ")
#print(kosdaq_tickers)
 
 