"""
关系建模页面 - 构建影像表现与诊断结论之间的关联关系
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import json
import time
import matplotlib.pyplot as plt
import networkx as nx
from pyvis.network import Network

# 导入自定义网络可视化工具
from utils.network_visualizer import create_relationship_graph

# 导入知识图谱模式组件
from pages.knowledge_graph_mode import display_knowledge_graph_ui

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和工具模块
import config
from utils.relationship_builder import RelationshipBuilder

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 关系建模",
    page_icon="🔗",
    layout="wide"
)

st.title("🔗 影像-诊断关系建模")
st.markdown("构建影像表现与诊断结论之间的关联关系模型，支持双向驱动报告生成。")

# 初始化状态
if "relationship_builder" not in st.session_state:
    if st.session_state.get("llm_client") is not None:
        st.session_state.relationship_builder = RelationshipBuilder(st.session_state.llm_client)
    else:
        st.error("LLM客户端未初始化，请先返回首页")
        st.stop()

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = {}

# 数据检查
if not st.session_state.get("analyzed_reports"):
    st.warning("请先在「结构分析」页面分析报告")
    
    if st.button("前往结构分析页面"):
        st.switch_page("pages/02_structure_analyzer.py")
    
    st.stop()

# 侧边栏
st.sidebar.header("关系建模选项")

modeling_mode = st.sidebar.radio(
    "建模模式",
    ["构建知识库", "查看关系模型", "知识图谱", "生成双向模板"]
)

# 构建知识库模式
if modeling_mode == "构建知识库":
    st.markdown("### 构建影像-诊断知识库")
    
    # 添加分析报告到知识库
    st.markdown("#### 从分析报告构建知识库")
    
    if st.button("添加所有分析报告到知识库", key="add_all_reports"):
        with st.spinner("正在处理分析报告..."):
            # 获取所有报告的映射关系
            added_count = 0
            
            for report_key, report_data in st.session_state.analyzed_reports.items():
                try:
                    if "结构化数据" in report_data and "影像诊断映射" in report_data["结构化数据"]:
                        mapping = report_data["结构化数据"]["影像诊断映射"]
                        st.session_state.relationship_builder.add_mapping(mapping)
                        added_count += 1
                except Exception as e:
                    st.error(f"添加报告 {report_key} 失败: {str(e)}")
            
            st.success(f"成功添加 {added_count} 份报告的映射关系到知识库")
    
    # 构建概率模型
    st.markdown("#### 构建影像-诊断概率模型")
    
    if st.button("构建概率模型", key="build_model"):
        with st.spinner("正在构建概率模型..."):
            model = st.session_state.relationship_builder.build_probability_model()
            st.session_state.knowledge_base["probability_model"] = model
            
            if model:
                st.success("概率模型构建完成！")
                
                # 展示部分模型结果
                if "诊断特征关联" in model:
                    st.write(f"已为 {len(model['诊断特征关联'])} 种诊断建立特征关联")
            else:
                st.error("概率模型构建失败，请确保已添加足够的映射关系")
    
    # 提取诊断指南
    st.markdown("#### 提取诊断指南")
    
    if st.button("生成诊断指南", key="generate_guidelines"):
        with st.spinner("正在生成诊断指南..."):
            guidelines = st.session_state.relationship_builder.extract_diagnostic_guidelines()
            st.session_state.knowledge_base["diagnostic_guidelines"] = guidelines
            
            if guidelines and "诊断指南" in guidelines:
                st.success(f"成功生成 {len(guidelines['诊断指南'])} 项诊断指南！")
            else:
                st.error("诊断指南生成失败")
    
    # 保存知识库
    st.markdown("#### 保存知识库")
    
    save_filename = st.text_input(
        "保存文件名", 
        f"knowledge_base_{pd.Timestamp.now().strftime('%Y%m%d')}.json"
    )
    
    if st.button("保存知识库", key="save_kb"):
        save_path = config.PROCESSED_DATA_DIR / save_filename
        
        st.session_state.relationship_builder.save_knowledge_base(save_path)
        
        st.success(f"知识库已保存到: {save_path}")

# 查看关系模型模式
elif modeling_mode == "查看关系模型":
    st.markdown("### 查看影像-诊断关系模型")
    
    # 加载知识库
    kb_files = list(config.PROCESSED_DATA_DIR.glob("knowledge_base_*.json"))
    
    if kb_files:
        kb_file_names = [file.name for file in kb_files]
        selected_kb = st.sidebar.selectbox("选择知识库文件", kb_file_names)
        
        if st.sidebar.button("加载知识库", key="load_kb"):
            with st.spinner("正在加载知识库..."):
                kb_path = config.PROCESSED_DATA_DIR / selected_kb
                
                if st.session_state.relationship_builder.load_knowledge_base(kb_path):
                    st.session_state.knowledge_base = st.session_state.relationship_builder.knowledge_base
                    st.success("知识库加载成功！")
                else:
                    st.error("知识库加载失败")
    else:
        st.sidebar.warning("未找到知识库文件，请先构建并保存知识库")
    
    # 检查是否有知识库数据
    if not st.session_state.knowledge_base:
        st.info("请先构建或加载知识库")
    else:
        # 诊断频率分布
        if "probability_model" in st.session_state.knowledge_base and "诊断频率" in st.session_state.knowledge_base["probability_model"]:
            st.markdown("#### 诊断频率分布")
            
            diag_freq = st.session_state.knowledge_base["probability_model"]["诊断频率"]
            
            # 创建诊断频率图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            diags = list(diag_freq.keys())
            freqs = list(diag_freq.values())
            
            # 按频率排序
            sorted_idx = np.argsort(freqs)[::-1]
            diags = [diags[i] for i in sorted_idx]
            freqs = [freqs[i] for i in sorted_idx]
            
            plt.bar(diags[:10], freqs[:10])
            plt.xticks(rotation=45, ha='right')
            plt.ylabel('频率')
            plt.title('前10位诊断频率分布')
            plt.tight_layout()
            
            st.pyplot(fig)
        
        # 诊断-特征关联
        if "probability_model" in st.session_state.knowledge_base and "诊断特征关联" in st.session_state.knowledge_base["probability_model"]:
            st.markdown("#### 诊断-特征关联")
            
            diag_features = st.session_state.knowledge_base["probability_model"]["诊断特征关联"]
            
            # 选择特定诊断
            diags = list(diag_features.keys())
            if diags:
                selected_diag = st.selectbox("选择要查看的诊断", diags)
                
                if selected_diag in diag_features:
                    diag_data = diag_features[selected_diag]
                    
                    # 展示诊断信息
                    st.markdown(f"**诊断**: {selected_diag}")
                    
                    if "鉴别要点" in diag_data:
                        st.markdown(f"**鉴别要点**: {diag_data['鉴别要点']}")
                    
                    # 展示关键特征
                    if "关键特征" in diag_data:
                        st.markdown("**关键特征:**")
                        
                        features_df = pd.DataFrame(diag_data["关键特征"])
                        st.table(features_df)
                    
                    # 特征组合
                    if "特征组合" in diag_data:
                        st.markdown("**特征组合:**")
                        
                        combos_df = pd.DataFrame(diag_data["特征组合"])
                        st.table(combos_df)
                        
                    # 添加可视化关系图
                    st.markdown("**关系可视化:**")
                    
                    # 准备节点和边数据
                    nodes = []
                    edges = []
                    
                    # 添加诊断节点
                    nodes.append({
                        "id": selected_diag,
                        "label": selected_diag,
                        "group": 1,
                        "shape": "circle",
                        "size": 30,
                        "title": f"诊断: {selected_diag}"
                    })
                    
                    # 添加特征节点和边
                    if "关键特征" in diag_data:
                        for i, feature in enumerate(diag_data["关键特征"]):
                            feature_name = feature.get("特征", f"特征{i+1}")
                            support = feature.get("支持度", "中")
                            
                            # 添加特征节点
                            nodes.append({
                                "id": feature_name,
                                "label": feature_name,
                                "group": 2,
                                "shape": "box",
                                "title": f"特征: {feature_name}"
                            })
                            
                            # 添加边
                            edges.append({
                                "from": feature_name,
                                "to": selected_diag,
                                "label": support,
                                "title": f"支持度: {support}"
                            })
                    
                    # 使用自定义网络可视化工具显示关系图
                    if nodes and edges:
                        create_relationship_graph(nodes, edges, title=f"{selected_diag} 关系图")
                    else:
                        st.info("没有足够的数据来生成关系图")
            else:
                st.info("无诊断-特征关联数据")
        
        # 诊断指南
        if "diagnostic_guidelines" in st.session_state.knowledge_base and "诊断指南" in st.session_state.knowledge_base["diagnostic_guidelines"]:
            st.markdown("#### 诊断指南")
            
            guidelines = st.session_state.knowledge_base["diagnostic_guidelines"]["诊断指南"]
            
            # 选择特定诊断指南
            guideline_diags = [g["诊断名称"] for g in guidelines if "诊断名称" in g]
            
            if guideline_diags:
                selected_guideline = st.selectbox("选择要查看的诊断指南", guideline_diags)
                
                # 查找选中的指南
                for guideline in guidelines:
                    if guideline.get("诊断名称") == selected_guideline:
                        with st.expander(f"{selected_guideline} 诊断指南", expanded=True):
                            # 展示详细指南
                            if "典型影像表现" in guideline:
                                st.markdown("**典型影像表现:**")
                                st.write(guideline["典型影像表现"])
                            
                            if "鉴别诊断特征" in guideline:
                                st.markdown("**鉴别诊断特征:**")
                                st.write(guideline["鉴别诊断特征"])
                            
                            if "容易混淆疾病" in guideline:
                                st.markdown("**容易混淆疾病:**")
                                for disease in guideline["容易混淆疾病"]:
                                    st.write(f"- {disease}")
                            
                            if "置信度评估" in guideline:
                                st.markdown("**置信度评估:**")
                                st.write(guideline["置信度评估"])
            else:
                st.info("无诊断指南数据")

# 知识图谱模式
elif modeling_mode == "知识图谱":
    display_knowledge_graph_ui()

# 生成双向模板模式
elif modeling_mode == "生成双向模板":
    st.markdown("### 生成影像-诊断双向模板")
    
    # 如果已有知识库，使用已有数据
    if "knowledge_base" in st.session_state and "bidirectional_templates" in st.session_state.knowledge_base:
        templates = st.session_state.knowledge_base["bidirectional_templates"]
        st.success("已加载现有模板")
    else:
        # 否则生成新模板
        if st.button("生成双向驱动模板", key="generate_templates"):
            with st.spinner("正在生成双向驱动模板..."):
                templates = st.session_state.relationship_builder.generate_bidirectional_templates()
                st.session_state.knowledge_base["bidirectional_templates"] = templates
                
                if templates:
                    st.success("双向驱动模板生成完成！")
                else:
                    st.error("模板生成失败，请确保已添加足够的映射关系")
    
    # 展示模板
    if "knowledge_base" in st.session_state and "bidirectional_templates" in st.session_state.knowledge_base:
        templates = st.session_state.knowledge_base["bidirectional_templates"]
        
        tab1, tab2 = st.tabs(["影像→诊断模板", "诊断→描述模板"])
        
        with tab1:
            st.markdown("#### 影像→诊断模板")
            
            if "影像诊断模板" in templates:
                img_diag_template = templates["影像诊断模板"]
                
                # 输入字段
                if "输入字段" in img_diag_template:
                    st.markdown("**输入字段:**")
                    for field in img_diag_template["输入字段"]:
                        st.write(f"- {field}")
                
                # 特征组合规则
                if "特征组合规则" in img_diag_template:
                    st.markdown("**特征组合规则:**")
                    for rule in img_diag_template["特征组合规则"]:
                        st.write(f"- {rule}")
                
                # 诊断推理规则
                if "诊断推理规则" in img_diag_template:
                    st.markdown("**诊断推理规则:**")
                    for rule in img_diag_template["诊断推理规则"]:
                        st.write(f"- {rule}")
            else:
                st.info("无影像→诊断模板数据")
        
        with tab2:
            st.markdown("#### 诊断→描述模板")
            
            if "诊断描述模板" in templates and "诊断列表" in templates["诊断描述模板"]:
                diag_list = templates["诊断描述模板"]["诊断列表"]
                
                # 选择特定诊断模板
                diag_names = [d["诊断"] for d in diag_list if "诊断" in d]
                
                if diag_names:
                    selected_diag = st.selectbox("选择要查看的诊断描述模板", diag_names)
                    
                    # 展示选定诊断的模板
                    for diag_template in diag_list:
                        if diag_template.get("诊断") == selected_diag:
                            st.markdown(f"**{selected_diag} 描述模板:**")
                            
                            if "描述模板" in diag_template:
                                for i, template in enumerate(diag_template["描述模板"]):
                                    st.markdown(f"{i+1}. `{template}`")
                else:
                    st.info("无诊断描述模板数据")
            else:
                st.info("无诊断→描述模板数据")
    
    # 保存模板
    st.markdown("#### 保存模板")
    
    save_filename = st.text_input(
        "保存文件名", 
        f"bidirectional_templates_{pd.Timestamp.now().strftime('%Y%m%d')}.json"
    )
    
    if st.button("保存模板", key="save_templates"):
        if "knowledge_base" in st.session_state and "bidirectional_templates" in st.session_state.knowledge_base:
            templates = st.session_state.knowledge_base["bidirectional_templates"]
            
            save_path = config.PROCESSED_DATA_DIR / save_filename
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            
            st.success(f"模板已保存到: {save_path}")
        else:
            st.error("没有可保存的模板数据")

# 进一步分析的链接
st.markdown("---")
next_col1, next_col2, next_col3 = st.columns([1, 2, 1])

with next_col2:
    if st.button("进入报告生成", use_container_width=True):
        st.switch_page("pages/04_report_generator.py")
