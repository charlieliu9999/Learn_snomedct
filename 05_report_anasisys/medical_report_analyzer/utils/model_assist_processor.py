"""
模型辅助处理器 - 使用LLM模型进行医学术语的标准化和关联
"""

import logging
import json
import hashlib
from typing import Dict, List, Any

from .llm_client import LLMClient
from .medical_terminology import STANDARD_LESION_FEATURES

# 设置日志
logger = logging.getLogger(__name__)

class ModelAssistProcessor:
    """
    模型辅助处理器 - 使用LLM处理医学术语的标准化和关联
    
    特点:
    1. 使用模型进行术语标准化，无需维护大量规则
    2. 内置缓存机制，避免重复处理
    3. 支持解剖结构的智能映射
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化模型辅助处理器
        
        参数:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        # 简单内存缓存
        self.cache = {
            "标准化特征": {},  # {feature_type+text: standardized}
            "位置映射": {}     # {location+structures_hash: mapped_structure}
        }
        self.cache_hits = 0
        self.cache_misses = 0
    
    def standardize_feature(self, feature_text: str, feature_type: str) -> str:
        """
        使用模型标准化单个特征描述
        
        参数:
            feature_text: 特征描述文本
            feature_type: 特征类型(形态、密度、边界等)
            
        返回:
            标准化后的特征描述
        """
        # 生成缓存键
        cache_key = f"{feature_type}:{feature_text}"
        
        # 检查缓存
        if cache_key in self.cache["标准化特征"]:
            self.cache_hits += 1
            return self.cache["标准化特征"][cache_key]
        
        self.cache_misses += 1
        # 准备标准选项
        standard_options = STANDARD_LESION_FEATURES.get(feature_type, [])
        options_str = ", ".join(standard_options) if standard_options else "无标准选项"
        
        # 准备提示词
        prompt = f"""
        请将以下医学影像报告中的"{feature_type}"描述标准化为最匹配的医学标准表达:
        
        原始描述: "{feature_text}"
        
        参考标准表达: [{options_str}]
        
        请直接返回标准化后的表达，不要添加任何解释。如果没有完全匹配的标准表达，
        请返回最接近的一个。如果实在无法匹配，则返回原文。
        """
        
        try:
            # 使用LLM进行标准化
            standardized = self.llm_client.generate(prompt).strip()
            
            # 清理可能的额外引号或空格
            standardized = standardized.strip('"\'').strip()
            
            # 如果返回为空或过长，使用原文
            if not standardized or len(standardized) > len(feature_text) * 2:
                standardized = feature_text
                
            # 缓存结果
            self.cache["标准化特征"][cache_key] = standardized
            return standardized
            
        except Exception as e:
            logger.warning(f"使用模型标准化'{feature_type}'失败: {str(e)}")
            return feature_text  # 失败时返回原文
    
    def standardize_lesion_features(self, lesion: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化单个病变的所有特征
        
        参数:
            lesion: 病变特征字典
            
        返回:
            标准化后的病变特征字典
        """
        standardized = lesion.copy()
        
        # 优先标准化最重要的几个字段
        key_fields = ["形态", "密度", "边界", "强化方式"]
        
        for field in key_fields:
            if field in lesion and lesion[field]:
                standardized[field] = self.standardize_feature(lesion[field], field)
        
        return standardized
    
    def batch_standardize_lesions(self, lesions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量标准化病变特征
        
        参数:
            lesions: 病变特征列表
            
        返回:
            标准化后的病变特征列表
        """
        return [self.standardize_lesion_features(lesion) for lesion in lesions]
    
    def map_location_to_structure(self, location: str, structure_map: Dict[str, Dict[str, Any]]) -> str:
        """
        将描述的解剖位置映射到标准结构
        
        参数:
            location: 解剖位置描述
            structure_map: 解剖结构映射字典
            
        返回:
            映射到的标准结构名称，如果无匹配则返回"其他"
        """
        # 直接匹配
        if location in structure_map:
            return location
        
        # 生成结构映射的哈希值用于缓存
        structures_key = hashlib.md5(json.dumps(structure_map, sort_keys=True).encode()).hexdigest()
        cache_key = f"{location}:{structures_key}"
        
        # 检查缓存
        if cache_key in self.cache["位置映射"]:
            self.cache_hits += 1
            return self.cache["位置映射"][cache_key]
        
        self.cache_misses += 1
        
        # 简单的字符串包含检查（不调用模型的快速方法）
        for structure, info in structure_map.items():
            original_text = info.get("原文", "")
            # 如果位置包含在结构名中，或结构的原文包含在位置中
            if structure in location or (original_text and original_text in location):
                self.cache["位置映射"][cache_key] = structure
                return structure
        
        # 准备结构信息
        structures_info = []
        for name, info in structure_map.items():
            structures_info.append({
                "标准名": name,
                "原文": info.get("原文", ""),
                "父结构": info.get("父结构", "")
            })
        
        # 准备提示词
        prompt = f"""
        请将以下医学影像报告中描述的解剖位置映射到最匹配的标准解剖结构:
        
        描述的位置: "{location}"
        
        可用的标准解剖结构:
        {json.dumps(structures_info, ensure_ascii=False, indent=2)}
        
        请只返回最匹配的标准结构的"标准名"字段值，如果没有合适匹配则返回"其他"。
        不要返回任何解释或其他内容。
        """
        
        try:
            # 调用模型获取映射结果
            result = self.llm_client.generate(prompt).strip()
            # 清理可能的额外引号或空格
            result = result.strip('"\'').strip()
            
            # 验证结果是否在结构图中
            if result in structure_map:
                self.cache["位置映射"][cache_key] = result
                return result
            else:
                self.cache["位置映射"][cache_key] = "其他"
                return "其他"
                
        except Exception as e:
            logger.warning(f"使用模型映射解剖位置失败: {str(e)}")
            self.cache["位置映射"][cache_key] = "其他"
            return "其他"
    
    def map_lesions_to_structures(self, lesions: List[Dict[str, Any]], 
                                structure_map: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        智能映射病变特征到解剖结构
        
        参数:
            lesions: 病变特征列表
            structure_map: 解剖结构映射
            
        返回:
            按解剖结构组织的病变特征字典
        """
        result = {}
        
        for lesion in lesions:
            location = lesion.get("解剖位置", "")
            if not location:
                continue
                
            # 使用模型辅助映射
            mapped_structure = self.map_location_to_structure(location, structure_map)
            
            # 记录映射结果
            if mapped_structure not in result:
                result[mapped_structure] = []
            
            # 复制病变并添加映射信息
            mapped_lesion = lesion.copy()
            mapped_lesion["映射结构"] = mapped_structure
            result[mapped_structure].append(mapped_lesion)
        
        return result
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "标准化特征_缓存大小": len(self.cache["标准化特征"]),
            "位置映射_缓存大小": len(self.cache["位置映射"])
        }
    
    def clear_cache(self):
        """清除缓存"""
        self.cache = {
            "标准化特征": {},
            "位置映射": {}
        }
        self.cache_hits = 0
        self.cache_misses = 0
