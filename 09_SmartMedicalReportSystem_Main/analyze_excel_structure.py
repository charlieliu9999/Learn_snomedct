import pandas as pd
import numpy as np

def analyze_excel_structure():
    """详细分析华西胸部CT报告的数据结构"""
    
    # 读取华西胸部CT报告
    file_path = '08_data/华西_胸部CT_报告.xlsx'
    
    try:
        # 读取完整数据
        df = pd.read_excel(file_path, engine='openpyxl')
        
        print("="*60)
        print("华西胸部CT报告 - 数据结构分析")
        print("="*60)
        
        # 基本信息
        print(f"\n数据维度：{df.shape}")
        print(f"总行数：{len(df)}")
        print(f"总列数：{len(df.columns)}")
        
        # 字段信息
        print(f"\n完整字段列表：")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")
        
        # 数据类型
        print(f"\n字段数据类型：")
        for col in df.columns:
            print(f"{col}: {df[col].dtype}")
        
        # 样本数据展示
        print(f"\n前3行完整数据：")
        for i in range(min(3, len(df))):
            print(f"\n--- 第{i+1}行 ---")
            for col in df.columns:
                value = df.iloc[i][col]
                if pd.isna(value):
                    print(f"{col}: [空值]")
                else:
                    # 截断过长文本
                    if isinstance(value, str) and len(value) > 100:
                        print(f"{col}: {value[:100]}...")
                    else:
                        print(f"{col}: {value}")
        
        # 关键字段统计
        key_fields = ['年龄', '性别', '诊断结论', '影像表现', '主诉', '诊断']
        available_key_fields = [f for f in key_fields if f in df.columns]
        
        print(f"\n关键字段统计：")
        for field in available_key_fields:
            non_null_count = df[field].notna().sum()
            print(f"{field}: {non_null_count}/{len(df)} 条记录有值")
            
            # 如果是分类字段，显示取值分布
            if field in ['性别'] and non_null_count > 0:
                print(f"  取值分布：{df[field].value_counts().to_dict()}")
        
        # 文本长度分析（针对诊断结论等长文本字段）
        text_fields = [col for col in df.columns if '诊断' in col or '表现' in col or '结论' in col]
        if text_fields:
            print(f"\n文本字段长度分析：")
            for field in text_fields:
                if field in df.columns:
                    lengths = df[field].dropna().astype(str).str.len()
                    if len(lengths) > 0:
                        print(f"{field}:")
                        print(f"  平均长度：{lengths.mean():.1f} 字符")
                        print(f"  最短：{lengths.min()} 字符")
                        print(f"  最长：{lengths.max()} 字符")
        
        return df
        
    except Exception as e:
        print(f"读取失败：{e}")
        return None

if __name__ == "__main__":
    df = analyze_excel_structure() 