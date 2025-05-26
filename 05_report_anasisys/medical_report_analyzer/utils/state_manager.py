"""
状态管理模块 - 用于保存和恢复应用状态
"""

import os
import json
import pickle
import pandas as pd
from pathlib import Path
import streamlit as st
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StateManager:
    """状态管理器，用于保存和恢复应用状态"""
    
    def __init__(self, state_dir=None):
        """
        初始化状态管理器
        
        参数:
            state_dir: 状态文件保存目录，默认为项目根目录下的states文件夹
        """
        if state_dir is None:
            # 默认使用项目根目录下的states文件夹
            self.state_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "states"
        else:
            self.state_dir = Path(state_dir)
        
        # 确保状态目录存在
        os.makedirs(self.state_dir, exist_ok=True)
        
        # 初始化状态列表
        self.states = self._load_state_list()
    
    def _load_state_list(self):
        """加载状态列表"""
        state_list_path = self.state_dir / "state_list.json"
        if os.path.exists(state_list_path):
            try:
                with open(state_list_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载状态列表失败: {str(e)}")
                return []
        return []
    
    def _save_state_list(self):
        """保存状态列表"""
        state_list_path = self.state_dir / "state_list.json"
        try:
            with open(state_list_path, 'w', encoding='utf-8') as f:
                json.dump(self.states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态列表失败: {str(e)}")
    
    def save_state(self, name, description=""):
        """
        保存当前会话状态
        
        参数:
            name: 状态名称
            description: 状态描述
        
        返回:
            成功返回True，失败返回False
        """
        try:
            # 创建状态数据
            state_data = {}
            
            # 保存会话状态变量
            for key in st.session_state:
                # 跳过大型对象和不可序列化的对象
                if key in ['llm_client']:
                    continue
                
                value = st.session_state[key]
                
                # 处理DataFrame
                if isinstance(value, pd.DataFrame):
                    # 将DataFrame保存为单独的文件
                    df_path = self.state_dir / f"{name}_{key}.pkl"
                    value.to_pickle(df_path)
                    state_data[key] = f"{name}_{key}.pkl"
                else:
                    # 尝试直接保存其他类型的数据
                    try:
                        # 检查是否可以JSON序列化
                        json.dumps(value)
                        state_data[key] = value
                    except (TypeError, OverflowError):
                        # 如果不能JSON序列化，尝试使用pickle
                        try:
                            pickle_path = self.state_dir / f"{name}_{key}.pkl"
                            with open(pickle_path, 'wb') as f:
                                pickle.dump(value, f)
                            state_data[key] = f"{name}_{key}.pkl"
                        except Exception as e:
                            logger.warning(f"无法保存状态变量 {key}: {str(e)}")
            
            # 保存状态数据
            state_path = self.state_dir / f"{name}.json"
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            # 更新状态列表
            timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            state_info = {
                "name": name,
                "description": description,
                "timestamp": timestamp,
                "path": str(state_path)
            }
            
            # 检查是否已存在同名状态
            for i, state in enumerate(self.states):
                if state["name"] == name:
                    self.states[i] = state_info
                    break
            else:
                self.states.append(state_info)
            
            # 保存状态列表
            self._save_state_list()
            
            logger.info(f"成功保存状态: {name}")
            return True
        
        except Exception as e:
            logger.error(f"保存状态失败: {str(e)}")
            return False
    
    def load_state(self, name):
        """
        加载指定状态
        
        参数:
            name: 状态名称
        
        返回:
            成功返回True，失败返回False
        """
        try:
            # 加载状态数据
            state_path = self.state_dir / f"{name}.json"
            if not os.path.exists(state_path):
                logger.error(f"状态文件不存在: {state_path}")
                return False
            
            with open(state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # 恢复会话状态变量
            for key, value in state_data.items():
                if isinstance(value, str) and value.endswith('.pkl'):
                    # 加载DataFrame或pickle对象
                    pkl_path = self.state_dir / value
                    if os.path.exists(pkl_path):
                        try:
                            # 尝试作为DataFrame加载
                            st.session_state[key] = pd.read_pickle(pkl_path)
                        except Exception:
                            # 如果不是DataFrame，尝试作为普通pickle对象加载
                            with open(pkl_path, 'rb') as f:
                                st.session_state[key] = pickle.load(f)
                else:
                    # 直接恢复其他类型的数据
                    st.session_state[key] = value
            
            logger.info(f"成功加载状态: {name}")
            return True
        
        except Exception as e:
            logger.error(f"加载状态失败: {str(e)}")
            return False
    
    def delete_state(self, name):
        """
        删除指定状态
        
        参数:
            name: 状态名称
        
        返回:
            成功返回True，失败返回False
        """
        try:
            # 删除状态文件
            state_path = self.state_dir / f"{name}.json"
            if os.path.exists(state_path):
                os.remove(state_path)
            
            # 删除相关的pickle文件
            for file in os.listdir(self.state_dir):
                if file.startswith(f"{name}_") and file.endswith(".pkl"):
                    os.remove(self.state_dir / file)
            
            # 更新状态列表
            self.states = [state for state in self.states if state["name"] != name]
            self._save_state_list()
            
            logger.info(f"成功删除状态: {name}")
            return True
        
        except Exception as e:
            logger.error(f"删除状态失败: {str(e)}")
            return False
    
    def get_state_list(self):
        """获取状态列表"""
        return self.states
    
    def state_exists(self, name):
        """检查状态是否存在"""
        return any(state["name"] == name for state in self.states)

# 创建全局状态管理器实例
state_manager = StateManager()
