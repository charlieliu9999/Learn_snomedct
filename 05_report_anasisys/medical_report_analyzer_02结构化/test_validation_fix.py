#!/usr/bin/env python3
"""
测试验证器修正效果的专门脚本
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def test_validation_fix():
    """测试验证器的修正效果"""
    
    print("🔍 验证器修正效果测试")
    print("=" * 80)
    
    # 加载第三个报告（有问题的报告）
    data_file = Path("data/processed/analyzed_reports_3_20250604_220917.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    target_report = results[2]
    
    print("📋 原始报告:")
    print(f"影像表现: {target_report['原始文本']['影像表现']}")
    print(f"诊断结论: {target_report['原始文本']['诊断结论']}")
    print()
    
    # 显示原始结果
    print("🔴 修正前的结构化数据:")
    original_data = target_report["结构化数据"]
    
    original_feature_count = len(original_data.get('病变特征', []))
    original_mapping_count = len(original_data.get('影像诊断映射', []))
    
    print(f"解剖结构数量: {len(original_data.get('解剖结构', []))}")
    print(f"病变特征数量: {original_feature_count}")
    print(f"诊断信息数量: {len(original_data.get('诊断信息', []))}")
    print(f"映射关系数量: {original_mapping_count}")
    
    print("\n病变特征详情:")
    features = original_data.get('病变特征', [])
    if not features:
        print("  ❌ 无病变特征")
    else:
        for i, feature in enumerate(features, 1):
            print(f"  {i}. {feature.get('名称', '未知')} - {feature.get('特征', {}).get('特性', '无描述')}")
    
    print("\n映射关系详情:")
    mappings = original_data.get('影像诊断映射', [])
    if not mappings:
        print("  ❌ 无映射关系")
    else:
        for i, mapping in enumerate(mappings, 1):
            print(f"  {i}. {mapping.get('影像发现', '')} → {mapping.get('对应诊断', '')}")
    
    print("\n" + "="*50)
    
    # 进行验证和修正
    validator = StructuredResultValidator()
    is_valid, issues, corrected_result = validator.validate_structured_result(target_report)
    
    print("🛠️ 验证过程:")
    print(f"验证通过: {is_valid}")
    print(f"发现问题: {len(issues)}个")
    
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n" + "="*50)
    
    # 显示修正后的结果
    print("🟢 修正后的结构化数据:")
    corrected_data = corrected_result["结构化数据"]
    
    print(f"解剖结构数量: {len(corrected_data.get('解剖结构', []))}")
    print(f"病变特征数量: {len(corrected_data.get('病变特征', []))}")
    print(f"诊断信息数量: {len(corrected_data.get('诊断信息', []))}")
    print(f"映射关系数量: {len(corrected_data.get('影像诊断映射', []))}")
    
    print("\n病变特征详情:")
    corrected_features = corrected_data.get('病变特征', [])
    if not corrected_features:
        print("  ❌ 仍无病变特征")
    else:
        for i, feature in enumerate(corrected_features, 1):
            feature_name = feature.get('名称', '未知')
            feature_detail = feature.get('特征', {})
            location = feature_detail.get('解剖位置', '')
            characteristic = feature_detail.get('特性', '')
            source = feature_detail.get('其他特征', '')
            print(f"  {i}. {feature_name}")
            print(f"     位置: {location}")
            print(f"     特性: {characteristic}")
            print(f"     来源: {source}")
    
    print("\n映射关系详情:")
    corrected_mappings = corrected_data.get('影像诊断映射', [])
    if not corrected_mappings:
        print("  ❌ 仍无映射关系")
    else:
        for i, mapping in enumerate(corrected_mappings, 1):
            print(f"  {i}. {mapping.get('影像发现', '')} → {mapping.get('对应诊断', '')} (置信度: {mapping.get('映射置信度', '')})")
    
    print("\n" + "="*80)
    
    # 对比总结
    print("📊 修正效果总结:")
    
    corrected_feature_count = len(corrected_data.get('病变特征', []))
    corrected_mapping_count = len(corrected_data.get('影像诊断映射', []))
    
    feature_change = corrected_feature_count - original_feature_count
    mapping_change = corrected_mapping_count - original_mapping_count
    
    print(f"病变特征: {original_feature_count} → {corrected_feature_count} (变化: {feature_change:+d})")
    print(f"映射关系: {original_mapping_count} → {corrected_mapping_count} (变化: {mapping_change:+d})")
    
    if corrected_feature_count > original_feature_count:
        print("✅ 成功重构了缺失的病变特征")
        print(f"   从 {original_feature_count} 个增加到 {corrected_feature_count} 个")
    
    if corrected_mapping_count > original_mapping_count:
        print("✅ 成功重构了缺失的映射关系")
        print(f"   从 {original_mapping_count} 个增加到 {corrected_mapping_count} 个")
    
    # 质量改进评估
    if original_feature_count == 0 and corrected_feature_count > 0:
        improvement_rate = "100%"
        print(f"🎯 病变特征提取改进率: {improvement_rate}")
    
    if original_mapping_count == 0 and corrected_mapping_count > 0:
        mapping_improvement_rate = "100%"
        print(f"🎯 映射关系建立改进率: {mapping_improvement_rate}")
    
    # 保存修正后的结果用于查看
    output_file = Path("corrected_report_3.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(corrected_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 修正后的结果已保存到: {output_file}")
    
    print("\n🔍 验证器工作原理说明:")
    print("1. 检测病变特征缺失: 分析影像表现文本中的病变关键词")
    print("2. 自动重构特征: 使用正则表达式提取位置-特征对")
    print("3. 重构映射关系: 基于重构的特征建立影像-诊断映射")
    print("4. 质量评估: 评估修正效果并生成报告")

if __name__ == "__main__":
    test_validation_fix() 