"""
临床应用接口
为影像科医生和临床医生提供智能化的结构化报告工具
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

from .llm_client import LLMClient
from .enhanced_entity_recognizer import EnhancedEntityRecognizer, MedicalEntity
from .template_engine import BidirectionalTemplateEngine
from .knowledge_graph_manager import KnowledgeGraphManager, MedicalEntity as KGEntity, MedicalRelationship

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ClinicalReport:
    """临床报告"""
    report_id: str
    patient_id: str
    study_type: str  # 'chest_ct', 'brain_mri', etc.
    original_text: str
    structured_data: Dict[str, Any]
    entities: List[MedicalEntity]
    diagnosis_suggestions: List[Dict[str, Any]]
    generated_description: str
    quality_score: float
    created_at: datetime
    updated_at: datetime

@dataclass
class QualityMetrics:
    """质量指标"""
    completeness_score: float  # 完整性评分
    accuracy_score: float      # 准确性评分
    consistency_score: float   # 一致性评分
    snomed_coverage: float     # SNOMED CT覆盖率
    overall_score: float       # 总体评分

class ClinicalApplicationInterface:
    """临床应用接口"""
    
    def __init__(self, llm_client: LLMClient, 
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j", 
                 neo4j_password: str = "password"):
        
        self.llm_client = llm_client
        
        # 初始化核心组件
        self.entity_recognizer = EnhancedEntityRecognizer(llm_client)
        self.template_engine = BidirectionalTemplateEngine(llm_client)
        self.knowledge_graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
        
        # 报告存储
        self.reports = {}
        
        logger.info("临床应用接口初始化完成")
    
    async def process_imaging_report(self, report_text: str, patient_id: str, study_type: str) -> ClinicalReport:
        """
        处理影像报告
        
        Args:
            report_text: 报告文本
            patient_id: 患者ID
            study_type: 检查类型
            
        Returns:
            处理后的临床报告
        """
        report_id = str(uuid.uuid4())
        
        try:
            # 第一步：实体识别和关系抽取
            logger.info("开始实体识别...")
            entities = await self.entity_recognizer.recognize_entities(report_text, study_type)
            
            # 第二步：结构化数据提取
            logger.info("提取结构化数据...")
            structured_data = self.entity_recognizer.entities_to_structured_data(entities)
            
            # 第三步：诊断建议生成
            logger.info("生成诊断建议...")
            diagnosis_suggestions = await self._generate_diagnosis_suggestions(structured_data)
            
            # 第四步：存储到知识图谱
            logger.info("存储到知识图谱...")
            await self._store_to_knowledge_graph(entities, report_id)
            
            # 第五步：质量评估
            logger.info("进行质量评估...")
            quality_score = await self._assess_report_quality(report_text, structured_data, entities)
            
            # 创建临床报告
            clinical_report = ClinicalReport(
                report_id=report_id,
                patient_id=patient_id,
                study_type=study_type,
                original_text=report_text,
                structured_data=structured_data,
                entities=entities,
                diagnosis_suggestions=diagnosis_suggestions,
                generated_description="",  # 稍后生成
                quality_score=quality_score,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 存储报告
            self.reports[report_id] = clinical_report
            
            logger.info(f"报告处理完成: {report_id}")
            return clinical_report
            
        except Exception as e:
            logger.error(f"处理影像报告失败: {e}")
            raise
    
    async def _generate_diagnosis_suggestions(self, structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成诊断建议"""
        try:
            # 提取关键发现
            findings = {}
            for category, items in structured_data.items():
                if category != "实体关系" and items:
                    findings[category] = [item.get("标准名", item.get("原文", "")) for item in items]
            
            # 使用模版引擎生成诊断建议
            diagnosis_result = await self.template_engine.imaging_to_diagnosis(findings)
            
            # 格式化诊断建议
            suggestions = []
            if isinstance(diagnosis_result, dict) and "primary_diagnosis" in diagnosis_result:
                suggestions.append({
                    "type": "primary",
                    "diagnosis": diagnosis_result["primary_diagnosis"]["name"],
                    "confidence": diagnosis_result["primary_diagnosis"]["confidence"],
                    "reasoning": diagnosis_result["primary_diagnosis"]["reasoning"]
                })
                
                for diff_diag in diagnosis_result.get("differential_diagnoses", []):
                    suggestions.append({
                        "type": "differential",
                        "diagnosis": diff_diag["name"],
                        "confidence": diff_diag["confidence"],
                        "reasoning": diff_diag["reasoning"]
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成诊断建议失败: {e}")
            return []
    
    async def _store_to_knowledge_graph(self, entities: List[MedicalEntity], report_id: str):
        """存储实体到知识图谱"""
        try:
            # 转换实体格式并存储
            for entity in entities:
                kg_entity = KGEntity(
                    entity_id=f"{report_id}_{entity.text}",
                    entity_type=entity.entity_type,
                    name=entity.text,
                    snomed_code=entity.snomed_code,
                    properties={
                        "confidence": entity.confidence,
                        "report_id": report_id,
                        "attributes": entity.attributes or {}
                    },
                    created_at=datetime.now()
                )
                
                self.knowledge_graph.store_medical_entity(kg_entity)
            
            # 存储实体间关系
            relationships = await self.entity_recognizer.extract_relationships(entities, "")
            for rel in relationships:
                kg_relationship = MedicalRelationship(
                    relationship_id=str(uuid.uuid4()),
                    source_entity_id=f"{report_id}_{rel.source_entity.text}",
                    target_entity_id=f"{report_id}_{rel.target_entity.text}",
                    relationship_type=rel.relationship_type,
                    properties={"evidence": rel.evidence_text},
                    confidence=rel.confidence,
                    created_at=datetime.now()
                )
                
                self.knowledge_graph.store_medical_relationship(kg_relationship)
                
        except Exception as e:
            logger.error(f"存储到知识图谱失败: {e}")
    
    async def _assess_report_quality(self, original_text: str, structured_data: Dict[str, Any], entities: List[MedicalEntity]) -> float:
        """评估报告质量"""
        try:
            # 计算完整性评分
            completeness = self._calculate_completeness(structured_data)
            
            # 计算SNOMED CT覆盖率
            snomed_coverage = self._calculate_snomed_coverage(entities)
            
            # 计算一致性评分
            consistency = await self._calculate_consistency(original_text, structured_data)
            
            # 计算总体评分
            overall_score = (completeness * 0.3 + snomed_coverage * 0.4 + consistency * 0.3)
            
            return overall_score
            
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            return 0.5
    
    def _calculate_completeness(self, structured_data: Dict[str, Any]) -> float:
        """计算完整性评分"""
        total_categories = len(structured_data)
        filled_categories = sum(1 for items in structured_data.values() if items)
        
        return filled_categories / total_categories if total_categories > 0 else 0.0
    
    def _calculate_snomed_coverage(self, entities: List[MedicalEntity]) -> float:
        """计算SNOMED CT覆盖率"""
        if not entities:
            return 0.0
        
        snomed_entities = sum(1 for entity in entities if entity.snomed_code)
        return snomed_entities / len(entities)
    
    async def _calculate_consistency(self, original_text: str, structured_data: Dict[str, Any]) -> float:
        """计算一致性评分"""
        try:
            # 使用LLM评估原文和结构化数据的一致性
            prompt = f"""
            请评估以下原始报告文本和结构化数据的一致性：
            
            原始文本：
            {original_text}
            
            结构化数据：
            {json.dumps(structured_data, ensure_ascii=False, indent=2)}
            
            请返回一个0-1之间的一致性评分，其中1表示完全一致，0表示完全不一致。
            只返回数字，不要其他文字。
            """
            
            result = self.llm_client.generate_text(prompt)
            try:
                score = float(result.strip())
                return max(0.0, min(1.0, score))
            except ValueError:
                return 0.5
                
        except Exception as e:
            logger.error(f"计算一致性评分失败: {e}")
            return 0.5
    
    def generate_structured_description(self, report_id: str, diagnosis_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成结构化描述（诊断→描述工作流）
        
        Args:
            report_id: 报告ID
            diagnosis_name: 诊断名称
            parameters: 描述参数
            
        Returns:
            生成的描述
        """
        try:
            result = self.template_engine.diagnosis_to_description(diagnosis_name, parameters)
            
            # 更新报告
            if report_id in self.reports:
                self.reports[report_id].generated_description = result.get("generated_description", "")
                self.reports[report_id].updated_at = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"生成结构化描述失败: {e}")
            return {"error": str(e)}
    
    def get_diagnostic_suggestions(self, findings: List[str]) -> List[Dict[str, Any]]:
        """
        获取诊断建议
        
        Args:
            findings: 发现列表
            
        Returns:
            诊断建议列表
        """
        try:
            # 使用知识图谱查找诊断路径
            paths = self.knowledge_graph.find_diagnostic_path(findings)
            
            # 转换为诊断建议
            suggestions = []
            for path in paths:
                if path["nodes"]:
                    # 找到路径中的诊断节点
                    diagnosis_nodes = [node for node in path["nodes"] if node["entity_type"] == "diagnosis"]
                    for diag_node in diagnosis_nodes:
                        suggestion = {
                            "diagnosis": diag_node["name"],
                            "snomed_code": diag_node["snomed_code"],
                            "confidence": sum(rel["confidence"] for rel in path["relationships"]) / len(path["relationships"]) if path["relationships"] else 0.5,
                            "path_length": path["path_length"],
                            "supporting_findings": findings
                        }
                        suggestions.append(suggestion)
            
            # 按置信度排序
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            
            return suggestions[:5]  # 返回前5个建议
            
        except Exception as e:
            logger.error(f"获取诊断建议失败: {e}")
            return []
    
    def get_report_quality_metrics(self, report_id: str) -> Optional[QualityMetrics]:
        """
        获取报告质量指标
        
        Args:
            report_id: 报告ID
            
        Returns:
            质量指标
        """
        if report_id not in self.reports:
            return None
        
        report = self.reports[report_id]
        
        try:
            completeness = self._calculate_completeness(report.structured_data)
            snomed_coverage = self._calculate_snomed_coverage(report.entities)
            
            return QualityMetrics(
                completeness_score=completeness,
                accuracy_score=0.8,  # 需要更复杂的计算
                consistency_score=0.8,  # 需要更复杂的计算
                snomed_coverage=snomed_coverage,
                overall_score=report.quality_score
            )
            
        except Exception as e:
            logger.error(f"获取质量指标失败: {e}")
            return None
    
    def get_report(self, report_id: str) -> Optional[ClinicalReport]:
        """获取报告"""
        return self.reports.get(report_id)
    
    def list_reports(self, patient_id: str = None) -> List[Dict[str, Any]]:
        """列出报告"""
        reports = []
        for report in self.reports.values():
            if patient_id is None or report.patient_id == patient_id:
                report_info = {
                    "report_id": report.report_id,
                    "patient_id": report.patient_id,
                    "study_type": report.study_type,
                    "quality_score": report.quality_score,
                    "created_at": report.created_at.isoformat(),
                    "updated_at": report.updated_at.isoformat()
                }
                reports.append(report_info)
        
        return reports
    
    def close(self):
        """关闭连接"""
        if self.knowledge_graph:
            self.knowledge_graph.close()
