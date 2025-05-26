#!/usr/bin/env python3
"""
医学影像报告SNOMED CT系统集成测试
验证系统各个组件的功能和集成效果
"""

import asyncio
import logging
import json
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'medical_report_analyzer'))

from medical_report_analyzer.utils.llm_client import LLMClient
from medical_report_analyzer.utils.clinical_application_interface import ClinicalApplicationInterface

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemIntegrationTest:
    """系统集成测试类"""
    
    def __init__(self):
        self.test_results = {}
        self.clinical_app = None
    
    async def setup(self):
        """初始化测试环境"""
        try:
            # 初始化LLM客户端（使用模拟客户端进行测试）
            llm_client = MockLLMClient()
            
            # 初始化临床应用接口
            self.clinical_app = ClinicalApplicationInterface(
                llm_client=llm_client,
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="test_password"
            )
            
            logger.info("测试环境初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"测试环境初始化失败: {e}")
            return False
    
    async def test_entity_recognition(self):
        """测试实体识别功能"""
        logger.info("开始测试实体识别功能...")
        
        test_text = """
        胸部CT平扫及增强扫描显示：
        右上肺叶可见约2.5cm×2.0cm大小的结节状软组织密度影，
        边缘毛刺状，增强扫描后呈轻度强化。
        周围可见少许胸膜牵拉征象。
        纵隔内可见多发淋巴结肿大，最大者约1.2cm。
        """
        
        try:
            # 测试实体识别
            entities = await self.clinical_app.entity_recognizer.recognize_entities(
                test_text, "chest_ct"
            )
            
            # 验证结果
            assert len(entities) > 0, "应该识别出至少一个实体"
            
            # 检查实体类型
            entity_types = set(entity.entity_type for entity in entities)
            expected_types = {"anatomy", "finding", "diagnosis"}
            
            self.test_results["entity_recognition"] = {
                "status": "PASS",
                "entities_count": len(entities),
                "entity_types": list(entity_types),
                "details": [
                    {
                        "text": entity.text,
                        "type": entity.entity_type,
                        "confidence": entity.confidence,
                        "snomed_code": entity.snomed_code
                    }
                    for entity in entities[:5]  # 只显示前5个
                ]
            }
            
            logger.info(f"实体识别测试通过，识别出 {len(entities)} 个实体")
            
        except Exception as e:
            self.test_results["entity_recognition"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"实体识别测试失败: {e}")
    
    async def test_report_processing(self):
        """测试完整报告处理流程"""
        logger.info("开始测试完整报告处理流程...")
        
        test_report = """
        检查所见：
        胸部CT平扫及增强扫描显示：
        1. 右上肺叶可见约2.5cm×2.0cm大小的结节状软组织密度影，边缘毛刺状，
           增强扫描后呈轻度强化，考虑恶性病变可能。
        2. 纵隔内可见多发淋巴结肿大，最大者约1.2cm。
        3. 双侧胸膜未见明显增厚，未见胸腔积液。
        4. 心脏大小形态正常，主动脉未见明显异常。
        
        诊断意见：
        右上肺叶占位性病变，考虑肺癌可能，建议进一步检查。
        """
        
        try:
            # 处理报告
            clinical_report = await self.clinical_app.process_imaging_report(
                report_text=test_report,
                patient_id="TEST_P001",
                study_type="chest_ct"
            )
            
            # 验证结果
            assert clinical_report.report_id is not None, "报告ID不能为空"
            assert clinical_report.quality_score > 0, "质量评分应该大于0"
            assert len(clinical_report.entities) > 0, "应该识别出实体"
            
            self.test_results["report_processing"] = {
                "status": "PASS",
                "report_id": clinical_report.report_id,
                "quality_score": clinical_report.quality_score,
                "entities_count": len(clinical_report.entities),
                "diagnosis_suggestions_count": len(clinical_report.diagnosis_suggestions),
                "structured_data": clinical_report.structured_data
            }
            
            logger.info(f"报告处理测试通过，质量评分: {clinical_report.quality_score:.2f}")
            
        except Exception as e:
            self.test_results["report_processing"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"报告处理测试失败: {e}")
    
    async def test_template_engine(self):
        """测试模版引擎功能"""
        logger.info("开始测试模版引擎功能...")
        
        try:
            # 测试诊断→描述工作流
            parameters = {
                "解剖位置": "右上肺叶",
                "大小": "2.5cm×2.0cm",
                "形态": "结节状",
                "边界": "毛刺状",
                "增强方式": "轻度强化"
            }
            
            description_result = self.clinical_app.template_engine.diagnosis_to_description(
                "肺癌", parameters
            )
            
            # 验证结果
            assert "generated_description" in description_result, "应该生成描述"
            assert description_result["generated_description"], "生成的描述不能为空"
            
            # 测试影像→诊断工作流
            imaging_findings = {
                "解剖结构": ["右上肺叶"],
                "病变特征": ["结节状影", "毛刺状边缘"],
                "增强特征": ["轻度强化"]
            }
            
            diagnosis_result = await self.clinical_app.template_engine.imaging_to_diagnosis(
                imaging_findings
            )
            
            self.test_results["template_engine"] = {
                "status": "PASS",
                "description_generation": {
                    "diagnosis": "肺癌",
                    "generated_description": description_result.get("generated_description", ""),
                    "snomed_code": description_result.get("snomed_code", "")
                },
                "diagnosis_suggestion": diagnosis_result
            }
            
            logger.info("模版引擎测试通过")
            
        except Exception as e:
            self.test_results["template_engine"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"模版引擎测试失败: {e}")
    
    async def test_knowledge_graph(self):
        """测试知识图谱功能"""
        logger.info("开始测试知识图谱功能...")
        
        try:
            # 测试诊断建议
            findings = ["右上肺叶结节", "毛刺状边缘", "淋巴结肿大"]
            suggestions = self.clinical_app.get_diagnostic_suggestions(findings)
            
            self.test_results["knowledge_graph"] = {
                "status": "PASS",
                "diagnostic_suggestions": suggestions,
                "findings_tested": findings
            }
            
            logger.info(f"知识图谱测试通过，获得 {len(suggestions)} 个诊断建议")
            
        except Exception as e:
            self.test_results["knowledge_graph"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"知识图谱测试失败: {e}")
    
    def generate_test_report(self):
        """生成测试报告"""
        report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for result in self.test_results.values() if result["status"] == "PASS"),
                "failed_tests": sum(1 for result in self.test_results.values() if result["status"] == "FAIL")
            },
            "test_details": self.test_results
        }
        
        # 保存测试报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试报告已保存到: {report_file}")
        
        # 打印摘要
        print("\n" + "="*60)
        print("测试结果摘要")
        print("="*60)
        print(f"总测试数: {report['test_summary']['total_tests']}")
        print(f"通过测试: {report['test_summary']['passed_tests']}")
        print(f"失败测试: {report['test_summary']['failed_tests']}")
        print("\n详细结果:")
        
        for test_name, result in self.test_results.items():
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_symbol} {test_name}: {result['status']}")
            if result["status"] == "FAIL":
                print(f"   错误: {result.get('error', 'Unknown error')}")
        
        print("="*60)
        
        return report
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行系统集成测试...")
        
        # 初始化
        if not await self.setup():
            logger.error("测试环境初始化失败，终止测试")
            return
        
        # 运行各项测试
        await self.test_entity_recognition()
        await self.test_template_engine()
        await self.test_knowledge_graph()
        await self.test_report_processing()
        
        # 生成测试报告
        report = self.generate_test_report()
        
        # 清理
        if self.clinical_app:
            self.clinical_app.close()
        
        logger.info("系统集成测试完成")
        return report

