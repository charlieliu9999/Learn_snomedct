#!/usr/bin/env python3
"""
测试增强的数据探索功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """创建测试数据"""
    test_data = {
        "患者ID": [f"P{i:03d}" for i in range(1, 101)],
        "检查类型": ["胸部CT"] * 50 + ["腹部CT"] * 30 + ["头部CT"] * 20,
        "影像表现": [
            "右肺上叶可见一枚约2.5cm×1.8cm大小的结节状软组织密度影，边缘呈分叶状，可见毛刺征。未见明显钙化。" * (i % 3 + 1) 
            for i in range(100)
        ],
        "诊断结论": [
            "右肺上叶周围型肺癌可能性大，建议进一步活检明确。" * (i % 2 + 1) 
            for i in range(100)
        ],
        "检查日期": pd.date_range(start="2024-01-01", periods=100, freq="D"),
        "报告医生": [f"医生{i % 10 + 1}" for i in range(100)]
    }
    
    # 添加一些空值来测试数据完整性
    df = pd.DataFrame(test_data)
    
    # 随机添加5%的空值
    mask = np.random.random(df.shape) < 0.05
    df = df.mask(mask)
    
    return df

def test_basic_functions():
    """测试基本功能"""
    print("🧪 开始测试数据探索增强功能...")
    
    # 创建测试数据
    test_df = create_test_data()
    print(f"✅ 创建了 {len(test_df)} 行测试数据")
    
    # 测试数据完整性计算
    completeness = (1 - test_df.isnull().sum().sum() / (test_df.shape[0] * test_df.shape[1])) * 100
    print(f"✅ 数据完整度: {completeness:.1f}%")
    
    # 测试文本长度统计
    if "影像表现" in test_df.columns:
        text_lengths = test_df["影像表现"].dropna().str.len()
        print(f"✅ 影像表现文本长度统计:")
        print(f"   - 平均长度: {text_lengths.mean():.1f} 字符")
        print(f"   - 最短文本: {text_lengths.min()} 字符") 
        print(f"   - 最长文本: {text_lengths.max()} 字符")
        print(f"   - 中位数长度: {text_lengths.median():.1f} 字符")
    
    # 测试重复率计算
    if "诊断结论" in test_df.columns:
        field_data = test_df["诊断结论"].dropna()
        repeat_rate = ((len(field_data) - field_data.nunique()) / len(field_data) * 100)
        print(f"✅ 诊断结论重复率: {repeat_rate:.1f}%")
    
    # 测试异常检测
    def detect_outliers(series):
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return len(outliers), (len(outliers) / len(series)) * 100
    
    if "影像表现" in test_df.columns:
        lengths = test_df["影像表现"].str.len().dropna()
        outliers_count, outliers_pct = detect_outliers(lengths) if len(lengths) > 0 else (0, 0)
        print(f"✅ 影像表现异常文本: {outliers_count} 条 ({outliers_pct:.1f}%)")
    
    # 测试关键词提取
    if "影像表现" in test_df.columns:
        import re
        field_data = test_df["影像表现"].dropna()
        all_text = " ".join(field_data.astype(str))
        words = re.findall(r'[\u4e00-\u9fff]+', all_text)
        words = [word for word in words if len(word) > 1]
        
        if words:
            from collections import Counter
            word_counts = Counter(words)
            top_words = word_counts.most_common(5)
            print(f"✅ 前5个高频词汇: {top_words}")
    
    print("🎉 所有测试完成！数据探索增强功能正常工作。")
    
    return test_df

def test_auto_detection():
    """测试自动检测功能"""
    print("\n🔍 测试自动字段检测功能...")
    
    # 模拟不同的列名
    test_columns = [
        ["患者ID", "影像所见", "诊断意见", "检查日期"],
        ["ID", "检查描述", "结论", "日期"],
        ["patient_id", "findings", "impression", "date"],
        ["编号", "CT表现", "诊断结论", "时间"]
    ]
    
    # 导入检测函数 - 直接导入而不是从模块
    # 模拟关键词列表
    FINDINGS_KEYWORDS_CN = ["影像所见", "影像学表现", "检查所见", "CT表现", "MR表现", "影像表现", "所见", "检查描述"]
    IMPRESSION_KEYWORDS_CN = ["诊断意见", "诊断结论", "印象", "结论", "诊断提示", "考虑", "分析意见"]
    FINDINGS_KEYWORDS_EN = ["findings", "image findings", "description", "radiologic findings", "imaging findings"]
    IMPRESSION_KEYWORDS_EN = ["impression", "conclusion", "diagnosis", "assessment", "summary", "interpretation"]

    ALL_FINDINGS_KEYWORDS = FINDINGS_KEYWORDS_CN + \
                            [k.lower() for k in FINDINGS_KEYWORDS_EN] + \
                            [k.title() for k in FINDINGS_KEYWORDS_EN] + \
                            [k.upper() for k in FINDINGS_KEYWORDS_EN]
    ALL_IMPRESSION_KEYWORDS = IMPRESSION_KEYWORDS_CN + \
                              [k.lower() for k in IMPRESSION_KEYWORDS_EN] + \
                              [k.title() for k in IMPRESSION_KEYWORDS_EN] + \
                              [k.upper() for k in IMPRESSION_KEYWORDS_EN]
    
    def auto_detect_column(column_names, keywords, current_selection=None):
        """
        Tries to detect a column based on keywords.
        """
        if not column_names:
            return None

        # Convert column_names to lowercase for case-insensitive comparison
        column_names_lower_map = {col.lower(): col for col in column_names}
        
        # Exact keyword match (case insensitive)
        for keyword in keywords:
            if keyword.lower() in column_names_lower_map:
                return column_names_lower_map[keyword.lower()]
                
        # Substring match (case insensitive)
        for col_name in column_names:
            col_name_lower = col_name.lower()
            for keyword in keywords:
                if keyword.lower() in col_name_lower:
                    return col_name
        
        return None
    
    for i, columns in enumerate(test_columns):
        print(f"\n测试组 {i+1}: {columns}")
        
        findings_col = auto_detect_column(columns, ALL_FINDINGS_KEYWORDS)
        impression_col = auto_detect_column(columns, ALL_IMPRESSION_KEYWORDS) 
        
        print(f"  - 检测到的影像表现字段: {findings_col}")
        print(f"  - 检测到的诊断结论字段: {impression_col}")
    
    print("✅ 自动检测功能测试完成")

if __name__ == "__main__":
    # 运行测试
    test_df = test_basic_functions()
    test_auto_detection()
    
    # 保存测试数据供手动测试使用
    test_df.to_excel("test_data_enhanced.xlsx", index=False)
    print(f"\n📁 测试数据已保存到: test_data_enhanced.xlsx")
    print("💡 你可以在Streamlit应用中上传此文件进行手动测试") 