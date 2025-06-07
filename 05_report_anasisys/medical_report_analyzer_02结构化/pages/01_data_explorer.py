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

# NEW: Define path for field preferences file
FIELD_PREFERENCES_FILE = Path(__file__).parent / "field_preferences.json"

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 初始化会话状态
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "raw_data" not in st.session_state:
    st.session_state.raw_data = None
    
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None

# Session state for selected key columns (driven by UI interaction or auto-detect)
if "findings_col" not in st.session_state:
    st.session_state.findings_col = None
if "impression_col" not in st.session_state:
    st.session_state.impression_col = None

# Session state for user-defined persistent preferences (loaded from file)
if "user_preferred_findings_col" not in st.session_state:
    st.session_state.user_preferred_findings_col = None
if "user_preferred_impression_col" not in st.session_state:
    st.session_state.user_preferred_impression_col = None
if "preferences_loaded" not in st.session_state: 
    st.session_state.preferences_loaded = False

# Keywords for auto-detection
FINDINGS_KEYWORDS_CN = ["影像所见", "影像学表现", "检查所见", "CT表现", "MR表现", "影像表现", "所见", "检查描述"]
IMPRESSION_KEYWORDS_CN = ["诊断意见", "诊断结论", "印象", "结论", "诊断提示", "考虑", "分析意见"]
FINDINGS_KEYWORDS_EN = ["findings", "image findings", "description", "radiologic findings", "imaging findings"]
IMPRESSION_KEYWORDS_EN = ["impression", "conclusion", "diagnosis", "assessment", "summary", "interpretation"]

ALL_FINDINGS_KEYWORDS = FINDINGS_KEYWORDS_CN + \
                        [k.lower() for k in FINDINGS_KEYWORDS_EN] + \
                        [k.title() for k in FINDINGS_KEYWORDS_EN] + \
                        [k.upper() for k in FINDINGS_KEYWORDS_EN]
ALL_IMPRESSION_KEYWORDS = IMPRESSION_KEYWORDS_CN + \
                          [k.lower() for k in IMPRESSION_KEYWORDS_EN] + \
                          [k.title() for k in IMPRESSION_KEYWORDS_EN] + \
                          [k.upper() for k in IMPRESSION_KEYWORDS_EN]

# NEW: Helper function for auto-detection
def auto_detect_column(column_names, keywords, current_selection=None):
    """
    Tries to detect a column based on keywords.
    Prioritizes exact matches of keywords, then substring matches.
    If a current_selection is provided and valid, it might be preferred or used as a fallback.
    Returns the column name or None.
    """
    if not column_names:
        return None

    # Convert column_names to lowercase for case-insensitive comparison
    column_names_lower_map = {col.lower(): col for col in column_names}
    
    # Exact keyword match (case insensitive)
    for keyword in keywords:
        if keyword.lower() in column_names_lower_map:
            return column_names_lower_map[keyword.lower()]
            
    # Substring match (case insensitive)
    for col_name in column_names:
        col_name_lower = col_name.lower()
        for keyword in keywords:
            if keyword.lower() in col_name_lower:
                return col_name
    
    # If a valid current selection exists, could return it here, or handle outside.
    # For now, if no keyword match, return None from detection.
    return None

# Function to load field preferences

# Function to load field preferences
def load_field_preferences():
    if FIELD_PREFERENCES_FILE.exists():
        try:
            with open(FIELD_PREFERENCES_FILE, "r", encoding="utf-8") as f:
                prefs = json.load(f)
                st.session_state.user_preferred_findings_col = prefs.get("preferred_findings_col")
                st.session_state.user_preferred_impression_col = prefs.get("preferred_impression_col")
        except Exception: # Silently ignore errors during preference loading
            pass
    st.session_state.preferences_loaded = True

# Function to save field preferences
def save_field_preferences():
    prefs_to_save = {
        "preferred_findings_col": st.session_state.get("findings_col"),
        "preferred_impression_col": st.session_state.get("impression_col")
    }
    try:
        with open(FIELD_PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs_to_save, f, ensure_ascii=False, indent=4)
        # Update the session state for loaded preferences to reflect immediate save
        st.session_state.user_preferred_findings_col = prefs_to_save["preferred_findings_col"]
        st.session_state.user_preferred_impression_col = prefs_to_save["preferred_impression_col"]
    except Exception as e:
        st.error(f"保存字段偏好失败: {e}")



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
                st.session_state.processed_data = None # Reset processed data
                st.session_state.findings_col = None # Reset for auto-detection
                st.session_state.impression_col = None # Reset for auto-detection
                st.success(f"成功加载 {len(df)} 条报告数据！")
            except Exception as e:
                st.error(f"加载数据失败: {str(e)}")
                st.session_state.data_loaded = False

