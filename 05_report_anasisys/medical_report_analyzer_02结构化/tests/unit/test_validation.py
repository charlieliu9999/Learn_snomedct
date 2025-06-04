#!/usr/bin/env python3
"""
测试结果验证器
"""

import json
import sys
import os
sys.path.append('.')
from utils.result_validator import StructuredResultValidator

def test_validation():
    """测试结果验证功能"""
    print("🔍 测试结果验证器...")
    
    # 读取原始分析结果
    file_path = 'data/processed/analyzed_reports_1_20250604_210332.json'
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取第一个分析结果
    result = data[0]
    
    # 创建验证器并验证
    validator = StructuredResultValidator()
    is_valid, issues, corrected = validator.validate_structured_result(result)
    
    print('\n=== 📊 质量评估报告 ===')
    print(validator.generate_quality_report(result))
    
    print('\n=== 🔧 修正后的结果预览 ===')
    corrected_data = corrected.get('结构化数据', {})
    
    print("\n🧬 解剖结构 (修正后):")
    for i, struct in enumerate(corrected_data.get('解剖结构', []), 1):
        print(f"  {i}. {struct.get('原文', '')} -> {struct.get('标准名', '')} (父结构: {struct.get('父结构', '')})")
    
    print("\n🔬 诊断信息 (修正后):")
    for i, diag in enumerate(corrected_data.get('诊断信息', []), 1):
        print(f"  {i}. 类型: {diag.get('类型', '')} | 描述: {diag.get('描述', '')}")
    
    print("\n🔗 影像诊断映射 (修正后):")
    for i, mapping in enumerate(corrected_data.get('影像诊断映射', []), 1):
        print(f"  {i}. {mapping.get('影像发现', '')} -> {mapping.get('对应诊断', '')} (置信度: {mapping.get('映射置信度', '')})")
    
    # 保存修正后的结果
    corrected_file = 'data/processed/corrected_analysis_result.json'
    with open(corrected_file, 'w', encoding='utf-8') as f:
        json.dump(corrected, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 修正后的结果已保存到: {corrected_file}")
    
    return is_valid, issues, corrected

if __name__ == "__main__":
    test_validation() 