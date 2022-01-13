import yaml
import sys

def main():
    if len(sys.argv) != 2:
        print('Usage: port.py [yml file]')
        sys.exit(1)

    f = sys.argv[1]
    with open(f, 'r') as fin:
        try:
            port = yaml.safe_load(fin)
        except yaml.YAMLError as ex:
            print(ex)
            exit(2)
    prices = {}
    strats = port['portfolio']['strategies']
    for key in strats:
        print(strats[key])
        spy = pdr.get_data_yahoo('SPY', start=begin, end=end, progress=False)['Adj Close']



if __name__ == '__main__':
    main()