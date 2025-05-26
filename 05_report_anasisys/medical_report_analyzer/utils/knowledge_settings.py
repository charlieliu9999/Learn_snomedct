"""
知识库设置管理模块
"""

import os
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeSettings:
    """知识库设置管理器"""
    
    def __init__(self):
        """初始化知识库设置管理器"""
        # 确定设置文件路径
        base_dir = Path(__file__).parent.parent / "data" / "knowledge"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = base_dir / "knowledge_settings.json"
        
        # 默认设置
        self.default_settings = {
            "auto_update": True,  # 默认自动更新知识库
            "quality_threshold": 0.7,  # 质量阈值，低于此值的结果不会被纳入知识库
            "max_entries_per_category": 1000  # 每个类别的最大条目数
        }
        
        # 加载设置
        self.settings = self._load_settings()
        
    def _load_settings(self):
        """加载设置"""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                # 合并用户设置和默认设置
                settings = self.default_settings.copy()
                settings.update(user_settings)
                return settings
            else:
                # 如果设置文件不存在，创建一个默认设置文件
                self._save_settings(self.default_settings)
                return self.default_settings
        except Exception as e:
            logger.error(f"加载知识库设置出错: {str(e)}")
            return self.default_settings
    
    def _save_settings(self, settings):
        """保存设置"""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logger.info(f"知识库设置已保存到: {self.settings_path}")
        except Exception as e:
            logger.error(f"保存知识库设置出错: {str(e)}")
    
    def get(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """设置值"""
        self.settings[key] = value
        self._save_settings(self.settings)
        
    def update(self, new_settings):
        """批量更新设置"""
        self.settings.update(new_settings)
        self._save_settings(self.settings)
        
    def should_update_knowledge_base(self, result_quality=1.0):
        """
        判断是否应该更新知识库
        
        参数:
            result_quality: 结果质量评分(0-1)，默认为1.0
            
        返回:
            布尔值，是否应该更新
        """
        if not self.get("auto_update", True):
            return False
            
        quality_threshold = self.get("quality_threshold", 0.7)
        if result_quality < quality_threshold:
            return False
            
        return True

# 创建全局实例
knowledge_settings = KnowledgeSettings()