class MockLLMClient:
    """模拟LLM客户端，用于测试"""
    
    def generate_text(self, prompt: str) -> str:
        """模拟文本生成"""
        if "一致性评分" in prompt:
            return "0.8"
        return "模拟生成的文本"
    
    def extract_json(self, prompt: str) -> dict:
        """模拟JSON提取"""
        if "实体" in prompt:
            return {
                "entities": [
                    {
                        "text": "右上肺叶",
                        "type": "anatomy",
                        "start_pos": 0,
                        "end_pos": 4,
                        "confidence": 0.9,
                        "attributes": {"location": "chest"}
                    },
                    {
                        "text": "结节状影",
                        "type": "finding",
                        "start_pos": 10,
                        "end_pos": 13,
                        "confidence": 0.8,
                        "attributes": {"morphology": "nodular"}
                    }
                ]
            }
        elif "诊断" in prompt:
            return {
                "primary_diagnosis": {
                    "name": "肺癌",
                    "confidence": 0.8,
                    "reasoning": "结节状影伴毛刺状边缘，高度提示恶性病变"
                },
                "differential_diagnoses": [
                    {
                        "name": "肺炎",
                        "confidence": 0.3,
                        "reasoning": "炎性病变可能性较低"
                    }
                ],
                "recommended_actions": ["建议活检确诊", "胸部增强CT复查"]
            }
        elif "关系" in prompt:
            return {
                "relationships": [
                    {
                        "source_entity_id": 0,
                        "target_entity_id": 1,
                        "relationship_type": "located_in",
                        "confidence": 0.9,
                        "evidence_text": "右上肺叶可见结节状影"
                    }
                ]
            }
        
        return {}

async def main():
    """主函数"""
    test_runner = SystemIntegrationTest()
    await test_runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
