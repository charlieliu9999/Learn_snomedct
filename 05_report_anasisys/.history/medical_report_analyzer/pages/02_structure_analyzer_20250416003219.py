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
import streamlit as st
import pandas as pd
import os
import sys
import json
import time
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
from collections import Counter

# 导入字体管理模块，确保中文显示正常
from utils import font_manager
from matplotlib.font_manager import FontProperties

# 导入字体配置
from utils import plot_utils

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和工具模块
import config
from utils.structure_extractor import StructureExtractor

# 配置中文字体
plot_utils.configure_chinese_font()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 结构分析",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 结构分析")
st.markdown("提取医学影像报告中的结构化信息，包括解剖结构、病变特征和诊断信息。")

# 侧边栏
st.sidebar.header("结构提取选项")

# 初始化状态
if "structure_extractor" not in st.session_state:
    if st.session_state.get("llm_client") is not None:
        st.session_state.structure_extractor = StructureExtractor(st.session_state.llm_client)
    else:
        st.error("LLM客户端未初始化，请先返回首页")
        st.stop()

# 检查API密钥是否设置
if "llm_config" in st.session_state:
    if st.session_state.llm_config.get("provider") == "openai" and not st.session_state.llm_config.get("api_key"):
        st.error("❗ OpenAI API密钥未设置，无法使用分析功能。请先在设置页面配置API密钥。")
        if st.button("前往设置页面"):
            st.switch_page("pages/00_settings.py")
        st.stop()

if "analyzed_reports" not in st.session_state:
    st.session_state.analyzed_reports = {}

# 数据检查
if not st.session_state.get("data_loaded", False):
    st.warning("请先在「数据探索」页面加载数据")
    
    if st.button("前往数据探索页面"):
        st.switch_page("pages/01_data_explorer.py")
    
    st.stop()

# 获取当前数据
data = st.session_state.processed_data if st.session_state.processed_data is not None else st.session_state.raw_data

# 统一的结构化分析与展示流程
analysis_mode = st.sidebar.radio("分析模式", ["单份报告分析", "批量报告分析"])
total_reports = len(data)

# 分页/单份选择
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

# 当前页报告索引与内容
st.markdown(f"**当前处理报告区间：{indices[0]+1} - {indices[-1]+1}（共{total_reports}份）**")

# 滚动/切换当前报告
current_idx = st.selectbox("选择要查看的报告", indices, format_func=lambda i: f"报告{i+1}")
report = data.iloc[current_idx]
st.markdown("#### 原始报告")
st.text_area("影像表现", report.get("影像表现", ""), height=120, disabled=True, key=f"img_{current_idx}")
st.text_area("诊断结论", report.get("诊断结论", ""), height=120, disabled=True, key=f"diag_{current_idx}")

# 分析当前报告并展示结构化结果和可视化
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


                    
                    

                # 分析步骤
                
# 创建一个回调函数来更新状态
def update_status(step_name, step_index):
    status_container.info(f"正在{step_name}...")
                    progress = (step_index + 1) / len(steps)
                    progress_bar.progress(progress)
                
                # 记录开始时间
                start_time = time.time()
                
                # 分析报告
                try:
                    # 注册回调函数
                    st.session_state.structure_extractor.status_callback = update_status
                    
                    # 执行分析
                    result = st.session_state.structure_extractor.analyze_single_report(image_text, diagnosis_text)
                    st.session_state.analyzed_reports[report_key] = result
                    
                    # 计算耗时
                    elapsed_time = time.time() - start_time
                    
                    # 清空状态容器
                    status_container.empty()
                    progress_container.empty()
                    
                    # 显示成功信息
                    st.success(f"分析完成！耗时: {elapsed_time:.2f}秒")
                except Exception as e:
                    status_container.error(f"分析过程中出错: {str(e)}")
            else:
                st.error("报告格式错误，需要包含「影像表现」和「诊断结论」列")

