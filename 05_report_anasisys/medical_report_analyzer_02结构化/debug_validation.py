#!/usr/bin/env python3
"""
调试验证器问题
"""

import json
import sys
import os
sys.path.append('.')
from utils.result_validator import StructuredResultValidator

def debug_validation():
    """调试验证功能"""
    print("🐛 调试验证器...")
    
    # 读取原始分析结果
    with open('data/processed/analyzed_reports_1_20250604_210332.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = data[0]
    
    print("\n=== 📋 原始结果分析 ===")
    original_structures = result["结构化数据"]["解剖结构"]
    print("原始解剖结构:")
    for i, struct in enumerate(original_structures, 1):
        print(f"  {i}. 原文: '{struct['原文']}' -> 标准名: '{struct['标准名']}' (父结构: {struct['父结构']})")
    
    original_diagnosis = result["结构化数据"]["诊断信息"]
    print(f"\n原始诊断信息:")
    for i, diag in enumerate(original_diagnosis, 1):
        print(f"  {i}. 类型: '{diag['类型']}' | 描述: '{diag['描述']}'")
    
    original_mappings = result["结构化数据"]["影像诊断映射"]
    print(f"\n原始影像诊断映射:")
    for i, mapping in enumerate(original_mappings, 1):
        print(f"  {i}. 影像发现: '{mapping['影像发现']}' -> 诊断: '{mapping['对应诊断']}' (置信度: {mapping['映射置信度']})")
    
    print("\n=== 🔍 手动问题识别 ===")
    
    # 手动识别问题
    manual_issues = []
    
    # 1. 检查解剖结构重复
    seen_texts = {}
    for struct in original_structures:
        original_text = struct['原文']
        if original_text in seen_texts:
            manual_issues.append(f"解剖结构重复: '{original_text}' 出现 {seen_texts[original_text] + 1} 次")
            seen_texts[original_text] += 1
        else:
            seen_texts[original_text] = 1
    
    # 2. 检查信息丢失
    for struct in original_structures:
        if "双侧" in struct['原文'] and "双侧" not in struct['标准名']:
            manual_issues.append(f"信息丢失: '{struct['原文']}' 标准名丢失'双侧'")
        if "幕上" in struct['原文'] and "幕上" not in struct['标准名']:
            manual_issues.append(f"信息丢失: '{struct['原文']}' 标准名丢失'幕上'")
    
    # 3. 检查错误拆分
    brain_groove_count = 0
    for struct in original_structures:
        if struct['原文'] == "脑沟、裂":
            brain_groove_count += 1
    if brain_groove_count > 1:
        manual_issues.append(f"错误拆分: '脑沟、裂' 被拆分为 {brain_groove_count} 个条目")
    
    # 4. 检查诊断分类
    for diag in original_diagnosis:
        if "脑萎缩" in diag['描述'] and diag['类型'] == "其他发现":
            manual_issues.append(f"诊断分类错误: '脑萎缩' 被归类为 '{diag['类型']}' 而非 '变性病变'")
    
    # 5. 检查模糊映射
    for mapping in original_mappings:
        if "综合影像表现" in mapping['影像发现']:
            manual_issues.append(f"使用模糊描述: '{mapping['影像发现']}'")
    
    print(f"手动识别的问题数: {len(manual_issues)}")
    for i, issue in enumerate(manual_issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n=== 🔧 验证器测试 ===")
    validator = StructuredResultValidator()
    is_valid, validator_issues, corrected = validator.validate_structured_result(result)
    
    print(f"验证器识别的问题数: {len(validator_issues)}")
    for i, issue in enumerate(validator_issues, 1):
        print(f"  {i}. {issue}")
    
    print(f"\n验证器判断结果通过: {is_valid}")
    print(f"手动判断应该通过: {len(manual_issues) == 0}")
    
    # 检查验证信息
    if "验证信息" in corrected:
        验证信息 = corrected["验证信息"]
        print(f"\n验证信息中的状态: {验证信息.get('验证通过', 'unknown')}")
        print(f"验证信息中的问题数: {验证信息.get('发现问题数', 'unknown')}")
    
    return manual_issues, validator_issues

if __name__ == "__main__":
    debug_validation() 