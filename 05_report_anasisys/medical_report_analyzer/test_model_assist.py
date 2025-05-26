#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型辅助处理器测试脚本
"""

import os
import sys
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入需要的模块
from utils.llm_client import LLMClient
from utils.structure_extractor import StructureExtractor
from utils.model_assist_processor import ModelAssistProcessor
from utils.knowledge_base import MedicalKnowledgeBase

# 测试数据 - 简单的病变特征和解剖结构
TEST_LESION_FEATURES = [
    {
        "解剖位置": "右肺上叶",
        "大小": "2.5cm",
        "形态": "类圆形",
        "密度": "软组织密度",
        "边界": "边缘不规则",
        "数量": "单发",
        "分布": "",
        "其他特征": "可见分叶、毛刺"
    },
    {
        "解剖位置": "右肺上叶尖后段",
        "大小": "1.2cm",
        "形态": "结节状",
        "密度": "中等密度",
        "边界": "边界模糊",
        "数量": "单发",
        "分布": "",
        "其他特征": "无钙化"
    },
    {
        "解剖位置": "左肺下叶基底段",
        "大小": "3mm",
        "形态": "小结节",
        "密度": "模糊影",
        "边界": "不清晰",
        "数量": "多发",
        "分布": "散在分布",
        "其他特征": ""
    }
]

# 使用中文解剖结构进行测试
TEST_ANATOMICAL_STRUCTURES = [
    {"原文": "右肺上叶", "标准名": "右肺上叶", "父结构": "右肺"},
    {"原文": "右肺中叶", "标准名": "右肺中叶", "父结构": "右肺"},
    {"原文": "右肺下叶", "标准名": "右肺下叶", "父结构": "右肺"},
    {"原文": "左肺上叶", "标准名": "左肺上叶", "父结构": "左肺"},
    {"原文": "左肺下叶", "标准名": "左肺下叶", "父结构": "左肺"}
]

def organize_structures(anatomical):
    """组织解剖结构（简化版）"""
    result = {}
    
    # 收集所有结构及其关系
    for structure in anatomical:
        std_name = structure.get("标准名", "")
        if not std_name:
            continue
            
        result[std_name] = {
            "原文": structure.get("原文", ""),
            "父结构": structure.get("父结构", ""),
            "子结构": []
        }
    
    # 建立父子关系
    for name, info in result.items():
        parent = info["父结构"]
        if parent and parent in result:
            if name not in result[parent]["子结构"]:
                result[parent]["子结构"].append(name)
    
    return result

def test_feature_standardization():
    """测试特征标准化功能 - 使用系统配置的模型"""
    print("="*50)
    print("测试特征标准化功能")
    print("="*50)
    
    # 从系统配置获取LLM配置
    from config import LLM_CONFIG
    import copy
    
    # 复制配置，避免修改全局配置
    config = copy.deepcopy(LLM_CONFIG)
    
    # 如果配置中没有API密钥，尝试从环境变量获取
    if not config.get("api_key"):
        config["api_key"] = os.environ.get("OPENAI_API_KEY", "")
    
    try:
        llm_client = LLMClient(config)
        print(f"已初始化LLM客户端: {config['provider']} - {config['model']}")
        
        # 初始化模型辅助处理器
        model_processor = ModelAssistProcessor(llm_client)
        print("已初始化模型辅助处理器")
        
        # 标准化病变特征
        print("\n原始病变特征:")
        for i, feature in enumerate(TEST_LESION_FEATURES):
            print(f"特征 {i+1}: {feature}")
        
        standardized_features = model_processor.batch_standardize_lesions(TEST_LESION_FEATURES)
        
        print("\n标准化后的病变特征:")
        for i, feature in enumerate(standardized_features):
            print(f"特征 {i+1}: {feature}")
            
        # 显示缓存统计
        cache_stats = model_processor.get_cache_stats()
        print(f"\n缓存统计: 命中 {cache_stats['hits']} 次, 未命中 {cache_stats['misses']} 次")
        
        return standardized_features
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

def test_lesion_mapping():
    """测试病变映射功能 - 使用系统配置的模型并进行中文处理"""
    print("\n" + "="*50)
    print("测试病变映射功能")
    print("="*50)
    
    # 从系统配置获取LLM配置
    from config import LLM_CONFIG
    import copy
    
    # 复制配置，避免修改全局配置
    config = copy.deepcopy(LLM_CONFIG)
    
    # 如果配置中没有API密钥，尝试从环境变量获取
    if not config.get("api_key"):
        config["api_key"] = os.environ.get("OPENAI_API_KEY", "")
    
    try:
        llm_client = LLMClient(config)
        print(f"已初始化LLM客户端: {config['provider']} - {config['model']}")
        
        # 组织解剖结构
        structure_map = organize_structures(TEST_ANATOMICAL_STRUCTURES)
        print("解剖结构组织完成:")
        for name, info in structure_map.items():
            print(f"  - {name}: 原文={info['原文']}")
        
        # 初始化模型辅助处理器
        model_processor = ModelAssistProcessor(llm_client)
        
        # 映射病变到解剖结构
        lesion_map = model_processor.map_lesions_to_structures(TEST_LESION_FEATURES, structure_map)
        
        print("\n病变映射结果:")
        for structure, lesions in lesion_map.items():
            print(f"\n解剖结构: {structure}")
            for lesion in lesions:
                print(f"  - {lesion.get('解剖位置')}: {lesion.get('形态')} ({lesion.get('大小')})")
                
        # 显示缓存统计
        cache_stats = model_processor.get_cache_stats()
        print(f"\n缓存统计: 命中 {cache_stats['hits']} 次, 未命中 {cache_stats['misses']} 次")
        
        return lesion_map
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

def test_end_to_end():
    """端到端测试 - 使用系统配置的模型进行中文结构化处理"""
    print("\n" + "="*50)
    print("端到端测试 - 简单报告分析")
    print("="*50)
    
    # 测试报告
    test_report = """
    双肺含气良好，未见明显异常密度影。右肺上叶尖后段可见一枚约1.2cm大小的结节影，密度均匀，边界尚清，未见明显分叶、毛刺征。纵隔内未见明显肿大淋巴结。双侧胸腔未见积液。心影大小、形态未见明显异常。
    """
    
    test_diagnosis = """
    右肺上叶小结节影，考虑炎性病变可能性大，建议抗炎治疗后复查。
    """
    
    # 从系统配置获取LLM配置
    from config import LLM_CONFIG
    import copy
    
    # 复制配置，避免修改全局配置
    config = copy.deepcopy(LLM_CONFIG)
    
    # 如果配置中没有API密钥，尝试从环境变量获取
    if not config.get("api_key"):
        config["api_key"] = os.environ.get("OPENAI_API_KEY", "")
    
    try:
        llm_client = LLMClient(config)
        print(f"已初始化LLM客户端: {config['provider']} - {config['model']}")
        
        # 初始化结构提取器
        extractor = StructureExtractor(llm_client)
        print("已初始化结构提取器")
        
        # 分析报告
        print("\n原始报告:")
        print(test_report)
        print("\n诊断:")
        print(test_diagnosis)
        
        print("\n开始分析报告...")
        result = extractor.analyze_single_report(test_report, test_diagnosis)
        
        # 打印结构化结果
        print("\n分析结果:")
        if "结构化数据" in result:
            print("\n解剖结构:")
            for structure in result["结构化数据"].get("解剖结构", []):
                print(f"  - {structure.get('原文')}: {structure.get('标准名')} (父结构: {structure.get('父结构')})")
                
            print("\n病变特征:")
            for lesion in result["结构化数据"].get("病变特征", []):
                print(f"  - 位置: {lesion.get('解剖位置')}")
                print(f"    大小: {lesion.get('大小')}")
                print(f"    形态: {lesion.get('形态')}")
                print(f"    密度: {lesion.get('密度')}")
                print(f"    边界: {lesion.get('边界')}")
                
            print("\n诊断信息:")
            for diagnosis in result["结构化数据"].get("诊断信息", []):
                print(f"  - {diagnosis.get('类型')}: {diagnosis.get('内容')}")
        
        # 打印调试信息
        if "调试信息" in result and "模型处理器_缓存统计" in result["调试信息"]:
            cache_stats = result["调试信息"]["模型处理器_缓存统计"]
            print(f"\n缓存统计: 命中 {cache_stats.get('hits', 0)} 次, 未命中 {cache_stats.get('misses', 0)} 次")
        
        return result
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

def save_result(result, name):
    """保存测试结果"""
    if not result:
        return
        
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{name}_{timestamp}.json")
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"\n结果已保存到: {filename}")

if __name__ == "__main__":
    print("="*50)
    print("模型辅助处理器测试 - 中文结构化处理")
    print("="*50)
    
    # 检查LLM配置
    from config import LLM_CONFIG
    print(f"使用配置的LLM模型: {LLM_CONFIG['provider']}/{LLM_CONFIG['model']}")
    
    # 测试特征标准化
    standardized_features = test_feature_standardization()
    save_result(standardized_features, "standardized_features")
    
    # 测试病变映射
    lesion_map = test_lesion_mapping()
    save_result(lesion_map, "lesion_map")
    
    # 端到端测试
    analysis_result = test_end_to_end()
    save_result(analysis_result, "analysis_result")
    
    print("\n"+"="*50)
    print("测试完成")
    print("="*50)
