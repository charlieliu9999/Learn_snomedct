"""
医学影像报告结构分析工具 - 主应用入口
"""

import streamlit as st
import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置和工具模块
from config import APP_CONFIG, LLM_CONFIG
from utils.llm_client import LLMClient
from utils.state_manager import state_manager
from utils.config_manager import config_manager

# 页面配置
st.set_page_config(
    page_title=APP_CONFIG["app_name"],
    page_icon=APP_CONFIG["app_icon"],
    layout="wide",
    initial_sidebar_state="expanded"
)

# 从配置文件加载用户设置
user_config = config_manager.get_config()

# 初始化会话状态
if "llm_config" not in st.session_state:
    # 如果配置文件中有LLM配置，优先使用配置文件中的设置
    if "llm_config" in user_config and user_config["llm_config"]:
        st.session_state.llm_config = user_config["llm_config"]
        st.info(f"已从配置文件加载 LLM 设置: {st.session_state.llm_config['provider']} - {st.session_state.llm_config['model']}")
    else:
        st.session_state.llm_config = LLM_CONFIG.copy()

# 初始化会话状态
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "raw_data" not in st.session_state:
    st.session_state.raw_data = None

if "processed_data" not in st.session_state:
    st.session_state.processed_data = None

if "llm_client" not in st.session_state:
    # 初始化LLM客户端
    try:
        # 确保使用最新的配置
        st.session_state.llm_client = LLMClient(st.session_state.llm_config)
        st.success(f"初始化LLM客户端成功: {st.session_state.llm_config['provider']} - {st.session_state.llm_config['model']}")
    except Exception as e:
        st.session_state.llm_client = None
        st.error(f"初始化LLM客户端失败: {str(e)}")

# 设置侧边栏
st.sidebar.title("医学影像报告分析工具")
st.sidebar.image("https://img.icons8.com/color/96/000000/medical-doctor.png", width=100)

# 侧边栏菜单
page = st.sidebar.radio(
    "导航",
    ["首页", "数据探索", "结构分析", "关系建模", "报告生成"],
    index=0
)

# 侧边栏状态信息
st.sidebar.markdown("---")
if st.session_state.data_loaded:
    st.sidebar.success(f"✅ 数据已加载: {st.session_state.raw_data.shape[0]} 条报告")
else:
    st.sidebar.warning("⚠️ 尚未加载数据")

if st.session_state.llm_client:
    st.sidebar.success(f"✅ LLM客户端已连接: {st.session_state.llm_config['provider']} - {st.session_state.llm_config['model']}")
else:
    st.sidebar.error("❌ LLM客户端未连接")

# 状态管理部分
st.sidebar.markdown("---")
with st.sidebar.expander("💾 状态管理"):
    # 状态保存
    state_name = st.text_input("状态名称", "my_state", key="state_name")
    state_desc = st.text_input("状态描述", "我的处理状态", key="state_desc")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("保存当前状态"):
            if state_manager.save_state(state_name, state_desc):
                st.success(f"状态 '{state_name}' 保存成功!")
            else:
                st.error("状态保存失败")
    
    # 状态加载
    state_list = state_manager.get_state_list()
    if state_list:
        state_options = [f"{s['name']} ({s['timestamp']})" for s in state_list]
        selected_state = st.selectbox("选择状态", state_options)
        selected_name = selected_state.split(" (")[0] if selected_state else ""
        
        with col2:
            if st.button("加载选中状态"):
                if state_manager.load_state(selected_name):
                    st.success(f"状态 '{selected_name}' 加载成功!")
                    st.experimental_rerun()
                else:
                    st.error("状态加载失败")
        
        # 显示状态描述
        for s in state_list:
            if s["name"] == selected_name:
                st.info(f"描述: {s['description']}\n时间: {s['timestamp']}")
                break
        
        # 删除状态
        if st.button("删除选中状态"):
            if state_manager.delete_state(selected_name):
                st.success(f"状态 '{selected_name}' 删除成功!")
                st.experimental_rerun()
            else:
                st.error("状态删除失败")
    else:
        st.info("暂无保存的状态")

st.sidebar.markdown("---")
st.sidebar.info("💡 提示: 先在「数据探索」页面加载数据")
st.sidebar.markdown("---")
st.sidebar.caption("© 2025 医学影像报告辅助工具")

