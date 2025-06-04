#!/usr/bin/env python3
"""
调试计数问题
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def debug_counts():
    """调试计数问题"""
    
    # 加载第三个报告
    data_file = Path("data/processed/analyzed_reports_3_20250604_220917.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    target_report = results[2]
    
    print("原始数据:")
    original_features = target_report["结构化数据"].get("病变特征", [])
    original_mappings = target_report["结构化数据"].get("影像诊断映射", [])
    
    print(f"原始病变特征数量: {len(original_features)}")
    print(f"原始映射关系数量: {len(original_mappings)}")
    print(f"原始病变特征内容: {original_features}")
    print(f"原始映射关系内容: {original_mappings}")
    
    # 进行验证
    validator = StructuredResultValidator()
    is_valid, issues, corrected_result = validator.validate_structured_result(target_report)
    
    print("\n修正后数据:")
    corrected_features = corrected_result["结构化数据"].get("病变特征", [])
    corrected_mappings = corrected_result["结构化数据"].get("影像诊断映射", [])
    
    print(f"修正后病变特征数量: {len(corrected_features)}")
    print(f"修正后映射关系数量: {len(corrected_mappings)}")
    
    print(f"\n变化:")
    print(f"病变特征: {len(original_features)} → {len(corrected_features)} (变化: {len(corrected_features) - len(original_features):+d})")
    print(f"映射关系: {len(original_mappings)} → {len(corrected_mappings)} (变化: {len(corrected_mappings) - len(original_mappings):+d})")

if __name__ == "__main__":
    debug_counts() 