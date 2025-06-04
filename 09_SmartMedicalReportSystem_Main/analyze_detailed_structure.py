import pandas as pd
import numpy as np

def analyze_excel_structure(file_path):
    """分析Excel文件的详细结构"""
    try:
        # 读取完整数据
        df = pd.read_excel(file_path, engine='openpyxl')
        
        print(f"\n{'='*60}")
        print(f"文件: {file_path}")
        print(f"{'='*60}")
        
        # 基本信息
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        
        # 字段信息
        print(f"\n字段结构:")
        for i, col in enumerate(df.columns):
            dtype = str(df[col].dtype)
            non_null = df[col].count()
            null_count = len(df) - non_null
            print(f"{i+1:2d}. {col:<20} | 类型: {dtype:<10} | 非空: {non_null:<5} | 空值: {null_count}")
        
        # 显示前3行样本数据
        print(f"\n前3行样本数据:")
        for i, row in df.head(3).iterrows():
            print(f"\n--- 第{i+1}行 ---")
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    value = "[空值]"
                elif isinstance(value, str) and len(str(value)) > 100:
                    value = str(value)[:100] + "..."
                print(f"{col}: {value}")
        
        return df
        
    except Exception as e:
        print(f"读取 {file_path} 失败: {e}")
        return None

# 分析主要文件
files = [
    '08_data/华西_胸部CT_报告.xlsx',
    '08_data/绥化_报告_模版.xlsx'
]

for file_path in files:
    df = analyze_excel_structure(file_path) 