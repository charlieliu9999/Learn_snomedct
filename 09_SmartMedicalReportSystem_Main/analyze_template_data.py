import pandas as pd

def analyze_template_data():
    print("=== 绥化报告模版数据分析 ===\n")
    
    # 读取数据
    df = pd.read_excel('08_data/绥化_报告_模版.xlsx', engine='openpyxl')
    
    print(f"数据总量: {len(df)} 行, {len(df.columns)} 列\n")
    
    # 显示所有字段名
    print("完整字段列表:")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. {col}")
    print()
    
    # 查看前20行数据，了解结构化模版的特点
    print("前20行数据:")
    print(df.head(20))
    print()
    
    # 分析诊断字段的唯一值
    print("诊断字段唯一值统计:")
    diagnosis_counts = df['诊断'].value_counts()
    print(f"总共 {len(diagnosis_counts)} 种不同诊断")
    print("前20个高频诊断:")
    print(diagnosis_counts.head(20))
    print()
    
    # 分析body_part_name字段
    if 'body_part_name' in df.columns:
        print("body_part_name 统计:")
        body_part_counts = df['body_part_name'].value_counts()
        print(body_part_counts)
    print()
    
    print("="*50)
    return df

if __name__ == "__main__":
    df = analyze_template_data() 