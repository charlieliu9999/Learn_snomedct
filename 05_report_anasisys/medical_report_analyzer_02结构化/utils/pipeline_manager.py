"""
数据流水线管理模块 - 提供统一的数据处理流程管理
"""

import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, List, Any, Optional, Callable

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineManager:
    """数据流水线管理器"""
    
    def __init__(self):
        """初始化流水线管理器"""
        self.pipeline_steps = [
            "数据结构化", 
            "关系建模", 
            "知识图谱构建", 
            "Neo4j存储", 
            "模板生成"
        ]
        
        # 初始化会话状态
        if "pipeline_state" not in st.session_state:
            st.session_state.pipeline_state = {
                "current_step": 0,
                "completed_steps": [],
                "step_data": {},
                "step_status": {}
            }
    
    def display_pipeline_view(self):
        """显示数据流水线进度视图"""
        st.markdown("### 数据处理流水线")
        
        # 获取当前状态
        current_step = st.session_state.pipeline_state["current_step"]
        completed_steps = st.session_state.pipeline_state["completed_steps"]
        step_status = st.session_state.pipeline_state["step_status"]
        
        # 创建列布局
        cols = st.columns(len(self.pipeline_steps))
        
        # 显示每个步骤的状态
        for i, step in enumerate(self.pipeline_steps):
            with cols[i]:
                if step in completed_steps:
                    st.success(step)
                elif i == current_step:
                    st.info(f"**{step}** ⟵")
                else:
                    st.text(step)
                
                # 显示步骤状态(如果有)
                if step in step_status:
                    status_text = step_status[step]
                    st.caption(status_text)
    
    def update_step(self, step_index: int, completed: bool = False, status: str = ""):
        """
        更新流水线步骤状态
        
        参数:
            step_index: 步骤索引
            completed: 是否已完成
            status: 状态描述
        """
        # 更新当前步骤
        st.session_state.pipeline_state["current_step"] = step_index
        
        # 更新步骤状态
        step_name = self.pipeline_steps[step_index]
        st.session_state.pipeline_state["step_status"][step_name] = status
        
        # 如果已完成，添加到已完成列表
        if completed and step_name not in st.session_state.pipeline_state["completed_steps"]:
            st.session_state.pipeline_state["completed_steps"].append(step_name)
    
    def store_step_data(self, step_name: str, data: Any):
        """
        存储步骤数据
        
        参数:
            step_name: 步骤名称
            data: 步骤数据
        """
        st.session_state.pipeline_state["step_data"][step_name] = data
    
    def get_step_data(self, step_name: str) -> Any:
        """
        获取步骤数据
        
        参数:
            step_name: 步骤名称
            
        返回:
            步骤数据
        """
        return st.session_state.pipeline_state["step_data"].get(step_name)
    
    def run_pipeline(self, 
                    steps: List[Dict[str, Any]], 
                    on_complete: Optional[Callable] = None):
        """
        执行完整流水线
        
        参数:
            steps: 步骤列表，每个步骤包含名称和执行函数
            on_complete: 完成后的回调函数
        """
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(steps):
            step_name = step.get("name", f"步骤{i+1}")
            step_func = step.get("function")
            
            if not step_func or not callable(step_func):
                logger.warning(f"步骤 {step_name} 没有可执行的函数")
                continue
            
            # 更新状态
            status_text.markdown(f"**执行: {step_name}**")
            
            # 执行步骤
            try:
                result = step_func()
                
                # 存储结果
                if "store_as" in step:
                    self.store_step_data(step["store_as"], result)
                
                # 更新进度
                progress_bar.progress((i+1)/len(steps))
                
            except Exception as e:
                logger.error(f"执行步骤 {step_name} 失败: {str(e)}")
                status_text.error(f"步骤 {step_name} 失败: {str(e)}")
                return False
        
        # 全部完成
        status_text.success("完整流水线执行完毕")
        
        # 调用完成回调
        if on_complete and callable(on_complete):
            on_complete()
            
        return True
    
    def display_data_dependencies(self, dependencies: Dict[str, Dict[str, Any]]):
        """
        显示数据依赖关系
        
        参数:
            dependencies: 依赖关系字典
        """
        st.markdown("### 数据依赖关系")
        
        # 显示依赖图
        dependency_graph = " → ".join(dependencies.keys())
        st.code(dependency_graph)
        
        # 显示每个依赖项的状态
        for name, info in dependencies.items():
            status = info.get("status", "未知")
            details = info.get("details", "")
            
            if status == "已加载":
                st.success(f"{name}: {status} {details}")
            elif status == "未加载":
                st.warning(f"{name}: {status} {details}")
            else:
                st.info(f"{name}: {status} {details}")
