"""
统一知识图谱流水线 - 整合关系建模和知识图谱功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json
import time
from pathlib import Path
import matplotlib.pyplot as plt

# 导入自定义模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.relationship_builder import RelationshipBuilder
from utils.pipeline_manager import PipelineManager
from pages.knowledge_graph_mode import display_knowledge_graph_ui

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 知识图谱流水线",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 医学知识图谱流水线")
st.markdown("整合影像-诊断关系建模、知识图谱构建和查询功能的统一流水线")
