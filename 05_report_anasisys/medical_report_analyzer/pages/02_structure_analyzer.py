"""
结构分析页面 - 用于提取医学影像报告的结构化信息
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
import time

# 引入列名映射配置
from config import COLUMN_MAPPINGS

# 导入字体管理和配置
from utils import font_manager
from utils import plot_utils

import config
from utils.structure_extractor import StructureExtractor
from utils.knowledge_settings import knowledge_settings
from utils.knowledge_base import MedicalKnowledgeBase
from utils.diagnosis_associator import DiagnosisAssociator

plot_utils.configure_chinese_font()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 结构分析",
    page_icon="🔬",
    layout="wide"
)

# 定义显示诊断与病变关联关系的函数
def display_associations(analysis_result):
    """显示诊断与病变的关联关系"""
    if "关联关系" not in analysis_result:
        st.info("未找到诊断与病变的关联数据，可能是因为关联分析未启用或分析失败。")
        
        # 提供手动创建关联的选项
        if st.button("手动创建关联"):
            try:
                # 获取结构化数据
                if "结构化数据" in analysis_result:
                    data = analysis_result["结构化数据"]
                    
                    # 检查是否有病变特征和诊断信息
                    lesions = data.get("病变特征", [])
                    diagnoses = data.get("诊断信息", [])
                    
                    if not lesions or not diagnoses:
                        st.warning("没有足够的病变特征或诊断信息来创建关联。")
                        return
                    
                    with st.spinner("正在创建诊断关联..."):
                        # 使用LLM客户端
                        llm_client = st.session_state.llm_client
                        # 创建诊断关联器
                        associator = DiagnosisAssociator(llm_client)
                        # 执行关联
                        associations = associator.associate_features_with_diagnoses(
                            lesions,
                            diagnoses,
                            data.get("解剖结构", [])
                        )
                        # 更新分析结果
                        analysis_result["关联关系"] = associations
                        st.success("关联创建成功！")
                        # 重新显示关联数据
                        st.experimental_rerun()
                else:
                    st.error("没有可用的结构化数据。")
            except Exception as e:
                st.error(f"创建关联失败: {str(e)}")
        return
    
    associations = analysis_result["关联关系"]
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 左侧显示诊断到病变的映射
    with col1:
        st.markdown("#### 诊断关联的病变")
        for diagnosis_id, info in associations.get("诊断到病变映射", {}).items():
            # 找到诊断信息
            diagnosis = None
            if "结构化数据" in analysis_result:
                diagnosis = next((d for d in analysis_result["结构化数据"].get("诊断信息", []) 
                                 if d.get("诊断ID") == diagnosis_id), {})
            
            if not diagnosis or not diagnosis.get("内容"):
                title = f"诊断 {diagnosis_id}"
            else:
                title = f"{diagnosis.get('内容', '未知诊断')}"
                
            with st.expander(title):
                st.markdown(f"**关联理由**: {info.get('关联理由', '无')}")
                
                # 显示关联的病变
                for lesion_id in info.get("相关病变列表", []):
                    lesion = None
                    if "结构化数据" in analysis_result:
                        lesion = next((l for l in analysis_result["结构化数据"].get("病变特征", []) 
                                        if l.get("病变ID") == lesion_id), {})
                    
                    strength = associations.get("关联强度", {}).get(diagnosis_id, {}).get(lesion_id, 0)
                    
                    if lesion:
                        st.markdown(f"""
                        <div style='border-left: 4px solid {'#28a745' if strength > 0.7 else '#ffc107' if strength > 0.4 else '#dc3545'}; padding-left: 10px; margin: 5px 0;'>
                          <b>位置</b>: {lesion.get('解剖位置', '未知')} | 
                          <b>大小</b>: {lesion.get('大小', '未知')} | 
                          <b>关联强度</b>: {strength:.2f}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"病变ID: {lesion_id} (无详细信息)")
    
    # 右侧显示病变到诊断的映射
    with col2:
        st.markdown("#### 病变关联的诊断")
        for lesion_id, info in associations.get("病变到诊断映射", {}).items():
            # 找到病变信息
            lesion = None
            if "结构化数据" in analysis_result:
                lesion = next((l for l in analysis_result["结构化数据"].get("病变特征", []) 
                               if l.get("病变ID") == lesion_id), {})
            
            if not lesion:
                title = f"病变 {lesion_id}"
            else:
                title = f"{lesion.get('解剖位置', '未知位置')} ({lesion.get('大小', '未知大小')})"
                
            with st.expander(title):
                # 显示关联的诊断
                for diagnosis_id in info.get("相关诊断列表", []):
                    diagnosis = None
                    if "结构化数据" in analysis_result:
                        diagnosis = next((d for d in analysis_result["结构化数据"].get("诊断信息", []) 
                                          if d.get("诊断ID") == diagnosis_id), {})
                    
                    strength = associations.get("关联强度", {}).get(diagnosis_id, {}).get(lesion_id, 0)
                    reason = info.get("关联理由", {}).get(diagnosis_id, "")
                    
                    if diagnosis:
                        st.markdown(f"""
                        <div style='border-left: 4px solid {'#28a745' if strength > 0.7 else '#ffc107' if strength > 0.4 else '#dc3545'}; padding-left: 10px; margin: 5px 0;'>
                          <b>诊断</b>: {diagnosis.get('内容', '未知')} | 
                          <b>类型</b>: {diagnosis.get('类型', '未知')} | 
                          <b>关联强度</b>: {strength:.2f}
                        </div>
                        """, unsafe_allow_html=True)
                        if reason:
                            st.markdown(f"**关联理由**: {reason}")
                    else:
                        st.markdown(f"诊断ID: {diagnosis_id} (无详细信息)")
    
    # 如果需要显示可视化网络图并启用了该功能
    if "show_visualization" in locals() and show_visualization:
        display_association_network(analysis_result)

