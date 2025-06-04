import pandas as pd
import numpy as np

def analyze_report_data():
    print("=== 华西胸部CT报告数据详细分析 ===\n")
    
    # 读取数据
    df = pd.read_excel('08_data/华西_胸部CT_报告.xlsx', engine='openpyxl')
    
    print(f"数据总量: {len(df)} 行, {len(df.columns)} 列\n")
    
    # 显示所有字段名
    print("完整字段列表:")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. {col}")
    print()
    
    # 数据类型和基本统计
    print("字段数据类型:")
    print(df.dtypes)
    print()
    
    # 查看前10行完整数据
    print("前10行完整数据:")
    print(df.head(10))
    print()
    
    # 重点分析可能的影像表现和诊断结论字段
    text_columns = []
    for col in df.columns:
        if df[col].dtype == 'object':
            # 检查文本长度
            avg_length = df[col].astype(str).str.len().mean()
            if avg_length > 20:  # 长文本字段
                text_columns.append(col)
    
    print("长文本字段分析:")
    for col in text_columns:
        lengths = df[col].astype(str).str.len()
        print(f"\n【{col}】")
        print(f"  平均长度: {lengths.mean():.1f} 字符")
        print(f"  最长: {lengths.max()} 字符")
        print(f"  最短: {lengths.min()} 字符")
        print(f"  样本内容:")
        for i, content in enumerate(df[col].head(3)):
            print(f"    {i+1}. {str(content)[:100]}...")
    
    print("\n" + "="*50)
    return df

if __name__ == "__main__":
    df = analyze_report_data() 