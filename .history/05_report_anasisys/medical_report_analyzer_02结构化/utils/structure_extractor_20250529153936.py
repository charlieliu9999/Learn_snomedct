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