elif analysis_mode == "批量报告分析":
    batch_size = st.sidebar.slider("选择批量分析数量", min_value=1, max_value=min(10, len(data)), value=3)
    start_idx = st.sidebar.number_input("起始索引", min_value=0, max_value=len(data)-batch_size, value=0)
    
    if st.sidebar.button("开始批量分析", key="analyze_batch"):
        progress_bar = st.progress(0)
        status_container = st.empty()
        error_container = st.empty()
        success_count = 0
        error_count = 0
        
        for i in range(batch_size):
            idx = start_idx + i
            report_key = f"report_{idx}"
            
            try:
                if report_key not in st.session_state.analyzed_reports:
                    status_container.info(f"正在分析第 {idx+1} 份报告...")
                    
                    sample_report = data.iloc[idx]
                    
                    if "影像表现" in sample_report and "诊断结论" in sample_report:
                        image_text = sample_report["影像表现"] if pd.notna(sample_report["影像表现"]) else ""
                        diagnosis_text = sample_report["诊断结论"] if pd.notna(sample_report["诊断结论"]) else ""
                        
                        # 分析报告并保存结果
                        result = st.session_state.structure_extractor.analyze_single_report(image_text, diagnosis_text)
                        
                        # 检查结果是否有效
                        if result and "结构化数据" in result and len(result["结构化数据"]) > 0:
                            st.session_state.analyzed_reports[report_key] = result
                            success_count += 1
                            status_container.success(f"第 {idx+1} 份报告分析成功")
                        else:
                            error_container.warning(f"第 {idx+1} 份报告分析结果为空，可能是模型调用失败")
                            error_count += 1
                    else:
                        error_container.warning(f"第 {idx+1} 份报告格式错误，需要包含「影像表现」和「诊断结论」列")
                        error_count += 1
                else:
                    status_container.info(f"第 {idx+1} 份报告已分析，跳过...")
                    success_count += 1
            except Exception as e:
                error_container.error(f"分析第 {idx+1} 份报告时出错: {str(e)}")
                error_count += 1
            
            # 更新进度
            progress_bar.progress((i + 1) / batch_size)
            time.sleep(0.1)  # 短暂延迟以展示进度
            
            # 每3个报告保存一次状态
            if (i + 1) % 3 == 0 or i == batch_size - 1:
                # 尝试保存当前状态
                try:
                    if "state_manager" in st.session_state:
                        st.session_state.state_manager.save_state("analyzed_reports", st.session_state.analyzed_reports)
                        status_container.info(f"已保存当前分析状态 ({i+1}/{batch_size})")
                except Exception as e:
                    error_container.warning(f"保存状态时出错: {str(e)}")
        
        status_container.empty()
        if success_count > 0:
            st.success(f"批量分析完成！成功: {success_count} 份, 失败: {error_count} 份")
        else:
            st.error(f"批量分析完成，但全部失败 ({error_count} 份)。请检查LLM配置和网络连接。")

# 保存分析结果
if st.session_state.analyzed_reports:
    st.sidebar.header("保存分析结果")
    
    save_filename = st.sidebar.text_input(
        "保存文件名", 
        f"analyzed_reports_{pd.Timestamp.now().strftime('%Y%m%d')}.json"
    )
    
    if st.sidebar.button("保存分析结果", key="save_analysis"):
        save_path = config.PROCESSED_DATA_DIR / save_filename
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.analyzed_reports, f, ensure_ascii=False, indent=2)
        
        st.sidebar.success(f"分析结果已保存到: {save_path}")

# 主要内容区域 - 分析结果展示

# 调试信息全局开关
调试模式 = st.sidebar.checkbox("显示调试信息", value=True, key="global_debug")

