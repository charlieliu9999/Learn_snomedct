"""
Neo4j数据库连接器，用于将知识图谱存储到Neo4j
"""

import logging
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目配置
import config
from .knowledge_graph import MedicalKnowledgeGraph

# 导入Neo4j库
try:
    from neo4j import GraphDatabase
except ImportError:
    logging.warning("未安装neo4j库，请使用 pip install neo4j 安装")

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jConnector:
    """Neo4j数据库连接器"""
    
    def __init__(self, uri=None, user=None, password=None, database=None):
        """
        初始化Neo4j连接器
        
        参数:
            uri: Neo4j服务器地址
            user: 用户名
            password: 密码
            database: 数据库名
        """
        # 使用参数或配置文件中的设置
        self.uri = uri or config.NEO4J_CONFIG["uri"]
        self.user = user or config.NEO4J_CONFIG["user"]
        self.password = password or config.NEO4J_CONFIG["password"]
        self.database = database or config.NEO4J_CONFIG["database"]
        
        self._driver = None
        try:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info(f"已连接到Neo4j数据库: {self.uri}")
        except Exception as e:
            logger.error(f"连接Neo4j数据库失败: {str(e)}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self._driver:
            self._driver.close()
            logger.info("已关闭Neo4j数据库连接")
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        返回:
            连接是否成功
        """
        try:
            with self._driver.session(database=self.database) as session:
                result = session.run("RETURN 1")
                record = result.single()
                if record and record[0] == 1:
                    logger.info("Neo4j数据库连接测试成功")
                    return True
                else:
                    logger.warning("Neo4j数据库连接测试失败")
                    return False
        except Exception as e:
            logger.error(f"Neo4j数据库连接测试异常: {str(e)}")
            return False
    
    def _escape_neo4j(self, value: str) -> str:
        """
        转义Neo4j特殊字符
        
        参数:
            value: 需要转义的字符串
            
        返回:
            转义后的字符串
        """
        if not isinstance(value, str):
            return value
        return value.replace("`", "``").replace("'", "\\'")
    
    def create_indexes(self):
        """创建必要的索引"""
        try:
            with self._driver.session(database=self.database) as session:
                # 为诊断创建索引
                session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{self._escape_neo4j('诊断')}) ON (n.id)")
                # 为影像特征创建索引
                session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{self._escape_neo4j('影像特征')}) ON (n.id)")
                # 为解剖部位创建索引
                session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{self._escape_neo4j('解剖部位')}) ON (n.id)")
                
                logger.info("已创建Neo4j索引")
        except Exception as e:
            logger.error(f"创建Neo4j索引失败: {str(e)}")
    
    def save_knowledge_graph(self, graph: MedicalKnowledgeGraph):
        """
        将知识图谱保存到Neo4j
        
        参数:
            graph: 知识图谱对象
        """
        # 确保连接可用
        if not self._driver:
            logger.error("未连接到Neo4j数据库")
            return
        
        # 创建索引
        self.create_indexes()
        
        try:
            with self._driver.session(database=self.database) as session:
                # 保存节点
                for node_id, node in graph.nodes.items():
                    node_type = node["type"]
                    properties = node["properties"]
                    
                    # 合并属性
                    all_props = {"id": node_id}
                    all_props.update(properties)
                    
                    # 创建Cypher查询
                    query = f"""
                    MERGE (n:{self._escape_neo4j(node_type)} {{id: $id}})
                    SET n += $props
                    """
                    
                    # 执行查询
                    session.run(query, {"id": node_id, "props": all_props})
                
                # 保存关系
                for relation in graph.relations:
                    from_id = relation["from_id"]
                    to_id = relation["to_id"]
                    rel_type = relation["type"]
                    properties = relation["properties"]
                    
                    # 获取节点类型
                    from_type = graph.nodes[from_id]["type"]
                    to_type = graph.nodes[to_id]["type"]
                    
                    # 创建Cypher查询
                    query = f"""
                    MATCH 
                      (a:{self._escape_neo4j(from_type)} {{id: $from_id}}),
                      (b:{self._escape_neo4j(to_type)} {{id: $to_id}})
                    MERGE (a)-[r:{self._escape_neo4j(rel_type)}]->(b)
                    SET r += $props
                    """
                    
                    # 执行查询
                    session.run(
                        query, 
                        {
                            "from_id": from_id,
                            "to_id": to_id,
                            "props": properties
                        }
                    )
                
                logger.info(f"已将知识图谱保存到Neo4j: {len(graph.nodes)}个节点, {len(graph.relations)}个关系")
        except Exception as e:
            logger.error(f"保存知识图谱到Neo4j失败: {str(e)}")
    
    def clear_database(self):
        """清空数据库"""
        try:
            with self._driver.session(database=self.database) as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("已清空Neo4j数据库")
        except Exception as e:
            logger.error(f"清空Neo4j数据库失败: {str(e)}")
    
    def query(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询
        
        参数:
            cypher_query: Cypher查询语句
            parameters: 查询参数
            
        返回:
            查询结果列表
        """
        if parameters is None:
            parameters = {}
            
        try:
            with self._driver.session(database=self.database) as session:
                result = session.run(cypher_query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"执行Cypher查询失败: {str(e)}")
            return []
    
    def find_relevant_diagnoses(self, features: List[str]) -> List[Dict[str, Any]]:
        """
        根据影像特征查找相关诊断
        
        参数:
            features: 影像特征列表
            
        返回:
            诊断列表，按相关性排序
        """
        if not features:
            return []
            
        # 构建Cypher查询
        query = """
        MATCH (f:`影像特征`)-[r:`提示`]->(d:`诊断`)
        WHERE f.id IN $features
        WITH d, count(r) AS rel_count, sum(r.confidence) AS total_confidence
        RETURN d.id AS diagnosis, d.name AS name, rel_count, 
               total_confidence / rel_count AS avg_confidence
        ORDER BY rel_count DESC, avg_confidence DESC
        LIMIT 10
        """
        
        return self.query(query, {"features": features})
    
    def find_features_for_diagnosis(self, diagnosis: str) -> List[Dict[str, Any]]:
        """
        根据诊断查找相关影像特征
        
        参数:
            diagnosis: 诊断名称
            
        返回:
            影像特征列表，按相关性排序
        """
        if not diagnosis:
            return []
            
        # 构建Cypher查询
        query = """
        MATCH (d:`诊断`)<-[r:`提示`]-(f:`影像特征`)
        WHERE d.id = $diagnosis
        RETURN f.id AS feature, f.name AS name, 
               r.confidence AS confidence, r.support_level AS support_level
        ORDER BY r.confidence DESC, r.support_level DESC
        """
        
        return self.query(query, {"diagnosis": diagnosis})
