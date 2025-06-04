"""
知识图谱模式UI组件 - 用于在relationship_builder.py中嵌入使用
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import base64
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
import config
from utils.neo4j_connector import Neo4jConnector

def display_knowledge_graph_ui():
    """显示知识图谱模式的UI界面"""
    st.markdown("### 医学知识图谱构建与查询")
    
    # 检查Neo4j连接
    neo4j_status = st.sidebar.empty()
    
    try:
        neo4j_client = Neo4jConnector()
        if neo4j_client.test_connection():
            neo4j_status.success("Neo4j连接成功")
        else:
            neo4j_status.error("Neo4j连接失败")
            st.warning("无法连接到Neo4j数据库，请检查配置或确保Neo4j服务已启动")
            # 禁用Neo4j存储
            config.USE_NEO4J = False
    except Exception as e:
        neo4j_status.error(f"Neo4j连接错误: {str(e)}")
        st.warning("无法连接到Neo4j数据库，请检查配置或确保Neo4j服务已启动")
        # 禁用Neo4j存储
        config.USE_NEO4J = False
    
    # 从JSON文件加载数据
    st.markdown("#### 从JSON文件加载数据")
    
    json_file = st.file_uploader("选择关系数据JSON文件", type=["json"])
    
    if json_file is not None:
        try:
            # 读取JSON文件内容
            data = json.load(json_file)
            
            # 检查数据格式
            if "feature_diagnosis_pairs" in data:
                # 显示数据统计
                pairs_count = len(data["feature_diagnosis_pairs"])
                st.success(f"成功加载JSON文件，包含 {pairs_count} 个特征-诊断关系对")
                
                # 加载到relationship_builder
                if st.button("导入关系数据", key="load_json_data", use_container_width=True):
                    with st.spinner("正在导入关系数据..."):
                        # 清空现有关系数据
                        st.session_state.relationship_builder.feature_diagnosis_pairs = []
                        
                        # 导入新数据
                        for pair in data["feature_diagnosis_pairs"]:
                            st.session_state.relationship_builder.feature_diagnosis_pairs.append(pair)
                        
                        st.success(f"已成功导入 {len(st.session_state.relationship_builder.feature_diagnosis_pairs)} 个特征-诊断关系")
            else:
                st.error("JSON文件格式不正确，未找到'feature_diagnosis_pairs'字段")
                
        except Exception as e:
            st.error(f"加载JSON文件失败: {str(e)}")
    
    # 数据统计和导出功能
    if hasattr(st.session_state, 'relationship_builder') and hasattr(st.session_state.relationship_builder, 'feature_diagnosis_pairs'):
        pairs_count = len(st.session_state.relationship_builder.feature_diagnosis_pairs)
        if pairs_count > 0:
            st.info(f"当前已加载 {pairs_count} 个特征-诊断关系对")
            
            # 添加导出功能
            col1, col2 = st.columns([1, 1])
            with col1:
                # 显示部分数据示例
                if st.checkbox("显示数据示例"):
                    sample_size = min(5, pairs_count)
                    sample_data = st.session_state.relationship_builder.feature_diagnosis_pairs[:sample_size]
                    
                    # 创建数据框
                    df = pd.DataFrame(sample_data)
                    st.dataframe(df, use_container_width=True)
            
            with col2:
                # 导出到JSON文件
                if st.button("导出关系数据到JSON", key="export_json", use_container_width=True):
                    try:
                        # 准备数据
                        export_data = {
                            "feature_diagnosis_pairs": st.session_state.relationship_builder.feature_diagnosis_pairs,
                            "export_date": str(pd.Timestamp.now()),
                            "count": pairs_count
                        }
                        
                        # 转换为JSON字符串
                        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                        
                        # 创建下载链接
                        b64 = base64.b64encode(json_str.encode()).decode()
                        href = f'<a href="data:application/json;base64,{b64}" download="feature_diagnosis_pairs_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.json">\u70b9\u51fb\u4e0b\u8f7d JSON \u6587\u4ef6</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success("已准备好文件下载链接")
                    except Exception as e:
                        st.error(f"导出JSON文件失败: {str(e)}")
            
            # 添加数据统计
            if st.checkbox("显示详细统计"):
                # 统计诊断和特征数量
                diagnoses = set(pair["diagnosis"] for pair in st.session_state.relationship_builder.feature_diagnosis_pairs if "diagnosis" in pair)
                features = set(pair["feature"] for pair in st.session_state.relationship_builder.feature_diagnosis_pairs if "feature" in pair)
                
                st.write(f"\u4e0d同诊断数量: {len(diagnoses)}")
                st.write(f"\u4e0d同特征数量: {len(features)}")
                
                # 按支持程度统计
                support_counts = {}
                for pair in st.session_state.relationship_builder.feature_diagnosis_pairs:
                    if "support_level" in pair:
                        level = pair["support_level"]
                        support_counts[level] = support_counts.get(level, 0) + 1
                
                if support_counts:
                    support_df = pd.DataFrame({
                        "支持程度": list(support_counts.keys()),
                        "数量": list(support_counts.values())
                    })
                    st.dataframe(support_df, use_container_width=True)
    
    # 分割线
    st.markdown("---")
    
    # 构建知识图谱
    st.markdown("#### 构建知识图谱")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("构建知识图谱", key="build_kg", use_container_width=True):
            with st.spinner("正在构建知识图谱..."):
                try:
                    # 构建知识图谱
                    graph = st.session_state.relationship_builder.build_knowledge_graph()
                    
                    # 更新会话状态
                    st.session_state.kg_built = True
                    
                    # 保存到Neo4j
                    if config.USE_NEO4J:
                        success = st.session_state.relationship_builder.save_to_neo4j()
                        if success:
                            st.success(f"知识图谱已成功构建并保存到Neo4j: {len(graph.nodes)}个节点, {len(graph.relations)}个关系")
                        else:
                            st.error("保存到Neo4j失败，但知识图谱已在内存中构建")
                            st.success(f"知识图谱已在内存中构建: {len(graph.nodes)}个节点, {len(graph.relations)}个关系")
                    else:
                        st.success(f"知识图谱已在内存中构建: {len(graph.nodes)}个节点, {len(graph.relations)}个关系")
                except Exception as e:
                    st.error(f"构建知识图谱失败: {str(e)}")
    
    with col2:
        if st.button("清空知识图谱", key="clear_kg", use_container_width=True):
            if config.USE_NEO4J and 'neo4j_client' in locals() and neo4j_client:
                try:
                    neo4j_client.clear_database()
                    st.success("Neo4j数据库已清空")
                except Exception as e:
                    st.error(f"清空Neo4j数据库失败: {str(e)}")
            
            # 清空内存中的图谱
            if hasattr(st.session_state.relationship_builder, 'graph'):
                st.session_state.relationship_builder.graph.clear()
                st.success("内存中的知识图谱已清空")
            
            # 更新会话状态
            st.session_state.kg_built = False
    
    # 分割线
    st.markdown("---")
    
    # 基于特征的诊断推理
    st.markdown("#### 基于特征的诊断推理")
    
    with st.form(key="feature_diagnosis_form"):
        features_text = st.text_area(
            "输入影像特征（每行一个）", 
            height=150,
            placeholder="例如：\n右肺下叶可见一枚约2cm大小的结节影\n边缘模糊\n内部密度不均匀"
        )
        
        submit_button = st.form_submit_button(label="推理可能的诊断", use_container_width=True)
    
    if submit_button and features_text:
        features = [f.strip() for f in features_text.split('\n') if f.strip()]
        
        if not features:
            st.warning("请输入至少一个有效的影像特征")
        else:
            with st.spinner("正在推理可能的诊断..."):
                try:
                    if config.USE_NEO4J and 'neo4j_client' in locals() and neo4j_client:
                        # 使用Neo4j进行查询
                        diagnoses = neo4j_client.find_relevant_diagnoses(features)
                        
                        if diagnoses:
                            st.success(f"找到 {len(diagnoses)} 个可能的诊断")
                            
                            # 创建诊断表格
                            df = pd.DataFrame(diagnoses)
                            df.columns = ["诊断", "名称", "关联特征数", "平均置信度"]
                            df["平均置信度"] = df["平均置信度"].map(lambda x: f"{x:.2%}")
                            
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("未找到与输入特征相关的诊断")
                    else:
                        # 使用内存中的知识图谱
                        if not hasattr(st.session_state, 'kg_built') or not st.session_state.kg_built:
                            st.warning("请先构建知识图谱")
                        else:
                            # 简单的内存匹配逻辑
                            matched_diagnoses = []
                            
                            for feature in features:
                                # 获取与特征相关的诊断关系
                                for relation in st.session_state.relationship_builder.graph.get_relations(type="INDICATES"):
                                    rel_feature = relation["from_id"]
                                    
                                    # 简单字符串匹配
                                    if feature.lower() in rel_feature.lower() or rel_feature.lower() in feature.lower():
                                        diagnosis = relation["to_id"]
                                        confidence = relation["properties"].get("confidence", 0)
                                        support_level = relation["properties"].get("support_level", "")
                                        
                                        matched_diagnoses.append({
                                            "diagnosis": diagnosis,
                                            "feature": rel_feature,
                                            "confidence": confidence,
                                            "support_level": support_level
                                        })
                            
                            if matched_diagnoses:
                                # 按诊断分组并计算评分
                                diagnosis_scores = {}
                                
                                for match in matched_diagnoses:
                                    diag = match["diagnosis"]
                                    conf = match["confidence"]
                                    
                                    if diag in diagnosis_scores:
                                        diagnosis_scores[diag]["count"] += 1
                                        diagnosis_scores[diag]["total_conf"] += conf
                                    else:
                                        diagnosis_scores[diag] = {
                                            "count": 1,
                                            "total_conf": conf
                                        }
                                
                                # 转换为列表并排序
                                result = []
                                for diag, scores in diagnosis_scores.items():
                                    result.append({
                                        "诊断": diag,
                                        "关联特征数": scores["count"],
                                        "平均置信度": scores["total_conf"] / scores["count"]
                                    })
                                
                                # 按特征数和置信度排序
                                result.sort(key=lambda x: (x["关联特征数"], x["平均置信度"]), reverse=True)
                                
                                if result:
                                    st.success(f"找到 {len(result)} 个可能的诊断")
                                    
                                    # 创建诊断表格
                                    df = pd.DataFrame(result)
                                    df["平均置信度"] = df["平均置信度"].map(lambda x: f"{x:.2%}")
                                    
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    st.info("未找到与输入特征相关的诊断")
                            else:
                                st.info("未找到与输入特征相关的诊断")
                except Exception as e:
                    st.error(f"诊断推理失败: {str(e)}")
    
    # 分割线
    st.markdown("---")
    
    # 基于诊断的特征生成
    st.markdown("#### 基于诊断的特征生成")
    
    with st.form(key="diagnosis_feature_form"):
        diagnosis = st.text_input(
            "输入诊断名称", 
            placeholder="例如：肺腺癌"
        )
        
        submit_button = st.form_submit_button(label="生成典型影像特征", use_container_width=True)
    
    if submit_button and diagnosis:
        with st.spinner("正在生成典型影像特征..."):
            try:
                if config.USE_NEO4J and 'neo4j_client' in locals() and neo4j_client:
                    # 使用Neo4j进行查询
                    features = neo4j_client.find_features_for_diagnosis(diagnosis)
                    
                    if features:
                        st.success(f"找到 {len(features)} 个与'{diagnosis}'相关的影像特征")
                        
                        # 创建特征表格
                        df = pd.DataFrame(features)
                        df.columns = ["特征ID", "特征名称", "置信度", "支持程度"]
                        df["置信度"] = df["置信度"].map(lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
                        
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info(f"未找到与'{diagnosis}'相关的影像特征")
                else:
                    # 使用内存中的知识图谱
                    if not hasattr(st.session_state, 'kg_built') or not st.session_state.kg_built:
                        st.warning("请先构建知识图谱")
                    else:
                        # 简单的内存匹配逻辑
                        matched_features = []
                        
                        # 获取与诊断相关的特征关系
                        for relation in st.session_state.relationship_builder.graph.get_relations(type="EXHIBITS"):
                            rel_diagnosis = relation["from_id"]
                            
                            # 简单字符串匹配
                            if diagnosis.lower() in rel_diagnosis.lower() or rel_diagnosis.lower() in diagnosis.lower():
                                feature = relation["to_id"]
                                typical = relation["properties"].get("typical", False)
                                
                                matched_features.append({
                                    "feature": feature,
                                    "diagnosis": rel_diagnosis,
                                    "typical": typical
                                })
                        
                        if matched_features:
                            # 整理特征信息
                            result = []
                            for match in matched_features:
                                result.append({
                                    "特征ID": match["feature"],
                                    "特征名称": match["feature"],
                                    "典型性": "典型" if match["typical"] else "非典型"
                                })
                            
                            # 按典型性排序
                            result.sort(key=lambda x: 0 if x["典型性"] == "典型" else 1)
                            
                            if result:
                                st.success(f"找到 {len(result)} 个与'{diagnosis}'相关的影像特征")
                                
                                # 创建特征表格
                                df = pd.DataFrame(result)
                                
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info(f"未找到与'{diagnosis}'相关的影像特征")
                        else:
                            st.info(f"未找到与'{diagnosis}'相关的影像特征")
            except Exception as e:
                st.error(f"特征生成失败: {str(e)}")
    
    # 分割线
    st.markdown("---")
    
    # 知识图谱统计信息
    st.markdown("#### 知识图谱统计信息")
    
    if config.USE_NEO4J and 'neo4j_client' in locals() and neo4j_client:
        try:
            # 执行Cypher查询获取统计信息
            query = """
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            """
            
            node_counts = neo4j_client.query(query)
            
            if node_counts:
                # 创建节点统计表格
                df = pd.DataFrame(node_counts)
                
                st.subheader("节点类型统计")
                st.dataframe(df, use_container_width=True)
                
                # 获取关系统计信息
                query = """
                MATCH ()-[r]->()
                RETURN type(r) AS relation_type, count(r) AS count
                """
                
                rel_counts = neo4j_client.query(query)
                
                if rel_counts:
                    # 创建关系统计表格
                    df = pd.DataFrame(rel_counts)
                    
                    st.subheader("关系类型统计")
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("知识图谱中没有节点数据")
        except Exception as e:
            st.error(f"获取知识图谱统计信息失败: {str(e)}")
    else:
        # 使用内存中的知识图谱
        if hasattr(st.session_state.relationship_builder, 'graph'):
            graph = st.session_state.relationship_builder.graph
            
            # 节点统计
            node_types = {}
            for node_id, node in graph.nodes.items():
                node_type = node["type"]
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node_types:
                # 创建节点统计表格
                node_df = pd.DataFrame({"节点类型": list(node_types.keys()), "数量": list(node_types.values())})
                
                st.subheader("节点类型统计")
                st.dataframe(node_df, use_container_width=True)
            else:
                st.info("知识图谱中没有节点数据")
            
            # 关系统计
            relation_types = {}
            for relation in graph.relations:
                rel_type = relation["type"]
                relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
            
            if relation_types:
                # 创建关系统计表格
                rel_df = pd.DataFrame({"关系类型": list(relation_types.keys()), "数量": list(relation_types.values())})
                
                st.subheader("关系类型统计")
                st.dataframe(rel_df, use_container_width=True)
            else:
                st.info("知识图谱中没有关系数据")
        else:
            st.info("请先构建知识图谱")
