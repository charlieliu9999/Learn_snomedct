"""
知识图谱管理器
整合Neo4j和KAG框架，提供医学知识图谱的存储、查询和推理功能
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import os
import sys

# 尝试导入Neo4j驱动
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None

# 尝试导入KAG框架
try:
    # 添加KAG框架路径
    kag_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '07_medicine_kag')
    sys.path.append(kag_path)
    from kag.interface import KagConfig, KagMemory
    KAG_AVAILABLE = True
except ImportError:
    KAG_AVAILABLE = False
    KagConfig = None
    KagMemory = None

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MedicalEntity:
    """医学实体"""
    entity_id: str
    entity_type: str  # 'anatomy', 'finding', 'diagnosis', 'procedure'
    name: str
    snomed_code: Optional[str] = None
    properties: Dict[str, Any] = None
    created_at: datetime = None

@dataclass
class MedicalRelationship:
    """医学关系"""
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    properties: Dict[str, Any] = None
    confidence: float = 1.0
    created_at: datetime = None

class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "password",
                 kag_config_path: str = None):

        self.neo4j_available = NEO4J_AVAILABLE
        self.kag_available = KAG_AVAILABLE

        # 初始化Neo4j连接
        if self.neo4j_available:
            try:
                self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                self._verify_neo4j_connection()
                logger.info("Neo4j连接成功")
            except Exception as e:
                logger.error(f"Neo4j连接失败: {e}")
                self.neo4j_available = False
                self.driver = None
        else:
            logger.warning("Neo4j驱动不可用")
            self.driver = None

        # 初始化KAG框架
        if self.kag_available:
            try:
                if kag_config_path and os.path.exists(kag_config_path):
                    self.kag_config = KagConfig.from_file(kag_config_path)
                else:
                    # 使用默认配置
                    self.kag_config = self._create_default_kag_config()

                self.kag_memory = KagMemory(self.kag_config)
                logger.info("KAG框架初始化成功")
            except Exception as e:
                logger.error(f"KAG框架初始化失败: {e}")
                self.kag_available = False
                self.kag_memory = None
        else:
            logger.warning("KAG框架不可用")
            self.kag_memory = None

        # 创建索引
        if self.neo4j_available:
            self._create_indexes()

    def _verify_neo4j_connection(self):
        """验证Neo4j连接"""
        with self.driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record["test"] != 1:
                raise Exception("Neo4j连接验证失败")

    def _create_default_kag_config(self) -> Any:
        """创建默认KAG配置"""
        # 这里应该根据实际的KAG配置格式来创建
        # 暂时返回一个占位符
        return None

    def _create_indexes(self):
        """创建Neo4j索引"""
        indexes = [
            "CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:MedicalEntity) ON (e.entity_id)",
            "CREATE INDEX snomed_code_index IF NOT EXISTS FOR (e:MedicalEntity) ON (e.snomed_code)",
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:MedicalEntity) ON (e.entity_type)",
            "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:MEDICAL_RELATION]-() ON (r.relationship_type)"
        ]

        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"创建索引失败: {e}")

    def store_medical_entity(self, entity: MedicalEntity) -> bool:
        """
        存储医学实体到知识图谱

        Args:
            entity: 医学实体

        Returns:
            是否存储成功
        """
        if not self.neo4j_available:
            logger.warning("Neo4j不可用，无法存储实体")
            return False

        try:
            with self.driver.session() as session:
                query = """
                MERGE (e:MedicalEntity {entity_id: $entity_id})
                SET e.entity_type = $entity_type,
                    e.name = $name,
                    e.snomed_code = $snomed_code,
                    e.properties = $properties,
                    e.created_at = $created_at,
                    e.updated_at = datetime()
                RETURN e
                """

                result = session.run(query, {
                    "entity_id": entity.entity_id,
                    "entity_type": entity.entity_type,
                    "name": entity.name,
                    "snomed_code": entity.snomed_code,
                    "properties": json.dumps(entity.properties or {}),
                    "created_at": entity.created_at or datetime.now()
                })

                record = result.single()
                if record:
                    logger.debug(f"实体存储成功: {entity.entity_id}")
                    return True
                else:
                    logger.error(f"实体存储失败: {entity.entity_id}")
                    return False

        except Exception as e:
            logger.error(f"存储实体失败: {e}")
            return False

    def store_medical_relationship(self, relationship: MedicalRelationship) -> bool:
        """
        存储医学关系到知识图谱

        Args:
            relationship: 医学关系

        Returns:
            是否存储成功
        """
        if not self.neo4j_available:
            logger.warning("Neo4j不可用，无法存储关系")
            return False

        try:
            with self.driver.session() as session:
                query = """
                MATCH (source:MedicalEntity {entity_id: $source_id})
                MATCH (target:MedicalEntity {entity_id: $target_id})
                MERGE (source)-[r:MEDICAL_RELATION {relationship_id: $relationship_id}]->(target)
                SET r.relationship_type = $relationship_type,
                    r.properties = $properties,
                    r.confidence = $confidence,
                    r.created_at = $created_at,
                    r.updated_at = datetime()
                RETURN r
                """

                result = session.run(query, {
                    "source_id": relationship.source_entity_id,
                    "target_id": relationship.target_entity_id,
                    "relationship_id": relationship.relationship_id,
                    "relationship_type": relationship.relationship_type,
                    "properties": json.dumps(relationship.properties or {}),
                    "confidence": relationship.confidence,
                    "created_at": relationship.created_at or datetime.now()
                })

                record = result.single()
                if record:
                    logger.debug(f"关系存储成功: {relationship.relationship_id}")
                    return True
                else:
                    logger.error(f"关系存储失败: {relationship.relationship_id}")
                    return False

        except Exception as e:
            logger.error(f"存储关系失败: {e}")
            return False

    def query_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据类型查询实体

        Args:
            entity_type: 实体类型
            limit: 返回数量限制

        Returns:
            实体列表
        """
        if not self.neo4j_available:
            return []

        try:
            with self.driver.session() as session:
                query = """
                MATCH (e:MedicalEntity {entity_type: $entity_type})
                RETURN e.entity_id as entity_id,
                       e.name as name,
                       e.snomed_code as snomed_code,
                       e.properties as properties
                LIMIT $limit
                """

                result = session.run(query, {
                    "entity_type": entity_type,
                    "limit": limit
                })

                entities = []
                for record in result:
                    entity_data = {
                        "entity_id": record["entity_id"],
                        "name": record["name"],
                        "snomed_code": record["snomed_code"],
                        "properties": json.loads(record["properties"] or "{}")
                    }
                    entities.append(entity_data)

                return entities

        except Exception as e:
            logger.error(f"查询实体失败: {e}")
            return []

    def query_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        查询实体的关系

        Args:
            entity_id: 实体ID

        Returns:
            关系列表
        """
        if not self.neo4j_available:
            return []

        try:
            with self.driver.session() as session:
                query = """
                MATCH (source:MedicalEntity {entity_id: $entity_id})-[r:MEDICAL_RELATION]->(target:MedicalEntity)
                RETURN r.relationship_id as relationship_id,
                       r.relationship_type as relationship_type,
                       r.confidence as confidence,
                       target.entity_id as target_entity_id,
                       target.name as target_name,
                       target.entity_type as target_type
                UNION
                MATCH (source:MedicalEntity)-[r:MEDICAL_RELATION]->(target:MedicalEntity {entity_id: $entity_id})
                RETURN r.relationship_id as relationship_id,
                       r.relationship_type as relationship_type,
                       r.confidence as confidence,
                       source.entity_id as target_entity_id,
                       source.name as target_name,
                       source.entity_type as target_type
                """

                result = session.run(query, {"entity_id": entity_id})

                relationships = []
                for record in result:
                    relationship_data = {
                        "relationship_id": record["relationship_id"],
                        "relationship_type": record["relationship_type"],
                        "confidence": record["confidence"],
                        "related_entity": {
                            "entity_id": record["target_entity_id"],
                            "name": record["target_name"],
                            "entity_type": record["target_type"]
                        }
                    }
                    relationships.append(relationship_data)

                return relationships

        except Exception as e:
            logger.error(f"查询实体关系失败: {e}")
            return []

    def find_diagnostic_path(self, findings: List[str], target_diagnosis: str = None) -> List[Dict[str, Any]]:
        """
        查找诊断路径

        Args:
            findings: 发现列表
            target_diagnosis: 目标诊断（可选）

        Returns:
            诊断路径列表
        """
        if not self.neo4j_available:
            return []

        try:
            with self.driver.session() as session:
                # 构建查询，查找从发现到诊断的路径
                if target_diagnosis:
                    query = """
                    MATCH path = (finding:MedicalEntity)-[*1..3]->(diagnosis:MedicalEntity)
                    WHERE finding.name IN $findings
                      AND diagnosis.name = $target_diagnosis
                      AND diagnosis.entity_type = 'diagnosis'
                    RETURN path, length(path) as path_length
                    ORDER BY path_length
                    LIMIT 10
                    """
                    params = {"findings": findings, "target_diagnosis": target_diagnosis}
                else:
                    query = """
                    MATCH path = (finding:MedicalEntity)-[*1..3]->(diagnosis:MedicalEntity)
                    WHERE finding.name IN $findings
                      AND diagnosis.entity_type = 'diagnosis'
                    RETURN path, length(path) as path_length
                    ORDER BY path_length
                    LIMIT 10
                    """
                    params = {"findings": findings}

                result = session.run(query, params)

                paths = []
                for record in result:
                    path_data = {
                        "path_length": record["path_length"],
                        "nodes": [],
                        "relationships": []
                    }

                    # 解析路径中的节点和关系
                    path = record["path"]
                    for node in path.nodes:
                        node_data = {
                            "entity_id": node.get("entity_id"),
                            "name": node.get("name"),
                            "entity_type": node.get("entity_type"),
                            "snomed_code": node.get("snomed_code")
                        }
                        path_data["nodes"].append(node_data)

                    for rel in path.relationships:
                        rel_data = {
                            "relationship_type": rel.get("relationship_type"),
                            "confidence": rel.get("confidence", 1.0)
                        }
                        path_data["relationships"].append(rel_data)

                    paths.append(path_data)

                return paths

        except Exception as e:
            logger.error(f"查找诊断路径失败: {e}")
            return []

    def get_entity_statistics(self) -> Dict[str, Any]:
        """
        获取实体统计信息

        Returns:
            统计信息字典
        """
        if not self.neo4j_available:
            return {}

        try:
            with self.driver.session() as session:
                # 统计各类型实体数量
                type_query = """
                MATCH (e:MedicalEntity)
                RETURN e.entity_type as entity_type, count(e) as count
                ORDER BY count DESC
                """

                type_result = session.run(type_query)
                entity_types = {}
                total_entities = 0

                for record in type_result:
                    entity_type = record["entity_type"]
                    count = record["count"]
                    entity_types[entity_type] = count
                    total_entities += count

                # 统计关系数量
                rel_query = """
                MATCH ()-[r:MEDICAL_RELATION]->()
                RETURN r.relationship_type as relationship_type, count(r) as count
                ORDER BY count DESC
                """

                rel_result = session.run(rel_query)
                relationship_types = {}
                total_relationships = 0

                for record in rel_result:
                    rel_type = record["relationship_type"]
                    count = record["count"]
                    relationship_types[rel_type] = count
                    total_relationships += count

                # 统计SNOMED CT覆盖率
                snomed_query = """
                MATCH (e:MedicalEntity)
                WHERE e.snomed_code IS NOT NULL AND e.snomed_code <> ''
                RETURN count(e) as snomed_entities
                """

                snomed_result = session.run(snomed_query)
                snomed_entities = snomed_result.single()["snomed_entities"]
                snomed_coverage = snomed_entities / total_entities if total_entities > 0 else 0

                return {
                    "total_entities": total_entities,
                    "total_relationships": total_relationships,
                    "entity_types": entity_types,
                    "relationship_types": relationship_types,
                    "snomed_coverage": snomed_coverage,
                    "snomed_entities": snomed_entities
                }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def find_similar_entities(self, entity_id: str, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        查找相似实体

        Args:
            entity_id: 实体ID
            similarity_threshold: 相似度阈值

        Returns:
            相似实体列表
        """
        if not self.neo4j_available:
            return []

        try:
            with self.driver.session() as session:
                # 基于共同关系查找相似实体
                query = """
                MATCH (e1:MedicalEntity {entity_id: $entity_id})-[r1:MEDICAL_RELATION]->(common:MedicalEntity)
                MATCH (e2:MedicalEntity)-[r2:MEDICAL_RELATION]->(common)
                WHERE e1 <> e2 AND e1.entity_type = e2.entity_type
                WITH e2, count(common) as common_relations,
                     collect(DISTINCT common.name) as shared_concepts
                MATCH (e1:MedicalEntity {entity_id: $entity_id})-[r:MEDICAL_RELATION]->()
                WITH e2, common_relations, shared_concepts, count(r) as total_relations_e1
                MATCH (e2)-[r:MEDICAL_RELATION]->()
                WITH e2, common_relations, shared_concepts, total_relations_e1, count(r) as total_relations_e2
                WITH e2, common_relations, shared_concepts,
                     toFloat(common_relations) / (total_relations_e1 + total_relations_e2 - common_relations) as similarity
                WHERE similarity >= $threshold
                RETURN e2.entity_id as entity_id,
                       e2.name as name,
                       e2.entity_type as entity_type,
                       e2.snomed_code as snomed_code,
                       similarity,
                       common_relations,
                       shared_concepts
                ORDER BY similarity DESC
                LIMIT 10
                """

                result = session.run(query, {
                    "entity_id": entity_id,
                    "threshold": similarity_threshold
                })

                similar_entities = []
                for record in result:
                    entity_data = {
                        "entity_id": record["entity_id"],
                        "name": record["name"],
                        "entity_type": record["entity_type"],
                        "snomed_code": record["snomed_code"],
                        "similarity_score": record["similarity"],
                        "common_relations": record["common_relations"],
                        "shared_concepts": record["shared_concepts"]
                    }
                    similar_entities.append(entity_data)

                return similar_entities

        except Exception as e:
            logger.error(f"查找相似实体失败: {e}")
            return []

    def get_concept_hierarchy(self, root_concept: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        获取概念层次结构

        Args:
            root_concept: 根概念
            max_depth: 最大深度

        Returns:
            层次结构字典
        """
        if not self.neo4j_available:
            return {}

        try:
            with self.driver.session() as session:
                query = """
                MATCH path = (root:MedicalEntity {name: $root_concept})-[:MEDICAL_RELATION*0..%d]->(child:MedicalEntity)
                WHERE ALL(r in relationships(path) WHERE r.relationship_type = 'is_a' OR r.relationship_type = 'part_of')
                RETURN path
                ORDER BY length(path)
                """ % max_depth

                result = session.run(query, {"root_concept": root_concept})

                hierarchy = {
                    "root": root_concept,
                    "children": {},
                    "total_nodes": 0
                }

                for record in result:
                    path = record["path"]
                    current_level = hierarchy

                    for node in path.nodes[1:]:  # 跳过根节点
                        node_name = node.get("name")
                        if node_name not in current_level["children"]:
                            current_level["children"][node_name] = {
                                "entity_id": node.get("entity_id"),
                                "entity_type": node.get("entity_type"),
                                "snomed_code": node.get("snomed_code"),
                                "children": {}
                            }
                            hierarchy["total_nodes"] += 1
                        current_level = current_level["children"][node_name]

                return hierarchy

        except Exception as e:
            logger.error(f"获取概念层次结构失败: {e}")
            return {}

    def batch_store_entities(self, entities: List[MedicalEntity]) -> Dict[str, int]:
        """
        批量存储实体

        Args:
            entities: 实体列表

        Returns:
            存储结果统计
        """
        if not self.neo4j_available:
            return {"success": 0, "failed": 0}

        success_count = 0
        failed_count = 0

        try:
            with self.driver.session() as session:
                # 使用事务批量处理
                with session.begin_transaction() as tx:
                    for entity in entities:
                        try:
                            query = """
                            MERGE (e:MedicalEntity {entity_id: $entity_id})
                            SET e.entity_type = $entity_type,
                                e.name = $name,
                                e.snomed_code = $snomed_code,
                                e.properties = $properties,
                                e.created_at = $created_at,
                                e.updated_at = datetime()
                            """

                            tx.run(query, {
                                "entity_id": entity.entity_id,
                                "entity_type": entity.entity_type,
                                "name": entity.name,
                                "snomed_code": entity.snomed_code,
                                "properties": json.dumps(entity.properties or {}),
                                "created_at": entity.created_at or datetime.now()
                            })

                            success_count += 1

                        except Exception as e:
                            logger.warning(f"批量存储实体失败: {entity.entity_id}, 错误: {e}")
                            failed_count += 1

                    tx.commit()

        except Exception as e:
            logger.error(f"批量存储事务失败: {e}")
            failed_count = len(entities)

        logger.info(f"批量存储完成: 成功 {success_count}, 失败 {failed_count}")
        return {"success": success_count, "failed": failed_count}

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")
