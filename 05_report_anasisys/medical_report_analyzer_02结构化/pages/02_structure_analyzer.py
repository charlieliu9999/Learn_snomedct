"""
结构分析页面 - 用于提取医学影像报告的结构化信息
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
import time

# 导入字体管理和配置
from utils import font_manager
from utils import plot_utils

import config
from utils.structure_extractor import StructureExtractor

plot_utils.configure_chinese_font()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 结构分析",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 结构分析")
st.markdown("提取医学影像报告中的结构化信息，包括解剖结构、病变特征和诊断信息。")

st.sidebar.header("结构提取选项")

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

current_idx = st.selectbox("选择要查看的报告", indices, format_func=lambda i: f"报告{i+1}")
report = data.iloc[current_idx]
st.markdown("#### 原始报告")
col1, col2 = st.columns(2)
with col1:
    st.text_area("影像表现", report.get("影像表现", ""), height=120, disabled=True, key=f"img_{current_idx}")
with col2:
    st.text_area("诊断结论", report.get("诊断结论", ""), height=120, disabled=True, key=f"diag_{current_idx}")

# 单份分析
if st.button("分析当前报告", key=f"analyze_{current_idx}"):
    with st.spinner("正在分析..."):
        extractor = st.session_state.structure_extractor
        # 确保报告包含必要字段
        image_text = report.get("影像表现", "") if pd.notna(report.get("影像表现", "")) else ""
        diagnosis_text = report.get("诊断结论", "") if pd.notna(report.get("诊断结论", "")) else ""
        result = extractor.analyze_single_report(image_text, diagnosis_text)
        st.session_state.analyzed_reports[f"report_{current_idx}"] = result
        st.success("结构化分析完成！")
        # 结构化结果分tab显示
        if "结构化数据" in result:
            tabs = st.tabs(["解剖结构", "病变特征", "诊断信息", "影像诊断映射"])
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
            with tabs[3]:
                st.subheader("影像诊断映射")
                st.json(data.get("影像诊断映射", []))

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
            with st.expander(f"报告{i+1}：{summary}"):
                st.json(result)
        else:
            st.write(f"报告{i+1}：未分析")

# 结果保存与下载
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