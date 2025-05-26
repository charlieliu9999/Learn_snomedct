"""
调试页面 - 用于显示模型的提示词和响应
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和工具模块
import config
from utils.llm_client import LLMClient

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 调试工具",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 LLM调试工具")
st.markdown("用于测试和调试LLM模型的提示词和响应")

# 初始化LLM客户端
if "llm_client" not in st.session_state:
    st.error("LLM客户端未初始化，请先返回首页")
    st.stop()

# 创建表单
with st.form("debug_form"):
    st.subheader("测试提示词")
    
    # 提示词输入
    prompt = st.text_area(
        "输入提示词",
        height=200,
        help="输入要发送给LLM的提示词"
    )
    
    # 系统提示词输入
    system_prompt = st.text_area(
        "系统提示词（可选）",
        height=100,
        help="输入系统提示词，可选"
    )
    
    # 选择输出格式
    output_format = st.radio(
        "输出格式",
        ["文本", "JSON"],
        horizontal=True
    )
    
    # 提交按钮
    submit = st.form_submit_button("发送到LLM")

# 处理提交
if submit:
    with st.spinner("正在处理请求..."):
        try:
            if output_format == "JSON":
                result = st.session_state.llm_client.extract_json(prompt, system_prompt)
                st.subheader("LLM响应（JSON）")
                st.json(result)
            else:
                result = st.session_state.llm_client.generate(prompt, system_prompt)
                st.subheader("LLM响应（文本）")
                st.write(result)
            
            # 显示模型信息
            st.success(f"成功获取响应！使用模型: {st.session_state.llm_client.provider}/{st.session_state.llm_client.model}")
            
        except Exception as e:
            st.error(f"处理请求时出错: {str(e)}")

# 显示当前LLM配置
st.sidebar.subheader("当前LLM配置")
if "llm_config" in st.session_state:
    config_display = st.session_state.llm_config.copy()
    if "api_key" in config_display and config_display["api_key"]:
        config_display["api_key"] = "******"  # 隐藏API密钥
    st.sidebar.json(config_display)

# 测试连接按钮
if st.sidebar.button("测试LLM连接"):
    with st.sidebar.spinner("正在测试连接..."):
        try:
            response = st.session_state.llm_client.generate("请简短回复：你是什么模型？", "你是一个医学影像报告分析助手")
            st.sidebar.success(f"连接测试成功！响应: {response}")
        except Exception as e:
            st.sidebar.error(f"连接测试失败: {str(e)}")

# 提示词示例
st.sidebar.subheader("提示词示例")
example_prompts = {
    "解剖结构提取": """
从以下胸部CT报告文本中提取所有提到的解剖结构，包括器官、组织和位置。

报告文本:
右肺上叶可见一枚约3cm大小的结节状软组织密度影，边缘毛糙，可见毛刺征、分叶征。未见明显钙化。增强后呈轻度不均匀强化。

请按以下JSON格式返回结果:
[
  {"原文": "右肺上叶", "标准名": "right upper lobe", "父结构": "right lung"},
  {"原文": "胸膜", "标准名": "pleura", "父结构": "thoracic cavity"},
  ...
]

仅返回报告中明确提到的解剖结构，不要添加推测的结构。
    """,
    "病变特征提取": """
从以下胸部CT报告文本中提取所有病变特征信息。

报告文本:
右肺上叶可见一枚约3cm大小的结节状软组织密度影，边缘毛糙，可见毛刺征、分叶征。未见明显钙化。增强后呈轻度不均匀强化。

请分析文本中描述的每个病变，提取以下特征：
1. 解剖位置 - 病变所在的具体解剖结构
2. 大小 - 病变的尺寸描述
3. 形态 - 病变的形状特征
4. 密度 - 病变的密度特征
5. 边界 - 病变边界的描述
6. 数量 - 病变的数量
7. 分布 - 病变的分布特征
8. 其他特征 - 其他相关描述

请按以下JSON格式返回结果:
[
  {
    "解剖位置": "右肺上叶",
    "大小": "3cm",
    "形态": "结节状",
    "密度": "软组织密度",
    "边界": "边缘毛糙",
    "数量": "单发",
    "分布": "",
    "其他特征": "可见毛刺征、分叶征，未见明显钙化，增强后呈轻度不均匀强化"
  }
]
    """
}

selected_example = st.sidebar.selectbox("选择示例", list(example_prompts.keys()))
if st.sidebar.button("加载示例"):
    st.experimental_rerun()  # 重新运行页面，但会带上查询参数
