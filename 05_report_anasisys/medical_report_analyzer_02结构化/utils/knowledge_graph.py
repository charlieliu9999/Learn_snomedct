"""
医学知识图谱基础模块
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 节点类型
NODE_TYPES = {
    "DIAGNOSIS": "诊断",
    "FEATURE": "影像特征",
    "ANATOMY": "解剖部位"
}

# 关系类型
RELATION_TYPES = {
    "INDICATES": "提示",  # 特征提示诊断
    "EXHIBITS": "表现为",  # 诊断表现为特征
    "LOCATED_AT": "位于",  # 特征位于解剖部位
    "COEXISTS_WITH": "共存"  # 特征与特征共存
}

class MedicalKnowledgeGraph:
    """医学知识图谱基础类"""
    
    def __init__(self):
        """初始化知识图谱"""
        self.nodes = {}  # 存储节点（诊断和特征）
        self.relations = []  # 存储关系
    
    def add_node(self, id: str, type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        添加节点
        
        参数:
            id: 节点唯一标识
            type: 节点类型
            properties: 节点属性
        """
        if not properties:
            properties = {}
            
        self.nodes[id] = {
            "type": type,
            "properties": properties
        }
        logger.debug(f"添加节点: {id}, 类型: {type}")
    
    def add_relation(self, from_id: str, to_id: str, type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        添加关系
        
        参数:
            from_id: 起始节点ID
            to_id: 目标节点ID
            type: 关系类型
            properties: 关系属性
        """
        if not properties:
            properties = {}
            
        # 确保节点存在
        if from_id not in self.nodes:
            logger.warning(f"添加关系失败: 起始节点 {from_id} 不存在")
            return
            
        if to_id not in self.nodes:
            logger.warning(f"添加关系失败: 目标节点 {to_id} 不存在")
            return
        
        relation = {
            "from_id": from_id,
            "to_id": to_id,
            "type": type,
            "properties": properties
        }
        
        self.relations.append(relation)
        logger.debug(f"添加关系: {from_id} --[{type}]--> {to_id}")
    
    def get_nodes(self, type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取节点
        
        参数:
            type: 节点类型，如果不指定则返回所有节点
            
        返回:
            节点列表
        """
        result = []
        for node_id, node_data in self.nodes.items():
            if type is None or node_data["type"] == type:
                result.append({
                    "id": node_id,
                    "type": node_data["type"],
                    "properties": node_data["properties"]
                })
        return result
    
    def get_relations(self, from_id: Optional[str] = None, to_id: Optional[str] = None, 
                     type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取关系
        
        参数:
            from_id: 起始节点ID，如果不指定则不筛选
            to_id: 目标节点ID，如果不指定则不筛选
            type: 关系类型，如果不指定则不筛选
            
        返回:
            关系列表
        """
        result = []
        for relation in self.relations:
            if (from_id is None or relation["from_id"] == from_id) and \
               (to_id is None or relation["to_id"] == to_id) and \
               (type is None or relation["type"] == type):
                result.append(relation)
        return result
    
    def to_json(self) -> str:
        """
        将知识图谱转换为JSON字符串
        
        返回:
            JSON字符串
        """
        kg_data = {
            "nodes": [{"id": k, **v} for k, v in self.nodes.items()],
            "relations": self.relations
        }
        return json.dumps(kg_data, ensure_ascii=False, indent=2)
    
    def from_json(self, json_str: str) -> None:
        """
        从JSON字符串加载知识图谱
        
        参数:
            json_str: JSON字符串
        """
        try:
            kg_data = json.loads(json_str)
            
            # 清空现有数据
            self.nodes = {}
            self.relations = []
            
            # 加载节点
            for node in kg_data.get("nodes", []):
                if "id" in node and "type" in node:
                    node_id = node.pop("id")
                    node_type = node.pop("type")
                    properties = node.get("properties", {})
                    self.add_node(node_id, node_type, properties)
            
            # 加载关系
            for relation in kg_data.get("relations", []):
                if all(k in relation for k in ["from_id", "to_id", "type"]):
                    self.add_relation(
                        relation["from_id"],
                        relation["to_id"],
                        relation["type"],
                        relation.get("properties", {})
                    )
                    
            logger.info(f"从JSON加载了 {len(self.nodes)} 个节点和 {len(self.relations)} 个关系")
        except Exception as e:
            logger.error(f"从JSON加载知识图谱失败: {str(e)}")
            raise
    
    def clear(self) -> None:
        """清空知识图谱"""
        self.nodes = {}
        self.relations = []
        logger.info("知识图谱已清空")
