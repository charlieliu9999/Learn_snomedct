"""
增强的医学实体识别器
结合大模型和SNOMED CT进行精确的医学实体识别和关系抽取
"""

import logging
import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .llm_client import LLMClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MedicalEntity:
    """医学实体"""
    text: str
    entity_type: str  # 'anatomy', 'finding', 'diagnosis', 'procedure'
    start_pos: int
    end_pos: int
    confidence: float
    snomed_code: Optional[str] = None
    snomed_term: Optional[str] = None
    attributes: Dict[str, Any] = None
    relationships: List[Dict[str, Any]] = None

@dataclass
class EntityRelationship:
    """实体关系"""
    source_entity: MedicalEntity
    target_entity: MedicalEntity
    relationship_type: str  # 'located_in', 'has_finding', 'suggests_diagnosis'
    confidence: float
    evidence_text: str

class EnhancedEntityRecognizer:
    """增强的医学实体识别器"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

        # 尝试导入SNOMED CT服务
        self.snomed_available = False
        self.snomed_service = None
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '03_Image_snomed_struction'))
            from enhanced_terminology_services import enhanced_terminology_service
            self.snomed_service = enhanced_terminology_service
            self.snomed_available = True
            logger.info("SNOMED CT服务已加载到实体识别器")
        except ImportError:
            logger.warning("SNOMED CT服务不可用，使用基础实体识别")

        # 实体类型映射
        self.entity_type_mapping = {
            "解剖结构": "anatomy",
            "病变特征": "finding",
            "诊断信息": "diagnosis",
            "检查方法": "procedure"
        }

        # 关系类型映射
        self.relationship_mapping = {
            "位于": "located_in",
            "发现": "has_finding",
            "提示": "suggests_diagnosis",
            "排除": "excludes_diagnosis"
        }

    async def recognize_entities(self, text: str, context: str = "") -> List[MedicalEntity]:
        """
        识别文本中的医学实体

        Args:
            text: 医学文本
            context: 上下文信息

        Returns:
            医学实体列表
        """
        entities = []

        try:
            # 第一步：使用大模型进行初步实体识别
            llm_entities = await self._extract_entities_with_llm(text, context)

            # 第二步：如果有SNOMED CT，进行术语验证和增强
            if self.snomed_available and self.snomed_service:
                entities = await self._enhance_entities_with_snomed(llm_entities, text)
            else:
                entities = llm_entities

            # 第三步：后处理和质量控制
            entities = self._post_process_entities(entities, text)

            logger.info(f"识别到 {len(entities)} 个医学实体")
            return entities

        except Exception as e:
            logger.error(f"实体识别失败: {e}")
            return []

    async def _extract_entities_with_llm(self, text: str, context: str) -> List[MedicalEntity]:
        """使用大模型提取实体"""
        prompt = f"""
        请从以下医学文本中识别所有医学实体，包括解剖结构、病变特征、诊断信息和检查方法。

        文本内容：
        {text}

        上下文：{context}

        请按以下JSON格式返回结果：
        {{
          "entities": [
            {{
              "text": "实体文本",
              "type": "anatomy|finding|diagnosis|procedure",
              "start_pos": 开始位置,
              "end_pos": 结束位置,
              "confidence": 0.0-1.0,
              "attributes": {{
                "size": "大小",
                "location": "位置",
                "severity": "严重程度"
              }}
            }}
          ]
        }}

        注意：
        1. 准确标记每个实体在原文中的位置
        2. 为每个实体分配合适的类型
        3. 提供置信度评分
        4. 提取相关属性信息
        """

        try:
            result = self.llm_client.extract_json(prompt)
            entities = []

            if isinstance(result, dict) and "entities" in result:
                for entity_data in result["entities"]:
                    entity = MedicalEntity(
                        text=entity_data.get("text", ""),
                        entity_type=entity_data.get("type", "unknown"),
                        start_pos=entity_data.get("start_pos", 0),
                        end_pos=entity_data.get("end_pos", 0),
                        confidence=entity_data.get("confidence", 0.5),
                        attributes=entity_data.get("attributes", {}),
                        relationships=[]
                    )
                    entities.append(entity)

            return entities

        except Exception as e:
            logger.error(f"大模型实体提取失败: {e}")
            return []

    async def _enhance_entities_with_snomed(self, entities: List[MedicalEntity], original_text: str) -> List[MedicalEntity]:
        """使用SNOMED CT增强实体信息"""
        enhanced_entities = []

        for entity in entities:
            try:
                # 根据实体类型选择合适的SNOMED CT语义标签
                semantic_context = self._get_semantic_context(entity.entity_type)

                # 验证术语
                validation_result = await self.snomed_service.validate_medical_term(
                    entity.text,
                    context=semantic_context
                )

                # 如果找到有效的SNOMED CT术语，增强实体信息
                if validation_result.is_valid and validation_result.snomed_entity:
                    entity.snomed_code = validation_result.snomed_entity.code
                    entity.snomed_term = validation_result.snomed_entity.term
                    entity.confidence = max(entity.confidence, validation_result.confidence)

                    # 添加SNOMED CT关系信息
                    if validation_result.snomed_entity.relationships:
                        if not entity.attributes:
                            entity.attributes = {}
                        entity.attributes["snomed_relationships"] = validation_result.snomed_entity.relationships

                enhanced_entities.append(entity)

            except Exception as e:
                logger.warning(f"SNOMED CT增强失败: {entity.text}, 错误: {e}")
                enhanced_entities.append(entity)

        return enhanced_entities

    def _get_semantic_context(self, entity_type: str) -> str:
        """根据实体类型获取SNOMED CT语义上下文"""
        context_mapping = {
            "anatomy": "body structure",
            "finding": "clinical finding",
            "diagnosis": "disorder",
            "procedure": "procedure"
        }
        return context_mapping.get(entity_type, "clinical finding")

    def _post_process_entities(self, entities: List[MedicalEntity], original_text: str) -> List[MedicalEntity]:
        """后处理实体列表"""
        # 去重
        unique_entities = []
        seen_texts = set()

        for entity in entities:
            if entity.text not in seen_texts:
                unique_entities.append(entity)
                seen_texts.add(entity.text)

        # 按置信度排序
        unique_entities.sort(key=lambda x: x.confidence, reverse=True)

        # 验证位置信息
        for entity in unique_entities:
            if entity.text in original_text:
                # 更新准确的位置信息
                start_pos = original_text.find(entity.text)
                if start_pos != -1:
                    entity.start_pos = start_pos
                    entity.end_pos = start_pos + len(entity.text)

        return unique_entities

    async def extract_relationships(self, entities: List[MedicalEntity], text: str) -> List[EntityRelationship]:
        """
        提取实体间的关系

        Args:
            entities: 实体列表
            text: 原始文本

        Returns:
            实体关系列表
        """
        relationships = []

        if len(entities) < 2:
            return relationships

        try:
            # 构建关系提取提示词
            entity_info = []
            for i, entity in enumerate(entities):
                entity_info.append(f"{i}: {entity.text} ({entity.entity_type})")

            prompt = f"""
            请分析以下医学文本中实体间的关系：

            原文：{text}

            实体列表：
            {chr(10).join(entity_info)}

            请识别实体间的关系，按以下JSON格式返回：
            {{
              "relationships": [
                {{
                  "source_entity_id": 0,
                  "target_entity_id": 1,
                  "relationship_type": "located_in|has_finding|suggests_diagnosis|excludes_diagnosis",
                  "confidence": 0.0-1.0,
                  "evidence_text": "支持此关系的文本片段"
                }}
              ]
            }}
            """

            result = self.llm_client.extract_json(prompt)

            if isinstance(result, dict) and "relationships" in result:
                for rel_data in result["relationships"]:
                    source_id = rel_data.get("source_entity_id")
                    target_id = rel_data.get("target_entity_id")

                    if (source_id is not None and target_id is not None and
                        0 <= source_id < len(entities) and 0 <= target_id < len(entities)):

                        relationship = EntityRelationship(
                            source_entity=entities[source_id],
                            target_entity=entities[target_id],
                            relationship_type=rel_data.get("relationship_type", "unknown"),
                            confidence=rel_data.get("confidence", 0.5),
                            evidence_text=rel_data.get("evidence_text", "")
                        )
                        relationships.append(relationship)

            logger.info(f"识别到 {len(relationships)} 个实体关系")
            return relationships

        except Exception as e:
            logger.error(f"关系提取失败: {e}")
            return []

    def entities_to_structured_data(self, entities: List[MedicalEntity]) -> Dict[str, Any]:
        """
        将实体和关系转换为结构化数据

        Args:
            entities: 实体列表
            relationships: 关系列表

        Returns:
            结构化数据
        """
        structured_data = {
            "解剖结构": [],
            "病变特征": [],
            "诊断信息": [],
            "检查方法": [],
            "实体关系": []
        }

        # 按类型分组实体
        type_mapping = {
            "anatomy": "解剖结构",
            "finding": "病变特征",
            "diagnosis": "诊断信息",
            "procedure": "检查方法"
        }

        for entity in entities:
            category = type_mapping.get(entity.entity_type, "其他")
            if category in structured_data:
                entity_dict = {
                    "原文": entity.text,
                    "标准名": entity.snomed_term or entity.text,
                    "置信度": entity.confidence,
                    "位置": f"{entity.start_pos}-{entity.end_pos}"
                }

                if entity.snomed_code:
                    entity_dict["snomed_code"] = entity.snomed_code

                if entity.attributes:
                    entity_dict.update(entity.attributes)

                structured_data[category].append(entity_dict)

        # 注意：关系信息需要单独调用extract_relationships方法获取

        return structured_data

    async def extract_relationships(self, entities: List[MedicalEntity], text: str) -> List[EntityRelationship]:
        """
        提取实体间的关系

        Args:
            entities: 实体列表
            text: 原始文本

        Returns:
            实体关系列表
        """
        relationships = []

        if len(entities) < 2:
            return relationships

        try:
            # 构建关系提取提示词
            entity_info = []
            for i, entity in enumerate(entities):
                entity_info.append(f"{i}: {entity.text} ({entity.entity_type})")

            prompt = f"""
            请分析以下医学文本中实体间的关系：

            原文：{text}

            实体列表：
            {chr(10).join(entity_info)}

            请识别实体间的关系，按以下JSON格式返回：
            {{
              "relationships": [
                {{
                  "source_entity_id": 0,
                  "target_entity_id": 1,
                  "relationship_type": "located_in|has_finding|suggests_diagnosis|excludes_diagnosis",
                  "confidence": 0.0-1.0,
                  "evidence_text": "支持此关系的文本片段"
                }}
              ]
            }}
            """

            result = self.llm_client.extract_json(prompt)

            if isinstance(result, dict) and "relationships" in result:
                for rel_data in result["relationships"]:
                    source_id = rel_data.get("source_entity_id")
                    target_id = rel_data.get("target_entity_id")

                    if (source_id is not None and target_id is not None and
                        0 <= source_id < len(entities) and 0 <= target_id < len(entities)):

                        relationship = EntityRelationship(
                            source_entity=entities[source_id],
                            target_entity=entities[target_id],
                            relationship_type=rel_data.get("relationship_type", "unknown"),
                            confidence=rel_data.get("confidence", 0.5),
                            evidence_text=rel_data.get("evidence_text", "")
                        )
                        relationships.append(relationship)

            logger.info(f"识别到 {len(relationships)} 个实体关系")
            return relationships

        except Exception as e:
            logger.error(f"关系提取失败: {e}")
            return []
