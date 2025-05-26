"""
数据探索页面 - 用于加载和查看医学影像报告数据
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import json

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 初始化会话状态
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "raw_data" not in st.session_state:
    st.session_state.raw_data = None
    
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None

# 导入绘图工具
from utils.plot_utils import create_pie_chart, create_bar_chart

# 导入配置和工具模块
import config
from utils.data_processor import (
    load_excel_data, clean_dataframe, extract_basic_stats, 
    get_report_sections, save_processed_data, load_processed_data
)

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 数据探索",
    page_icon="🔍",
    layout="wide"
)

st.title("📊 数据探索")

# 侧边栏
st.sidebar.header("数据加载选项")

data_source = st.sidebar.radio(
    "选择数据来源",
    ["默认数据文件", "本地数据文件", "已处理数据"]
)

if data_source == "默认数据文件":
    st.sidebar.info(f"使用默认数据文件: {config.DEFAULT_DATA_FILE}")
    
    if st.sidebar.button("加载默认数据", key="load_default"):
        with st.spinner("正在加载默认数据..."):
            try:
                df = load_excel_data(config.DEFAULT_DATA_PATH)
                st.session_state.raw_data = df
                st.session_state.data_loaded = True
                st.success(f"成功加载 {len(df)} 条报告数据！")
            except Exception as e:
                st.error(f"加载数据失败: {str(e)}")
                st.session_state.data_loaded = False

elif data_source == "本地数据文件":
    # 添加两种选择方式
    selection_method = st.sidebar.radio(
        "选择方式",
        ["输入路径", "选择目录"]
    )
    
    file_path = ""
    
    if selection_method == "输入路径":
        file_path = st.sidebar.text_input("输入本地Excel文件路径", "/Users/charlieliu/Desktop/华西-报告质控/胸部CT报告-0401.xlsx")
    else:  # 选择目录
        # 先选择目录
        dir_path = st.sidebar.text_input("输入目录路径", "/Users/charlieliu/Desktop/华西-报告质控")
        
        if dir_path and os.path.isdir(dir_path):
            # 列出目录中的Excel文件
            excel_files = [f for f in os.listdir(dir_path) if f.endswith(('.xlsx', '.xls'))]
            if excel_files:
                selected_file = st.sidebar.selectbox("选择Excel文件", excel_files)
                if selected_file:
                    file_path = os.path.join(dir_path, selected_file)
            else:
                st.sidebar.warning("指定目录下没有Excel文件")
        elif dir_path:
            st.sidebar.error(f"目录不存在: {dir_path}")
    
    if file_path:
        if st.sidebar.button("加载本地数据", key="load_local"):
            with st.spinner("正在加载本地数据..."):
                try:
                    # 检查文件是否存在
                    if not os.path.exists(file_path):
                        st.sidebar.error(f"文件不存在: {file_path}")
                    else:
                        st.sidebar.info(f"正在读取文件: {file_path}")
                        df = pd.read_excel(file_path)
                        st.session_state.raw_data = df
                        st.session_state.data_loaded = True
                        st.success(f"成功加载 {len(df)} 条报告数据！")
                except Exception as e:
                    st.error(f"加载数据失败: {str(e)}")
                    st.session_state.data_loaded = False

elif data_source == "已处理数据":
    processed_files = list(config.PROCESSED_DATA_DIR.glob("*.pkl"))
    if processed_files:
        file_names = [file.name for file in processed_files]
        selected_file = st.sidebar.selectbox("选择已处理的数据文件", file_names)
        
        if st.sidebar.button("加载已处理数据", key="load_processed"):
            with st.spinner("正在加载已处理数据..."):
                try:
                    file_path = config.PROCESSED_DATA_DIR / selected_file
                    df = load_processed_data(file_path)
                    st.session_state.processed_data = df
                    st.session_state.raw_data = df
                    st.session_state.data_loaded = True
                    st.success(f"成功加载 {len(df)} 条报告数据！")
                except Exception as e:
                    st.error(f"加载数据失败: {str(e)}")
                    st.session_state.data_loaded = False
    else:
        st.sidebar.warning("未找到已处理的数据文件")

# 数据处理选项
if st.session_state.data_loaded:
    st.sidebar.header("数据处理选项")
    
    if st.sidebar.button("清洗数据", key="clean_data"):
        with st.spinner("正在清洗数据..."):
            df_clean = clean_dataframe(st.session_state.raw_data)
            st.session_state.processed_data = df_clean
            st.success(f"数据清洗完成！处理后数据包含 {len(df_clean)} 行。")
    
    if st.session_state.processed_data is not None:
        save_filename = st.sidebar.text_input("保存文件名", f"processed_data_{pd.Timestamp.now().strftime('%Y%m%d')}.pkl")
        
        if st.sidebar.button("保存处理后的数据", key="save_data"):
            save_path = config.PROCESSED_DATA_DIR / save_filename
            save_processed_data(st.session_state.processed_data, save_path)
            st.sidebar.success(f"数据已保存到: {save_path}")

# 主要内容区域
if not st.session_state.data_loaded:
    st.info("请从侧边栏加载数据")
    
    # 示例数据展示
    st.markdown("### 📋 数据格式示例")
    
    example_data = {
        "患者ID": ["P001", "P002", "P003"],
        "检查类型": ["胸部CT", "胸部CT", "胸部CT"],
        "影像表现": [
            "右肺上叶可见一枚约2.5cm×1.8cm大小的结节状软组织密度影，边缘呈分叶状，可见毛刺征。未见明显钙化。",
            "双肺弥漫性分布多发斑片状、磨玻璃密度影，以双下肺为著。部分病灶呈'铺路石'样改变。",
            "右肺上叶可见一空洞性病变，大小约3.2cm×2.5cm，壁厚约3mm，壁内侧欠光整。周围可见少许纤维索条影。"
        ],
        "诊断结论": [
            "右肺上叶周围型肺癌可能性大，建议进一步活检明确。",
            "病毒性肺炎，考虑COVID-19肺炎。",
            "右肺上叶空洞性病变，考虑肺结核可能性大。"
        ]
    }
    
    st.table(pd.DataFrame(example_data))
    
    st.markdown("""
    ### 📝 数据要求
    
    1. Excel文件应至少包含以下列:
       - **影像表现**: 医生对影像的描述
       - **诊断结论**: 医生给出的诊断
    
    2. 可选列:
       - 患者ID/姓名
       - 检查类型
       - 检查日期
       - 检查设备
       - 报告医生
    """)

else:
    # 数据已加载时的处理
    # 数据总览
    data_to_display = st.session_state.processed_data if st.session_state.processed_data is not None else st.session_state.raw_data
    
    st.markdown("### 📊 数据总览")
    
    st.write(f"数据形状: {data_to_display.shape[0]} 行 × {data_to_display.shape[1]} 列")
    
    col_info, missing_info = st.columns(2)
    
    with col_info:
        st.write("列信息:")
        col_info_df = pd.DataFrame({
            "列名": data_to_display.columns,
            "数据类型": data_to_display.dtypes.astype(str),
            "非空值数量": data_to_display.count().values
        })
        st.table(col_info_df)
    
    with missing_info:
        # 缺失值可视化
        st.write("缺失值占比:")
        missing_data = data_to_display.isnull().sum() / len(data_to_display) * 100
        missing_df = pd.DataFrame({
            "列名": missing_data.index,
            "缺失比例(%)": missing_data.values.round(2)
        })
        
        # 只显示有缺失的列
        missing_df = missing_df[missing_df["缺失比例(%)"] > 0]
        
        if len(missing_df) > 0:
            # 使用我们的绘图工具创建条形图
            fig, ax = create_bar_chart(
                missing_df["缺失比例(%)"].values, 
                missing_df["列名"].values, 
                title="数据缺失情况",
                xlabel="缺失比例(%)",
                ylabel="列名"
            )
            st.pyplot(fig)
        else:
            st.info("数据完整，无缺失值")
    
    # 数据列选择器
    st.markdown("### 🔍 数据浏览")
    
    column_selector = st.multiselect(
        "选择要查看的列",
        options=list(data_to_display.columns),
        default=["影像表现", "诊断结论"] if "影像表现" in data_to_display.columns and "诊断结论" in data_to_display.columns else list(data_to_display.columns[:2])
    )
    
    if column_selector:
        st.dataframe(data_to_display[column_selector].head(10))
    
    # 提取基本统计信息
    st.markdown("### 📈 数据统计分析")
    
    with st.expander("查看基本统计信息"):
        stats = extract_basic_stats(data_to_display)
        
        st.write(f"报告总数: {stats['报告总数']}")
        
        # 如果有诊断分布信息，显示诊断分布图
        if '前10位诊断分布' in stats:
            st.write("主要诊断分布:")
            # 创建诊断分布图
            diagnosis_data = stats['前10位诊断分布']
            labels = list(diagnosis_data.keys())
            sizes = list(diagnosis_data.values())
            
            # 使用我们的绘图工具创建饼图
            fig, ax = create_pie_chart(sizes, labels, title='主要诊断分布')
            st.pyplot(fig)
    
    # 影像表现和诊断结论详细分析
    if "影像表现" in data_to_display.columns and "诊断结论" in data_to_display.columns:
        st.markdown("### 📑 报告详细分析")
        
        sample_idx = st.slider("选择报告样本索引", 0, len(data_to_display) - 1, 0)
        
        sample_report = data_to_display.iloc[sample_idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 影像表现")
            
            if pd.notna(sample_report["影像表现"]):
                st.write(sample_report["影像表现"])
                
                # 尝试分解报告
                sections = get_report_sections(sample_report["影像表现"])
                
                if len(sections) > 1:  # 如果成功分解为多个部分
                    st.markdown("##### 分解后的结构")
                    for section_name, content in sections.items():
                        with st.expander(section_name):
                            st.write(content)
            else:
                st.write("无影像表现数据")
        
        with col2:
            st.markdown("#### 诊断结论")
            
            if pd.notna(sample_report["诊断结论"]):
                st.write(sample_report["诊断结论"])
                
                # 简单处理诊断结论
                diagnoses = sample_report["诊断结论"].split("。")
                if len(diagnoses) > 1:
                    st.markdown("##### 分解后的诊断")
                    for i, diag in enumerate(diagnoses):
                        if diag.strip():
                            st.write(f"{i+1}. {diag.strip()}")
            else:
                st.write("无诊断结论数据")
    
    # 进一步分析的链接
    st.markdown("---")
    next_col1, next_col2, next_col3 = st.columns([1, 2, 1])
    
    with next_col2:
        if st.button("开始结构分析", use_container_width=True):
            st.switch_page("pages/02_structure_analyzer.py")
