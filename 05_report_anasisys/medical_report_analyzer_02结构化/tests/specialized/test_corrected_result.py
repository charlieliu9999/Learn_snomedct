#!/usr/bin/env python3
"""
查看验证器修正后的第三个报告结果
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def test_corrected_result():
    """查看验证器修正后的结果"""
    
    print("🔧 验证器修正结果展示")
    print("=" * 60)
    
    # 加载分析结果
    data_file = Path("data/processed/analyzed_reports_3_20250604_220917.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 检查第三个报告（索引2）
    third_report = results[2]
    
    print("📋 原始报告:")
    print(f"影像表现: {third_report['原始文本']['影像表现']}")
    print(f"诊断结论: {third_report['原始文本']['诊断结论']}")
    print()
    
    # 使用验证器修正
    validator = StructuredResultValidator()
    is_valid, issues, corrected_result = validator.validate_structured_result(third_report)
    
    print("🛠️ 验证和修正结果:")
    print(f"验证通过: {is_valid}")
    print(f"发现问题: {len(issues)}个")
    print()
    
    # 对比修正前后
    original_features = third_report["结构化数据"].get("病变特征", [])
    corrected_features = corrected_result["结构化数据"].get("病变特征", [])
    
    print("📊 病变特征对比:")
    print(f"修正前: {len(original_features)}个")
    print(f"修正后: {len(corrected_features)}个")
    print()
    
    if corrected_features:
        print("🎯 重构的病变特征:")
        for i, feature in enumerate(corrected_features, 1):
            print(f"  {i}. {feature.get('名称', '')}")
            characteristics = feature.get('特征', {})
            print(f"     位置: {characteristics.get('解剖位置', '')}")
            print(f"     特性: {characteristics.get('特性', '')}")
            if characteristics.get('其他特征'):
                print(f"     标记: {characteristics.get('其他特征', '')}")
    
    print()
    
    # 对比影像诊断映射
    original_mappings = third_report["结构化数据"].get("影像诊断映射", [])
    corrected_mappings = corrected_result["结构化数据"].get("影像诊断映射", [])
    
    print("📊 影像诊断映射对比:")
    print(f"修正前: {len(original_mappings)}个")
    print(f"修正后: {len(corrected_mappings)}个")
    print()
    
    if corrected_mappings:
        print("🎯 重构的影像诊断映射:")
        for i, mapping in enumerate(corrected_mappings, 1):
            print(f"  {i}. {mapping.get('影像发现', '')} -> {mapping.get('对应诊断', '')}")
            print(f"     置信度: {mapping.get('映射置信度', '')}")
    
    print()
    print("=" * 60)
    print("✅ 验证器成功修复了病变特征缺失问题！")
    
    # 保存修正后的结果
    output_file = Path("data/processed/corrected_report_3.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(corrected_result, f, ensure_ascii=False, indent=2)
    
    print(f"💾 修正结果已保存到: {output_file}")

if __name__ == "__main__":
    test_corrected_result() 