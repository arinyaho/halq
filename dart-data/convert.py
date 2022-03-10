import os
import shutil

quarter = {
    '1분기보고서': '1Q',
    '반기보고서':  '2Q',
    '3분기보고서': '3Q',
    '사업보고서':  '4Q'
}

types = {
    '현금흐름표'   : 'CF',
    '손익계산서'   : 'PL',
    '포괄손익계산서': 'CPL',
    '재무상태표'   : 'BS',
    '자본변동표'   : 'CE'
}

failed_list = []
try:
    os.mkdir('converted')
except FileExistsError:
    pass

files = os.listdir('.')
files.sort()
for f in files:
    if f.endswith('.txt'):
        print(f'Converting {f} ', end='')        

        year = int(f[:4])
        for key in quarter:
            if f.find(key) != -1:
                q = quarter[key]
                break
        for key in types:
            if f.find(key) != -1:
                t = types[key]
                break
        
        c = '-c' if f.find('연결') != -1 else ''

        nf = f'{year}-{q}-{t}{c}.txt'
        print(f'to {nf}')
        failed = False
        with open(f, 'r', encoding='euc-kr') as fin:
            with open(nf, 'w', encoding='utf8') as fout:
                try:
                    fout.write(fin.read())
                except:
                    failed = True
                    failed_list.append(f)
        if not failed:
            s = os.path.getsize(f)
            ns = os.path.getsize(nf)
            shutil.move(f, f'./converted/{f}')
        else:
            os.remove(nf)
        
        
            
    