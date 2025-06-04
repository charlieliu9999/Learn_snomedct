"""
结构提取器模块，负责从医学报告中提取结构化信息
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional

from .llm_client import LLMClient
from .prompt_templates import PromptTemplateManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def __init__(self, llm_client: LLMClient):
    """
    初始化结构提取器
    
    参数:
        llm_client: LLM客户端实例
    """
    self.llm_client = llm_client
    self.status_callback = None  # 状态回调函数
    
    # 添加提示词模板管理器
    self.prompt_manager = PromptTemplateManager()
    
    # 添加简单缓存
    self.cache = {}
    self.debug_info = {}
    
    # 默认报告类型
    self.report_type = "default"