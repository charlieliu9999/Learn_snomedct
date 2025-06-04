#!/usr/bin/env python3
"""
使用有问题的数据测试验证器
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def test_validator_with_problematic_data():
    """使用有问题的数据测试验证器"""
    
    print("🧪 验证器质量检测测试")
    print("=" * 60)
    
    # 创建有问题的测试数据（模拟我们之前分析发现的问题）
    problematic_result = {
        "结构化数据": {
            "解剖结构": [
                {"原文": "双侧大脑半球", "标准名": "大脑半球", "父结构": "脑"},  # 丢失"双侧"信息
                {"原文": "脑实质", "标准名": "脑实质", "父结构": "脑"},
                {"原文": "幕上脑室系统", "标准名": "脑室系统", "父结构": "脑"},  # 丢失"幕上"信息
                {"原文": "脑沟、裂", "标准名": "脑沟", "父结构": "大脑"},  # 错误拆分1
                {"原文": "脑沟、裂", "标准名": "脑裂", "父结构": "大脑"},  # 错误拆分2（重复）
                {"原文": "脑回", "标准名": "脑回", "父结构": "大脑"},
                {"原文": "中线结构", "标准名": "中线结构", "父结构": "脑"}
            ],
            "病变特征": [
                {
                    "名称": "幕上脑室系统-扩大",
                    "特征": {
                        "解剖位置": "幕上脑室系统",
                        "特性": "扩大"
                    }
                },
                {
                    "名称": "脑沟、裂-增宽",
                    "特征": {
                        "解剖位置": "脑沟、裂",
                        "特性": "增宽"
                    }
                }
            ],
            "诊断信息": [
                {"类型": "其他发现", "描述": "脑萎缩"}  # 错误分类，应该是"变性病变"
            ],
            "影像诊断映射": [
                {
                    "影像发现": "综合影像表现",  # 使用了禁用的模糊描述
                    "对应诊断": "脑萎缩", 
                    "映射置信度": "低"
                }
            ]
        },
        "原始文本": {
            "影像表现": "双侧大脑半球对称，脑实质内未见明显异常密度影，幕上脑室系统扩大，脑沟、裂增宽，脑回变窄，中线结构居中。",
            "诊断结论": "脑萎缩。"
        }
    }
    
    print("📋 测试数据（模拟有问题的分析结果）:")
    print("- 解剖结构: 7个（包含重复和信息丢失）")
    print("- 诊断信息: 1个（分类错误）") 
    print("- 映射关系: 1个（使用模糊描述）")
    print()
    
    # 初始化验证器
    validator = StructuredResultValidator()
    
    # 进行验证
    print("🔍 开始验证...")
    is_valid, issues, corrected_result = validator.validate_structured_result(problematic_result)
    
    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 发现问题'}")
    print(f"发现问题数量: {len(issues)}")
    print()
    
    if issues:
        print("📋 发现的具体问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print()
        
        # 显示修正前后对比
        print("🔧 修正前后对比:")
        print()
        
        # 解剖结构对比
        print("📍 解剖结构修正:")
        original_structures = problematic_result["结构化数据"]["解剖结构"]
        corrected_structures = corrected_result["结构化数据"]["解剖结构"]
        
        print(f"  修正前数量: {len(original_structures)}")
        print(f"  修正后数量: {len(corrected_structures)}")
        
        print("  详细对比:")
        for i, (orig, corr) in enumerate(zip(original_structures, corrected_structures), 1):
            orig_name = orig.get("标准名", "")
            corr_name = corr.get("标准名", "")
            if orig_name != corr_name:
                print(f"    {i}. '{orig.get('原文', '')}': '{orig_name}' → '{corr_name}' ✅")
            else:
                print(f"    {i}. '{orig.get('原文', '')}': '{orig_name}' (无变化)")
        print()
        
        # 诊断信息对比
        print("🏥 诊断信息修正:")
        original_diagnoses = problematic_result["结构化数据"]["诊断信息"]
        corrected_diagnoses = corrected_result["结构化数据"]["诊断信息"]
        
        for orig, corr in zip(original_diagnoses, corrected_diagnoses):
            orig_type = orig.get("类型", "")
            corr_type = corr.get("类型", "")
            description = orig.get("描述", "")
            if orig_type != corr_type:
                print(f"  '{description}': '{orig_type}' → '{corr_type}' ✅")
            else:
                print(f"  '{description}': '{orig_type}' (无变化)")
        print()
        
        # 映射关系对比
        print("🔗 映射关系修正:")
        original_mappings = problematic_result["结构化数据"]["影像诊断映射"]
        corrected_mappings = corrected_result["结构化数据"]["影像诊断映射"]
        
        print(f"  修正前数量: {len(original_mappings)}")
        print(f"  修正后数量: {len(corrected_mappings)}")
        
        if len(original_mappings) != len(corrected_mappings):
            print("  映射关系已重新构建:")
            for i, mapping in enumerate(corrected_mappings, 1):
                print(f"    {i}. {mapping.get('影像发现', '')} → {mapping.get('对应诊断', '')} ({mapping.get('映射置信度', '')})")
        
        # 计算质量改进
        quality_score = max(0, (10 - len(issues)) / 10 * 100)
        print(f"\n📊 质量评估:")
        print(f"  修正前问题数: {len(issues)}")
        print(f"  修正后质量分数: {quality_score:.1f}%")
        
        # 保存修正结果
        output_file = Path("data/processed/validator_test_corrected.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(corrected_result, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 修正结果已保存到: {output_file}")
        
    else:
        print("🎉 数据质量良好，未发现问题")
    
    print("\n" + "=" * 60)
    print("✅ 验证器测试完成")

if __name__ == "__main__":
    test_validator_with_problematic_data() 