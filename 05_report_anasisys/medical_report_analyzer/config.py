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
# 使用Ollama的qwen2.5:14b模型进行中文处理
LLM_CONFIG = {
    "provider": "ollama",  # 大模型提供商
    "model": "qwen2.5:14b",  # 模型名称
    "temperature": 0.2,  # 温度参数
    "max_tokens": 2000,  # 最大输出标记数
    "api_base": "http://localhost:11434",  # Ollama默认地址
    "api_key": "",  # Ollama不需要API密钥
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

# 数据列名映射配置 - 支持多种不同的列名格式
COLUMN_MAPPINGS = {
    # 影像表现列的可能名称映射
    "影像表现": [
        "影像表现", "影像所见", "检查所见", "影像发现", "检查发现", 
        "findings", "finding", "image findings", "radiologic findings",
        "所见", "表现", "observation"
    ],
    # 诊断结论列的可能名称映射
    "诊断结论": [
        "诊断结论", "诊断意见", "影像诊断", "诊断", "印象",
        "impression", "diagnosis", "conclusion", "radiology diagnosis",
        "意见", "结论"
    ]
}

# 处理流程配置
PROCESSING_CONFIG = {
    # 结构化过程配置
    "structuring": {
        "enabled": True,
        "max_text_length": 2000,  # 单次处理的最大文本长度
        "process_long_reports": True  # 是否分段处理长报告
    },
    
    # 解剖结构关系配置
    "anatomical_relations": {
        "enabled": True,
        "use_knowledge_base": True,  # 是否使用知识库辅助构建关系
        "build_structure_tree": True  # 是否构建解剖结构树
    },
    
    # 诊断关联配置
    "diagnosis_association": {
        "enabled": True,
        "min_association_score": 0.3,  # 最低关联强度阈值
        "cache_enabled": True,  # 是否启用缓存
        "show_visualization": True  # 是否显示可视化图表
    },
    
    # 知识库配置
    "knowledge_base": {
        "auto_update": True,  # 是否自动更新知识库
        "min_quality_score": 0.6  # 知识库更新的最低质量分数
    },
    
    # 报告生成配置
    "report_generation": {
        "enabled": True,
        "include_associations": True,  # 是否在报告中包含关联信息
        "format": "markdown"  # 报告格式(markdown/html/text)
    }
}
