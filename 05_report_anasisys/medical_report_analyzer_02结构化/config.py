"""
配置文件，存储应用的全局设置
"""

import os
from pathlib import Path

# 项目路径
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = PROJECT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# 确保必要的目录存在
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# 数据文件配置
DEFAULT_DATA_FILE = "胸部CT报告-0401.xlsx"
DEFAULT_DATA_PATH = Path("/Users/charlieliu/Desktop/华西-报告质控") / DEFAULT_DATA_FILE

# 应用配置
APP_TITLE = "医学影像报告结构分析工具"
APP_DESCRIPTION = "基于大模型的医学报告结构化分析工具"
APP_CONFIG = {
    "app_name": "医学影像报告智能分析系统",
    "app_description": "基于大模型的医学影像报告结构化分析与生成工具",
    "app_icon": "🏥",
    "version": "1.0.0"
}

# LLM配置 
# 默认使用免费模型，可根据需要替换为其他模型
LLM_CONFIG = {
    "provider": "openai",  # 大模型提供商
    "model": "gpt-3.5-turbo",  # 模型名称
    "temperature": 0.2,  # 温度参数
    "max_tokens": 2000,  # 最大输出标记数
    "api_base": "",  # API基础URL，默认空字符串表示使用默认URL
    "api_key": "",  # 请在环境变量中设置，不要硬编码
}

# 支持的模型列表
SUPPORTED_PROVIDERS = [
    {"name": "OpenAI", "value": "openai", "requires_key": True},
    {"name": "Ollama", "value": "ollama", "requires_key": False}
]

# OpenAI模型列表
OPENAI_MODELS = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-turbo"
]

# Ollama模型列表
OLLAMA_MODELS = [
    "qwen2.5:14b",
    "llama3:8b",
    "llama3:70b",
    "mistral:7b",
    "gemma:7b"
]

# 定义常见的胸部CT解剖结构
CHEST_ANATOMY = [
    "胸廓", "胸膜", "右肺上叶", "右肺中叶", "右肺下叶", 
    "左肺上叶", "左肺下叶", "气管", "支气管", 
    "肺门", "纵隔", "心脏", "心包", "主动脉", 
    "食道", "胸腔积液"
]

# 病变特征列表
LESION_FEATURES = {
    "位置": ["中央型", "周围型", "肺门", "纵隔", "胸膜下"],
    "大小": ["毫米", "厘米"],
    "密度": ["低密度", "等密度", "高密度", "钙化", "脂肪密度"],
    "形态": ["结节状", "肿块", "团片状", "条索状", "蜂窝状", "磨玻璃"],
    "边界": ["光整", "毛刺", "分叶", "模糊", "清晰"],
    "强化方式": ["轻度强化", "中度强化", "明显强化", "环形强化", "不均匀强化"]
}

# 常见诊断
COMMON_DIAGNOSES = [
    "肺炎", "肺结核", "肺癌", "转移瘤", "肺气肿", 
    "支气管扩张", "胸腔积液", "胸膜炎", "纵隔肿瘤",
    "淋巴结肿大", "肺不张", "肺纤维化"
]
