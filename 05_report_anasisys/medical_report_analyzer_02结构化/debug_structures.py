#!/usr/bin/env python3
"""
调试解剖结构数据
"""

import json
from pathlib import Path

def debug_structures():
    """调试解剖结构"""
    
    # 加载分析结果
    data_file = Path("data/processed/analyzed_reports_2_20250604_220510.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("=== 第一个报告的解剖结构分析 ===")
    
    first_result = results[0]
    structures = first_result.get("结构化数据", {}).get("解剖结构", [])
    
    print(f"原始文本: {first_result.get('原始文本', {}).get('影像表现', '')}")
    print(f"解剖结构数量: {len(structures)}")
    print()
    
    for i, structure in enumerate(structures, 1):
        print(f"{i}. 原文: '{structure.get('原文', '')}' -> 标准名: '{structure.get('标准名', '')}' (父结构: {structure.get('父结构', '')})")
    
    print("\n=== 检查是否存在脑沟、裂拆分问题 ===")
    
    # 检查是否有脑沟和脑裂分开的情况
    brain_sulci_items = [s for s in structures if "脑沟" in s.get("原文", "") or "脑裂" in s.get("原文", "") or "脑沟" in s.get("标准名", "") or "脑裂" in s.get("标准名", "")]
    
    if brain_sulci_items:
        print("发现与脑沟/脑裂相关的项目:")
        for item in brain_sulci_items:
            print(f"  - 原文: '{item.get('原文', '')}' -> 标准名: '{item.get('标准名', '')}'")
    else:
        print("未发现脑沟/脑裂相关项目")
    
    print("\n=== 人工检查潜在问题 ===")
    
    # 检查信息丢失
    for structure in structures:
        original = structure.get("原文", "")
        standard = structure.get("标准名", "")
        
        # 检查双侧信息丢失
        if "双侧" in original and "双侧" not in standard:
            print(f"⚠️  双侧信息丢失: '{original}' -> '{standard}'")
        
        # 检查幕上信息丢失
        if "幕上" in original and "幕上" not in standard:
            print(f"⚠️  幕上信息丢失: '{original}' -> '{standard}'")
        
        # 检查简化过度
        if len(original) > len(standard) + 5:  # 允许一些合理的简化
            print(f"⚠️  可能过度简化: '{original}' -> '{standard}'")
    
    print("\n=== 第一个报告的诊断信息分析 ===")
    
    diagnoses = first_result.get("结构化数据", {}).get("诊断信息", [])
    
    for i, diagnosis in enumerate(diagnoses, 1):
        print(f"{i}. 类型: '{diagnosis.get('类型', '')}' - 描述: '{diagnosis.get('描述', '')}'")
        
        # 检查诊断分类是否准确
        description = diagnosis.get("描述", "")
        diagnosis_type = diagnosis.get("类型", "")
        
        if "脑萎缩" in description:
            expected_type = "变性病变"
            if diagnosis_type != expected_type:
                print(f"⚠️  诊断分类可能不准确: '{description}' 被归类为 '{diagnosis_type}'，建议改为 '{expected_type}'")
            else:
                print(f"✅ 诊断分类正确: '{description}' -> '{diagnosis_type}'")

if __name__ == "__main__":
    debug_structures() 