"""
结构分析页面 - 用于提取医学影像报告的结构化信息
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# ================= KnowledgeForge Integration: Start =================
# Add project root to the path to allow importing from 06_KnowledgeForge
import sys
import os
# This assumes the script is run from the project root or via streamlit run
# It navigates up from 'pages' -> 'medical_report_analyzer_02' -> '05_report_anasisys' -> root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    # 导入新的SNOMED CT分析器和可视化功能
    from KnowledgeForge_Project.knowledgeforge import (
        process as knowledgeforge_process,
        analyze_medical_report_with_snomed,
        display_snomed_visualization
    )
    KNOWLEDGEFORGE_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import KnowledgeForge: {e}")
    KNOWLEDGEFORGE_AVAILABLE = False
# ================= KnowledgeForge Integration: End ===================

# 导入字体管理和配置
from utils import font_manager
from utils import plot_utils

import config
from utils.structure_extractor import StructureExtractor
from utils.result_validator import StructuredResultValidator

plot_utils.configure_chinese_font()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 结构分析",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 结构分析")
st.markdown("提取医学影像报告中的结构化信息，包括解剖结构、病变特征和诊断信息。")

st.sidebar.header("结构提取选项")

# 在导入部分之后，主要逻辑之前添加验证结果显示函数
def display_validation_results(original_result, validation_result, issues, corrected_result):
    """显示验证结果的可视化界面"""
    
    st.markdown("### 🔍 质量验证结果")
    
    # 验证状态总览
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        validation_status = "✅ 通过" if validation_result else "⚠️ 有问题"
        st.metric("验证状态", validation_status)
    
    with col2:
        st.metric("发现问题", f"{len(issues)} 个")
    
    with col3:
        # 计算质量分数
        total_checks = 10  # 假设总共10项检查
        quality_score = max(0, (total_checks - len(issues)) / total_checks * 100)
        st.metric("质量分数", f"{quality_score:.0f}%")
    
    with col4:
        # 计算改进程度
        improvement = len(issues) if issues else 0
        st.metric("修正项目", f"{improvement} 项")
    
    if issues:
        # 问题详情展示
        st.markdown("#### 📋 发现的问题")
        
        # 问题分类统计
        problem_categories = {
            "解剖结构问题": 0,
            "诊断分类问题": 0, 
            "映射关系问题": 0,
            "其他问题": 0
        }
        
        for issue in issues:
            if "解剖结构" in issue or "拆分" in issue or "重复" in issue:
                problem_categories["解剖结构问题"] += 1
            elif "诊断分类" in issue:
                problem_categories["诊断分类问题"] += 1
            elif "映射" in issue or "模糊" in issue:
                problem_categories["映射关系问题"] += 1
            else:
                problem_categories["其他问题"] += 1
        
        # 问题分类可视化
        if any(problem_categories.values()):
            category_col1, category_col2 = st.columns(2)
            
            with category_col1:
                st.markdown("**问题分类统计：**")
                for category, count in problem_categories.items():
                    if count > 0:
                        st.write(f"• {category}: {count} 个")
            
            with category_col2:
                # 创建问题分布饼图
                import matplotlib.pyplot as plt
                import matplotlib.font_manager as fm
                
                # 设置中文字体
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
                plt.rcParams['axes.unicode_minus'] = False
                
                active_categories = {k: v for k, v in problem_categories.items() if v > 0}
                if active_categories:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
                    ax.pie(active_categories.values(), labels=active_categories.keys(), 
                           autopct='%1.1f%%', colors=colors[:len(active_categories)])
                    ax.set_title('问题分布', fontsize=14, fontweight='bold')
                    st.pyplot(fig)
        
        # 详细问题列表
        with st.expander("🔍 查看详细问题列表", expanded=False):
            for i, issue in enumerate(issues, 1):
                # 根据问题类型设置不同的图标
                if "错误" in issue or "拆分" in issue:
                    icon = "🚨"
                elif "修正" in issue:
                    icon = "🔧"
                elif "替换" in issue:
                    icon = "🔄"
                else:
                    icon = "⚠️"
                
                st.write(f"{icon} **问题 {i}**: {issue}")
        
        # 修正前后对比
        st.markdown("#### 📊 修正前后对比")
        
        comparison_tabs = st.tabs(["解剖结构对比", "诊断信息对比", "映射关系对比"])
        
        with comparison_tabs[0]:
            # 解剖结构对比
            col_before, col_after = st.columns(2)
            
            with col_before:
                st.markdown("**修正前:**")
                original_structures = original_result.get("结构化数据", {}).get("解剖结构", [])
                for i, struct in enumerate(original_structures, 1):
                    st.write(f"{i}. {struct.get('原文', '')} → {struct.get('标准名', '')}")
            
            with col_after:
                st.markdown("**修正后:**")
                corrected_structures = corrected_result.get("结构化数据", {}).get("解剖结构", [])
                for i, struct in enumerate(corrected_structures, 1):
                    # 检查是否有修正
                    original_name = struct.get('标准名', '')
                    original_struct = next((s for s in original_structures if s.get('原文') == struct.get('原文')), {})
                    original_standard = original_struct.get('标准名', '')
                    
                    if original_name != original_standard:
                        st.write(f"{i}. {struct.get('原文', '')} → **{original_name}** ✅")
                    else:
                        st.write(f"{i}. {struct.get('原文', '')} → {original_name}")
        
        with comparison_tabs[1]:
            # 诊断信息对比
            col_before, col_after = st.columns(2)
            
            with col_before:
                st.markdown("**修正前:**")
                original_diagnoses = original_result.get("结构化数据", {}).get("诊断信息", [])
                for i, diag in enumerate(original_diagnoses, 1):
                    st.write(f"{i}. 类型: {diag.get('类型', '')} | 描述: {diag.get('描述', '')}")
            
            with col_after:
                st.markdown("**修正后:**")
                corrected_diagnoses = corrected_result.get("结构化数据", {}).get("诊断信息", [])
                for i, diag in enumerate(corrected_diagnoses, 1):
                    # 检查是否有修正
                    original_diag = original_diagnoses[i-1] if i-1 < len(original_diagnoses) else {}
                    if diag.get('类型') != original_diag.get('类型'):
                        st.write(f"{i}. 类型: **{diag.get('类型', '')}** ✅ | 描述: {diag.get('描述', '')}")
                    else:
                        st.write(f"{i}. 类型: {diag.get('类型', '')} | 描述: {diag.get('描述', '')}")
        
        with comparison_tabs[2]:
            # 映射关系对比
            col_before, col_after = st.columns(2)
            
            with col_before:
                st.markdown("**修正前:**")
                original_mappings = original_result.get("结构化数据", {}).get("影像诊断映射", [])
                for i, mapping in enumerate(original_mappings, 1):
                    confidence_color = "🔴" if mapping.get('映射置信度') == "低" else "🟡" if mapping.get('映射置信度') == "中" else "🟢"
                    st.write(f"{i}. {mapping.get('影像发现', '')} → {mapping.get('对应诊断', '')} {confidence_color}")
            
            with col_after:
                st.markdown("**修正后:**")
                corrected_mappings = corrected_result.get("结构化数据", {}).get("影像诊断映射", [])
                for i, mapping in enumerate(corrected_mappings, 1):
                    confidence_color = "🔴" if mapping.get('映射置信度') == "低" else "🟡" if mapping.get('映射置信度') == "中" else "🟢"
                    st.write(f"{i}. {mapping.get('影像发现', '')} → {mapping.get('对应诊断', '')} {confidence_color} ✅")
        
        # 修正建议操作
        st.markdown("#### 🎯 处理建议")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("✅ 接受所有修正", type="primary", use_container_width=True):
                # 用修正后的结果替换原始结果
                st.session_state.analyzed_reports[f"report_{st.session_state.get('current_report_idx', 0)}"] = corrected_result
                st.success("✅ 已接受所有修正建议，结果已更新！")
                st.experimental_rerun()
        
        with action_col2:
            if st.button("🔍 查看详细报告", use_container_width=True):
                # 生成详细的质量报告
                validator = StructuredResultValidator()
                detailed_report = validator.generate_quality_report(original_result)
                
                with st.expander("📄 详细质量评估报告", expanded=True):
                    st.markdown(detailed_report)
        
        with action_col3:
            if st.button("💾 保存修正结果", use_container_width=True):
                # 保存修正后的结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"corrected_analysis_{timestamp}.json"
                
                # 确保目录存在
                output_dir = Path("data/processed")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_path = output_dir / filename
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(corrected_result, f, ensure_ascii=False, indent=2)
                
                st.success(f"💾 修正结果已保存到: {output_path}")
    
    else:
        st.success("🎉 恭喜！分析结果质量良好，未发现需要修正的问题。")
        
        # 显示质量指标
        quality_metrics = st.columns(3)
        
        with quality_metrics[0]:
            st.metric("解剖结构", f"{len(original_result.get('结构化数据', {}).get('解剖结构', []))} 个", "✅ 准确")
        
        with quality_metrics[1]:
            st.metric("诊断信息", f"{len(original_result.get('结构化数据', {}).get('诊断信息', []))} 个", "✅ 准确")
        
        with quality_metrics[2]:
            st.metric("映射关系", f"{len(original_result.get('结构化数据', {}).get('影像诊断映射', []))} 个", "✅ 高质量")

# ================= KnowledgeForge Integration: Start =================
def display_knowledgeforge_results(kf_result: dict):
    """专门用于显示KnowledgeForge处理后的结果"""
    st.markdown("### ✨ KnowledgeForge 深度分析结果")
    
    if not kf_result:
        st.error("KnowledgeForge 返回了空结果。")
        return

    tabs = st.tabs(["**💎 实体与关系**", "**📄 完整JSON输出**"])

    with tabs[0]:
        st.markdown("#### 核心实体提取与标准化")
        
        findings = kf_result.get("ClinicalFindings", [])
        diagnoses = kf_result.get("Diagnoses", [])

        if not findings and not diagnoses:
            st.warning("未提取到临床发现或诊断信息。")
            return

        for i, entity in enumerate(findings + diagnoses):
            entity_type = entity.get("EntityType", "未知实体")
            original_text = entity.get("Finding") or entity.get("Diagnosis")
            
            with st.expander(f"**{entity_type} {i+1}: {original_text}**", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**语义ID**: `{entity.get('semantic_id', 'N/A')}`")
                    if entity.get("related_finding_ids"):
                        st.markdown(f"**关联发现ID**:")
                        for rel_id in entity["related_finding_ids"]:
                            st.code(rel_id, language='text')

                with col2:
                    if entity.get("Standardization"):
                        std = entity["Standardization"]
                        st.markdown(f"**标准术语**: {std.get('term_en')} / {std.get('term_zh')}")
                        st.markdown(f"**SNOMED CT ID**: `{std.get('sct_id', 'N/A')}`")
                        st.markdown(f"**层级路径**: `{std.get('hierarchy_en', 'N/A')}`")
                
                if entity.get("AnatomicalLocation") and entity["AnatomicalLocation"].get("Standardization"):
                    st.markdown("---")
                    st.markdown("**解剖位置标准化**")
                    anat_std = entity["AnatomicalLocation"]["Standardization"]
                    st.markdown(f"**标准术语**: {anat_std.get('term_en')} / {anat_std.get('term_zh')}")
                    st.markdown(f"**SNOMED CT ID**: `{anat_std.get('sct_id', 'N/A')}`")
                    st.markdown(f"**层级路径**: `{anat_std.get('hierarchy_en', 'N/A')}`")


    with tabs[1]:
        st.json(kf_result)
# ================= KnowledgeForge Integration: End ===================

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

# 获取用户选择的字段名，设置默认值以保持兼容性
findings_column = st.session_state.get("findings_col", "影像表现")
impression_column = st.session_state.get("impression_col", "诊断结论")

# 检查字段是否存在，如果不存在则尝试自动检测或提示用户
if findings_column not in data.columns or impression_column not in data.columns:
    st.error(f"⚠️ 所选字段不存在于当前数据中")
    st.markdown(f"**当前选择的字段:**")
    st.markdown(f"- 影像表现字段: `{findings_column}`")
    st.markdown(f"- 诊断结论字段: `{impression_column}`")
    st.markdown(f"**数据中可用的字段:** {', '.join(data.columns)}")
    
    if st.button("返回数据探索页面重新选择字段"):
        st.switch_page("pages/01_data_explorer.py")
    st.stop()

# 显示当前使用的字段信息
st.sidebar.markdown("### 📋 当前分析字段")
st.sidebar.info(f"影像表现: **{findings_column}**\n\n诊断结论: **{impression_column}**")
if st.sidebar.button("🔧 修改字段选择"):
    st.switch_page("pages/01_data_explorer.py")

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
    st.text_area(f"{findings_column}", report.get(findings_column, ""), height=120, disabled=True, key=f"img_{current_idx}")
with col2:
    st.text_area(f"{impression_column}", report.get(impression_column, ""), height=120, disabled=True, key=f"diag_{current_idx}")

# 分析按钮区域
analysis_col1, analysis_col2, analysis_col3 = st.columns([1, 1, 1])

# 单份分析 - 原始流程
with analysis_col1:
    if st.button("分析当前报告", key=f"analyze_{current_idx}", use_container_width=True):
        with st.spinner("正在分析..."):
            extractor = st.session_state.structure_extractor
            # 使用动态字段名获取内容
            image_text = report.get(findings_column, "") if pd.notna(report.get(findings_column, "")) else ""
            diagnosis_text = report.get(impression_column, "") if pd.notna(report.get(impression_column, "")) else ""
            result = extractor.analyze_single_report(image_text, diagnosis_text)
            st.session_state.analyzed_reports[f"report_{current_idx}"] = result
            st.success("结构化分析完成！")
            
            # 自动进行质量验证
            st.markdown("---")
            with st.spinner("正在进行质量验证..."):
                validator = StructuredResultValidator()
                is_valid, issues, corrected_result = validator.validate_structured_result(result)
                
                # 显示验证结果的可视化界面
                display_validation_results(result, is_valid, issues, corrected_result)
            
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

# 预留给其他分析功能的区域
with analysis_col2:
    st.info("💡 此区域可用于添加其他分析功能")

# ================= KnowledgeForge Integration: Start =================
with analysis_col3:
    if KNOWLEDGEFORGE_AVAILABLE:
        if st.button("🧠 SNOMED CT 智能分析", type="primary", key=f"snomed_analyze_{current_idx}", use_container_width=True):
            st.session_state.snomed_result = None  # Clear previous results
            
            with st.spinner("🔍 正在使用专业SNOMED CT分析器处理医学报告..."):
                # 获取报告文本
                image_text = report.get(findings_column, "") if pd.notna(report.get(findings_column, "")) else ""
                diagnosis_text = report.get(impression_column, "") if pd.notna(report.get(impression_column, "")) else ""
                
                # 使用新的SNOMED CT分析器
                db_path = os.path.join(project_root, "KnowledgeForge_Project", "data", "knowledge.db")
                
                if not os.path.exists(db_path):
                    st.error(f"KnowledgeForge数据库未找到，路径：{db_path}")
                else:
                    try:
                        # 创建进度条和状态显示
                        progress_bar = st.progress(0)
                        status_container = st.empty()
                        
                        def update_progress(message: str, percentage: int):
                            """进度回调函数"""
                            progress_bar.progress(percentage / 100)
                            status_container.info(f"⏳ {message}")
                        
                        # 使用带进度回调的分析器
                        from knowledgeforge.snomed_report_analyzer import SNOMEDReportAnalyzer
                        analyzer = SNOMEDReportAnalyzer(db_path, progress_callback=update_progress)
                        
                        # 分析医学报告
                        snomed_result = analyzer.analyze_medical_report(
                            findings_text=image_text,
                            diagnosis_text=diagnosis_text,
                            patient_info={"report_id": current_idx}
                        )
                        
                        # 清理进度显示
                        progress_bar.empty()
                        status_container.empty()
                        
                        st.session_state.snomed_result = snomed_result
                        
                        # 显示处理结果摘要
                        if "error" not in snomed_result:
                            quality = snomed_result.get("quality_assessment", {})
                            col1, col2, col3, col4 = st.columns(4)
                            
                            entity_count = quality.get("entity_count", 0)
                            relationship_count = quality.get("relationship_count", 0)
                            overall_score = quality.get("overall_score", 0)
                            processing_time = snomed_result.get("processing_time", 0)
                            
                            with col1:
                                st.metric("实体数量", entity_count)
                            with col2:
                                st.metric("关系数量", relationship_count)
                            with col3:
                                st.metric("质量分数", f"{overall_score:.2f}")
                            with col4:
                                st.metric("处理时间", f"{processing_time:.1f}秒")
                            
                            # 根据结果显示不同的消息
                            if entity_count == 0 and relationship_count == 0:
                                st.warning("⚠️ 分析完成，但未提取到实体或关系。这可能是由于：\n"
                                         "- 文本内容过于简单或不明确\n"
                                         "- LLM模型理解困难\n"
                                         "- 网络连接问题\n\n"
                                         "建议：检查输入文本是否完整，或重新尝试分析。")
                            else:
                                st.success("✅ SNOMED CT智能分析完成！")
                        else:
                            # 显示详细错误信息
                            error_msg = snomed_result.get('error', '未知错误')
                            llm_error = snomed_result.get('llm_raw_output', {}).get('error', '')
                            
                            st.error(f"❌ 分析失败：{error_msg}")
                            
                            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                                st.info("💡 **超时问题解决建议：**\n"
                                       "1. 检查Ollama服务是否正常运行\n"
                                       "2. 尝试重启Ollama服务\n"
                                       "3. 简化输入文本长度\n"
                                       "4. 等待片刻后重试")
                            elif "connection" in error_msg.lower():
                                st.info("💡 **连接问题解决建议：**\n"
                                       "1. 确保Ollama正在运行：`ollama serve`\n"
                                       "2. 检查端口11434是否被占用\n"
                                       "3. 重启Ollama服务")
                            
                            if llm_error:
                                with st.expander("🔍 查看详细错误信息"):
                                    st.code(llm_error)
                            
                    except Exception as e:
                        st.error(f"❌ SNOMED CT分析出错：{str(e)}")
    else:
        st.warning("KnowledgeForge 模块未找到，SNOMED CT智能分析功能不可用。")

# Display SNOMED CT results if they exist in session state
if "snomed_result" in st.session_state and st.session_state.snomed_result:
    snomed_result = st.session_state.snomed_result
    
    if "error" not in snomed_result:
        st.markdown("---")
        st.markdown("### 🧠 SNOMED CT 智能分析结果")
        
        # 显示可视化结果
        entities = snomed_result.get("extracted_entities", [])
        relationships = snomed_result.get("relationships", [])
        hierarchy_data = snomed_result.get("hierarchy_data", [])
        
        if entities or relationships or hierarchy_data:
            # 使用新的可视化功能
            display_snomed_visualization(entities, relationships, hierarchy_data)
        
        # 显示详细分析数据
        with st.expander("📊 查看详细分析数据", expanded=False):
            st.json(snomed_result)
    else:
        st.error(f"SNOMED CT分析失败：{snomed_result.get('error', '未知错误')}")

# ================= KnowledgeForge Integration: End ===================

# 原有的分析结果展示逻辑
if f"report_{current_idx}" in st.session_state.analyzed_reports and not st.session_state.get("kf_result"):
    result = st.session_state.analyzed_reports[f"report_{current_idx}"]
    # ... (existing result display logic) ...

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
                    image_text = rpt.get(findings_column, "") if pd.notna(rpt.get(findings_column, "")) else ""
                    diagnosis_text = rpt.get(impression_column, "") if pd.notna(rpt.get(impression_column, "")) else ""
                    result = extractor.analyze_single_report(image_text, diagnosis_text)
                    
                    # 自动进行质量验证和修正
                    validator = StructuredResultValidator()
                    is_valid, issues, corrected_result = validator.validate_structured_result(result)
                    
                    # 如果有问题，自动接受修正结果
                    if not is_valid and issues:
                        st.session_state.analyzed_reports[f"report_{i}"] = corrected_result
                        # 保存验证信息
                        st.session_state.analyzed_reports[f"report_{i}"]["validation_info"] = {
                            "original_result": result,
                            "issues": issues,
                            "quality_score": max(0, (10 - len(issues)) / 10 * 100)
                        }
                    else:
                        st.session_state.analyzed_reports[f"report_{i}"] = result
                        st.session_state.analyzed_reports[f"report_{i}"]["validation_info"] = {
                            "issues": [],
                            "quality_score": 100
                        }
                progress_bar.progress((idx + 1) / total_count)
            st.success(f"本页报告全部分析完成！")
    
    # 3. 质量统计汇总
    if analyzed_count > 0:
        st.markdown("---")
        st.markdown("#### 📊 批量分析质量统计")
        
        # 统计质量信息
        quality_scores = []
        total_issues = 0
        corrected_reports = 0
        
        for i in indices:
            key = f"report_{i}"
            if key in st.session_state.analyzed_reports:
                result = st.session_state.analyzed_reports[key]
                validation_info = result.get("validation_info", {})
                quality_score = validation_info.get("quality_score", 100)
                issues = validation_info.get("issues", [])
                
                quality_scores.append(quality_score)
                total_issues += len(issues)
                if issues:
                    corrected_reports += 1
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            # 显示统计指标
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.metric("平均质量分数", f"{avg_quality:.1f}%")
            
            with stat_col2:
                st.metric("发现问题总数", f"{total_issues} 个")
            
            with stat_col3:
                st.metric("修正报告数", f"{corrected_reports} 份")
            
            with stat_col4:
                correction_rate = (corrected_reports / analyzed_count) * 100 if analyzed_count > 0 else 0
                st.metric("修正率", f"{correction_rate:.1f}%")
            
            # 质量分布图
            if len(quality_scores) > 1:
                import matplotlib.pyplot as plt
                
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
                plt.rcParams['axes.unicode_minus'] = False
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
                
                # 质量分数分布
                ax1.hist(quality_scores, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
                ax1.set_title('质量分数分布', fontsize=14, fontweight='bold')
                ax1.set_xlabel('质量分数 (%)')
                ax1.set_ylabel('报告数量')
                ax1.grid(True, alpha=0.3)
                
                # 质量等级饼图
                excellent = sum(1 for score in quality_scores if score >= 90)
                good = sum(1 for score in quality_scores if 70 <= score < 90)
                poor = sum(1 for score in quality_scores if score < 70)
                
                labels = []
                sizes = []
                colors = []
                
                if excellent > 0:
                    labels.append(f'优秀 ({excellent})')
                    sizes.append(excellent)
                    colors.append('#4CAF50')
                
                if good > 0:
                    labels.append(f'良好 ({good})')
                    sizes.append(good)
                    colors.append('#FFC107')
                
                if poor > 0:
                    labels.append(f'需改进 ({poor})')
                    sizes.append(poor)
                    colors.append('#F44336')
                
                if sizes:
                    ax2.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors)
                    ax2.set_title('质量等级分布', fontsize=14, fontweight='bold')
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
    
    # 4. 按钮下方实时显示每份报告的分析结果信息
    st.markdown("---")
    st.markdown("#### 本页报告分析结果一览：")
    for i in indices:
        key = f"report_{i}"
        if key in st.session_state.analyzed_reports:
            result = st.session_state.analyzed_reports[key]
            summary = "结构化成功"
            
            # 获取验证信息
            validation_info = result.get("validation_info", {})
            quality_score = validation_info.get("quality_score", 100)
            issues = validation_info.get("issues", [])
            
            if "结构化数据" in result:
                diag_count = len(result["结构化数据"].get("诊断信息", []))
                summary += f"，诊断数：{diag_count}"
            
            # 添加质量状态
            if quality_score >= 90:
                quality_icon = "🟢"
                quality_text = "优秀"
            elif quality_score >= 70:
                quality_icon = "🟡"
                quality_text = "良好"
            else:
                quality_icon = "🔴"
                quality_text = "需要改进"
            
            summary += f"，质量：{quality_icon}{quality_text}({quality_score:.0f}%)"
            
            if issues:
                summary += f"，修正了{len(issues)}个问题"
            
            with st.expander(f"报告{i+1}：{summary}"):
                # 显示质量信息
                if validation_info:
                    quality_col1, quality_col2 = st.columns(2)
                    with quality_col1:
                        st.metric("质量分数", f"{quality_score:.0f}%")
                    with quality_col2:
                        st.metric("发现问题", f"{len(issues)} 个")
                    
                    if issues:
                        st.markdown("**检测到的问题：**")
                        for idx, issue in enumerate(issues[:3], 1):  # 只显示前3个问题
                            st.write(f"{idx}. {issue}")
                        if len(issues) > 3:
                            st.write(f"... 还有 {len(issues) - 3} 个问题")
                        
                        # 如果有原始结果，提供对比查看选项
                        if "original_result" in validation_info:
                            if st.button(f"查看修正详情 - 报告{i+1}", key=f"view_details_{i}"):
                                st.markdown("---")
                                display_validation_results(
                                    validation_info["original_result"], 
                                    False, 
                                    issues, 
                                    result
                                )
                
                # 显示结构化结果
                st.markdown("**结构化结果：**")
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