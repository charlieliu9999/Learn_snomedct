import pandas as pd
import numpy as np

def analyze_excel_structure(file_path):
    """全面分析Excel文件的结构和内容"""
    print(f"\n{'='*60}")
    print(f"文件分析: {file_path}")
    print(f"{'='*60}")
    
    try:
        # 读取完整数据
        df = pd.read_excel(file_path, engine='openpyxl')
        
        print(f"数据维度: {df.shape[0]} 行 x {df.shape[1]} 列")
        print(f"\n列名清单:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\n数据类型:")
        for col in df.columns:
            print(f"  {col}: {df[col].dtype}")
        
        print(f"\n缺失值统计:")
        missing = df.isnull().sum()
        for col in df.columns:
            if missing[col] > 0:
                print(f"  {col}: {missing[col]} ({missing[col]/len(df)*100:.1f}%)")
        
        print(f"\n各列样本值预览:")
        for col in df.columns:
            print(f"\n--- {col} ---")
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) <= 5:
                print(f"  唯一值: {list(unique_vals)}")
            else:
                print(f"  样本值: {list(unique_vals[:3])} ... (共{len(unique_vals)}个唯一值)")
            
            # 如果是文本列且内容较长，显示长度统计
            if df[col].dtype == 'object':
                text_lengths = df[col].dropna().astype(str).str.len()
                if text_lengths.max() > 50:
                    print(f"  文本长度: 最短{text_lengths.min()}, 最长{text_lengths.max()}, 平均{text_lengths.mean():.1f}")
        
        return df
    
    except Exception as e:
        print(f"读取失败: {e}")
        return None

# 分析所有文件
files = [
    '08_data/华西_胸部CT_报告.xlsx',
    '08_data/绥化_报告_模版.xlsx'
]

dataframes = {}
for file_path in files:
    df = analyze_excel_structure(file_path)
    if df is not None:
        dataframes[file_path] = df 