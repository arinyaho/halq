from corp import Market, Corp
import re, sys


# http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101


_dart_code_sales1 = 'ifrs_Revenue'
_dart_code_sales2 = 'ifrs-full_Revenue'

_dart_code_net_income1 = 'ifrs_ProfitLoss'
_dart_code_net_income2 = 'ifrs-full_ProfitLoss'

_dart_code_cash_flow1 = 'ifrs_CashFlowsFromUsedInOperatingActivities'
_dart_code_cash_flow2 = 'ifrs-full_CashFlowsFromUsedInOperatingActivities'

# 무형자산의 취득
_dart_code_capex1 = 'ifrs_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities'
_dart_code_capex2 = 'ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities'
# 유형자산의 취득
_dart_code_capex3 = 'ifrs_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'
_dart_code_capex4 = 'ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'

_dart_kospi_title = '유가증권시장상장법인'
_dart_kosdaq_title = '코스닥시장상장법인'


def _load_pl(filename, corps):
    value_fields = set(['당기', '당기 1분기 3개월', '당기 반기 3개월', '당기 3분기 3개월'])

    # Sales, Net-Income
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:        
        fields = fin.readline().split('\t')
        print(f'Reading {filename}, fields: {len(fields)}')
        value_index = 12
        if len(fields[12].strip()) == 0:
            value_index = 13                
                
        for line in fin:
            data = line.split('\t')
            type = data[3].strip()
            field = data[11].strip()
            field = re.sub('[^()가-힣]', '', field)
            field_code = data[10].strip()

            value = data[value_index].strip()
            stock = data[1][1:-1]

            if type == _dart_kosdaq_title or type == _dart_kospi_title:
                name = data[2].strip()
                market = Market.KOSDAQ if type == _dart_kosdaq_title else Market.KOSPI
                
                if stock not in corps:
                    corps[stock] = Corp(name, stock, market)

                c = corps[stock]
                if value is None or len(value) == 0:
                    continue
                
                try:
                    if field == '당기순이익' or field == '당기순이익(손실)' or field == '분기순이익' or field == '분기순이익(손실)' or field_code == _dart_code_net_income1 or field_code == _dart_code_net_income2:
                        net_income = int(value.replace(',', ''))
                        c.net_income = net_income
                    elif field == '매출액' or field == "매출" or field == '수익(매출액)' or field_code == _dart_code_sales1 or field_code == _dart_code_sales2:
                        c.sales = int(value.replace(',', ''))
                    elif field == '영업이익(손실)' or field == '영업이익':
                        c.profit = int(value.replace(',', ''))
                except ValueError:
                    print('Invalid', c.name, field, value)
                    # del corps[stock]


def _load_cf(filename, corps):
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
        fields = fin.readline().split('\t')
        print(f'Reading {filename}, fields: {len(fields)}')
        value_index = 12
        if len(fields[12].strip()) == 0:
            value_index = 13     
        for line in fin:
            data = line.split('\t')
            type = data[3].strip()
            field = data[11].strip().replace("'", '').replace('"', '')
            field = re.sub('[^()가-힣]', '', field)
            field_code = data[10].strip()
            stock = data[1][1:-1].strip()
            value = data[value_index].strip()

            if type == _dart_kosdaq_title or type == _dart_kospi_title:            
                if stock not in corps:
                    continue

                c = corps[stock]
                
                if value is None or len(value) == 0:
                    continue

                try:
                    if field == '영업활동현금흐름' or field == '영업활동으로인한현금흐름' or field_code == _dart_code_cash_flow1 or field_code == _dart_code_cash_flow2:
                        c.cash_flow = int(value.replace(',', ''))
                    # elif field == '무형자산의취득' or field_code == _dart_code_capex1:
                    elif field_code == _dart_code_capex1 or field_code == _dart_code_capex2:
                        if c.capex is None:
                            c.capex = 0
                        c.capex += int(value.replace(',', ''))
                    # elif field == '유형자산의취득' or field_code == _dart_code_capex2:
                    elif field_code == _dart_code_capex3 or field_code == _dart_code_capex4:
                        if c.capex is None:
                            c.capex = 0
                        c.capex += int(value.replace(',', ''))
                except ValueError:
                    print('Invalid', c.name, field, value)
                    # del corps[stock]


def _load_bs(filename, corps):        
    with open('dart-data/' + filename, 'r', encoding='utf-8') as fin:    
        fields = fin.readline().split('\t')
        print(f'Reading {filename}, fields: {len(fields)}')
        value_index = 12
        if len(fields[12].strip()) == 0:
            value_index = 13        
        for line in fin:
            data = line.split('\t')
            type = data[3].strip()
            field = data[11].strip()
            stock = data[1][1:-1]
            value = data[value_index].strip()

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
    filename = f'{year}-{quarter}Q-Stocks.csv'
    _load_shares(filename, corps)

    for corp in corps.values():
        asdict = corp.__dict__
        valid = True
        # print(asdict)
        for v in asdict.values():
            if v is None:
                valid = False
        if not valid:
            corps_invalid[corp.stock] = corp
            pass

    for stock in corps_invalid:
        del corps[stock]
    
    return corps


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
    
    
'''
year = 2021
corps = load_corps(year, 1)
print(f'Coporations with full data: {len(corps)}')




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