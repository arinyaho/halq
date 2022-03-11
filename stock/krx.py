from .corp import Market, Corp
import re


# http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101


_dart_code_sales = 'ifrs-full_Revenue'
_dart_code_net_income = 'ifrs-full_ProfitLoss'
_dart_code_cash_flow = 'ifrs-full_CashFlowsFromUsedInOperatingActivities'

_dart_kospi_title = '유가증권시장상장법인'
_dart_kosdaq_title = '코스닥시장상장법인'


def _load_pl(filename, corps):
    # Sales, Net-Income
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:
        print(f'Reading {filename}')        
        for line in fin:
            data = line.split('\t')
            type = data[3].strip()
            field = data[11].strip()
            field = re.sub('[^()가-힣]', '', field)
            field_code = data[10].strip()
            value = data[12].strip()
            stock = data[1][1:-1]

            if type == _dart_kosdaq_title or type == _dart_kospi_title:
                name = data[2].strip()
                market = Market.KOSDAQ if type == _dart_kosdaq_title else Market.KOSPI
                
                if stock not in corps:
                    corps[stock] = Corp(name, stock, market)
                
                c = corps[stock]
                
                try:
                    if field == '당기순이익' or field == '당기순이익(손실)' or field == '분기순이익' or field == '분기순이익(손실)' or field_code == _dart_code_net_income:
                        if len(value) > 0:
                            net_income = int(value.replace(',', ''))
                            c.net_income = net_income
                    elif field == '매출액' or field == "매출" or field == '수익(매출액)' or field_code == _dart_code_sales:
                        if len(value) > 0:
                            c.sales = int(value.replace(',', ''))
                    elif field == '영업이익(손실)' or field == '영업이익':
                        if len(value) > 0:
                            c.profit = int(value.replace(',', ''))
                except ValueError:
                    print('Invalid', c.name, field, value)
                    # del corps[stock]


def _load_cf(filename, corps):
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
        print(f'Reading {filename}')        
        for line in fin:
            data = line.split('\t')
            type = data[3].strip()
            field = data[11].strip().replace("'", '').replace('"', '')
            field = re.sub('[^()가-힣]', '', field)
            stock = data[1][1:-1].strip()
            value = data[12].strip()

            if type == _dart_kosdaq_title or type == _dart_kospi_title:            
                if stock not in corps:
                    continue

                name = data[2].strip()            
                c = corps[stock]
                
                try:
                    #if field.find('영업활동현금흐름') != -1 and field != '영업활동현금흐름':                    
                    #     print(f'Debug: Unexpected field name: {field}')
                    if field == '영업활동현금흐름' or field == '영업활동으로인한현금흐름' or filename == _dart_code_cash_flow:
                        if len(value) > 0:
                            c.cash_flow = int(value.replace(',', ''))                    
                except ValueError:
                    print('Invalid', c.name, field, value)
                    # del corps[stock]


def _load_bs(filename, corps):        
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
        print(f'Reading {filename}')        
        for line in fin:
            data = line.split('\t')
            type = data[3].strip()
            field = data[11].strip()
            stock = data[1][1:-1]
            value = data[12].strip()

            if type == _dart_kosdaq_title or type == _dart_kospi_title:
                if stock not in corps:
                    continue

                c = corps[stock]
                
                try:
                    if field == '자본총계':
                        c.book_value = int(value.replace(',', ''))
                except ValueError:
                    print('Invalid', c.name, field, value)
                    # del corps[stock]


def _load_shares(filename, corps):
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
        print(f'Reading {filename}')        
        for line in fin:
            data = line.split(',')
            stock = data[0].strip().replace('"', '')
            market = data[2].strip().lower().replace('"', '')

            if market != 'kospi' and market != 'kosdaq':
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

def _load_data(corps, year, quarter, type, c=False):
    cs = '-c' if c else ''
    filename = f'{year}-{quarter}Q-{type}{cs}.txt'
    if type == 'PL':    _load_pl(filename, corps)
    if type == 'CPL':   _load_pl(filename, corps)
    if type == 'CF':    _load_cf(filename, corps)
    if type == 'BS':    _load_bs(filename, corps)

def load_corps(year, quarter):
    corps = {}
    corps_invalid = {}

    # 손익계산서(연결)
    _load_data(corps, year, quarter, 'PL', False)    
    _load_data(corps, year, quarter, 'PL', True)

    # 포괄손익계산서(연결)
    _load_data(corps, year, quarter, 'CPL', False)    
    _load_data(corps, year, quarter, 'CPL', True)
    
    # 현금흐름표(연결)
    _load_data(corps, year, quarter, 'CF', False)    
    _load_data(corps, year, quarter, 'CF', True)

    # 재무상태표(연결)
    _load_data(corps, year, quarter, 'BS', False)    
    _load_data(corps, year, quarter, 'BS', True)

    # 시가총액, 상장주식수
    filename = f'{year}-{1}Q-Stocks.csv'
    _load_shares(filename, corps)

    for corp in corps.values():
        asdict = corp.__dict__
        valid = True
        for v in asdict.values():
            if v is None:
                valid = False
        if not valid:
            corps_invalid[corp.stock] = corp
            pass

    for stock in corps_invalid:
        del corps[stock]
    
    return corps

year = 2021
corps = load_corps(year, 1)
print(f'Coporations with full data: {len(corps)}')



'''
# Cash-Flow
type = 'CF'
filename = f'{year}-{quarter}Q-{type}.txt'


# Shares



for corp in corps.values():
    asdict = corp.__dict__
    valid = True
    for v in asdict.values():
        if v is None:
            valid = False
    if not valid:
        print(corp.__dict__)
'''