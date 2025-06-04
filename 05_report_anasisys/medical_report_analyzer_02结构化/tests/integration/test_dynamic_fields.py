#!/usr/bin/env python3
"""
测试动态字段功能 - 验证系统能正确处理用户选择的字段名
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data_with_custom_columns():
    """创建包含自定义列名的测试数据"""
    
    # 测试数据集1：英文列名
    test_data_en = {
        "patient_id": [f"P{i:03d}" for i in range(1, 51)],
        "exam_type": ["Chest CT"] * 25 + ["Abdominal CT"] * 25,
        "impressing": [  # 注意这里是 impressing，不是 impression
            f"Patient {i} shows findings of nodular lesions in the right upper lobe, measuring approximately 2.5cm×1.8cm. Spiculated margins noted." 
            for i in range(1, 51)
        ],
        "finding": [  # 注意这里是 finding，不是 findings
            f"Patient {i}: Right upper lobe lung cancer suspected. Recommend further biopsy for confirmation." 
            for i in range(1, 51)
        ],
        "exam_date": pd.date_range(start="2024-01-01", periods=50, freq="D"),
        "radiologist": [f"Dr. Smith {i % 5 + 1}" for i in range(50)]
    }
    
    # 测试数据集2：中文非标准列名
    test_data_cn = {
        "患者编号": [f"病人{i:03d}" for i in range(1, 51)],
        "检查项目": ["胸部CT"] * 30 + ["腹部CT"] * 20,
        "影像所见": [
            f"患者{i}：右肺上叶可见一枚约2.5cm×1.8cm大小的结节状软组织密度影，边缘呈分叶状，可见毛刺征。未见明显钙化。" 
            for i in range(1, 51)
        ],
        "诊断意见": [
            f"患者{i}：右肺上叶周围型肺癌可能性大，建议进一步活检明确。" 
            for i in range(1, 51)
        ],
        "检查时间": pd.date_range(start="2024-01-01", periods=50, freq="D"),
        "报告医师": [f"医生{i % 8 + 1}" for i in range(50)]
    }
    
    return pd.DataFrame(test_data_en), pd.DataFrame(test_data_cn)

def test_extract_basic_stats():
    """测试extract_basic_stats函数的动态字段功能"""
    print("🧪 测试extract_basic_stats函数的动态字段功能...")
    
    # 导入函数
    from utils.data_processor import extract_basic_stats
    
    # 创建测试数据
    df_en, df_cn = create_test_data_with_custom_columns()
    
    # 测试1：英文列名，指定impression_col
    print("\n📋 测试1：英文列名数据 (impressing, finding)")
    stats_en = extract_basic_stats(df_en, impression_col="finding")
    
    print(f"  - 报告总数: {stats_en['报告总数']}")
    print(f"  - 使用的诊断字段: {stats_en.get('诊断字段', '未检测到')}")
    if '前10位诊断分布' in stats_en:
        print(f"  - 诊断分布条目数: {len(stats_en['前10位诊断分布'])}")
        print(f"  - 前3个诊断: {list(stats_en['前10位诊断分布'].keys())[:3]}")
    
    # 测试2：中文列名，指定impression_col
    print("\n📋 测试2：中文列名数据 (影像所见, 诊断意见)")
    stats_cn = extract_basic_stats(df_cn, impression_col="诊断意见")
    
    print(f"  - 报告总数: {stats_cn['报告总数']}")
    print(f"  - 使用的诊断字段: {stats_cn.get('诊断字段', '未检测到')}")
    if '前10位诊断分布' in stats_cn:
        print(f"  - 诊断分布条目数: {len(stats_cn['前10位诊断分布'])}")
        print(f"  - 前3个诊断: {list(stats_cn['前10位诊断分布'].keys())[:3]}")
    
    # 测试3：不指定impression_col，测试自动检测
    print("\n📋 测试3：自动检测功能")
    stats_auto = extract_basic_stats(df_en, impression_col=None)
    print(f"  - 自动检测到的诊断字段: {stats_auto.get('诊断字段', '未检测到')}")
    
    return True

def test_auto_detection():
    """测试自动字段检测功能"""
    print("\n🔍 测试自动字段检测功能...")
    
    # 模拟不同的列名组合
    test_cases = [
        {
            "name": "标准中文列名",
            "columns": ["患者ID", "影像表现", "诊断结论", "检查日期"],
            "expected_findings": "影像表现",
            "expected_impression": "诊断结论"
        },
        {
            "name": "非标准中文列名", 
            "columns": ["编号", "影像所见", "诊断意见", "时间"],
            "expected_findings": "影像所见",
            "expected_impression": "诊断意见"
        },
        {
            "name": "英文列名",
            "columns": ["id", "impressing", "finding", "date"],
            "expected_findings": None,  # impressing不在标准关键词中
            "expected_impression": None   # finding不在标准关键词中
        },
        {
            "name": "标准英文列名",
            "columns": ["id", "findings", "impression", "date"],
            "expected_findings": "findings",
            "expected_impression": "impression"
        }
    ]
    
    # 导入检测函数
    from utils.data_processor import extract_basic_stats
    
    # 模拟关键词列表（从data_explorer.py复制）
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
    
    def auto_detect_column(column_names, keywords):
        """简化的自动检测函数"""
        if not column_names:
            return None

        column_names_lower_map = {col.lower(): col for col in column_names}
        
        # 精确匹配
        for keyword in keywords:
            if keyword.lower() in column_names_lower_map:
                return column_names_lower_map[keyword.lower()]
                
        # 子字符串匹配
        for col_name in column_names:
            col_name_lower = col_name.lower()
            for keyword in keywords:
                if keyword.lower() in col_name_lower:
                    return col_name
        
        return None
    
    for test_case in test_cases:
        print(f"\n  测试案例: {test_case['name']}")
        print(f"    列名: {test_case['columns']}")
        
        findings_detected = auto_detect_column(test_case['columns'], ALL_FINDINGS_KEYWORDS)
        impression_detected = auto_detect_column(test_case['columns'], ALL_IMPRESSION_KEYWORDS)
        
        print(f"    检测到的影像表现字段: {findings_detected}")
        print(f"    检测到的诊断结论字段: {impression_detected}")
        
        # 验证结果
        findings_ok = findings_detected == test_case['expected_findings']
        impression_ok = impression_detected == test_case['expected_impression']
        
        print(f"    影像表现检测: {'✅' if findings_ok else '❌'}")
        print(f"    诊断结论检测: {'✅' if impression_ok else '❌'}")

def test_data_browsing_defaults():
    """测试数据浏览的默认列选择逻辑"""
    print("\n📊 测试数据浏览默认列选择逻辑...")
    
    df_en, df_cn = create_test_data_with_custom_columns()
    
    # 模拟session_state
    test_cases = [
        {
            "name": "英文字段选择",
            "df": df_en,
            "findings_col": "impressing",
            "impression_col": "finding",
            "expected_defaults": ["impressing", "finding"]
        },
        {
            "name": "中文字段选择", 
            "df": df_cn,
            "findings_col": "影像所见",
            "impression_col": "诊断意见",
            "expected_defaults": ["影像所见", "诊断意见"]
        },
        {
            "name": "无字段选择",
            "df": df_en,
            "findings_col": None,
            "impression_col": None,
            "expected_defaults": list(df_en.columns[:2])  # 前两列
        }
    ]
    
    for test_case in test_cases:
        print(f"\n  测试案例: {test_case['name']}")
        
        # 模拟默认列选择逻辑
        default_columns = []
        if test_case['findings_col'] and test_case['findings_col'] in test_case['df'].columns:
            default_columns.append(test_case['findings_col'])
        if test_case['impression_col'] and test_case['impression_col'] in test_case['df'].columns:
            default_columns.append(test_case['impression_col'])
        
        if not default_columns:
            default_columns = list(test_case['df'].columns[:2]) if len(test_case['df'].columns) >= 2 else list(test_case['df'].columns)
        
        print(f"    期望的默认列: {test_case['expected_defaults']}")
        print(f"    实际的默认列: {default_columns}")
        print(f"    结果: {'✅' if default_columns == test_case['expected_defaults'] else '❌'}")

if __name__ == "__main__":
    print("🚀 开始测试动态字段功能...")
    
    # 创建测试数据文件
    df_en, df_cn = create_test_data_with_custom_columns()
    df_en.to_excel("test_data_english_fields.xlsx", index=False)
    df_cn.to_excel("test_data_chinese_fields.xlsx", index=False)
    print("📁 已创建测试数据文件:")
    print("  - test_data_english_fields.xlsx (impressing, finding)")
    print("  - test_data_chinese_fields.xlsx (影像所见, 诊断意见)")
    
    # 运行测试
    try:
        test_extract_basic_stats()
        test_auto_detection()
        test_data_browsing_defaults()
        
        print("\n🎉 所有动态字段功能测试完成！")
        print("\n💡 使用建议:")
        print("1. 在Streamlit应用中上传 test_data_english_fields.xlsx")
        print("2. 观察系统是否能正确处理 'impressing' 和 'finding' 字段")
        print("3. 验证数据浏览、统计分析、质量评估都基于用户选择的字段")
        print("4. 测试字段偏好保存和加载功能")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 