if analysis_mode == "单份报告分析":
    if report_key in st.session_state.analyzed_reports:
        report_analysis = st.session_state.analyzed_reports[report_key]
        
        # 展示原始数据
        with st.expander("原始报告", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 影像表现")
                st.write(report_analysis["原始数据"]["影像表现"])
            
            with col2:
                st.markdown("#### 诊断结论")
                st.write(report_analysis["原始数据"]["诊断结论"])
        
        # 展示结构化数据
        tab1, tab2, tab3, tab4 = st.tabs(["报告部分", "解剖结构", "病变特征", "影像-诊断映射"])
        
        with tab1:
            st.markdown("### 报告部分")
            
            if "报告部分" in report_analysis["结构化数据"] and report_analysis["结构化数据"]["报告部分"]:
                sections = report_analysis["结构化数据"]["报告部分"]
                
                for section_name, content in sections.items():
                    with st.expander(section_name, expanded=True):
                        st.write(content)
            else:
                st.info("未提取到报告部分")
                
            # 显示调试信息
            if "调试信息" in report_analysis and "报告部分_提示词" in report_analysis["调试信息"]:
                with st.expander("调试信息 - 提示词与响应", expanded=False):
                    st.markdown("#### 提示词")
                    st.code(report_analysis["调试信息"]["报告部分_提示词"], language="markdown")
                    
                    st.markdown("#### 模型响应")
                    if "报告部分_响应" in report_analysis["调试信息"]:
                        st.json(report_analysis["调试信息"]["报告部分_响应"])
        
        with tab2:
            st.markdown("### 解剖结构")
            
            if "解剖结构" in report_analysis["结构化数据"] and report_analysis["结构化数据"]["解剖结构"]:
                structures = report_analysis["结构化数据"]["解剖结构"]
                
                # 展示解剖结构表格
                st.dataframe(pd.DataFrame(structures))
                
                # 显示调试信息
                if "调试信息" in report_analysis and "解剖结构_提示词" in report_analysis["调试信息"]:
                    with st.expander("调试信息 - 提示词与响应", expanded=False):
                        st.markdown("#### 提示词")
                        st.code(report_analysis["调试信息"]["解剖结构_提示词"], language="markdown")
                        
                        st.markdown("#### 模型响应")
                        if "解剖结构_响应" in report_analysis["调试信息"]:
                            st.json(report_analysis["调试信息"]["解剖结构_响应"])
                
                # 尝试可视化解剖结构关系
                if len(structures) > 1:
                    try:
                        st.markdown("#### 解剖结构关系")
                        
                        # 构建父子关系
                        G = nx.DiGraph()
                        
                        for struct in structures:
                            if "原文" in struct and "父结构" in struct:
                                child = struct["原文"]
                                parent = struct["父结构"]
                                
                                G.add_node(child)
                                G.add_node(parent)
                                G.add_edge(parent, child)
                        
                        # 确保中文字体正确配置
                        font_manager.initialize_chinese_font()
                        
                        # 绘制图形
                        plt.figure(figsize=(10, 8))
                        pos = nx.spring_layout(G)
                        
                        # 绘制节点和边
                        nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=1500)
                        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=15)
                        
                        # 获取字体属性对象，保证节点标签中文显示
                        # 获取可用的中文字体路径
                        import os
                        # 多路径 fallback，确保总能找到可用字体
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

                        # 手动绘制节点标签，彻底解决中文问题
                        ax = plt.gca()
                        for node, (x, y) in pos.items():
                            ax.text(x, y, str(node), fontproperties=font_prop, fontsize=12, ha='center', va='center')
                        plt.title("解剖结构关系图", fontproperties=font_prop)
                        plt.axis('off')  # 隐藏坐标轴
                        st.pyplot(plt.gcf())
                    except Exception as e:
                        st.error(f"可视化解剖结构关系时出错: {str(e)}")
            else:
                st.info("未提取到解剖结构")
        
        with tab3:
            st.markdown("### 病变特征")
            
            if "病变特征" in report_analysis["结构化数据"] and report_analysis["结构化数据"]["病变特征"]:
                features = report_analysis["结构化数据"]["病变特征"]
                
                for i, feature in enumerate(features):
                    with st.expander(f"病变 {i+1}: {feature.get('解剖位置', '未知位置')}", expanded=True):
                        # 将字典转换为表格展示
                        for key, value in feature.items():
                            if value:  # 只显示非空值
                                st.markdown(f"**{key}**: {value}")
            else:
                st.info("未提取到病变特征")
        
        with tab4:
            st.markdown("### 影像-诊断映射")
            
            if "影像诊断映射" in report_analysis["结构化数据"]:
                mapping = report_analysis["结构化数据"]["影像诊断映射"]
                
                # 展示诊断列表
                if "诊断列表" in mapping and mapping["诊断列表"]:
                    st.markdown("#### 诊断列表")
                    for diag in mapping["诊断列表"]:
                        st.write(f"- {diag.get('诊断名称', '未知诊断')} ({diag.get('诊断确定性', '未知确定性')})")
                
                # 展示影像特征列表
                if "影像特征列表" in mapping and mapping["影像特征列表"]:
                    st.markdown("#### 影像特征列表")
                    for feature in mapping["影像特征列表"]:
                        st.write(f"- **{feature.get('解剖位置', '未知位置')}**: {feature.get('特征描述', '无描述')}")
                
                # 展示映射关系
                if "映射关系" in mapping and mapping["映射关系"]:
                    st.markdown("#### 映射关系")
                    for relation in mapping["映射关系"]:
                        with st.expander(f"{relation.get('诊断', '未知诊断')} (支持程度: {relation.get('支持程度', '未知')})", expanded=True):
                            st.markdown("**支持特征:**")
                            for feature in relation.get("支持特征", []):
                                st.write(f"- {feature}")
                            
                            if "解释" in relation:
                                st.markdown("**解释:**")
                                st.write(relation["解释"])
            else:
                st.info("未提取到影像-诊断映射")
    
    else:
        st.info("请先分析报告")

