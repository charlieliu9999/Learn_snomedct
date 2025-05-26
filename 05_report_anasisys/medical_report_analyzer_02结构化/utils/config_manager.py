"""
配置管理模块 - 用于保存和加载应用配置
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器，用于保存和加载应用配置"""
    
    def __init__(self, config_dir=None):
        """
        初始化配置管理器
        
        参数:
            config_dir: 配置文件保存目录，默认为项目根目录
        """
        if config_dir is None:
            # 默认使用项目根目录
            self.config_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        else:
            self.config_dir = Path(config_dir)
        
        # 配置文件路径
        self.config_file = self.config_dir / "user_config.json"
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")
                return {}
        return {}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置到文件
        
        参数:
            config: 配置字典
        
        返回:
            成功返回True，失败返回False
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.config = config
            logger.info(f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config
    
    def update_config(self, key: str, value: Any) -> bool:
        """
        更新配置项
        
        参数:
            key: 配置项键名
            value: 配置项值
        
        返回:
            成功返回True，失败返回False
        """
        try:
            self.config[key] = value
            return self.save_config(self.config)
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置项值
        
        参数:
            key: 配置项键名
            default: 默认值
        
        返回:
            配置项值，如果不存在则返回默认值
        """
        return self.config.get(key, default)


class OllamaManager:
    """Ollama模型管理器，用于获取Ollama可用模型列表"""
    
    def __init__(self, api_base: str = "http://localhost:11434"):
        """
        初始化Ollama管理器
        
        参数:
            api_base: Ollama API基础URL
        """
        self.api_base = api_base
    
    def get_available_models(self) -> List[str]:
        """
        获取Ollama可用模型列表
        
        返回:
            模型名称列表，如果获取失败则返回空列表
        """
        try:
            url = f"{self.api_base}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            
            # 按字母顺序排序
            models.sort()
            
            logger.info(f"获取到 {len(models)} 个Ollama模型")
            return models
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {str(e)}")
            return []
    
    def is_server_running(self) -> bool:
        """
        检查Ollama服务器是否运行
        
        返回:
            如果服务器正在运行则返回True，否则返回False
        """
        try:
            url = f"{self.api_base}/api/version"
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except Exception:
            return False


# 创建全局配置管理器实例
config_manager = ConfigManager()