elif data_source == "本地数据文件":
    uploaded_file = st.sidebar.file_uploader(
        "上传本地Excel文件", 
        type=["xlsx", "xls"],
        help="请上传包含医学影像报告的Excel文件 (.xlsx 或 .xls)。系统将从此文件加载数据进行分析。"
    )
    
    if uploaded_file is not None:
        # 使用新的 key "load_local_uploaded" 避免与旧按钮冲突 (如果旧代码意外残留)
        if st.sidebar.button("加载上传的数据", key="load_local_uploaded"): 
            with st.spinner("正在加载上传的本地数据..."):
                try:
                    st.sidebar.info(f"正在读取上传的文件: {uploaded_file.name}")
                    # uploaded_file 是一个内存中的类文件对象，pandas可以直接读取
                    df = pd.read_excel(uploaded_file)
                    st.session_state.raw_data = df
                    st.session_state.data_loaded = True
                    st.session_state.processed_data = None # 清除旧的处理数据
                    st.session_state.findings_col = None # Reset for auto-detection
                    st.session_state.impression_col = None # Reset for auto-detection
                    st.success(f"成功加载 {len(df)} 条报告数据！ (来自: {uploaded_file.name})")
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
                    st.session_state.raw_data = df # Also load into raw_data if it's the base
                    st.session_state.data_loaded = True
                    st.session_state.findings_col = None # Reset for auto-detection
                    st.session_state.impression_col = None # Reset for auto-detection
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
    
    # REVISED: Section for defining key report fields with corrected strings
    st.markdown("### 🎯 关键字段定义")
    report_columns = list(data_to_display.columns)
    
    options_for_selectbox = [""] if not report_columns else report_columns
    default_idx = 0

    # Determine initial selections based on preferences and auto-detection
    # This logic ensures that session_state.findings_col and session_state.impression_col are set
    # before the selectboxes are rendered, using the priority:
    # 1. User's loaded preferences (if valid in current columns)
    # 2. Auto-detected keywords
    # (If a user manually changes a selectbox, that value is stored in session_state and will be used directly
    #  by the selectbox's `index` in subsequent reruns, unless data is reloaded which resets these.)

    # Reset to None only if data just loaded (indicated by findings_col being None from load block)
    # This allows user's current session changes to persist until next data load.
    # The logic for resetting findings_col/impression_col to None is already in data loading blocks.

    current_findings_val = st.session_state.get("findings_col")
    current_impression_val = st.session_state.get("impression_col")
    
    # Attempt to set from preferences if not already set by user in this session or if current is invalid
    pref_f = st.session_state.get("user_preferred_findings_col")
    if pref_f and pref_f in report_columns:
        if current_findings_val is None or current_findings_val not in report_columns:
            st.session_state.findings_col = pref_f
            current_findings_val = pref_f

    pref_i = st.session_state.get("user_preferred_impression_col")
    if pref_i and pref_i in report_columns and pref_i != current_findings_val: 
        if current_impression_val is None or current_impression_val not in report_columns or current_impression_val == current_findings_val:
            st.session_state.impression_col = pref_i
            current_impression_val = pref_i

    # Fallback to auto-detection if preferences didn't apply or were not sufficient
    if st.session_state.get("findings_col") is None or st.session_state.get("findings_col") not in report_columns:
        st.session_state.findings_col = auto_detect_column(report_columns, ALL_FINDINGS_KEYWORDS)

    impression_candidates = [col for col in report_columns if col != st.session_state.get("findings_col")]
    if not impression_candidates: impression_candidates = report_columns

    if st.session_state.get("impression_col") is None or \
       st.session_state.get("impression_col") not in report_columns or \
       st.session_state.get("impression_col") == st.session_state.get("findings_col"):
        st.session_state.impression_col = auto_detect_column(impression_candidates, ALL_IMPRESSION_KEYWORDS)

    try:
        findings_default_idx = report_columns.index(st.session_state.findings_col) if st.session_state.findings_col in report_columns else default_idx
    except ValueError:
        findings_default_idx = default_idx

    try:
        impression_candidates_for_idx = [col for col in report_columns if col != st.session_state.findings_col]
        if not impression_candidates_for_idx: impression_candidates_for_idx = report_columns
        impression_default_idx = impression_candidates_for_idx.index(st.session_state.impression_col) if st.session_state.impression_col in impression_candidates_for_idx else default_idx
    except ValueError:
        impression_default_idx = default_idx

    # -- Manually Corrected Selectbox Widgets and Logic --
    col1, col2 = st.columns(2)
    with col1:
        selected_findings_col = st.selectbox(
            label='1. 选择“影像表现”字段:',
            options=report_columns,
            index=findings_default_idx,
            key='findings_select'
        )

    with col2:
        selected_impression_col = st.selectbox(
            label='2. 选择“诊断结论”字段:',
            options=report_columns,
            index=impression_default_idx,
            key='impression_select'
        )

    st.session_state.findings_col = selected_findings_col
    st.session_state.impression_col = selected_impression_col
    
    if st.session_state.get("findings_col") and st.session_state.get("impression_col"):
        if st.session_state.findings_col == st.session_state.impression_col and len(report_columns) > 1:
            st.warning(f"“影像表现”和“诊断结论”不应选择同一列 ('{st.session_state.findings_col}'). 请分别指定.")
        else:
            st.success(f"已指定关键字段：影像表现列 = **'{st.session_state.findings_col}'**，诊断结论列 = **'{st.session_state.impression_col}'**")
    elif report_columns:
        st.info("请在上方选择或确认“影像表现”和“诊断结论”对应的列.")
    
    # Add Save Preferences button
    if report_columns and st.session_state.get("findings_col") and st.session_state.get("impression_col"):
        if st.button("💾 保存当前字段选择为偏好", key="save_field_prefs_button"):
            save_field_preferences()
            st.toast("字段选择偏好已成功保存!", icon="✅")
    
    # 数据列选择器
    st.markdown("### 🔍 数据浏览")
    
    # 智能默认选择：优先使用用户指定的关键字段
    default_columns = []
    if st.session_state.get("findings_col") and st.session_state.findings_col in data_to_display.columns:
        default_columns.append(st.session_state.findings_col)
    if st.session_state.get("impression_col") and st.session_state.impression_col in data_to_display.columns:
        default_columns.append(st.session_state.impression_col)
    
    # 如果没有用户指定的字段，或者字段不存在，则使用前两列作为默认
    if not default_columns:
        default_columns = list(data_to_display.columns[:2]) if len(data_to_display.columns) >= 2 else list(data_to_display.columns)
    
    column_selector = st.multiselect(
        "选择要查看的列",
        options=list(data_to_display.columns),
        default=default_columns
    )
    
    if column_selector:
        st.dataframe(data_to_display[column_selector].head(10))
    
    # 增强的数据统计分析
    st.markdown("### 📈 数据统计分析")
    
    # 基本统计信息
    with st.expander("查看基本统计信息", expanded=True):
        # 传递用户选择的诊断结论字段给统计函数
        impression_col_for_stats = st.session_state.get("impression_col") if st.session_state.get("impression_col") else None
        stats = extract_basic_stats(data_to_display, impression_col=impression_col_for_stats)
        
        # 创建三列布局显示核心指标
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("报告总数", stats['报告总数'])
        
        with metric_col2:
            completeness = (1 - data_to_display.isnull().sum().sum() / (data_to_display.shape[0] * data_to_display.shape[1])) * 100
            st.metric("数据完整度", f"{completeness:.1f}%")
        
        with metric_col3:
            st.metric("字段数量", data_to_display.shape[1])
        
        # 如果有诊断分布信息，显示诊断分布图
        if '前10位诊断分布' in stats:
            # 显示实际使用的字段名
            diagnosis_field_name = stats.get('诊断字段', '诊断结论')
            st.write(f"主要诊断分布 (基于字段: **{diagnosis_field_name}**):")
            
            # 创建诊断分布图
            diagnosis_data = stats['前10位诊断分布']
            labels = list(diagnosis_data.keys())
            sizes = list(diagnosis_data.values())
            
            # 使用我们的绘图工具创建饼图
            chart_title = f'{diagnosis_field_name} - 主要诊断分布'
            fig, ax = create_pie_chart(sizes, labels, title=chart_title)
            st.pyplot(fig)
    
    # 详细字段分析
    if st.session_state.get("findings_col") and st.session_state.get("impression_col"):
        st.markdown("### 🔍 关键字段详细分析")
        
        # 字段选择器用于详细分析
        analysis_field = st.selectbox(
            "选择要详细分析的字段",
            options=[st.session_state.findings_col, st.session_state.impression_col],
            key="analysis_field_selector"
        )
        
        if analysis_field and analysis_field in data_to_display.columns:
            field_data = data_to_display[analysis_field].dropna()
            
            # 创建两列布局
            analysis_col1, analysis_col2 = st.columns(2)
            
            with analysis_col1:
                st.markdown(f"#### 📊 {analysis_field} - 统计指标")
                
                # 文本长度统计
                text_lengths = field_data.str.len()
                
                # 显示统计指标
                st.write("**文本长度统计:**")
                length_stats = {
                    "平均长度": f"{text_lengths.mean():.1f} 字符",
                    "最短文本": f"{text_lengths.min()} 字符",
                    "最长文本": f"{text_lengths.max()} 字符",
                    "中位数长度": f"{text_lengths.median():.1f} 字符"
                }
                
                for stat_name, stat_value in length_stats.items():
                    st.write(f"- {stat_name}: {stat_value}")
                
                # 唯一值统计
                st.write("**内容统计:**")
                st.write(f"- 总记录数: {len(field_data)}")
                st.write(f"- 唯一内容数: {field_data.nunique()}")
                st.write(f"- 重复率: {((len(field_data) - field_data.nunique()) / len(field_data) * 100):.1f}%")
                
                # 空值统计
                null_count = data_to_display[analysis_field].isnull().sum()
                st.write(f"- 空值数量: {null_count}")
                st.write(f"- 空值比例: {(null_count / len(data_to_display) * 100):.1f}%")
            
            with analysis_col2:
                st.markdown(f"#### 📈 {analysis_field} - 可视化分析")
                
                # 文本长度分布直方图
                if len(text_lengths) > 0:
                    fig, ax = create_bar_chart(
                        np.histogram(text_lengths, bins=20)[0],
                        [f"{int(edge)}" for edge in np.histogram(text_lengths, bins=20)[1][:-1]],
                        title=f"{analysis_field} 文本长度分布",
                        xlabel="文本长度区间",
                        ylabel="频次"
                    )
                    st.pyplot(fig)
                
                # 最常见的关键词（简单词频统计）
                st.markdown("**常见关键词分析:**")
                
                # 简单的词频统计（基于空格和标点分割）
                import re
                all_text = " ".join(field_data.astype(str))
                # 简单的中文分词（按标点和空格）
                words = re.findall(r'[\u4e00-\u9fff]+', all_text)
                words = [word for word in words if len(word) > 1]  # 过滤单字
                
                if words:
                    from collections import Counter
                    word_counts = Counter(words)
                    top_words = word_counts.most_common(10)
                    
                    if top_words:
                        word_df = pd.DataFrame(top_words, columns=['词语', '频次'])
                        st.dataframe(word_df, use_container_width=True)
                
        # 字段内容预览
        st.markdown("### 📋 字段内容预览")
        
        preview_col1, preview_col2 = st.columns(2)
        
        with preview_col1:
            st.markdown(f"#### {st.session_state.findings_col}")
            findings_data = data_to_display[st.session_state.findings_col].dropna()
            if len(findings_data) > 0:
                # 显示几个示例
                sample_size = min(3, len(findings_data))
                for i in range(sample_size):
                    with st.expander(f"示例 {i+1}", expanded=(i==0)):
                        st.write(findings_data.iloc[i])
        
        with preview_col2:
            st.markdown(f"#### {st.session_state.impression_col}")
            impression_data = data_to_display[st.session_state.impression_col].dropna()
            if len(impression_data) > 0:
                # 显示几个示例
                sample_size = min(3, len(impression_data))
                for i in range(sample_size):
                    with st.expander(f"示例 {i+1}", expanded=(i==0)):
                        st.write(impression_data.iloc[i])
        
        # 数据质量评估
        st.markdown("### 🔬 数据质量评估")
        
        quality_col1, quality_col2 = st.columns(2)
        
        with quality_col1:
            st.markdown("#### 数据完整性检查")
            
            # 检查关键字段的数据完整性
            findings_completeness = (data_to_display[st.session_state.findings_col].notna().sum() / len(data_to_display)) * 100
            impression_completeness = (data_to_display[st.session_state.impression_col].notna().sum() / len(data_to_display)) * 100
            
            completeness_data = {
                '字段': [st.session_state.findings_col, st.session_state.impression_col],
                '完整度(%)': [f"{findings_completeness:.1f}%", f"{impression_completeness:.1f}%"],
                '状态': ['✅' if findings_completeness > 90 else '⚠️' if findings_completeness > 70 else '❌',
                        '✅' if impression_completeness > 90 else '⚠️' if impression_completeness > 70 else '❌']
            }
            
            st.dataframe(pd.DataFrame(completeness_data), use_container_width=True)
        
        with quality_col2:
            st.markdown("#### 数据一致性检查")
            
            # 检查是否有异常短或异常长的文本
            findings_lengths = data_to_display[st.session_state.findings_col].str.len().dropna()
            impression_lengths = data_to_display[st.session_state.impression_col].str.len().dropna()
            
            # 异常检测（使用四分位数方法）
            def detect_outliers(series):
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                return len(outliers), (len(outliers) / len(series)) * 100
            
            findings_outliers, findings_outlier_pct = detect_outliers(findings_lengths) if len(findings_lengths) > 0 else (0, 0)
            impression_outliers, impression_outlier_pct = detect_outliers(impression_lengths) if len(impression_lengths) > 0 else (0, 0)
            
            outlier_data = {
                '字段': [st.session_state.findings_col, st.session_state.impression_col],
                '异常记录数': [findings_outliers, impression_outliers],
                '异常比例': [f"{findings_outlier_pct:.1f}%", f"{impression_outlier_pct:.1f}%"]
            }
            
            st.dataframe(pd.DataFrame(outlier_data), use_container_width=True)
    
    # 基于用户选择字段的详细分析
    if st.session_state.get("findings_col") and st.session_state.get("impression_col") and \
       st.session_state.findings_col in data_to_display.columns and st.session_state.impression_col in data_to_display.columns:
        st.markdown("### 📑 报告详细分析")
        
        sample_idx = st.slider("选择报告样本索引", 0, len(data_to_display) - 1, 0)
        
        sample_report = data_to_display.iloc[sample_idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {st.session_state.findings_col}")
            
            if pd.notna(sample_report[st.session_state.findings_col]):
                st.write(sample_report[st.session_state.findings_col])
                
                # 尝试分解报告
                sections = get_report_sections(sample_report[st.session_state.findings_col])
                
                if len(sections) > 1:  # 如果成功分解为多个部分
                    st.markdown("##### 分解后的结构")
                    for section_name, content in sections.items():
                        with st.expander(section_name):
                            st.write(content)
            else:
                st.write(f"无{st.session_state.findings_col}数据")
        
        with col2:
            st.markdown(f"#### {st.session_state.impression_col}")
            
            if pd.notna(sample_report[st.session_state.impression_col]):
                st.write(sample_report[st.session_state.impression_col])
                
                # 简单处理诊断结论
                diagnoses = sample_report[st.session_state.impression_col].split("。")
                if len(diagnoses) > 1:
                    st.markdown("##### 分解后的诊断")
                    for i, diag in enumerate(diagnoses):
                        if diag.strip():
                            st.write(f"{i+1}. {diag.strip()}")
            else:
                st.write(f"无{st.session_state.impression_col}数据")
    
    # 进一步分析的链接
    st.markdown("---")
    next_col1, next_col2, next_col3 = st.columns([1, 2, 1])
    
    with next_col2:
        if st.button("开始结构分析", use_container_width=True):
            st.switch_page("pages/02_structure_analyzer.py")


# Load preferences when the script runs (once per session or if not already loaded)
if not st.session_state.preferences_loaded:
    load_field_preferences()
