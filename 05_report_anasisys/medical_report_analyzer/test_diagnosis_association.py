"""
测试诊断关联器功能
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from medical_report_analyzer.utils.llm_client import LLMClient
from medical_report_analyzer.utils.diagnosis_associator import DiagnosisAssociator
from medical_report_analyzer.config import LLM_CONFIG

def setup_test_data():
    """准备测试数据"""
    # 病变特征测试数据
    lesions = [
        {
            "解剖位置": "右肺上叶尖后段",
            "大小": "1.2cm",
            "形态": "结节状",
            "密度": "中等密度",
            "边界": "边缘不规则",
            "数量": "单发",
            "分布": "",
            "其他特征": "可见分叶、毛刺"
        },
        {
            "解剖位置": "左肺下叶基底段",
            "大小": "3mm",
            "形态": "小结节",
            "密度": "磨玻璃密度",
            "边界": "边界清晰",
            "数量": "多发",
            "分布": "散在分布",
            "其他特征": "钙化"
        },
        {
            "解剖位置": "纵隔",
            "大小": "1.5cm",
            "形态": "类圆形",
            "密度": "软组织密度",
            "边界": "边界清晰",
            "数量": "单发",
            "分布": "",
            "其他特征": "均匀密度"
        }
    ]
    
    # 诊断信息测试数据
    diagnoses = [
        {
            "类型": "高度疑似",
            "内容": "右肺上叶结节，考虑肺癌可能性大",
            "可信度": "高"
        },
        {
            "类型": "确诊",
            "内容": "左肺散在小结节，炎性病变",
            "可信度": "中"
        },
        {
            "类型": "待排除",
            "内容": "纵隔淋巴结肿大可能",
            "可信度": "低"
        }
    ]
    
    # 解剖结构测试数据
    structures = [
        {
            "标准名": "右肺上叶",
            "原文": "右肺上叶",
            "父结构": "右肺"
        },
        {
            "标准名": "左肺下叶",
            "原文": "左肺下叶",
            "父结构": "左肺"
        },
        {
            "标准名": "纵隔",
            "原文": "纵隔",
            "父结构": ""
        }
    ]
    
    return {
        "lesions": lesions,
        "diagnoses": diagnoses,
        "structures": structures
    }

def test_association(llm_client):
    """测试诊断关联功能"""
    print("==================================================")
    print("诊断关联测试")
    print("==================================================")
    
    # 获取测试数据
    test_data = setup_test_data()
    
    # 初始化诊断关联器
    associator = DiagnosisAssociator(llm_client)
    print(f"已初始化诊断关联器")
    
    # 执行关联
    print("\n开始建立诊断与病变的关联关系...\n")
    associations = associator.associate_features_with_diagnoses(
        test_data["lesions"],
        test_data["diagnoses"],
        test_data["structures"]
    )
    
    # 显示关联结果
    print("\n诊断到病变的映射结果:")
    for diagnosis_id, info in associations["诊断到病变映射"].items():
        # 找到对应的诊断
        diagnosis = next((d for d in test_data["diagnoses"] if d.get("诊断ID") == diagnosis_id), {})
        print(f"  - 诊断: {diagnosis.get('内容', '未知')}") 
        print(f"    相关病变: {info.get('相关病变列表', [])}")
        print(f"    关联理由: {info.get('关联理由', '未提供')}")
        print()
    
    # 显示病变到诊断的映射
    print("\n病变到诊断的映射结果:")
    for lesion_id, info in associations["病变到诊断映射"].items():
        # 找到对应的病变
        lesion = next((l for l in test_data["lesions"] if l.get("病变ID") == lesion_id), {})
        print(f"  - 病变位置: {lesion.get('解剖位置', '未知')}, 大小: {lesion.get('大小', '未知')}")
        print(f"    相关诊断: {info.get('相关诊断列表', [])}")
        print()
    
    # 显示关联强度
    print("\n关联强度评估:")
    for diagnosis_id, strengths in associations["关联强度"].items():
        # 找到对应的诊断
        diagnosis = next((d for d in test_data["diagnoses"] if d.get("诊断ID") == diagnosis_id), {})
        print(f"  - 诊断: {diagnosis.get('内容', '未知')}")
        
        for lesion_id, strength in strengths.items():
            # 找到对应的病变
            lesion = next((l for l in test_data["lesions"] if l.get("病变ID") == lesion_id), {})
            print(f"    与 '{lesion.get('解剖位置', '未知')}' 的关联强度: {strength:.2f}")
    
    # 保存结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"diagnosis_association_{timestamp}.json")
    
    # 更新测试数据
    test_results = {
        "原始数据": test_data,
        "关联结果": associations,
        "缓存统计": associator.get_cache_stats()
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    print("\n缓存统计:", associator.get_cache_stats())
    
    return associations

def test_end_to_end(llm_client):
    """端到端测试 - 解析报告并建立关联"""
    print("\n==================================================")
    print("端到端测试 - 报告解析与关联")
    print("==================================================")
    
    from medical_report_analyzer.utils.structure_extractor import StructureExtractor
    
    # 初始化结构提取器
    extractor = StructureExtractor(llm_client)
    print("已初始化结构提取器")
    
    # 测试报告
    report = """
    双肺含气良好，未见明显异常密度影。右肺上叶尖后段可见一枚约1.2cm大小的结节影，密度不均，边缘不规则，可见毛刺征和分叶征。纵隔内可见多枚肿大淋巴结，最大约1.5cm。双侧胸腔未见积液。心影大小、形态未见明显异常。
    """
    
    diagnosis = """
    1. 右肺上叶结节，考虑恶性肿瘤可能性大，建议进一步CT引导下穿刺或PET-CT检查；
    2. 纵隔淋巴结肿大，考虑转移可能。
    """
    
    print("\n原始报告:")
    print(report.strip())
    print("\n诊断:")
    print(diagnosis.strip())
    
    print("\n开始分析报告...")
    result = extractor.extract_core_information(report, diagnosis)
    
    # 显示分析结果
    print("\n分析结果:")
    
    # 显示解剖结构
    print("\n解剖结构:")
    for structure in result.get("解剖结构", []):
        print(f"  - {structure.get('标准名', '')}: {structure.get('原文', '')} (父结构: {structure.get('父结构', '')})")
    
    # 显示病变特征
    print("\n病变特征:")
    for lesion in result.get("病变特征", []):
        print(f"  - 位置: {lesion.get('解剖位置', '')}")
        print(f"    大小: {lesion.get('大小', '')}")
        print(f"    形态: {lesion.get('形态', '')}")
        print(f"    密度: {lesion.get('密度', '')}")
        print(f"    边界: {lesion.get('边界', '')}")
        print(f"    ID: {lesion.get('病变ID', '')}")
        if lesion.get("相关诊断列表"):
            print(f"    相关诊断: {lesion.get('相关诊断列表', [])}")
        print()
    
    # 显示诊断信息
    print("\n诊断信息:")
    for diagnosis in result.get("诊断信息", []):
        print(f"  - 类型: {diagnosis.get('类型', '')}")
        print(f"    内容: {diagnosis.get('内容', '')}")
        print(f"    ID: {diagnosis.get('诊断ID', '')}")
        if diagnosis.get("相关病变列表"):
            print(f"    相关病变: {diagnosis.get('相关病变列表', [])}")
            print(f"    关联理由: {diagnosis.get('关联理由', '')}")
        print()
    
    # 显示关联关系
    if "关联关系" in result:
        print("\n关联强度:")
        for diagnosis_id, strengths in result["关联关系"].get("关联强度", {}).items():
            # 找到对应的诊断
            diagnosis = next((d for d in result["诊断信息"] if d.get("诊断ID") == diagnosis_id), {})
            if diagnosis and strengths:
                print(f"  - 诊断 '{diagnosis.get('内容', '未知').split('，')[0]}' 的关联强度:")
                for lesion_id, strength in strengths.items():
                    # 找到对应的病变
                    lesion = next((l for l in result["病变特征"] if l.get("病变ID") == lesion_id), {})
                    if lesion:
                        print(f"    与 '{lesion.get('解剖位置', '未知')}' 的关联强度: {strength:.2f}")
    
    # 保存结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"end_to_end_association_{timestamp}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    
    return result

def main():
    """主函数"""
    print("==================================================")
    print("诊断关联器测试")
    print("==================================================")
    
    # 初始化LLM客户端
    provider = LLM_CONFIG.get("provider", "ollama")
    model = LLM_CONFIG.get("model", "qwen2.5:14b")
    print(f"使用配置的LLM模型: {provider}/{model}")
    
    llm_client = LLMClient(LLM_CONFIG)
    print(f"已初始化LLM客户端: {llm_client.provider} - {llm_client.model}")
    
    # 执行测试
    test_association(llm_client)
    
    # 执行端到端测试
    test_end_to_end(llm_client)
    
    print("\n==================================================")
    print("测试完成")
    print("==================================================")

if __name__ == "__main__":
    main()
