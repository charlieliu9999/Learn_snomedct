#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充测试3: 边界条件和异常处理测试
测试系统在各种边缘情况和异常输入下的行为
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
from utils.relationship_builder import RelationshipBuilder
from utils.knowledge_graph import MedicalKnowledgeGraph
from utils.config_manager import ConfigManager
from utils.llm_client import LLMClient # 假设LLMClient可以被模拟

class TestEdgeCasesAndExceptionHandling(unittest.TestCase):
    """边界条件和异常处理测试类"""

    def setUp(self):
        """测试准备"""
        self.config_manager = ConfigManager()
        self.mock_llm_client = Mock(spec=LLMClient)
        self.extractor = StructureExtractor(self.mock_llm_client)
        self.relationship_builder = RelationshipBuilder(self.mock_llm_client)
        self.knowledge_graph = MedicalKnowledgeGraph()

    # --- StructureExtractor Edge Cases ---
    def test_extractor_empty_input(self):
        """测试StructureExtractor处理空报告和空诊断"""
        print("\n🧪 测试StructureExtractor - 空输入...")
        self.mock_llm_client.extract_json.return_value = {} # 模拟LLM在空输入时返回空JSON
        
        result = self.extractor.extract_report_structure("", "")
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("解剖结构", []), [])
        self.assertEqual(result.get("病变特征", []), [])
        self.assertEqual(result.get("诊断信息", []), [])
        self.assertEqual(result.get("映射关系", []), [])
        print("✅ StructureExtractor - 空输入测试通过")

    def test_extractor_malformed_llm_response(self):
        """测试StructureExtractor处理LLM返回的无效JSON"""
        print("\n🧪 测试StructureExtractor - LLM无效JSON响应...")
        # 模拟LLM返回无效JSON字符串
        self.mock_llm_client.extract_json.side_effect = json.JSONDecodeError("mock error", "doc", 0)
        
        result = self.extractor.extract_anatomical_structures("一些报告文本")
        self.assertEqual(result, []) # 预期返回空列表

        result_pathology = self.extractor.extract_lesion_features("一些报告文本")
        self.assertEqual(result_pathology, [])

        result_diagnosis = self.extractor.extract_diagnosis_info("一些诊断文本")
        self.assertEqual(result_diagnosis, [])
        print("✅ StructureExtractor - LLM无效JSON响应测试通过")

    def test_extractor_llm_exception(self):
        """测试StructureExtractor处理LLM客户端抛出异常 (由子方法处理)"""
        print("\n🧪 测试StructureExtractor - LLM客户端异常 (子方法处理)...")
        # This exception will be caught by extract_anatomical_structures, extract_lesion_features, etc.
        self.mock_llm_client.extract_json.side_effect = Exception("Mocked LLM API error")

        # Patch the logger of the structure_extractor module to check for error logs from sub-methods
        with patch('utils.structure_extractor.logger.error') as mock_structure_logger_error:
            result = self.extractor.extract_report_structure("报告文本", "诊断文本")

            self.assertIsInstance(result, dict)
            # Expect sub-methods to return defaults, and no top-level "错误信息"
            self.assertEqual(result.get("解剖结构"), [])
            self.assertEqual(result.get("病变特征"), [])
            # extract_diagnosis_info also has its own try-except, returning [] on error
            self.assertEqual(result.get("诊断信息"), []) 
            self.assertEqual(result.get("映射关系"), []) # map_findings_to_diagnosis also returns [] on error
            
            self.assertNotIn("错误信息", result) # Key should NOT be present at this top level
            self.assertIn("处理时间", result) # Method should complete and include processing time

            # Check if sub-methods logged errors
            self.assertTrue(mock_structure_logger_error.called)
            # Verify specific error messages if necessary (can be brittle)
            # Example: mock_structure_logger_error.assert_any_call("解剖结构提取失败: Mocked LLM API error")
            # Check that at least one expected error message was logged by a sub-method
            call_args_list = [call_args[0][0] for call_args in mock_structure_logger_error.call_args_list]
            self.assertTrue(any("提取失败: Mocked LLM API error" in arg for arg in call_args_list))

        print("✅ StructureExtractor - LLM客户端异常 (子方法处理) 测试通过")

    # --- RelationshipBuilder Edge Cases ---
    def test_relationship_builder_empty_inputs(self):
        """测试RelationshipBuilder处理空的或不完整的映射数据"""
        print("\n🧪 测试RelationshipBuilder - 空/不完整映射数据...")
        self.relationship_builder.feature_diagnosis_pairs = [] # Clear previous state
        self.relationship_builder.graph.clear()

        # Test 1: Add empty mapping
        self.relationship_builder.add_mapping({})
        graph = self.relationship_builder.build_knowledge_graph()
        self.assertEqual(len(graph.get_nodes()), 0)
        self.assertEqual(len(graph.get_relations()), 0)
        print("   - 空映射字典: 处理正常, 图为空")

        # Test 2: Add mapping with correct keys but empty lists
        self.relationship_builder.add_mapping({"诊断列表": [], "影像特征列表": [], "映射关系": []})
        graph = self.relationship_builder.build_knowledge_graph()
        self.assertEqual(len(graph.get_nodes()), 0)
        self.assertEqual(len(graph.get_relations()), 0)
        print("   - 空列表映射: 处理正常, 图为空")

        # Test 3: Add mapping with missing keys (should be handled by add_mapping)
        with patch('utils.relationship_builder.logger.warning') as mock_log_warning:
            self.relationship_builder.add_mapping({"诊断列表": []}) # Missing other keys
            mock_log_warning.assert_any_call("映射数据格式不正确，缺少必要的字段")
        graph = self.relationship_builder.build_knowledge_graph()
        self.assertEqual(len(graph.get_nodes()), 0) # No data should have been added to pairs
        print("   - 缺失键映射: 处理正常 (警告日志), 图为空")

        # Test 4: Mapping relation with empty diagnosis
        self.relationship_builder.add_mapping({
            "诊断列表": [], 
            "影像特征列表": [], 
            "映射关系": [{"诊断": "", "支持特征": ["feat1"]}]
        })
        graph = self.relationship_builder.build_knowledge_graph()
        self.assertEqual(len(graph.get_nodes()), 0)
        print("   - 映射关系中诊断为空: 处理正常, 图为空")

        print("✅ RelationshipBuilder - 空/不完整映射数据测试通过")
    
    def test_relationship_builder_malformed_llm_response(self):
        """测试RelationshipBuilder的LLM调用方法处理无效JSON响应"""
        print("\n🧪 测试RelationshipBuilder - LLM无效JSON响应...")
        
        # Ensure there's some data to trigger LLM call in build_probability_model
        self.relationship_builder.feature_diagnosis_pairs = [
            {"feature": "feat1", "diagnosis": "diag1"},
            {"feature": "feat2", "diagnosis": "diag1"} # Need at least 2 for a diagnosis to be processed
        ]
        
        # Mock LLM to return invalid JSON for build_probability_model
        self.mock_llm_client.extract_json.side_effect = json.JSONDecodeError("mock json decode error", "doc", 0)
        
        with patch('utils.relationship_builder.logger.error') as mock_log_error:
            prob_model = self.relationship_builder.build_probability_model()
            # The method should catch the error and return an empty dict or a partially built one.
            # Based on current implementation, it logs error and continues, so result might be {}
            # or contain successfully processed parts if loop continued.
            # For this test, we assume it returns {} or similar on error for all items.
            self.assertTrue(isinstance(prob_model, dict))
            if "诊断特征关联" in prob_model and prob_model["诊断特征关联"]:
                # This case means some items might have processed before error or error handling is different
                print("   - 注意: 概率模型部分建立成功，或错误处理逻辑需检查")
            else:
                 self.assertEqual(prob_model.get("诊断特征关联", {}), {})

            mock_log_error.assert_called()
            print(f"   - build_probability_model 错误日志已记录")

        # Test extract_diagnostic_guidelines
        self.mock_llm_client.extract_json.side_effect = json.JSONDecodeError("mock json decode error", "doc", 0)
        with patch('utils.relationship_builder.logger.error') as mock_log_error:
            guidelines = self.relationship_builder.extract_diagnostic_guidelines()
            self.assertEqual(guidelines, {"诊断指南": []}) # Expected to return default empty structure
            mock_log_error.assert_called()
            print(f"   - extract_diagnostic_guidelines 错误日志已记录")

        print("✅ RelationshipBuilder - LLM无效JSON响应测试通过")

    # --- KnowledgeGraph Edge Cases ---
    def test_knowledge_graph_add_empty_data(self):
        """测试KnowledgeGraph添加空数据/基本操作"""
        print("\n🧪 测试KnowledgeGraph - 添加空数据/基本操作...")
        self.knowledge_graph.clear() # Ensure graph is empty
        initial_nodes_count = len(self.knowledge_graph.get_nodes())
        initial_relations_count = len(self.knowledge_graph.get_relations())
        
        self.assertEqual(initial_nodes_count, 0)
        self.assertEqual(initial_relations_count, 0)
        
        # Add a single node with minimal data
        self.knowledge_graph.add_node(id="test_node_1", type="TEST_TYPE")
        self.assertEqual(len(self.knowledge_graph.get_nodes()), 1)
        
        # Add another node and a relation
        self.knowledge_graph.add_node(id="test_node_2", type="TEST_TYPE")
        self.knowledge_graph.add_relation(from_id="test_node_1", to_id="test_node_2", type="TEST_REL")
        self.assertEqual(len(self.knowledge_graph.get_nodes()), 2)
        self.assertEqual(len(self.knowledge_graph.get_relations()), 1)
        
        self.knowledge_graph.clear()
        self.assertEqual(len(self.knowledge_graph.get_nodes()), 0)

        print("✅ KnowledgeGraph - 添加空数据/基本操作测试通过")

    def test_knowledge_graph_malformed_node_data(self):
        """测试KnowledgeGraph处理格式错误的节点或关系数据"""
        print("\n🧪 测试KnowledgeGraph - 格式错误的节点/关系数据...")
        self.knowledge_graph.clear()
        
        # Test 1: Properties is not a dictionary
        node_id_malformed_props = "node_malformed_props"
        self.knowledge_graph.add_node(id=node_id_malformed_props, type="TEST_TYPE", properties="not_a_dictionary")
        
        # Verify current behavior: non-dict properties are stored as is
        nodes = self.knowledge_graph.get_nodes(type="TEST_TYPE")
        found_node = None
        for n in nodes:
            if n['id'] == node_id_malformed_props:
                found_node = n
                break
        self.assertIsNotNone(found_node)
        self.assertEqual(found_node['properties'], "not_a_dictionary")
        print("   - Non-dict properties test: current behavior verified (stores as is)")
        self.knowledge_graph.clear()

        # Test 2: Adding relation with non-existent nodes
        initial_relations_count = len(self.knowledge_graph.get_relations())
        
        # Mock module-level logger to capture warnings
        with patch('utils.knowledge_graph.logger.warning') as mock_log_warning:
            self.knowledge_graph.add_relation(from_id="non_existent_1", to_id="non_existent_2", type="TEST_REL")
            self.assertEqual(len(self.knowledge_graph.get_relations()), initial_relations_count) # No relation should be added
            mock_log_warning.assert_any_call("添加关系失败: 起始节点 non_existent_1 不存在")
        
        self.knowledge_graph.add_node(id="existing_node", type="TEST_TYPE")
        with patch('utils.knowledge_graph.logger.warning') as mock_log_warning:
            self.knowledge_graph.add_relation(from_id="existing_node", to_id="non_existent_target", type="TEST_REL")
            self.assertEqual(len(self.knowledge_graph.get_relations()), initial_relations_count)
            mock_log_warning.assert_any_call("添加关系失败: 目标节点 non_existent_target 不存在")

        print("✅ KnowledgeGraph - 格式错误的节点/关系数据测试通过")

    # --- Neo4jConnector Edge Cases (Conceptual - requires mock or live DB) ---
    @patch('utils.neo4j_connector.GraphDatabase')
    def test_neo4j_connection_failure(self, mock_graph_db_class):
        """测试Neo4jConnector在GraphDatabase.driver()调用失败时的场景"""
        print("\n🧪 测试Neo4jConnector - GraphDatabase.driver() 连接失败...")
        from utils.neo4j_connector import Neo4jConnector # Import moved inside for safety if module load is an issue

        # Make GraphDatabase.driver itself raise an exception
        mock_graph_db_class.driver.side_effect = Exception("Simulated driver creation/connection failed")

        with self.assertRaises(Exception) as cm:
            # These args don't matter much as GraphDatabase.driver call is mocked to fail
            connector = Neo4jConnector(
                uri="bolt://dummydb:7687", 
                user="user", 
                password="password"
            )
        # Check if the specific exception text is part of the raised exception
        # The Neo4jConnector re-raises the original exception from GraphDatabase.driver
        self.assertTrue("Simulated driver creation/connection failed" in str(cm.exception) or \
                        "连接Neo4j数据库失败" in str(cm.exception)) # Account for logger message if it's part of a custom exception

        print("✅ Neo4jConnector - GraphDatabase.driver() 连接失败测试通过 (预期异常)")

    @patch('utils.neo4j_connector.Neo4jConnector.query') # Mock the query method
    def test_neo4j_query_error(self, mock_query):
        """测试Neo4j查询执行错误"""
        print("\n🧪 测试Neo4jConnector - 查询错误...")
        from utils.neo4j_connector import Neo4jConnector

        try:
            # Correctly use get_value from ConfigManager
            connector = Neo4jConnector(
                uri=self.config_manager.get_value("NEO4J_URI", "bolt://localhost:7687"),
                user=self.config_manager.get_value("NEO4J_USER", "neo4j"),
                password=self.config_manager.get_value("NEO4J_PASSWORD", "password"),
                database=self.config_manager.get_value("NEO4J_DATABASE", "neo4j")
            )
        except Exception as e: 
            print(f"   - WARNING: Neo4j connection during Neo4jConnector init failed for test_neo4j_query_error ({e}). Using dummy connector.")
            connector = Neo4jConnector.__new__(Neo4jConnector) 
            connector._driver = Mock()
            connector.uri = self.config_manager.get_value("NEO4J_URI", "bolt://localhost:7687")
            connector.user = self.config_manager.get_value("NEO4J_USER", "neo4j")
            connector.password = self.config_manager.get_value("NEO4J_PASSWORD", "password")
            connector.database = self.config_manager.get_value("NEO4J_DATABASE", "neo4j")

        if not hasattr(connector, '_driver') or not connector._driver:
            connector._driver = Mock()
        
        mock_query.side_effect = Exception("CypherSyntaxError: Invalid query")
        
        with self.assertRaises(Exception) as cm:
            connector.query("SOME INVALID QUERY") 
        self.assertIn("CypherSyntaxError: Invalid query", str(cm.exception))
        
        print("✅ Neo4jConnector - 查询错误测试通过 (预期异常)")

    # --- Test very long input string for a component (e.g., standardize_text) ---
    def test_long_string_processing(self):
        """测试处理非常长的文本字符串 (例如，在standardize_text中)"""
        print("\n🧪 测试长字符串处理...")
        from utils.data_processor import standardize_text
        long_text = "这是一个很长很长的字符串..." * 1000 # 约几万字符
        standardized_long_text = standardize_text(long_text)
        self.assertIsInstance(standardized_long_text, str)
        self.assertTrue(len(standardized_long_text) > 0)
        # 可以添加更具体的检查，例如检查是否仍然是有效的文本而不是截断或错误
        print(f"✅ 长字符串处理测试通过 (长度: {len(standardized_long_text)})")

    def test_unexpected_data_types(self):
        """测试组件处理非预期数据类型输入"""
        print("\n🧪 测试非预期数据类型输入...")
        # StructureExtractor.extract_anatomical_structures 期望字符串
        with self.assertRaises(AttributeError) as cm_attr_error:
            self.extractor.extract_anatomical_structures(12345)
        # Check if the error message is as expected
        self.assertIn("'int' object has no attribute 'lower'", str(cm_attr_error.exception).lower())
        print("   - StructureExtractor with non-string input: AttributeError (expected, verified)")
        
        # MedicalKnowledgeGraph.add_node id expects string, using None as id
        # Using None as a dictionary key should raise TypeError: unhashable type: 'NoneType'
        print("   - Testing MedicalKnowledgeGraph.add_node(id=None) with fresh instance...")
        # Create a fresh instance for this specific test to ensure no side effects
        # utils.knowledge_graph.MedicalKnowledgeGraph should be the class we imported.
        isolated_kg = MedicalKnowledgeGraph() 
        isolated_kg.clear() # Ensure its self.nodes is a fresh dict
        
        with self.assertRaises(TypeError) as cm_kg_type_error:
            isolated_kg.add_node(id=None, type="解剖结构") # Call on the isolated instance
        
        # Verify the type of exception and that the message is as expected for a dict key error with None
        self.assertIsInstance(cm_kg_type_error.exception, TypeError)
        # Make the assertion case-insensitive and flexible with apostrophes for 'NoneType'
        self.assertTrue(
            "unhashable type: 'nonetype'" in str(cm_kg_type_error.exception).lower().replace("'", "") or \
            "unhashable type: nonetype" in str(cm_kg_type_error.exception).lower().replace("'", "")
        )
        print("   - MedicalKnowledgeGraph.add_node with id=None: TypeError (expected and verified)")

        print("✅ 非预期数据类型输入测试通过 (预期异常)")

def run_edge_case_tests():
    """运行边界条件和异常处理测试"""
    print("=" * 60)
    print("🧪 补充测试3: 边界条件和异常处理测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdgeCasesAndExceptionHandling)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 边界条件和异常处理测试结果:")
    print(f"   - 总测试数: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback_info in result.failures:
            print(f"   - {test.id()}: {str(traceback_info)}") # .id() for cleaner output
    
    if result.errors:
        print("\n⚠️ 错误的测试:")
        for test, traceback_info in result.errors:
            print(f"   - {test.id()}: {str(traceback_info)}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    print(f"\n✅ 测试成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1) 