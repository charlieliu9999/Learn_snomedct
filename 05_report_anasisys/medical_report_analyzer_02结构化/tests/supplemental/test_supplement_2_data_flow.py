#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充测试2: 数据处理流程完整测试
测试数据预处理、清洗、验证和格式转换功能
"""

import sys
import os
import json
import unittest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from utils.data_processor import clean_dataframe, standardize_text, get_report_sections, extract_basic_stats
from utils.config_manager import ConfigManager

class TestDataProcessingFlow(unittest.TestCase):
    """数据处理流程测试类"""
    
    def setUp(self):
        """测试准备"""
        self.config_manager = ConfigManager()
        
        # 测试数据
        self.test_data = [
            {
                "影像表现": "患者张某，男，45岁。CT检查显示：双肺多发小结节，最大约8mm。",
                "诊断结论": "双肺多发小结节，性质待定，建议随访。"
            },
            {
                "影像表现": "   患者李某，女，38岁。   胸部X线：右下肺斑片状阴影。   ",
                "诊断结论": "   右下肺炎症可能。   "
            },
            {
                "影像表现": "",
                "诊断结论": "无异常发现"
            }
        ]
        
        # 创建测试DataFrame
        self.test_df = pd.DataFrame(self.test_data)
        
        # 预期的清洗结果
        self.expected_cleaned = [
            {
                "影像表现": "患者张某，男，45岁。CT检查显示：双肺多发小结节，最大约8mm。",
                "诊断结论": "双肺多发小结节，性质待定，建议随访。"
            },
            {
                "影像表现": "患者李某，女，38岁。胸部X线：右下肺斑片状阴影。",
                "诊断结论": "右下肺炎症可能。"
            }
        ]
    
    def test_data_cleaning(self):
        """测试数据清洗功能"""
        print("\n🧪 测试数据清洗功能...")
        
        # 测试文本标准化
        dirty_text = "   患者张某，男，45岁。   CT检查显示：双肺多发小结节。   "
        cleaned_text = standardize_text(dirty_text)
        
        # 验证清洗结果
        expected = "患者张某,男,45岁. CT检查显示:双肺多发小结节."
        self.assertEqual(cleaned_text, expected)
        
        # 测试DataFrame清洗
        cleaned_df = clean_dataframe(self.test_df)
        self.assertIsInstance(cleaned_df, pd.DataFrame)
        self.assertLessEqual(len(cleaned_df), len(self.test_df))  # 可能过滤了一些行
        
        print(f"✅ 数据清洗测试通过")
        print(f"   - 原文本长度: {len(dirty_text)}")
        print(f"   - 清洗后长度: {len(cleaned_text)}")
        print(f"   - DataFrame清洗: {len(self.test_df)} → {len(cleaned_df)} 行")
    
    def test_data_validation(self):
        """测试数据验证功能"""
        print("\n🧪 测试数据验证功能...")
        
        # 测试有效数据
        valid_data = {
            "影像表现": "患者张某，男，45岁。CT检查显示：双肺多发小结节。",
            "诊断结论": "双肺多发小结节，性质待定。"
        }
        
        is_valid, error_msg = validate_report_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # 测试无效数据（缺少影像表现）
        invalid_data = {
            "影像表现": "",
            "诊断结论": "双肺多发小结节，性质待定。"
        }
        
        is_valid, error_msg = validate_report_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("影像表现", error_msg)
        
        print(f"✅ 数据验证测试通过")
        print(f"   - 有效数据验证: 通过")
        print(f"   - 无效数据检测: 通过")
    
    def test_batch_data_processing(self):
        """测试批量数据处理"""
        print("\n🧪 测试批量数据处理...")
        
        # 创建模拟的LLM客户端
        mock_llm_client = Mock()
        
        # 模拟结构化提取结果
        mock_extraction_result = {
            "解剖结构": [
                {"原文": "双肺", "标准名称": "双侧肺", "父结构": "呼吸系统"}
            ],
            "病变特征": [
                {
                    "名称": "肺部结节",
                    "特征": {
                        "解剖位置": "双肺",
                        "大小": "8mm",
                        "特性": "多发小结节"
                    }
                }
            ],
            "诊断信息": [
                {
                    "描述": "双肺多发小结节，性质待定",
                    "严重程度": "中等",
                    "建议": "随访"
                }
            ],
            "映射关系": [
                {
                    "影像发现": "双肺多发小结节",
                    "对应诊断": "双肺多发小结节，性质待定",
                    "置信度": 0.85
                }
            ]
        }
        
        # 执行批量处理
        with patch('utils.structure_extractor.StructureExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor.extract_report_structure.return_value = mock_extraction_result
            mock_extractor_class.return_value = mock_extractor
            
            results = process_medical_reports(self.test_df, mock_llm_client)
        
        # 验证处理结果
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # 验证第一个结果的结构
        first_result = results[0]
        self.assertIn("结构化数据", first_result)
        self.assertIn("原始文本", first_result)
        self.assertIn("分析信息", first_result)
        
        print(f"✅ 批量数据处理测试通过")
        print(f"   - 处理数据量: {len(results)}")
        print(f"   - 结果结构: {list(first_result.keys())}")
    
    def test_data_format_conversion(self):
        """测试数据格式转换"""
        print("\n🧪 测试数据格式转换...")
        
        # 测试DataFrame到字典列表的转换
        dict_list = self.test_df.to_dict('records')
        
        # 验证转换结果
        self.assertIsInstance(dict_list, list)
        self.assertEqual(len(dict_list), len(self.test_data))
        
        for i, record in enumerate(dict_list):
            self.assertEqual(record["影像表现"], self.test_data[i]["影像表现"])
            self.assertEqual(record["诊断结论"], self.test_data[i]["诊断结论"])
        
        # 测试字典列表到JSON的转换
        json_str = json.dumps(dict_list, ensure_ascii=False, indent=2)
        
        # 验证JSON格式
        parsed_json = json.loads(json_str)
        self.assertEqual(len(parsed_json), len(dict_list))
        
        print(f"✅ 数据格式转换测试通过")
        print(f"   - DataFrame → 字典列表: 成功")
        print(f"   - 字典列表 → JSON: 成功")
        print(f"   - JSON大小: {len(json_str)} 字符")
    
    def test_data_preprocessing_pipeline(self):
        """测试完整的数据预处理管道"""
        print("\n🧪 测试完整的数据预处理管道...")
        
        # 模拟完整的预处理流程
        processed_data = []
        
        for record in self.test_data:
            # 1. 数据清洗
            cleaned_record = {
                "影像表现": clean_report_text(record["影像表现"]),
                "诊断结论": clean_report_text(record["诊断结论"])
            }
            
            # 2. 数据验证
            is_valid, error_msg = validate_report_data(cleaned_record)
            
            # 3. 只保留有效数据
            if is_valid:
                processed_data.append(cleaned_record)
            else:
                print(f"   - 跳过无效数据: {error_msg}")
        
        # 验证预处理结果
        self.assertEqual(len(processed_data), 2)  # 应该过滤掉1条无效数据
        
        # 验证数据质量
        for record in processed_data:
            self.assertNotEqual(record["影像表现"].strip(), "")
            self.assertNotEqual(record["诊断结论"].strip(), "")
        
        print(f"✅ 数据预处理管道测试通过")
        print(f"   - 原始数据: {len(self.test_data)} 条")
        print(f"   - 有效数据: {len(processed_data)} 条")
        print(f"   - 过滤率: {(len(self.test_data) - len(processed_data)) / len(self.test_data) * 100:.1f}%")
    
    def test_large_dataset_processing(self):
        """测试大数据集处理性能"""
        print("\n🧪 测试大数据集处理性能...")
        
        # 生成大量测试数据
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "影像表现": f"患者{i}号，CT检查显示：肺部结节{i}个。",
                "诊断结论": f"肺部结节，建议随访{i}。"
            })
        
        large_df = pd.DataFrame(large_dataset)
        
        # 测试处理时间
        import time
        start_time = time.time()
        
        # 执行数据清洗和验证
        processed_count = 0
        for _, row in large_df.iterrows():
            cleaned_record = {
                "影像表现": clean_report_text(row["影像表现"]),
                "诊断结论": clean_report_text(row["诊断结论"])
            }
            
            is_valid, _ = validate_report_data(cleaned_record)
            if is_valid:
                processed_count += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证处理结果
        self.assertEqual(processed_count, 100)
        self.assertLess(processing_time, 5.0)  # 应该在5秒内完成
        
        print(f"✅ 大数据集处理测试通过")
        print(f"   - 数据量: {len(large_dataset)} 条")
        print(f"   - 处理时间: {processing_time:.3f} 秒")
        print(f"   - 处理速度: {len(large_dataset) / processing_time:.1f} 条/秒")
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        print("\n🧪 测试错误恢复机制...")
        
        # 测试包含异常数据的处理
        problematic_data = [
            {
                "影像表现": "正常数据",
                "诊断结论": "正常诊断"
            },
            {
                "影像表现": None,  # 异常数据
                "诊断结论": "诊断"
            },
            {
                "影像表现": "正常数据2",
                "诊断结论": "正常诊断2"
            }
        ]
        
        # 测试错误处理
        processed_data = []
        error_count = 0
        
        for record in problematic_data:
            try:
                # 处理可能的None值
                if record["影像表现"] is None:
                    record["影像表现"] = ""
                if record["诊断结论"] is None:
                    record["诊断结论"] = ""
                
                cleaned_record = {
                    "影像表现": clean_report_text(record["影像表现"]),
                    "诊断结论": clean_report_text(record["诊断结论"])
                }
                
                is_valid, error_msg = validate_report_data(cleaned_record)
                if is_valid:
                    processed_data.append(cleaned_record)
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"   - 处理错误: {str(e)}")
        
        # 验证错误恢复
        self.assertEqual(len(processed_data), 2)  # 应该成功处理2条数据
        self.assertEqual(error_count, 1)  # 应该有1条错误数据
        
        print(f"✅ 错误恢复机制测试通过")
        print(f"   - 成功处理: {len(processed_data)} 条")
        print(f"   - 错误数据: {error_count} 条")

def run_data_flow_tests():
    """运行数据处理流程测试"""
    print("=" * 60)
    print("🧪 补充测试2: 数据处理流程完整测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataProcessingFlow)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 数据处理流程测试结果:")
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
    success = run_data_flow_tests()
    sys.exit(0 if success else 1) 