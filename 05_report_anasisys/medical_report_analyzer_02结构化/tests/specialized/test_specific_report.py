#!/usr/bin/env python3
"""
测试特定报告的病变特征缺失问题
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def test_specific_report():
    """测试第三个报告的病变特征缺失问题"""
    
    print("🔍 检查第三个报告的病变特征缺失问题")
    print("=" * 60)
    
    # 加载分析结果
    data_file = Path("data/processed/analyzed_reports_3_20250604_220917.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 检查第三个报告（索引2）
    third_report = results[2]
    
    print("📋 第三个报告详情:")
    print(f"影像表现: {third_report['原始文本']['影像表现']}")
    print(f"诊断结论: {third_report['原始文本']['诊断结论']}")
    print()
    
    # 分析结构化数据
    structured_data = third_report.get("结构化数据", {})
    
    print("📊 当前结构化结果:")
    print(f"解剖结构数量: {len(structured_data.get('解剖结构', []))}")
    print(f"病变特征数量: {len(structured_data.get('病变特征', []))}")  # 这里应该是0，有问题！
    print(f"诊断信息数量: {len(structured_data.get('诊断信息', []))}")
    print(f"影像诊断映射数量: {len(structured_data.get('影像诊断映射', []))}")
    print()
    
    # 分析影像表现文本，找出应该提取的病变特征
    image_text = third_report['原始文本']['影像表现']
    print("🔍 人工分析应该包含的病变特征:")
    
    expected_features = [
        {
            "名称": "枕叶-片状低密度影",
            "描述": "枕叶见片状低密度影",
            "解剖位置": "枕叶",
            "特性": "片状低密度影"
        },
        {
            "名称": "枕叶内-斑片状高密度影", 
            "描述": "其内尚可见斑片状高密度影",
            "解剖位置": "枕叶内",
            "特性": "斑片状高密度影"
        },
        {
            "名称": "中线结构-移位",
            "描述": "中线结构轻度移位",
            "解剖位置": "中线结构", 
            "特性": "轻度移位"
        },
        {
            "名称": "病变-脑回样强化",
            "描述": "增强扫描病变呈脑回样强化",
            "解剖位置": "枕叶病变",
            "特性": "脑回样强化"
        }
    ]
    
    for i, feature in enumerate(expected_features, 1):
        print(f"  {i}. {feature['名称']}")
        print(f"     位置: {feature['解剖位置']}")
        print(f"     特性: {feature['特性']}")
    
    print(f"\n❌ 严重问题: 应该提取{len(expected_features)}个病变特征，但实际提取了0个！")
    print()
    
    # 使用验证器检查
    print("🔧 使用验证器检查:")
    validator = StructuredResultValidator()
    is_valid, issues, corrected_result = validator.validate_structured_result(third_report)
    
    print(f"验证状态: {'✅ 通过' if is_valid else '❌ 发现问题'}")
    print(f"发现问题数: {len(issues)}")
    
    if issues:
        print("发现的问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("⚠️  验证器没有发现病变特征缺失问题！")
        print("这说明验证器需要增强功能。")
    
    print()
    
    # 检查是否是提取过程的问题
    print("🔎 分析可能的原因:")
    
    # 1. 检查调试信息中的提示词
    debug_info = third_report.get("调试信息", {})
    feature_prompt = debug_info.get("病变特征_提示词", "")
    
    if "枕叶见片状低密度影" in feature_prompt:
        print("  ✅ 提示词中包含了正确的影像表现文本")
    else:
        print("  ❌ 提示词中的文本与实际影像表现不匹配")
        print(f"     提示词文本开头: {feature_prompt[:100]}...")
        print(f"     实际影像表现: {image_text}")
    
    # 2. 检查是否LLM返回了空结果
    print("  📝 分析: LLM可能在病变特征提取步骤中返回了空结果")
    print("  🎯 建议: 需要改进病变特征提取的提示词和验证逻辑")
    
    print("\n" + "=" * 60)
    print("🎯 建议修复措施:")
    print("1. 增强验证器：添加病变特征缺失检测")
    print("2. 改进病变特征提取提示词")
    print("3. 添加提取结果的二次确认机制")
    print("4. 对这类严重问题进行重新处理")

if __name__ == "__main__":
    test_specific_report() 