#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
医学报告网络关系可视化工具
"""

import matplotlib.pyplot as plt
import networkx as nx
from .font_manager import apply_chinese_font_to_figure
import streamlit as st

# 导入字体管理模块，确保中文显示正常
from . import font_manager

def create_relationship_graph(nodes, edges, title="影像-诊断关系图"):
    """
    创建并显示影像-诊断关系图，使用matplotlib和networkx绘制
    
    参数:
        nodes: 节点列表，每个节点是一个字典，包含id、label、group等属性
        edges: 边列表，每个边是一个字典，包含from、to、label等属性
        title: 图表标题
    """
    # 创建有向图
    G = nx.DiGraph()
    
    # 节点属性映射
    node_groups = {}
    node_shapes = {}
    node_sizes = {}
    node_labels = {}
    
    # 添加节点和节点属性
    for node in nodes:
        node_id = node["id"]
        G.add_node(node_id)
        node_labels[node_id] = node.get("label", node_id)
        node_groups[node_id] = node.get("group", 1)
        node_shapes[node_id] = "o" if node.get("shape", "dot") in ["circle", "dot"] else "s"
        node_sizes[node_id] = node.get("size", 1200)
    
    # 添加边
    edge_labels = {}
    for edge in edges:
        source = edge["from"]
        target = edge["to"]
        G.add_edge(source, target)
        if "label" in edge and edge["label"]:
            edge_labels[(source, target)] = edge["label"]
    
    # 创建绘图
    plt.figure(figsize=(10, 8))
    
    # 设置布局 - 使用spring_layout提供良好的节点分布
    pos = nx.spring_layout(G, k=0.9, iterations=50)
    
    # 按组和形状绘制节点
    for group in set(node_groups.values()):
        group_nodes = [n for n, g in node_groups.items() if g == group]
        
        # 为不同组设置不同颜色
        if group == 1:  # 诊断节点
            color = "#D2E5FF"  # 浅蓝色
            edgecolor = "#2B7CE9"  # 深蓝色边框
        else:  # 特征节点
            color = "#FFD2D9"  # 浅粉色
            edgecolor = "#FF6F91"  # 深粉色边框
        
        # 按形状分别绘制
        for shape in set(node_shapes.values()):
            shape_nodes = [n for n in group_nodes if node_shapes[n] == shape]
            if shape_nodes:
                node_size = [node_sizes[n] for n in shape_nodes]
                nx.draw_networkx_nodes(G, pos, nodelist=shape_nodes, node_shape=shape,
                                      node_color=color, edgecolors=edgecolor,
                                      node_size=node_size, linewidths=2)
    
    # 绘制边
    nx.draw_networkx_edges(G, pos, edge_color='#888888', connectionstyle='arc3,rad=0.1',
                         arrowsize=15, width=1.5, alpha=0.7, arrows=True)
    
    # 绘制节点标签
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12, font_family='sans-serif')
    
    # 绘制边标签
    if edge_labels:
        # 稍微调整边标签位置以避免重叠
        label_pos = {}
        for edge, _ in edge_labels.items():
            # 获取源节点和目标节点的位置
            source_pos = pos[edge[0]]
            target_pos = pos[edge[1]]
            # 计算边的中点，并稍微向外偏移
            label_pos[edge] = ((source_pos[0] + target_pos[0]) / 2,
                               (source_pos[1] + target_pos[1]) / 2)
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10,
                                   font_family='sans-serif', alpha=0.7)
    
    # 设置图表标题和样式
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    
    apply_chinese_font_to_figure(plt.gcf())
    st.pyplot(plt.gcf())
    plt.close()
    
    return G