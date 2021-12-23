import FinanceDataReader as fdr
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
import argparse
from datetime import datetime, timedelta

yf.pdr_override()

# 거래소별 전체 종목코드: KRX (KOSPI, KODAQ, KONEX), NASDAQ, NYSE, AMEX, S&P 500

#df_krx = fdr.StockListing('KRX')
#print(df_krx.head())


def parse():
    parser = argparse.ArgumentParser(description="Hal-To Quant")
    parser.add_argument('--strategy', '-s', type=str, help='Strategy')
    parser.add_argument('--date', '-d', type=str, help='Rebalancing base date')
    parser.add_argument('--backtest', action='store_true', help='Backtest')
    parser.add_argument('--begin', type=str, help='Backtest begin')
    parser.add_argument('--end', type=str, help='Backtest end')
    return parser.parse_args()


def profit(ticker, date, dayOffset):
    e = date
    if type(e) == str:
        e = datetime.datetime.strptime(e, '%Y-%m-%d')
    b = e + datetime.timedelta(days=-dayOffset)
    spy = fdr.DataReader(ticker, b, e)
    f = spy.head(1).iloc[0]['Close']
    r = spy.tail(1).iloc[0]['Close']
    return r/f - 1.


def dual_momentum_original(date):
    spy = profit('SPY', date, 365)
    efa = profit('EFA', date, 365)
    bil = profit('BIL', date, 365)

    print("Original Dual Momentum: Monthly Rebalancing")
    print("Yearly Profit (%s)" % date)
    print("  SPY: %f" % spy)
    print("  EFA: %f" % efa)
    print("  BIL: %f" % bil)

    if spy > bil:
        ticker = 'SPY' if spy > efa else 'EFA'
    else:
        ticker = 'AGG'

    print("Asset to buy: %s 100%%" % ticker)


def dual_momentum_original_backtest(begin, end):
    spy = pdr.get_data_yahoo('SPY', start=begin, end=end)['Close']
    efa = pdr.get_data_yahoo('EFA', start=begin, end=end)['Close']
    bil = pdr.get_data_yahoo('BIL', start=begin, end=end)['Close']
    dmo = pd.concat([spy, efa, bil], axis=1).dropna()
    dmo.columns = ['SPY', 'EFA', 'BIL']
    dmo = dmo.resample(rule='M').apply(lambda x: x[-1])

    
    print(dmo.head())

def main():
    args = parse()
    if args.strategy == 'dmo':     
        date = args.date if args.date is not None else datetime.now()
        
        if args.backtest:
            dual_momentum_original_backtest(args.begin, args.end)
        else:
            if args.date is None:
                date = datetime.now()
            dual_momentum_original(date)
    else:
        print('Strategy not supported: %s' % args.strategy)

if __name__ == '__main__':
    main()
