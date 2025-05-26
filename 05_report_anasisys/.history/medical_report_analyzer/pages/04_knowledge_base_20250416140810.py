"""
知识库页面 - 显示和管理医学知识库内容
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
import time
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path

# 添加字体管理和配置
from utils import font_manager
from utils import plot_utils

import config
from utils.knowledge_base import MedicalKnowledgeBase

plot_utils.configure_chinese_font()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 知识库",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 医学知识库")
st.markdown("查看、管理和利用结构化提取积累的医学知识库")

# 初始化知识库
@st.cache_resource
def get_knowledge_base():
    return MedicalKnowledgeBase()

kb = get_knowledge_base()

# 加载知识库数据
try:
    with open(kb.db_path, 'r', encoding='utf-8') as f:
        knowledge_data = json.load(f)
    
    # 获取统计数据
    anatomical_count = len(knowledge_data.get("解剖结构关系", {}))
    diagnosis_count = len(knowledge_data.get("常见诊断", {}))
    mapping_count = len(knowledge_data.get("特征-诊断映射", {}))
    
    # 统计显示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("解剖结构数量", anatomical_count)
    
    with col2:
        st.metric("记录诊断数量", diagnosis_count)
    
    with col3:
        st.metric("特征-诊断映射数", mapping_count)
    
    # 知识库内容浏览
    tab1, tab2, tab3, tab4 = st.tabs(["解剖结构", "诊断信息", "影像-诊断映射", "原始数据"])
    
    # 解剖结构标签页
    with tab1:
        st.markdown("### 解剖结构关系")
        
        if anatomical_count > 0:
            # 创建解剖结构层次图
            G = nx.DiGraph()
            
            # 添加节点和边
            for structure, info in knowledge_data["解剖结构关系"].items():
                if "父结构" in info and info["父结构"]:
                    parent = info["父结构"]
                    count = info.get("计数", 1)
                    G.add_node(structure, count=count)
                    G.add_node(parent, count=1)  # 确保父节点存在
                    G.add_edge(parent, structure)
            
            if len(G.nodes) > 0:
                # 创建图形
                fig, ax = plt.subplots(figsize=(10, 8))
                
                try:
                    # 尝试使用层次布局
                    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
                except:
                    # 如果失败，使用弹簧布局
                    pos = nx.spring_layout(G, k=0.5, iterations=50)
                
                # 设置节点大小基于计数
                node_sizes = [30 + min(G.nodes[n].get("count", 1) * 5, 30) for n in G.nodes]
                
                # 绘制图形
                nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="skyblue", alpha=0.8)
                nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=15)
                nx.draw_networkx_labels(G, pos, font_size=10, font_family="SimHei")
                
                plt.title("解剖结构层次关系图", fontsize=15)
                plt.axis("off")
                st.pyplot(fig)
            
            # 显示解剖结构表格
            structure_data = []
            for structure, info in knowledge_data["解剖结构关系"].items():
                structure_data.append({
                    "解剖结构": structure,
                    "父结构": info.get("父结构", ""),
                    "出现次数": info.get("计数", 1)
                })
            
            if structure_data:
                st.dataframe(pd.DataFrame(structure_data).sort_values("出现次数", ascending=False), use_container_width=True)
        else:
            st.info("暂无解剖结构数据")
    
    # 诊断信息标签页
    with tab2:
        st.markdown("### 常见诊断信息")
        
        if diagnosis_count > 0:
            # 创建诊断信息表格
            diagnosis_data = []
            for diagnosis, info in knowledge_data["常见诊断"].items():
                # 提取分布信息
                type_dist = info.get("类型分布", {})
                diagnosis_data.append({
                    "诊断描述": diagnosis,
                    "出现次数": info.get("计数", 1),
                    "确诊次数": type_dist.get("确诊", 0),
                    "高度疑似次数": type_dist.get("高度疑似", 0),
                    "待排除次数": type_dist.get("待排除", 0),
                    "建议次数": type_dist.get("建议", 0),
                    "其他发现次数": type_dist.get("其他发现", 0)
                })
            
            if diagnosis_data:
                st.dataframe(pd.DataFrame(diagnosis_data).sort_values("出现次数", ascending=False), use_container_width=True)
            
            # 绘制诊断类型分布饼图
            if diagnosis_data:
                # 计算各类型总数
                type_counts = {
                    "确诊": sum(d["确诊次数"] for d in diagnosis_data),
                    "高度疑似": sum(d["高度疑似次数"] for d in diagnosis_data),
                    "待排除": sum(d["待排除次数"] for d in diagnosis_data),
                    "建议": sum(d["建议次数"] for d in diagnosis_data),
                    "其他发现": sum(d["其他发现次数"] for d in diagnosis_data)
                }
                
                # 移除零值
                type_counts = {k: v for k, v in type_counts.items() if v > 0}
                
                if type_counts:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.pie(
                        type_counts.values(), 
                        labels=type_counts.keys(), 
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0']
                    )
                    ax.axis('equal')
                    plt.title("诊断类型分布", fontsize=15)
                    st.pyplot(fig)
        else:
            st.info("暂无诊断信息数据")
    
    # 影像-诊断映射标签页
    with tab3:
        st.markdown("### 影像特征与诊断映射关系")
        
        if mapping_count > 0:
            # 创建映射表格
            mapping_data = []
            for feature, diagnoses in knowledge_data["特征-诊断映射"].items():
                # 找出最常见的诊断
                top_diagnosis = max(diagnoses.items(), key=lambda x: x[1]) if diagnoses else ("", 0)
                
                mapping_data.append({
                    "影像特征": feature,
                    "最常见诊断": top_diagnosis[0],
                    "对应次数": top_diagnosis[1],
                    "诊断数量": len(diagnoses)
                })
            
            if mapping_data:
                st.dataframe(pd.DataFrame(mapping_data).sort_values("对应次数", ascending=False), use_container_width=True)
            
            # 详细显示具体映射关系
            if mapping_data:
                selected_feature = st.selectbox(
                    "选择影像特征查看详细诊断映射:", 
                    options=[m["影像特征"] for m in mapping_data],
                    format_func=lambda x: f"{x[:50]}..." if len(x) > 50 else x
                )
                
                if selected_feature:
                    diagnoses = knowledge_data["特征-诊断映射"].get(selected_feature, {})
                    
                    if diagnoses:
                        # 创建诊断分布条形图
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 排序并截取名称
                        items = sorted(diagnoses.items(), key=lambda x: x[1], reverse=True)
                        labels = [f"{d[0][:30]}..." if len(d[0]) > 30 else d[0] for d in items]
                        values = [d[1] for d in items]
                        
                        bars = ax.bar(labels, values, color='skyblue')
                        
                        # 调整图形
                        plt.xticks(rotation=45, ha='right')
                        plt.title(f"'{selected_feature[:50]}...'的诊断分布")
                        plt.tight_layout()
                        
                        st.pyplot(fig)
        else:
            st.info("暂无影像-诊断映射数据")
    
    # 原始数据标签页
    with tab4:
        st.markdown("### 原始知识库数据")
        st.json(knowledge_data)
        
        # 提供下载选项
        json_data = json.dumps(knowledge_data, ensure_ascii=False, indent=2)
        st.download_button(
            "下载知识库JSON文件",
            data=json_data,
            file_name="medical_knowledge_base.json",
            mime="application/json"
        )
except Exception as e:
    st.error(f"加载知识库失败: {str(e)}")
    st.info("知识库可能尚未创建或为空。请先使用「结构分析」页面处理一些报告。")

# 高级管理功能
st.markdown("---")
st.markdown("### 知识库管理")

with st.expander("知识库管理选项"):
    # 提供清空选项
    if st.button("清空知识库", type="primary", help="删除所有累积的知识库内容，谨慎操作！"):
        try:
            # 备份当前知识库
            backup_path = kb.db_path.replace(".json", f"_backup_{time.strftime('%Y%m%d_%H%M%S')}.json")
            if os.path.exists(kb.db_path):
                with open(kb.db_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                
                # 创建新的空知识库
                empty_kb = {
                    "解剖结构关系": {},
                    "常见诊断": {},
                    "特征-诊断映射": {},
                    "用户修正记录": {}
                }
                
                with open(kb.db_path, 'w', encoding='utf-8') as f:
                    json.dump(empty_kb, f, ensure_ascii=False, indent=2)
                
                st.success(f"知识库已清空，旧数据已备份到: {backup_path}")
                st.info("请刷新页面查看更新后的知识库")
            else:
                st.info("知识库文件不存在，无需清空")
        except Exception as e:
            st.error(f"清空知识库失败: {str(e)}")
    
    # 知识库自动更新设置
    kb_auto_update = st.checkbox("自动更新知识库", value=True, help="自动将新分析的报告结果添加到知识库")
    
    if st.button("应用设置"):
        # 保存设置
        try:
            settings_path = os.path.join(os.path.dirname(kb.db_path), "knowledge_settings.json")
            settings = {"auto_update": kb_auto_update}
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            st.success("知识库设置已保存")
        except Exception as e:
            st.error(f"保存设置失败: {str(e)}")

st.markdown("""
### 知识库使用说明

医学知识库会从结构化处理的报告中自动积累知识，包括：

1. **解剖结构关系**：记录解剖结构之间的层次关系
2. **诊断信息**：累积常见诊断及其分类
3. **影像-诊断映射**：建立影像特征与诊断之间的对应关系

系统会利用这些知识来提高后续报告的结构化准确性。例如：
- 根据已知的解剖结构关系，正确识别父子结构
- 基于已有的影像-诊断映射，提高诊断关联的准确性
- 发现不一致的解剖结构标准化结果，并进行修正

随着处理的报告数量增加，知识库会变得更加丰富，提取准确性也将不断提高。
""")