#!/usr/bin/env python3
"""
详细展示验证过程和修正差异
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def debug_validation_details():
    """详细展示验证过程和修正差异"""
    
    print("🔍 质量验证详细分析")
    print("=" * 80)
    
    # 加载最新的分析结果
    data_file = Path("data/processed/analyzed_reports_3_20250604_220917.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 分析第三个报告（索引为2，您提到的有问题的报告）
    target_report = results[2]
    
    print("📋 报告详情:")
    print(f"影像表现: {target_report['原始文本']['影像表现']}")
    print(f"诊断结论: {target_report['原始文本']['诊断结论']}")
    print()
    
    # 进行详细验证
    validator = StructuredResultValidator()
    is_valid, issues, corrected_result = validator.validate_structured_result(target_report)
    
    print("🛠️ 验证结果概览:")
    print(f"验证通过: {is_valid}")
    print(f"发现问题: {len(issues)}个")
    print()
    
    print("📝 发现的具体问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    print()
    
    # 详细对比解剖结构
    print("🏗️ 解剖结构修正对比:")
    original_structures = target_report["结构化数据"].get("解剖结构", [])
    corrected_structures = corrected_result["结构化数据"].get("解剖结构", [])
    
    print(f"原始数量: {len(original_structures)}个")
    print(f"修正数量: {len(corrected_structures)}个")
    print()
    
    # 逐项对比
    max_len = max(len(original_structures), len(corrected_structures))
    for i in range(max_len):
        print(f"第{i+1}项:")
        
        if i < len(original_structures):
            orig = original_structures[i]
            print(f"  原始: {orig.get('原文', '')} → {orig.get('标准名', '')} (父结构: {orig.get('父结构', '')})")
        else:
            print(f"  原始: [无]")
        
        if i < len(corrected_structures):
            corr = corrected_structures[i]
            print(f"  修正: {corr.get('原文', '')} → {corr.get('标准名', '')} (父结构: {corr.get('父结构', '')})")
        else:
            print(f"  修正: [无]")
        
        # 检查是否有修改
        if i < len(original_structures) and i < len(corrected_structures):
            orig_item = original_structures[i]
            corr_item = corrected_structures[i]
            
            changes = []
            if orig_item.get('标准名') != corr_item.get('标准名'):
                changes.append(f"标准名: '{orig_item.get('标准名')}' → '{corr_item.get('标准名')}'")
            if orig_item.get('父结构') != corr_item.get('父结构'):
                changes.append(f"父结构: '{orig_item.get('父结构')}' → '{corr_item.get('父结构')}'")
            
            if changes:
                print(f"  🔧 修改: {'; '.join(changes)}")
            else:
                print(f"  ✅ 无变化")
        
        print()
    
    # 详细对比诊断信息
    print("🩺 诊断信息修正对比:")
    original_diagnoses = target_report["结构化数据"].get("诊断信息", [])
    corrected_diagnoses = corrected_result["结构化数据"].get("诊断信息", [])
    
    for i, (orig, corr) in enumerate(zip(original_diagnoses, corrected_diagnoses), 1):
        print(f"诊断{i}:")
        print(f"  原始: 类型='{orig.get('类型', '')}' | 描述='{orig.get('描述', '')}'")
        print(f"  修正: 类型='{corr.get('类型', '')}' | 描述='{corr.get('描述', '')}'")
        
        if orig.get('类型') != corr.get('类型'):
            print(f"  🔧 类型修改: '{orig.get('类型')}' → '{corr.get('类型')}'")
        if orig.get('描述') != corr.get('描述'):
            print(f"  🔧 描述修改: '{orig.get('描述')}' → '{corr.get('描述')}'")
        
        if orig == corr:
            print(f"  ✅ 无变化")
        print()
    
    # 详细对比病变特征
    print("🔬 病变特征修正对比:")
    original_features = target_report["结构化数据"].get("病变特征", [])
    corrected_features = corrected_result["结构化数据"].get("病变特征", [])
    
    print(f"原始数量: {len(original_features)}个")
    print(f"修正数量: {len(corrected_features)}个")
    
    if len(original_features) != len(corrected_features):
        print(f"🔧 数量变化: {len(original_features)} → {len(corrected_features)}")
    
    # 显示具体的病变特征对比
    if len(original_features) == 0 and len(corrected_features) > 0:
        print("🚨 原始结果缺失病变特征，验证器自动重构了以下特征:")
        for i, feature in enumerate(corrected_features, 1):
            print(f"  {i}. {feature.get('位置', '')} - {feature.get('特征描述', '')} (来源: {feature.get('来源', '')})")
    else:
        max_features = max(len(original_features), len(corrected_features))
        for i in range(max_features):
            print(f"特征{i+1}:")
            if i < len(original_features):
                orig = original_features[i]
                print(f"  原始: {orig.get('位置', '')} - {orig.get('特征描述', '')}")
            else:
                print(f"  原始: [无]")
            
            if i < len(corrected_features):
                corr = corrected_features[i]
                print(f"  修正: {corr.get('位置', '')} - {corr.get('特征描述', '')} (来源: {corr.get('来源', '')})")
            else:
                print(f"  修正: [无]")
            print()
    
    # 详细对比映射关系
    print("\n🔗 影像诊断映射修正对比:")
    original_mappings = target_report["结构化数据"].get("影像诊断映射", [])
    corrected_mappings = corrected_result["结构化数据"].get("影像诊断映射", [])
    
    print(f"原始数量: {len(original_mappings)}个")
    print(f"修正数量: {len(corrected_mappings)}个")
    
    if len(original_mappings) == 0 and len(corrected_mappings) > 0:
        print("🚨 原始结果缺失映射关系，验证器自动重构了以下映射:")
        for i, mapping in enumerate(corrected_mappings, 1):
            print(f"  {i}. {mapping.get('影像发现', '')} → {mapping.get('对应诊断', '')} (置信度: {mapping.get('映射置信度', '')})")
    else:
        max_mappings = max(len(original_mappings), len(corrected_mappings))
        for i in range(max_mappings):
            print(f"映射{i+1}:")
            if i < len(original_mappings):
                orig = original_mappings[i]
                print(f"  原始: {orig.get('影像发现', '')} → {orig.get('对应诊断', '')} (置信度: {orig.get('映射置信度', '')})")
            else:
                print(f"  原始: [无]")
            
            if i < len(corrected_mappings):
                corr = corrected_mappings[i]
                print(f"  修正: {corr.get('影像发现', '')} → {corr.get('对应诊断', '')} (置信度: {corr.get('映射置信度', '')})")
            else:
                print(f"  修正: [无]")
            
            # 检查变化
            if i < len(original_mappings) and i < len(corrected_mappings):
                orig = original_mappings[i]
                corr = corrected_mappings[i]
                changes = []
                if orig.get('影像发现') != corr.get('影像发现'):
                    changes.append(f"影像发现: '{orig.get('影像发现')}' → '{corr.get('影像发现')}'")
                if orig.get('对应诊断') != corr.get('对应诊断'):
                    changes.append(f"对应诊断: '{orig.get('对应诊断')}' → '{corr.get('对应诊断')}'")
                if orig.get('映射置信度') != corr.get('映射置信度'):
                    changes.append(f"置信度: '{orig.get('映射置信度')}' → '{corr.get('映射置信度')}'")
                
                if changes:
                    print(f"  🔧 修改: {'; '.join(changes)}")
                else:
                    print(f"  ✅ 无变化")
            print()
    
    print("=" * 80)
    print("📊 验证规则说明:")
    print()
    print("1. 解剖结构验证:")
    print("   - 检测重复结构 (如 脑沟、裂 被拆分为 脑沟 + 脑裂)")
    print("   - 保留重要修饰词 (如 双侧、幕上)")
    print("   - 修正错误拆分 (将拆分项合并为完整概念)")
    print()
    print("2. 诊断信息验证:")
    print("   - 检查诊断分类准确性")
    print("   - 脑萎缩 → 变性病变")
    print("   - 脑梗塞 → 血管相关")
    print()
    print("3. 病变特征验证:")
    print("   - 检测缺失的病变特征")
    print("   - 基于关键词自动重构")
    print("   - 验证特征描述合理性")
    print()
    print("4. 影像诊断映射验证:")
    print("   - 检测模糊描述 (如 '综合影像表现')")
    print("   - 替换为具体病变特征")
    print("   - 评估映射置信度")

if __name__ == "__main__":
    debug_validation_details() 