elif analysis_mode == "批量报告分析":
    if st.session_state.analyzed_reports:
        st.markdown("### 批量分析结果统计")
        
        # 计算分析报告数量
        num_analyzed = len(st.session_state.analyzed_reports)
        st.write(f"已分析报告数量: {num_analyzed}")
        
        # 汇总诊断信息
        all_diagnoses = []
        for report_key, report_data in st.session_state.analyzed_reports.items():
            if "结构化数据" in report_data and "诊断信息" in report_data["结构化数据"]:
                for diag in report_data["结构化数据"]["诊断信息"]:
                    if "诊断名称" in diag:
                        all_diagnoses.append(diag["诊断名称"])
        
        if all_diagnoses:
            st.markdown("#### 诊断分布")
            diag_counter = Counter(all_diagnoses)
            
            # 创建诊断分布图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            top_diags = dict(diag_counter.most_common(10))
            sns.barplot(x=list(top_diags.keys()), y=list(top_diags.values()), ax=ax)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.title("诊断分布")
            plt.xlabel("诊断名称")
            plt.ylabel("出现次数")
            
            st.pyplot(fig)
        
        # 汇总解剖结构信息
        all_structures = []
        for report_key, report_data in st.session_state.analyzed_reports.items():
            if "结构化数据" in report_data and "解剖结构" in report_data["结构化数据"]:
                for struct in report_data["结构化数据"]["解剖结构"]:
                    if "原文" in struct:
                        all_structures.append(struct["原文"])
        
        if all_structures:
            st.markdown("#### 常见解剖结构")
            struct_counter = Counter(all_structures)
            
            # 创建解剖结构分布图
            fig, ax = plt.subplots(figsize=(10, 6))
            
            top_structs = dict(struct_counter.most_common(10))
            sns.barplot(x=list(top_structs.keys()), y=list(top_structs.values()), ax=ax)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.title("解剖结构分布")
            plt.xlabel("解剖结构")
            plt.ylabel("出现次数")
            
            st.pyplot(fig)
        
        # 展示样本报告
        st.markdown("#### 样本报告分析")
        
        report_keys = list(st.session_state.analyzed_reports.keys())
        selected_report = st.selectbox("选择报告", report_keys)
        
        if selected_report:
            report_analysis = st.session_state.analyzed_reports[selected_report]
            
            # 展示原始数据
            with st.expander("原始报告"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 影像表现")
                    st.write(report_analysis["原始数据"]["影像表现"])
                
                with col2:
                    st.markdown("#### 诊断结论")
                    st.write(report_analysis["原始数据"]["诊断结论"])
            
            # 展示结构化数据概要
            with st.expander("结构化数据概要", expanded=True):
                if "诊断信息" in report_analysis["结构化数据"]:
                    st.markdown("**诊断信息:**")
                    for diag in report_analysis["结构化数据"]["诊断信息"]:
                        st.write(f"- {diag.get('诊断名称', '未知诊断')} ({diag.get('诊断确定性', '未知确定性')})")
                
                if "病变特征" in report_analysis["结构化数据"]:
                    st.markdown("**病变数量:**")
                    st.write(f"共发现 {len(report_analysis['结构化数据']['病变特征'])} 个病变特征")
                
                # 如果开启了调试模式，显示完整调试信息
                # 不在这里显示调试信息，避免嵌套expander
                if 调试模式 and "调试信息" in report_analysis:
                    st.markdown("---")
                    st.markdown("### 完整调试信息")
            
