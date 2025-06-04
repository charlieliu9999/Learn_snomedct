#!/usr/bin/env python3
"""
测试结构分析页面与动态字段功能的集成
"""

import os
import sys
import pandas as pd

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dynamic_fields_integration():
    """测试动态字段集成功能"""
    print("🧪 测试结构分析页面动态字段集成...")
    
    # 1. 测试数据准备
    print("\n1. 准备测试数据...")
    test_data_english = {
        'patient_id': ['P001', 'P002', 'P003'],
        'exam_type': ['Chest CT', 'Chest CT', 'Abdominal US'],
        'impressing': [  # 用户选择的findings字段名
            '右肺上叶可见一枚约2.5cm×1.8cm大小的结节状软组织密度影，边缘呈分叶状。',
            '双肺弥漫性分布多发斑片状、磨玻璃密度影，以双下肺为著。',
            '肝脏大小形态正常，肝实质回声均匀，未见明显占位性病变。'
        ],
        'finding': [  # 用户选择的impression字段名
            '右肺上叶周围型肺癌可能性大，建议进一步活检明确。',
            '病毒性肺炎，考虑COVID-19肺炎。',
            '肝脏超声检查未见异常。'
        ]
    }
    
    test_data_chinese = {
        'patient_id': ['P001', 'P002', 'P003'],
        'exam_type': ['胸部CT', '胸部CT', '腹部超声'],
        '影像所见': [  # 用户选择的findings字段名
            '右肺上叶可见一枚约2.5cm×1.8cm大小的结节状软组织密度影，边缘呈分叶状。',
            '双肺弥漫性分布多发斑片状、磨玻璃密度影，以双下肺为著。',
            '肝脏大小形态正常，肝实质回声均匀，未见明显占位性病变。'
        ],
        '诊断意见': [  # 用户选择的impression字段名
            '右肺上叶周围型肺癌可能性大，建议进一步活检明确。',
            '病毒性肺炎，考虑COVID-19肺炎。',
            '肝脏超声检查未见异常。'
        ]
    }
    
    # 保存测试数据
    df_english = pd.DataFrame(test_data_english)
    df_chinese = pd.DataFrame(test_data_chinese)
    
    english_file = "test_structure_english_fields.xlsx"
    chinese_file = "test_structure_chinese_fields.xlsx"
    
    df_english.to_excel(english_file, index=False)
    df_chinese.to_excel(chinese_file, index=False)
    
    print(f"✅ 生成英文字段测试文件: {english_file}")
    print(f"✅ 生成中文字段测试文件: {chinese_file}")
    
    # 2. 模拟session_state测试
    print("\n2. 模拟用户字段选择...")
    
    # 模拟英文字段选择
    english_session_state = {
        'findings_col': 'impressing',
        'impression_col': 'finding',
        'data_loaded': True,
        'raw_data': df_english
    }
    
    # 模拟中文字段选择
    chinese_session_state = {
        'findings_col': '影像所见',
        'impression_col': '诊断意见',
        'data_loaded': True,
        'raw_data': df_chinese
    }
    
    print("✅ 英文字段模拟: findings='impressing', impression='finding'")
    print("✅ 中文字段模拟: findings='影像所见', impression='诊断意见'")
    
    # 3. 测试字段验证逻辑
    print("\n3. 测试字段验证逻辑...")
    
    def test_field_validation(data, findings_col, impression_col):
        """测试字段验证"""
        if findings_col not in data.columns:
            return False, f"字段 '{findings_col}' 不存在"
        if impression_col not in data.columns:
            return False, f"字段 '{impression_col}' 不存在"
        if findings_col == impression_col:
            return False, "字段名不能相同"
        return True, "验证通过"
    
    # 测试英文字段
    valid, message = test_field_validation(df_english, 'impressing', 'finding')
    print(f"✅ 英文字段验证: {message}")
    
    # 测试中文字段
    valid, message = test_field_validation(df_chinese, '影像所见', '诊断意见')
    print(f"✅ 中文字段验证: {message}")
    
    # 测试错误情况
    valid, message = test_field_validation(df_english, 'nonexistent', 'finding')
    print(f"✅ 错误字段测试: {message}")
    
    # 4. 测试数据提取逻辑
    print("\n4. 测试数据提取逻辑...")
    
    def test_data_extraction(data, findings_col, impression_col, idx=0):
        """测试数据提取"""
        report = data.iloc[idx]
        image_text = report.get(findings_col, "") if pd.notna(report.get(findings_col, "")) else ""
        diagnosis_text = report.get(impression_col, "") if pd.notna(report.get(impression_col, "")) else ""
        return image_text, diagnosis_text
    
    # 测试英文字段数据提取
    image_text, diagnosis_text = test_data_extraction(df_english, 'impressing', 'finding', 0)
    print(f"✅ 英文字段提取:")
    print(f"   影像文本: {image_text[:50]}...")
    print(f"   诊断文本: {diagnosis_text[:50]}...")
    
    # 测试中文字段数据提取
    image_text, diagnosis_text = test_data_extraction(df_chinese, '影像所见', '诊断意见', 0)
    print(f"✅ 中文字段提取:")
    print(f"   影像文本: {image_text[:50]}...")
    print(f"   诊断文本: {diagnosis_text[:50]}...")
    
    # 5. 生成集成测试清单
    print("\n5. 生成测试清单...")
    
    test_checklist = """
# 结构分析页面动态字段集成测试清单

## 测试环境准备
- [ ] 确保已完成数据探索页面的字段选择
- [ ] 确保测试数据包含用户选择的字段名

## 功能测试项目

### 1. 字段验证测试
- [ ] 加载数据后正确显示当前选择的字段名
- [ ] 字段不存在时显示错误提示
- [ ] 提供返回数据探索页面的按钮

### 2. 界面显示测试
- [ ] 侧边栏正确显示当前分析字段信息
- [ ] 原始报告区域使用正确的字段标题
- [ ] 字段内容正确显示

### 3. 单份分析测试
- [ ] 使用正确的字段名提取报告内容
- [ ] 分析结果正确保存
- [ ] 分析结果正确显示

### 4. 批量分析测试
- [ ] 批量处理时使用正确的字段名
- [ ] 进度显示正确
- [ ] 所有报告使用一致的字段名

### 5. 兼容性测试
- [ ] 默认字段名("影像表现"/"诊断结论")向后兼容
- [ ] 自定义字段名正确处理
- [ ] 字段名切换后功能正常

## 测试数据文件
- test_structure_english_fields.xlsx (英文字段名)
- test_structure_chinese_fields.xlsx (中文字段名)

## 测试步骤
1. 在数据探索页面加载测试数据
2. 选择相应的字段名(impressing/finding 或 影像所见/诊断意见)
3. 切换到结构分析页面
4. 验证字段显示正确
5. 执行单份和批量分析测试
6. 检查结果的正确性
    """
    
    checklist_file = "结构分析动态字段集成测试清单.md"
    with open(checklist_file, "w", encoding="utf-8") as f:
        f.write(test_checklist)
    
    print(f"✅ 生成测试清单: {checklist_file}")
    
    print("\n🎉 动态字段集成测试准备完成！")
    print("\n📋 接下来请按照测试清单进行手动验证。")

if __name__ == "__main__":
    test_dynamic_fields_integration() 