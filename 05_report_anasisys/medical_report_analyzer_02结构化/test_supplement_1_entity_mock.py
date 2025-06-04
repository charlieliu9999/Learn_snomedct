#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充测试1: 实体识别功能模拟测试
绕过LLM API问题，使用模拟响应验证业务逻辑
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from utils.structure_extractor import StructureExtractor
from utils.config_manager import ConfigManager

class TestEntityExtractionWithMock(unittest.TestCase):
    """实体识别功能模拟测试类"""
    
    def setUp(self):
        """测试准备"""
        self.config_manager = ConfigManager()
        
        # 创建模拟LLM客户端
        self.mock_llm_client = Mock()
        
        # 初始化实体提取器
        self.extractor = StructureExtractor(self.mock_llm_client)
        
        # 测试用医学报告
        self.test_report = """
        患者张某，男，45岁。主诉：胸痛3天。
        
        CT检查显示：
        1. 双肺多发小结节，最大约8mm，位于右上肺叶
        2. 纵隔淋巴结肿大，最大短径约15mm
        3. 胸腔少量积液
        
        印象：
        1. 双肺多发小结节，性质待定，建议随访或进一步检查
        2. 纵隔淋巴结肿大
        3. 胸腔积液
        """
        
        # 模拟LLM响应数据
        self.mock_responses = {
            'anatomy': {
                'structures': ['双肺', '右上肺叶', '纵隔', '胸腔'],
                'locations': ['双侧', '右上', '纵隔', '胸腔内'],
                'confidence': 0.92
            },
            'pathology': {
                'findings': ['多发小结节', '淋巴结肿大', '胸腔积液'],
                'measurements': ['8mm', '15mm'],
                'characteristics': ['多发', '小', '肿大', '少量'],
                'confidence': 0.88
            },
            'diagnosis': {
                'impressions': ['双肺多发小结节，性质待定', '纵隔淋巴结肿大', '胸腔积液'],
                'recommendations': ['随访', '进一步检查'],
                'urgency': 'medium',
                'confidence': 0.85
            }
        }
    
    def test_anatomy_extraction_with_mock(self):
        """测试解剖结构提取（模拟响应）"""
        print("\n🧪 测试解剖结构提取（模拟响应）...")
        
        # 设置模拟响应 - 返回解剖结构列表格式
        mock_anatomical_structures = [
            {"原文": "双肺", "标准名称": "双侧肺", "父结构": "呼吸系统"},
            {"原文": "右上肺叶", "标准名称": "右上肺叶", "父结构": "右肺"},
            {"原文": "纵隔", "标准名称": "纵隔", "父结构": "胸腔"},
            {"原文": "胸腔", "标准名称": "胸腔", "父结构": "胸部"}
        ]
        self.mock_llm_client.extract_json.return_value = {"解剖结构": mock_anatomical_structures}
        
        # 执行测试
        result = self.extractor.extract_anatomical_structures(self.test_report)
        
        # 验证结果
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # 验证具体内容
        found_structures = [s.get("标准名称", "") for s in result]
        self.assertIn('双侧肺', found_structures)
        self.assertIn('右上肺叶', found_structures)
        
        print(f"✅ 解剖结构提取测试通过")
        print(f"   - 提取结构数量: {len(result)}")
        print(f"   - 结构列表: {[s.get('标准名称', '') for s in result[:3]]}")
    
    def test_pathology_extraction_with_mock(self):
        """测试病理特征提取（模拟响应）"""
        print("\n🧪 测试病理特征提取（模拟响应）...")
        
        # 设置模拟响应 - 返回病变特征列表格式
        mock_lesion_features = [
            {
                "名称": "肺部结节",
                "特征": {
                    "解剖位置": "右上肺叶",
                    "大小": "8mm",
                    "特性": "多发小结节",
                    "形态": "圆形",
                    "密度": "软组织密度"
                }
            },
            {
                "名称": "纵隔淋巴结肿大",
                "特征": {
                    "解剖位置": "纵隔",
                    "大小": "15mm",
                    "特性": "肿大",
                    "形态": "椭圆形"
                }
            }
        ]
        self.mock_llm_client.extract_json.return_value = {"病变特征": mock_lesion_features}
        
        # 执行测试
        result = self.extractor.extract_lesion_features(self.test_report)
        
        # 验证结果
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # 验证具体内容
        feature_names = [f.get("名称", "") for f in result]
        self.assertIn('肺部结节', feature_names)
        self.assertIn('纵隔淋巴结肿大', feature_names)
        
        print(f"✅ 病理特征提取测试通过")
        print(f"   - 特征数量: {len(result)}")
        print(f"   - 特征列表: {[f.get('名称', '') for f in result]}")
    
    def test_diagnosis_extraction_with_mock(self):
        """测试诊断信息提取（模拟响应）"""
        print("\n🧪 测试诊断信息提取（模拟响应）...")
        
        # 设置模拟响应 - 返回诊断信息列表格式
        mock_diagnosis_info = [
            {
                "描述": "双肺多发小结节，性质待定",
                "严重程度": "中等",
                "建议": "随访或进一步检查"
            },
            {
                "描述": "纵隔淋巴结肿大",
                "严重程度": "轻微",
                "建议": "定期复查"
            },
            {
                "描述": "胸腔积液",
                "严重程度": "轻微", 
                "建议": "观察"
            }
        ]
        self.mock_llm_client.extract_json.return_value = {"诊断信息": mock_diagnosis_info}
        
        # 使用测试诊断文本
        test_diagnosis = "双肺多发小结节，性质待定；纵隔淋巴结肿大；胸腔积液"
        
        # 执行测试
        result = self.extractor.extract_diagnosis_info(test_diagnosis)
        
        # 验证结果
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # 验证具体内容
        diagnosis_descriptions = [d.get("描述", "") for d in result]
        self.assertIn('双肺多发小结节，性质待定', diagnosis_descriptions)
        self.assertIn('纵隔淋巴结肿大', diagnosis_descriptions)
        
        print(f"✅ 诊断信息提取测试通过")
        print(f"   - 诊断数量: {len(result)}")
        print(f"   - 诊断列表: {[d.get('描述', '')[:15] + '...' for d in result]}")
    
    def test_complete_extraction_flow(self):
        """测试完整的三层提取流程"""
        print("\n🧪 测试完整的三层提取流程...")
        
        # 设置所有阶段的模拟响应
        mock_structures = [
            {"原文": "双肺", "标准名称": "双侧肺", "父结构": "呼吸系统"},
            {"原文": "右上肺叶", "标准名称": "右上肺叶", "父结构": "右肺"}
        ]
        
        mock_features = [
            {
                "名称": "肺部结节",
                "特征": {
                    "解剖位置": "右上肺叶",
                    "大小": "8mm",
                    "特性": "多发小结节"
                }
            }
        ]
        
        mock_diagnoses = [
            {
                "描述": "双肺多发小结节，性质待定",
                "严重程度": "中等",
                "建议": "随访或进一步检查"
            }
        ]
        
        mock_mappings = [
            {
                "影像发现": "右上肺叶多发小结节",
                "对应诊断": "双肺多发小结节，性质待定",
                "置信度": 0.85
            }
        ]
        
        # 模拟各个方法的返回
        responses = [
            {"解剖结构": mock_structures},
            {"病变特征": mock_features},
            {"诊断信息": mock_diagnoses},
            {"映射关系": mock_mappings}
        ]
        self.mock_llm_client.extract_json.side_effect = responses
        
        # 执行完整流程
        test_diagnosis = "双肺多发小结节，性质待定"
        result = self.extractor.extract_report_structure(self.test_report, test_diagnosis)
        
        # 验证结果结构
        self.assertIsInstance(result, dict)
        self.assertIn('解剖结构', result)
        self.assertIn('病变特征', result)
        self.assertIn('诊断信息', result)
        self.assertIn('映射关系', result)
        
        # 验证每个部分的内容
        self.assertIsInstance(result['解剖结构'], list)
        self.assertIsInstance(result['病变特征'], list)
        self.assertIsInstance(result['诊断信息'], list)
        self.assertIsInstance(result['映射关系'], list)
        
        print(f"✅ 完整提取流程测试通过")
        print(f"   - 解剖结构: {len(result['解剖结构'])}")
        print(f"   - 病变特征: {len(result['病变特征'])}")
        print(f"   - 诊断信息: {len(result['诊断信息'])}")
        print(f"   - 映射关系: {len(result['映射关系'])}")
    
    def test_cache_mechanism(self):
        """测试缓存机制"""
        print("\n🧪 测试缓存机制...")
        
        # 第一次调用
        mock_structures = [
            {"原文": "双肺", "标准名称": "双侧肺", "父结构": "呼吸系统"}
        ]
        self.mock_llm_client.extract_json.return_value = {"解剖结构": mock_structures}
        
        result1 = self.extractor.extract_anatomical_structures(self.test_report)
        
        # 第二次调用同样的报告（应该使用缓存）
        result2 = self.extractor.extract_anatomical_structures(self.test_report)
        
        # 验证结果一致
        self.assertEqual(result1, result2)
        
        # 验证LLM只被调用了一次（如果缓存工作正常）
        self.assertEqual(self.mock_llm_client.extract_json.call_count, 1)
        
        print(f"✅ 缓存机制测试通过")
        print(f"   - LLM调用次数: {self.mock_llm_client.extract_json.call_count}")
        print(f"   - 缓存命中: 是")
    
    def test_error_handling(self):
        """测试错误处理机制"""
        print("\n🧪 测试错误处理机制...")
        
        # 模拟LLM抛出异常
        self.mock_llm_client.extract_json.side_effect = Exception("LLM connection error")
        
        # 执行测试（应该优雅处理错误）
        result = self.extractor.extract_anatomical_structures(self.test_report)
        
        # 验证错误处理
        self.assertIsInstance(result, list)
        # 系统应该返回空列表或默认结构
        self.assertEqual(result, [])
        
        print(f"✅ 错误处理测试通过")
        print(f"   - 错误响应处理: 正常")
    
    def test_different_response_qualities(self):
        """测试不同质量响应的处理"""
        print("\n🧪 测试不同质量响应的处理...")
        
        # 测试高质量响应
        high_quality_structures = [
            {"原文": "右上肺叶", "标准名称": "右上肺叶", "父结构": "右肺"},
            {"原文": "左下肺叶", "标准名称": "左下肺叶", "父结构": "左肺"},
            {"原文": "纵隔", "标准名称": "纵隔", "父结构": "胸腔"},
            {"原文": "胸膜", "标准名称": "胸膜", "父结构": "胸腔"}
        ]
        
        # 测试低质量响应
        low_quality_structures = [
            {"原文": "肺", "标准名称": "肺", "父结构": "呼吸系统"}
        ]
        
        test_cases = [
            ("高质量", high_quality_structures),
            ("低质量", low_quality_structures)
        ]
        
        for quality, structures in test_cases:
            self.mock_llm_client.extract_json.return_value = {"解剖结构": structures}
            result = self.extractor.extract_anatomical_structures(self.test_report)
            
            self.assertIsInstance(result, list)
            print(f"   - {quality}响应处理: 正常（结构数量: {len(result)}）")
        
        print(f"✅ 不同质量响应测试通过")

def run_entity_mock_tests():
    """运行实体识别模拟测试"""
    print("=" * 60)
    print("🧪 补充测试1: 实体识别功能模拟测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEntityExtractionWithMock)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 实体识别模拟测试结果:")
    print(f"   - 总测试数: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️ 错误的测试:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ 测试成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_entity_mock_tests()
    sys.exit(0 if success else 1) 