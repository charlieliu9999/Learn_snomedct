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
st.text_area("影像表现", report.get("影像表现", ""), height=120, disabled=True, key=f"img_{current_idx}")
st.text_area("诊断结论", report.get("诊断结论", ""), height=120, disabled=True, key=f"diag_{current_idx}")

# 分析当前报告
if st.button("分析当前报告", key=f"analyze_{current_idx}"):
    with st.spinner("正在分析..."):
        extractor = st.session_state.structure_extractor
        result = extractor.analyze_report(report) if hasattr(extractor, "analyze_report") else extractor.extract(report)
        st.session_state.analyzed_reports[f"report_{current_idx}"] = result
        st.success("结构化分析完成！")
        st.json(result)
        # 可视化（如有）
        if "结构化数据" in result and "解剖结构" in result["结构化数据"]:
            from utils.network_visualizer import draw_structure_graph
            draw_structure_graph(result["结构化数据"]["解剖结构"])

# 批量分析本页全部报告
if analysis_mode == "批量报告分析":
    if st.button("批量分析本页全部报告"):
        with st.spinner("正在批量分析..."):
            extractor = st.session_state.structure_extractor
            for i in indices:
                if f"report_{i}" not in st.session_state.analyzed_reports:
                    rpt = data.iloc[i]
                    result = extractor.analyze_report(rpt) if hasattr(extractor, "analyze_report") else extractor.extract(rpt)
                    st.session_state.analyzed_reports[f"report_{i}"] = result
            st.success(f"本页报告全部分析完成！")

# 结果保存与下载
if st.button("保存当前已分析结果为JSON"):
    analyzed = [st.session_state.analyzed_reports[k] for k in sorted(st.session_state.analyzed_reports) if k.startswith("report_")]
    save_path = f"analyzed_reports_{len(analyzed)}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(analyzed, f, ensure_ascii=False, indent=2)
    st.success(f"已保存：{save_path}")
    st.download_button("下载JSON", data=json.dumps(analyzed, ensure_ascii=False), file_name=save_path)