# 关联网络图可视化函数
def display_association_network(analysis_result):
    """显示诊断与病变的关联网络图"""
    if "关联关系" not in analysis_result:
        return
    
    st.markdown("### 诊断-病变关联网络")
    
    # 准备网络图数据
    associations = analysis_result["关联关系"]
    
    try:
        # 创建数据结构，用于绘制网络图
        nodes_data = []
        edges_data = []
        
        # 结构化数据
        structured_data = analysis_result.get("结构化数据", {})
        
        # 添加诊断节点
        for diagnosis in structured_data.get("诊断信息", []):
            if "诊断ID" in diagnosis:
                nodes_data.append({
                    "id": diagnosis["诊断ID"],
                    "label": diagnosis.get("内容", "")[:20] + "…" if len(diagnosis.get("内容", "")) > 20 else diagnosis.get("内容", ""),
                    "group": "diagnosis"
                })
        
        # 添加病变节点
        for lesion in structured_data.get("病变特征", []):
            if "病变ID" in lesion:
                nodes_data.append({
                    "id": lesion["病变ID"],
                    "label": f"{lesion.get('解剖位置', '')} ({lesion.get('大小', '')})",
                    "group": "lesion"
                })
        
        # 添加关联边
        for diagnosis_id, info in associations.get("诊断到病变映射", {}).items():
            for lesion_id in info.get("相关病变列表", []):
                strength = associations.get("关联强度", {}).get(diagnosis_id, {}).get(lesion_id, 0.5)
                edges_data.append({
                    "from": diagnosis_id,
                    "to": lesion_id,
                    "width": strength * 5,  # 根据强度调整线条宽度
                    "title": f"关联强度: {strength:.2f}"
                })
        
        # 生成网络图HTML代码
        if nodes_data and edges_data:
            # 使用NetworkX和PyVis创建交互式网络图
            try:
                import networkx as nx
                from pyvis.network import Network
                import tempfile
                
                # 创建网络图
                G = nx.DiGraph()
                for node in nodes_data:
                    G.add_node(node["id"], label=node["label"], group=node["group"])
                for edge in edges_data:
                    G.add_edge(edge["from"], edge["to"], weight=edge["width"], title=edge["title"])
                
                # 使用PyVis创建交互式图
                net = Network(height="500px", width="100%", directed=True, notebook=False)
                net.from_nx(G)
                
                # 设置节点颜色
                net.set_options("""
                const options = {
                    "nodes": {
                        "shape": "dot",
                        "size": 16,
                        "font": {"size": 12, "face": "Arial"},
                        "borderWidth": 2,
                        "shadow": true
                    },
                    "edges": {
                        "width": 2,
                        "shadow": true,
                        "smooth": {"type": "continuous"}
                    },
                    "groups": {
                        "diagnosis": {"color": {"background": "#6E75A4", "border": "#555"}},
                        "lesion": {"color": {"background": "#E8A87C", "border": "#C38D5F"}}
                    },
                    "physics": {
                        "stabilization": true,
                        "barnesHut": {
                            "gravitationalConstant": -2000,
                            "springConstant": 0.04,
                            "springLength": 150
                        }
                    }
                };
                """)
                
                # 保存为临时HTML文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                    temp_html_path = tmp_file.name
                    net.save_graph(temp_html_path)
                    
                    # 打开并读取HTML内容
                    with open(temp_html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # 在Streamlit中显示
                    st.components.v1.html(html_content, height=500)
                    
                    # 删除临时文件
                    import os
                    os.unlink(temp_html_path)
                    
            except ImportError:
                # 如果缺少必要库，使用简单的matplotlib图
                import matplotlib.pyplot as plt
                import networkx as nx
                
                G = nx.DiGraph()
                for node in nodes_data:
                    G.add_node(node["id"], label=node["label"], group=node["group"])
                for edge in edges_data:
                    G.add_edge(edge["from"], edge["to"], weight=edge["width"])
                
                # 绘制简单图
                plt.figure(figsize=(10, 8))
                pos = nx.spring_layout(G, seed=42)
                
                # 绘制节点
                diagnosis_nodes = [n for n in G.nodes() if G.nodes[n].get("group") == "diagnosis"]
                lesion_nodes = [n for n in G.nodes() if G.nodes[n].get("group") == "lesion"]
                
                nx.draw_networkx_nodes(G, pos, nodelist=diagnosis_nodes, node_color='#6E75A4', node_size=500)
                nx.draw_networkx_nodes(G, pos, nodelist=lesion_nodes, node_color='#E8A87C', node_size=500)
                
                # 绘制边
                nx.draw_networkx_edges(G, pos, arrows=True)
                
                # 绘制标签
                labels = {n: G.nodes[n].get('label', n) for n in G.nodes()}
                nx.draw_networkx_labels(G, pos, labels, font_size=10, font_family="Arial")
                
                plt.title("诊断-病变关联网络")
                plt.axis('off')
                st.pyplot(plt)
        else:
            st.info("没有足够的诊断和病变数据来绘制关联网络图。")
            
    except Exception as e:
        st.error(f"绘制关联网络图失败: {str(e)}")

st.title("🔬 结构分析")
st.markdown("提取医学影像报告中的结构化信息，包括解剖结构、病变特征和诊断信息。")

st.sidebar.header("结构提取选项")

# 知识库选项
with st.sidebar.expander("知识库设置", expanded=False):
    kb_auto_update = st.checkbox("自动更新知识库", 
                              value=knowledge_settings.get("auto_update", True),
                              help="自动将新分析的报告结果添加到知识库")
    
    quality_threshold = st.slider("结果质量阈值", 
                               min_value=0.0, max_value=1.0, 
                               value=knowledge_settings.get("quality_threshold", 0.7),
                               step=0.1,
                               help="低于此阈值的结果不会被加入知识库")
    
    if st.button("应用设置"):
        knowledge_settings.update({
            "auto_update": kb_auto_update,
            "quality_threshold": quality_threshold
        })
        st.success("知识库设置已保存")
        
    st.info("提示：您可以在「知识库」页面查看详细的知识库内容")

# 初始化结构提取器
if "structure_extractor" not in st.session_state:
    if st.session_state.get("llm_client") is not None:
        st.session_state.structure_extractor = StructureExtractor(st.session_state.llm_client)
    else:
        st.error("LLM客户端未初始化，请先返回首页")
        st.stop()

if "llm_config" in st.session_state:
    if st.session_state.llm_config.get("provider") == "openai" and not st.session_state.llm_config.get("api_key"):
        st.error("❗ OpenAI API密钥未设置，无法使用分析功能。请先在设置页面配置API密钥。")
        if st.button("前往设置页面"):
            st.switch_page("pages/00_settings.py")
        st.stop()

if "analyzed_reports" not in st.session_state:
    st.session_state.analyzed_reports = {}

if not st.session_state.get("data_loaded", False):
    st.warning("请先在「数据探索」页面加载数据")
    if st.button("前往数据探索页面"):
        st.switch_page("pages/01_data_explorer.py")
    st.stop()

# 获取数据
data = st.session_state.processed_data if st.session_state.processed_data is not None else st.session_state.raw_data
total_reports = len(data)

# 统一分页/单份逻辑
analysis_mode = st.sidebar.radio("分析模式", ["单份报告分析", "批量报告分析"])
if analysis_mode == "单份报告分析":
    page_size = 1
    page = st.sidebar.number_input("报告索引", min_value=1, max_value=total_reports, value=1)
    indices = [page-1]
else:
    page_size = st.sidebar.slider("每页报告数", 1, 50, 10)
    page = st.sidebar.number_input("页码", min_value=1, max_value=(total_reports-1)//page_size+1, value=1)
    start = (page-1)*page_size
    end = min(start+page_size, total_reports)
    indices = list(range(start, end))

st.markdown(f"**当前处理报告区间：{indices[0]+1} - {indices[-1]+1}（共{total_reports}份）**")

# 关联可视化配置
use_association = st.sidebar.checkbox(
    "开启诊断关联分析", 
    value=config.PROCESSING_CONFIG["diagnosis_association"]["enabled"],
    help="启用后将自动分析诊断与病变特征之间的关联"
)

show_visualization = False
if use_association:
    show_visualization = st.sidebar.checkbox(
        "显示关联网络图", 
        value=config.PROCESSING_CONFIG["diagnosis_association"]["show_visualization"],
        help="启用后将展示诊断与病变关联的可视化图表"
    )

current_idx = st.selectbox("选择要查看的报告", indices, format_func=lambda i: f"报告{i+1}")
report = data.iloc[current_idx]

# 获取影像表现和诊断结论文本
def get_text_from_report(report, standard_column, fallback_columns):
    """从报告中获取文本，支持多种列名格式"""
    # 首先检查标准列名
    if standard_column in report.index and pd.notna(report[standard_column]):
        return report[standard_column]
    
    # 如果标准列名不存在或为空，尝试候选列名
    for col in fallback_columns:
        if col in report.index and pd.notna(report[col]):
            return report[col]
    
    # 如果所有列名都未找到，返回空字符串
    return ""

# 获取文本内容，优先使用标准列名，如果不存在则尝试候选列名
image_text = get_text_from_report(report, "影像表现", COLUMN_MAPPINGS.get("影像表现", []))
diagnosis_text = get_text_from_report(report, "诊断结论", COLUMN_MAPPINGS.get("诊断结论", []))

st.markdown("#### 原始报告")
col1, col2 = st.columns(2)
with col1:
    st.text_area("影像表现", image_text, height=120, disabled=True, key=f"img_{current_idx}")
with col2:
    st.text_area("诊断结论", diagnosis_text, height=120, disabled=True, key=f"diag_{current_idx}")

# 单份分析
if st.button("分析当前报告", key=f"analyze_{current_idx}"):
    with st.spinner("正在分析..."):
        extractor = st.session_state.structure_extractor
        # 使用之前已获取的文本内容
        # 这里的image_text和diagnosis_text是前面通过get_text_from_report函数获取的
        # 已经考虑了多种列名格式
        result = extractor.analyze_single_report(image_text, diagnosis_text)
        st.session_state.analyzed_reports[f"report_{current_idx}"] = result
        st.success("结构化分析完成！")
        # 结构化结果分tab显示
        if "结构化数据" in result:
            tabs = st.tabs(["解剖结构", "病变特征", "诊断信息", "诊断与病变关联", "影像诊断映射"])
            data = result["结构化数据"]
            with tabs[0]:
                st.subheader("解剖结构")
                st.json(data.get("解剖结构", []))
                # 可视化
                if data.get("解剖结构"):
                    from utils.network_visualizer import create_relationship_graph
                    structures = data["解剖结构"]
                    nodes = []
                    edges = []
                    for i, struct in enumerate(structures):
                        if "原文" in struct:
                            node_id = f"n{i}"
                            nodes.append({
                                "id": node_id,
                                "label": struct["原文"],
                                "group": 1
                            })
                            if "父结构" in struct and struct["父结构"]:
                                parent_id = None
                                for j, parent_node in enumerate(nodes):
                                    if parent_node["label"] == struct["父结构"]:
                                        parent_id = parent_node["id"]
                                        break
                                if parent_id is None:
                                    parent_id = f"p{i}"
                                    nodes.append({
                                        "id": parent_id,
                                        "label": struct["父结构"],
                                        "group": 2
                                    })
                                edges.append({
                                    "from": parent_id,
                                    "to": node_id,
                                    "label": ""
                                })
                    if nodes:
                        # ==== 强制指定matplotlib中文字体（KISS方案）====
                        import os
                        import matplotlib
                        import matplotlib.pyplot as plt
                        from matplotlib.font_manager import FontProperties
                        font_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"
                        if not os.path.exists(font_path):
                            font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
                        if not os.path.exists(font_path):
                            font_path = "/System/Library/Fonts/STHeiti Light.ttc"
                        if not os.path.exists(font_path):
                            font_path = "/System/Library/Fonts/Arial Unicode.ttf"
                        if not os.path.exists(font_path):
                            st.error("未检测到可用的中文字体文件，请检查系统字体配置。")
                            st.stop()
                        font_prop = FontProperties(fname=font_path)
                        matplotlib.rcParams['font.sans-serif'] = [font_prop.get_name()]
                        matplotlib.rcParams['axes.unicode_minus'] = False
                        # ==== 绘制关系图，label/title自动全局中文支持 ====
                        import networkx as nx
                        G = nx.DiGraph()
                        for node in nodes:
                            G.add_node(node["id"], label=node["label"], group=node["group"])
                        for edge in edges:
                            G.add_edge(edge["from"], edge["to"], label=edge.get("label", ""))
                        pos = nx.spring_layout(G)
                        labels = nx.get_node_attributes(G, 'label')
                        groups = nx.get_node_attributes(G, 'group')
                        plt.figure(figsize=(8, 6))
                        nx.draw_networkx_nodes(G, pos, node_color=[groups[n] for n in G.nodes()], cmap=plt.cm.Set1, node_size=800)
                        nx.draw_networkx_edges(G, pos, arrows=True)
                        nx.draw_networkx_labels(G, pos, labels, font_size=12)
                        plt.title("解剖结构关系图")
                        plt.axis('off')
                        st.pyplot(plt)
                        plt.close()
            with tabs[1]:
                st.subheader("病变特征")
                st.json(data.get("病变特征", []))
            with tabs[2]:
                st.subheader("诊断信息")
                st.json(data.get("诊断信息", []))
            # 诊断与病变关联显示
            with tabs[3]:
                st.subheader("诊断与病变关联")
                display_associations(result)
                
            with tabs[4]:
                st.subheader("影像诊断映射")
                st.json(data.get("影像诊断映射", []))
                
        # 添加解剖描述模式分析按钮
        st.markdown("---")
        if st.button("提取解剖描述模式", key=f"extract_desc_pattern_{current_idx}"):
            with st.spinner("正在提取解剖描述模式..."):
                extractor = st.session_state.structure_extractor
                # 获取报告文本
                image_text = report.get("影像表现", "") if pd.notna(report.get("影像表现", "")) else ""
                diagnosis_text = report.get("诊断结论", "") if pd.notna(report.get("诊断结论", "")) else ""
                
                # 提取描述模式
                description_patterns = extractor.extract_anatomical_descriptions(image_text, diagnosis_text)
                
                if "解剖描述模式" in description_patterns:
                    # 显示提取结果
                    st.session_state.analyzed_reports[f"report_pattern_{current_idx}"] = description_patterns
                    
                    # 更新知识库（如果设置允许）
                    result_quality = 0.8  # 默认质量评分
                    if knowledge_settings.should_update_knowledge_base(result_quality):
                        kb = MedicalKnowledgeBase()
                        kb.update_anatomical_description_patterns(description_patterns["解剖描述模式"])
                        st.success("描述模式已添加到知识库！")
                    
                    # 显示提取结果
                    with st.expander("解剖描述模式提取结果", expanded=True):
                        # 创建表格展示
                        patterns_data = []
                        for p in description_patterns["解剖描述模式"]:
                            patterns_data.append({
                                "解剖结构": p.get("解剖结构", ""),
                                "描述模式": p.get("描述模式", ""),
                                "标准表达数": len(p.get("标准表达", [])),
                                "异常类型数": len(p.get("异常类型", []))
                            })
                        
                        if patterns_data:
                            st.dataframe(pd.DataFrame(patterns_data))
                            
                            # 选择特定结构查看详情
                            structure_names = [p["解剖结构"] for p in description_patterns["解剖描述模式"]]
                            if structure_names:
                                selected = st.selectbox("选择解剖结构查看详情:", structure_names)
                                for p in description_patterns["解剖描述模式"]:
                                    if p["解剖结构"] == selected:
                                        st.markdown(f"**{selected} 的描述模式:**")
                                        st.write(f"模式: {p.get('描述模式', '')}")
                                        
                                        st.markdown("**标准表达:**")
                                        for expr in p.get("标准表达", []):
                                            st.write(f"- {expr}")
                                        
                                        st.markdown("**异常类型:**")
                                        for ab_type in p.get("异常类型", []):
                                            st.write(f"- {ab_type}")
                                        
                                        break
                        
                        # 提供原始JSON数据
                        with st.expander("原始JSON数据"):
                            st.json(description_patterns)
                else:
                    st.error("无法提取解剖描述模式")

# 批量分析
if analysis_mode == "批量报告分析":
    # 1. 上方显示批量处理进度条和当前进度，并展示已完成报告编号及关键信息
    analyzed_count = 0
    finished_info = []
    total_count = len(indices)
    for i in indices:
        key = f"report_{i}"
        if key in st.session_state.analyzed_reports:
            analyzed_count += 1
            result = st.session_state.analyzed_reports[key]
            if "结构化数据" in result:
                diag_count = len(result["结构化数据"].get("诊断信息", []))
                finished_info.append(f"{i+1}(成功,诊断数:{diag_count})")
            elif "分析错误" in result:
                finished_info.append(f"{i+1}(失败)")
            else:
                finished_info.append(f"{i+1}(成功)")
    finished_str = ", ".join(finished_info) if finished_info else "无"
    st.markdown(f"#### 批量分析进度：{analyzed_count}/{total_count}")
    st.markdown(f"**已完成报告编号及状态：** {finished_str}")
    st.progress(analyzed_count / total_count if total_count else 0)
    
    # 2. 批量分析按钮及处理逻辑
    if st.button("批量分析本页全部报告"):
        with st.spinner("正在批量分析..."):
            extractor = st.session_state.structure_extractor
            progress_bar = st.progress(0)
            for idx, i in enumerate(indices):
                if f"report_{i}" not in st.session_state.analyzed_reports:
                    rpt = data.iloc[i]
                    image_text = rpt.get("影像表现", "") if pd.notna(rpt.get("影像表现", "")) else ""
                    diagnosis_text = rpt.get("诊断结论", "") if pd.notna(rpt.get("诊断结论", "")) else ""
                    result = extractor.analyze_single_report(image_text, diagnosis_text)
                    st.session_state.analyzed_reports[f"report_{i}"] = result
                progress_bar.progress((idx + 1) / total_count)
            st.success(f"本页报告全部分析完成！")
    
    # 3. 按钮下方实时显示每份报告的分析结果信息
    st.markdown("---")
    st.markdown("#### 本页报告分析结果一览：")
    for i in indices:
        key = f"report_{i}"
        if key in st.session_state.analyzed_reports:
            result = st.session_state.analyzed_reports[key]
            summary = "结构化成功"
            if "结构化数据" in result:
                diag_count = len(result["结构化数据"].get("诊断信息", []))
                summary += f"，诊断数：{diag_count}"
            
            # 计算质量评分
            result_quality = 0.8  # 默认质量评分
            if "结构化数据" in result:
                diagnoses_count = len(result["结构化数据"].get("诊断信息", []))
                if diagnoses_count > 0:
                    result_quality = min(0.7 + diagnoses_count * 0.1, 1.0)  # 每个诊断增加0.1分，最高1.0
            
            # 显示质量评分和知识库状态
            kb_status = "已纳入知识库" if knowledge_settings.should_update_knowledge_base(result_quality) else "未纳入知识库"
            summary += f" (质量: {result_quality:.1f}, {kb_status})"
                
            with st.expander(f"报告{i+1}：{summary}"):
                # 添加手动控制知识库更新
                col1, col2 = st.columns([3, 1])
                with col2:
                    if knowledge_settings.should_update_knowledge_base(result_quality):
                        if st.button(f"从知识库中移除 #{i+1}", key=f"remove_kb_{i}"):
                            # 这里只标记不纳入，实际上无法从知识库中删除已有数据
                            # TODO: 实现更完善的知识库数据管理
                            st.warning("注意：如果数据已经添加到知识库，无法删除。这将防止未来的新分析加入知识库。")
                    else:
                        if st.button(f"添加到知识库 #{i+1}", key=f"add_kb_{i}"):
                            try:
                                from utils.knowledge_base import MedicalKnowledgeBase
                                kb = MedicalKnowledgeBase()
                                kb.update_with_report(result)
                                st.success("已成功添加到知识库")
                            except Exception as e:
                                st.error(f"添加到知识库失败: {str(e)}")
                
                with col1:
                    st.json(result)
        else:
            st.write(f"报告{i+1}：未分析")

# 结果保存与下载
col1, col2 = st.columns(2)

with col1:
    if st.button("保存当前已分析结果为JSON"):
        analyzed = [st.session_state.analyzed_reports[k] for k in sorted(st.session_state.analyzed_reports) if k.startswith("report_")]
        import os
        import time
        import json
        # 优先保存到data/processed目录
        base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
        if not os.path.exists(base_dir):
            base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(base_dir, exist_ok=True)
        save_path = os.path.join(base_dir, f"analyzed_reports_{len(analyzed)}_{time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(analyzed, f, ensure_ascii=False, indent=2)
        st.success(f"已保存：{save_path}")
        st.download_button("下载JSON", data=json.dumps(analyzed, ensure_ascii=False), file_name=save_path)

with col2:
    if st.button("查看知识库内容", help="跳转到知识库页面"):
        st.switch_page("pages/04_knowledge_base.py")