# 主页内容
if page == "首页":
    st.title("医学影像报告智能分析系统")
    
    # 项目介绍
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 📋 项目概述
        
        本系统旨在通过人工智能技术对医学影像报告进行结构化分析，实现以下目标：
        
        1. **结构化提取**：从自由文本报告中提取结构化信息
        2. **关联分析**：建立影像表现与诊断结论的关联关系
        3. **双向驱动**：支持影像→诊断和诊断→描述两种工作流
        4. **知识累积**：不断积累医学影像诊断知识
        
        ## 🚀 功能模块
        
        - **数据探索**：浏览和分析原始报告数据
        - **结构分析**：提取报告的结构化信息
        - **关系建模**：建立影像-诊断映射关系
        - **报告生成**：基于模型生成标准化报告
        """)
    
    with col2:
        st.markdown("""
        ## 📊 使用流程
        
        1. 加载报告数据
        2. 数据预处理和清洗
        3. 进行结构化分析
        4. 构建关系模型
        5. 生成标准化报告
        
        ## 🔧 技术支持
        
        - 基于大语言模型（LLM）的文本分析
        - 结构化数据提取和处理
        - 知识图谱建模
        - 交互式数据可视化
        """)
    
    # 快速开始
    st.markdown("---")
    st.markdown("## 🏁 快速开始")
    
    quick_start_col1, quick_start_col2, quick_start_col3 = st.columns(3)
    
    with quick_start_col1:
        st.info("### 1. 数据准备")
        st.markdown("""
        - 准备Excel格式的医学影像报告
        - 确保包含「影像表现」和「诊断结论」列
        - 点击左侧导航栏的「数据探索」开始
        """)
    
    with quick_start_col2:
        st.info("### 2. 结构分析")
        st.markdown("""
        - 自动提取报告结构
        - 识别解剖结构和病变特征
        - 构建影像-诊断关联关系
        """)
    
    with quick_start_col3:
        st.info("### 3. 模型应用")
        st.markdown("""
        - 使用双向驱动模式辅助报告撰写
        - 从影像发现推导可能诊断
        - 从诊断生成标准化描述
        """)
    
    # 示例展示
    st.markdown("---")
    st.markdown("## 💡 系统架构")
    
    # 使用更简单的方式显示中文系统架构图
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📊 数据输入层")
        st.info("""
        - Excel报告导入
        - 手动文本输入
        - 批量数据处理
        """)
    
    with col2:
        st.markdown("### 🔍 处理分析层")
        st.info("""
        - 结构化提取
        - 特征识别
        - 关系构建
        """)
    
    with col3:
        st.markdown("### 🧠 模型应用层")
        st.info("""
        - LLM推理
        - 双向驱动
        - 知识图谱
        """)
    
    with col4:
        st.markdown("### 📈 展示交互层")
        st.info("""
        - 可视化图表
        - 结构化报告
        - 辅助诊断
        """)
    
    st.markdown("---")
    st.markdown("### 🛠️ 基础设施层")
    st.success("Streamlit框架 | 数据处理库 | LLM接口 | 配置管理")
    
    st.caption("医学影像报告分析系统架构图（中文版）")
    
    # 数据流程
    st.markdown("---")
    st.markdown("## 🔄 数据流程")
    
    process_col1, process_col2, process_col3, process_col4 = st.columns(4)
    
    with process_col1:
        st.markdown("### 📥 数据输入")
        st.markdown("- 原始报告Excel文件\n- 手动录入的报告文本")
    
    with process_col2:
        st.markdown("### 🔍 特征提取")
        st.markdown("- 解剖结构识别\n- 病变特征提取\n- 诊断信息提取")
    
    with process_col3:
        st.markdown("### 🔗 关系建模")
        st.markdown("- 影像-诊断映射\n- 特征组合分析\n- 诊断规则归纳")
    
    with process_col4:
        st.markdown("### 📤 输出应用")
        st.markdown("- 双向驱动模板\n- 结构化报告生成\n- 辅助诊断推荐")
    
    # 开始使用按钮
    st.markdown("---")
    start_col1, start_col2, start_col3 = st.columns([1, 2, 1])
    
    with start_col2:
        if st.button("开始使用", key="start_button", help="点击开始使用系统", use_container_width=True):
            st.switch_page("pages/01_data_explorer.py")

# 其他页面通过多页面应用实现（位于pages目录）
