#!/usr/bin/env python3
"""
测试步骤3: 关系建模测试
"""
import sys
import os
sys.path.append('.')

print("🔗 步骤3: 关系建模测试")
print("=" * 50)

# 模拟数据 - 实际处理结果的格式
mock_mapping_data = {
    "诊断列表": [
        {"类型": "肿瘤相关", "描述": "右肺上叶结节，考虑恶性病变可能"},
        {"类型": "感染相关", "描述": "双肺散在结节，炎性或其他"},
        {"类型": "血管相关", "描述": "主动脉壁钙化"}
    ],
    "影像特征列表": [
        {
            "名称": "右肺上叶结节",
            "特征": {"解剖位置": "右肺上叶", "大小": "1.5cm", "形态": "结节状", "边界": "毛糙"}
        },
        {
            "名称": "双肺散在结节",
            "特征": {"解剖位置": "双肺", "大小": "小", "形态": "结节状", "分布": "散在"}
        },
        {
            "名称": "主动脉壁钙化",
            "特征": {"解剖位置": "主动脉壁", "特性": "钙化"}
        }
    ],
    "映射关系": [
        {
            "影像发现": "右肺上叶1.5cm毛糙边界结节",
            "对应诊断": "右肺上叶结节，考虑恶性病变可能",
            "映射置信度": "高"
        },
        {
            "影像发现": "双肺散在小结节",
            "对应诊断": "双肺散在结节，炎性或其他",
            "映射置信度": "中"
        }
    ]
}

try:
    # 初始化关系建模器
    print("3.1 初始化关系建模组件...")
    import config
    from utils.config_manager import config_manager
    from utils.llm_client import LLMClient
    from utils.relationship_builder import RelationshipBuilder
    
    user_config = config_manager.get_config()
    llm_config = user_config.get('llm_config', config.LLM_CONFIG)
    llm_client = LLMClient(llm_config)
    relationship_builder = RelationshipBuilder(llm_client)
    
    print("✅ 关系建模组件初始化成功")
    
    # 测试添加映射数据
    print("\n3.2 测试添加映射数据...")
    try:
        relationship_builder.add_mapping(mock_mapping_data)
        print(f"✅ 映射数据添加成功")
        print(f"   - 当前特征-诊断对数量: {len(relationship_builder.feature_diagnosis_pairs)}")
        
        # 显示部分数据
        if relationship_builder.feature_diagnosis_pairs:
            for i, pair in enumerate(relationship_builder.feature_diagnosis_pairs[:3]):
                print(f"   [{i+1}] 特征: {pair.get('feature', 'N/A')}")
                print(f"       诊断: {pair.get('diagnosis', 'N/A')}")
                print(f"       支持程度: {pair.get('support_level', 'N/A')}")
    except Exception as e:
        print(f"❌ 添加映射数据失败: {str(e)}")
    
    # 测试概率模型构建 (不依赖LLM)
    print("\n3.3 测试概率模型构建...")
    try:
        # 添加更多模拟数据以便测试
        for i in range(3):
            relationship_builder.feature_diagnosis_pairs.append({
                "feature": f"测试特征{i+1}",
                "diagnosis": "肺癌",
                "support_level": "高",
                "explanation": f"测试解释{i+1}"
            })
        
        # 统计信息
        diagnosis_counts = {}
        for pair in relationship_builder.feature_diagnosis_pairs:
            diag = pair.get("diagnosis", "未知")
            diagnosis_counts[diag] = diagnosis_counts.get(diag, 0) + 1
        
        print(f"✅ 统计信息计算成功")
        print(f"   - 总诊断类型: {len(diagnosis_counts)}")
        for diag, count in diagnosis_counts.items():
            print(f"   - {diag}: {count} 次")
            
    except Exception as e:
        print(f"❌ 概率模型构建失败: {str(e)}")
    
    # 测试知识图谱构建
    print("\n3.4 测试知识图谱构建...")
    try:
        from utils.knowledge_graph import MedicalKnowledgeGraph
        
        graph = relationship_builder.build_knowledge_graph()
        print(f"✅ 知识图谱构建成功")
        print(f"   - 节点数量: {len(graph.nodes)}")
        print(f"   - 关系数量: {len(graph.relations)}")
        
        # 显示节点类型统计
        node_types = {}
        for node_id, node_data in graph.nodes.items():
            node_type = node_data.get("type", "未知")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("   - 节点类型分布:")
        for ntype, count in node_types.items():
            print(f"     {ntype}: {count} 个")
            
    except Exception as e:
        print(f"❌ 知识图谱构建失败: {str(e)}")
    
    # 测试知识库保存和加载
    print("\n3.5 测试知识库保存和加载...")
    try:
        import tempfile
        import json
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        # 保存知识库
        relationship_builder.save_knowledge_base(temp_file)
        print(f"✅ 知识库保存成功: {temp_file}")
        
        # 检查文件内容
        with open(temp_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print(f"   - 保存的特征-诊断对: {len(saved_data.get('feature_diagnosis_pairs', []))}")
        
        # 测试加载
        new_builder = RelationshipBuilder(llm_client)
        success = new_builder.load_knowledge_base(temp_file)
        
        if success:
            print(f"✅ 知识库加载成功")
            print(f"   - 加载的特征-诊断对: {len(new_builder.feature_diagnosis_pairs)}")
        else:
            print("❌ 知识库加载失败")
        
        # 清理临时文件
        os.unlink(temp_file)
        
    except Exception as e:
        print(f"❌ 知识库保存/加载测试失败: {str(e)}")
    
    # 测试Neo4j连接 (可选)
    print("\n3.6 测试Neo4j连接...")
    try:
        if config.USE_NEO4J:
            from utils.neo4j_connector import Neo4jConnector
            neo4j_client = Neo4jConnector()
            
            if neo4j_client.test_connection():
                print("✅ Neo4j连接测试成功")
            else:
                print("⚠️ Neo4j连接测试失败")
        else:
            print("⚠️ Neo4j未启用，跳过测试")
    except Exception as e:
        print(f"⚠️ Neo4j测试失败: {str(e)}")
    
    print("\n🎉 步骤3测试完成!")
    
except Exception as e:
    print(f"❌ 步骤3测试失败: {str(e)}")
    import traceback
    traceback.print_exc() 