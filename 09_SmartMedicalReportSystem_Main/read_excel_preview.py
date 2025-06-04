import pandas as pd

files = [
    '08_data/华西_胸部CT_报告.xlsx',
    '08_data/绥化_报告_模版.xlsx',
    '08_data/华西_胸部CT_0509.xlsx'
]

for f in files:
    print(f'\n==== {f} ====')
    try:
        df = pd.read_excel(f, nrows=5, engine='openpyxl')
        print(df)
    except Exception as e:
        print(f'读取失败: {e}') 