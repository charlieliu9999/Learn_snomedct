#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from src.models.snomed_analyzer import SnomedAnalyzer

def test_analyzer():
    """测试SNOMED CT分析器在多种医学影像报告案例上的表现"""
    
    # 初始化分析器
    analyzer = SnomedAnalyzer()
    
    # 测试案例集合
    test_cases = [
        {
            "name": "肺结节CT案例",
            "text": "右上肺可见一枚类圆形结节，大小约8mm×7mm，边缘略呈毛刺状，CT值约45HU，较3个月前（6mm×5mm）略有增大。右下肺见一枚磨玻璃样结节，直径约5mm，边界清晰，与3个月前大小无明显变化。",
            "section": "findings"
        },
        {
            "name": "肝脏超声案例",
            "text": "肝脏大小正常，形态规则，包膜光滑，实质回声均匀，未见明显异常回声。肝内管道结构清晰，肝静脉、门静脉显示清楚，未见明显扩张。",
            "section": "findings"
        },
        {
            "name": "脑部MRI案例",
            "text": "双侧大脑半球对称，脑沟、脑池及脑室系统未见异常。左侧颞叶可见一类圆形异常信号影，大小约2.3cm×2.1cm，T1WI呈等低信号，T2WI呈高信号，增强扫描呈环形强化。周围可见少量水肿带。",
            "section": "findings"
        },
        {
            "name": "胸部X线案例",
            "text": "两肺野透亮度正常，肺纹理清晰，未见明显异常密度影。心影大小正常，形态规则。两侧膈肌光滑，肋膈角锐利。纵隔未见增宽。",
            "section": "findings"
        }
    ]
    
    # 分析所有测试案例
    results = []
    for case in test_cases:
        print(f"\n=== 测试案例: {case['name']} ===")
        print(f"原文: {case['text']}")
        
        # 分析文本
        result = analyzer.analyze_text(case['text'], case['section'])
        
        # 保存结果
        results.append({
            "case": case,
            "result": result
        })
        
        # 打印分析结果
        print(f"\n分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 验证结果
        entities = result.get("entities", [])
        relationships = result.get("relationships", [])
        
        print(f"\n识别到的实体数量: {len(entities)}")
        print(f"识别到的关系数量: {len(relationships)}")
        
        # 检查关系的合理性
        if entities and relationships:
            entity_map = {entity["id"]: entity["text"] for entity in entities}
            print("\n关系验证:")
            for rel in relationships:
                source = entity_map.get(rel["source_id"], "未知")
                target = entity_map.get(rel["target_id"], "未知")
                print(f"{source} --[{rel['relation_type']}]--> {target}")
    
    # 保存测试结果到文件
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 test_results.json")

if __name__ == "__main__":
    test_analyzer()
