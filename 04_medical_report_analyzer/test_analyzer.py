#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from src.models.snomed_analyzer import SnomedAnalyzer

def test_analyzer():
    """测试SNOMED CT分析器在肺结节案例上的表现"""
    
    # 初始化分析器
    analyzer = SnomedAnalyzer()
    
    # 测试案例1：用户提供的肺结节案例
    test_case1 = "右上肺可见一枚类圆形结节，大小约8mm×7mm，边缘略呈毛刺状，CT值约45HU，较3个月前（6mm×5mm）略有增大。"
    test_case2 = "右下肺见一枚磨玻璃样结节，直径约5mm，边界清晰，与3个月前大小无明显变化。"
    
    # 分析测试案例
    result1 = analyzer.analyze_text(test_case1, 'findings')
    result2 = analyzer.analyze_text(test_case2, 'findings')
    
    # 打印分析结果
    print("=== 测试案例1分析结果 ===")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    print("\n=== 测试案例2分析结果 ===")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
    
    # 验证结果是否包含预期的实体
    expected_entities1 = ["右上肺", "类圆形结节", "8mm×7mm", "边缘略呈毛刺状", "CT值约45HU", "略有增大"]
    expected_entities2 = ["右下肺", "磨玻璃样结节", "5mm", "边界清晰", "大小无明显变化"]
    
    # 检查实体是否被正确识别
    entities1 = [entity["text"] for entity in result1.get("entities", [])]
    entities2 = [entity["text"] for entity in result2.get("entities", [])]
    
    print("\n=== 验证结果 ===")
    print(f"案例1预期实体: {expected_entities1}")
    print(f"案例1实际识别: {entities1}")
    print(f"案例1实体识别正确率: {sum(1 for e in expected_entities1 if e in entities1) / len(expected_entities1) * 100:.2f}%")
    
    print(f"\n案例2预期实体: {expected_entities2}")
    print(f"案例2实际识别: {entities2}")
    print(f"案例2实体识别正确率: {sum(1 for e in expected_entities2 if e in entities2) / len(expected_entities2) * 100:.2f}%")
    
    # 检查关系是否被正确识别
    relationships1 = result1.get("relationships", [])
    relationships2 = result2.get("relationships", [])
    
    print(f"\n案例1关系数量: {len(relationships1)}")
    print(f"案例2关系数量: {len(relationships2)}")
    
    # 验证关系的合理性
    entity_map1 = {entity["id"]: entity["text"] for entity in result1.get("entities", [])}
    entity_map2 = {entity["id"]: entity["text"] for entity in result2.get("entities", [])}
    
    print("\n=== 案例1关系验证 ===")
    for rel in relationships1:
        source = entity_map1.get(rel["source_id"], "未知")
        target = entity_map1.get(rel["target_id"], "未知")
        print(f"{source} --[{rel['relation_type']}]--> {target}")
    
    print("\n=== 案例2关系验证 ===")
    for rel in relationships2:
        source = entity_map2.get(rel["source_id"], "未知")
        target = entity_map2.get(rel["target_id"], "未知")
        print(f"{source} --[{rel['relation_type']}]--> {target}")

if __name__ == "__main__":
    test_analyzer()
