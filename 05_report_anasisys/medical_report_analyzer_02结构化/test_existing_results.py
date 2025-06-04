#!/usr/bin/env python3
"""
测试现有分析结果的验证器
"""

import json
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.result_validator import StructuredResultValidator

def test_existing_results():
    """测试现有的分析结果"""
    
    # 加载分析结果
    data_file = Path("data/processed/analyzed_reports_2_20250604_220510.json")
    
    if not data_file.exists():
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"📁 加载了 {len(results)} 个分析结果")
        print("=" * 60)
        
        # 初始化验证器
        validator = StructuredResultValidator()
        
        for i, result in enumerate(results, 1):
            print(f"\n🔍 验证报告 {i}:")
            
            # 显示原始文本信息
            original_text = result.get("原始文本", {})
            image_text = original_text.get("影像表现", "未知")[:50] + "..."
            diagnosis_text = original_text.get("诊断结论", "未知")
            
            print(f"   影像表现: {image_text}")
            print(f"   诊断结论: {diagnosis_text}")
            
            # 进行验证
            is_valid, issues, corrected_result = validator.validate_structured_result(result)
            
            # 显示验证结果
            print(f"   验证状态: {'✅ 通过' if is_valid else '⚠️ 有问题'}")
            print(f"   发现问题: {len(issues)} 个")
            
            if issues:
                print("   具体问题:")
                for j, issue in enumerate(issues, 1):
                    print(f"     {j}. {issue}")
                
                # 显示关键修正
                print("\n   🔧 主要修正:")
                
                # 检查解剖结构修正
                original_structures = result.get("结构化数据", {}).get("解剖结构", [])
                corrected_structures = corrected_result.get("结构化数据", {}).get("解剖结构", [])
                
                if len(original_structures) != len(corrected_structures):
                    print(f"     - 解剖结构数量: {len(original_structures)} → {len(corrected_structures)}")
                
                # 检查诊断分类修正
                original_diagnoses = result.get("结构化数据", {}).get("诊断信息", [])
                corrected_diagnoses = corrected_result.get("结构化数据", {}).get("诊断信息", [])
                
                for orig, corr in zip(original_diagnoses, corrected_diagnoses):
                    if orig.get("类型") != corr.get("类型"):
                        print(f"     - 诊断分类: '{orig.get('类型')}' → '{corr.get('类型')}'")
                
                # 检查映射修正
                original_mappings = result.get("结构化数据", {}).get("影像诊断映射", [])
                corrected_mappings = corrected_result.get("结构化数据", {}).get("影像诊断映射", [])
                
                if len(original_mappings) != len(corrected_mappings):
                    print(f"     - 映射关系数量: {len(original_mappings)} → {len(corrected_mappings)}")
                
                # 计算质量分数
                quality_score = max(0, (10 - len(issues)) / 10 * 100)
                print(f"   质量分数: {quality_score:.1f}%")
                
                # 保存修正后的结果示例
                if i == 1:  # 只保存第一个修正结果作为示例
                    corrected_file = Path("data/processed/corrected_example.json")
                    with open(corrected_file, 'w', encoding='utf-8') as f:
                        json.dump(corrected_result, f, ensure_ascii=False, indent=2)
                    print(f"   💾 修正结果已保存到: {corrected_file}")
            
            else:
                print("   🎉 质量良好，无需修正")
            
            print("-" * 40)
        
        # 总结
        print(f"\n📊 验证总结:")
        total_reports = len(results)
        reports_with_issues = sum(1 for result in results if not validator.validate_structured_result(result)[0])
        
        print(f"   - 总报告数: {total_reports}")
        print(f"   - 有问题报告: {reports_with_issues}")
        print(f"   - 质量良好报告: {total_reports - reports_with_issues}")
        print(f"   - 整体质量率: {((total_reports - reports_with_issues) / total_reports * 100):.1f}%")
        
    except Exception as e:
        print(f"❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_existing_results() 