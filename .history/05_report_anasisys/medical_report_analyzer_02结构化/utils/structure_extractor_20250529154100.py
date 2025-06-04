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

    def detect_report_type(self, report_text: str) -> str:
        """
        检测报告类型
        
        参数:
            report_text: 报告文本
        
        返回:
            报告类型 (胸部CT, 腹部超声, 等)
        """
        # 简单的关键词匹配规则
        report_text_lower = report_text.lower()
        
        if "ct" in report_text_lower and ("胸" in report_text or "肺" in report_text):
            return "胸部CT"
        elif "超声" in report_text_lower and ("腹" in report_text or "肝" in report_text or "胆" in report_text):
            return "腹部超声"
        elif "mri" in report_text_lower:
            return "MRI"
        
        # 默认返回通用类型
        return "default"
def _get_cache_key(self, text: str) -> str:
    """
    生成缓存键
    
    参数:
        text: 文本内容
    
    返回:
        缓存键
    """
    # 使用MD5哈希作为缓存键
    return hashlib.md5(text.encode('utf-8')).hexdigest()

    def extract_anatomical_structures(self, report_text: str) -> List[Dict[str, str]]:
        """
        从报告文本中提取解剖结构
        
        参数:
            report_text: 报告文本
        
        返回:
            解剖结构列表，每个结构包含原文、标准名称和父结构
        """
        # 检查缓存
        cache_key = self._get_cache_key(f"anatomical_{report_text}")
        if cache_key in self.cache:
            logger.info("使用缓存的解剖结构提取结果")
            return self.cache[cache_key]
        
        # 检测报告类型
        report_type = self.detect_report_type(report_text)
        
        # 使用模板管理器获取提示词
        prompt = self.prompt_manager.get_prompt(
            "anatomical", 
            report_type, 
            report_text=report_text
        )
        
        # 保存提示词用于调试
        self.debug_info["解剖结构_提示词"] = prompt
        self.debug_info["解剖结构_报告类型"] = report_type
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["解剖结构_响应"] = result
            
            if isinstance(result, list):
                # 保存到缓存
                self.cache[cache_key] = result
                return result
            elif isinstance(result, dict) and "error" in result:
                logger.error(f"提取解剖结构失败: {result['error']}")
                return []
            else:
                return []
        except Exception as e:
            logger.error(f"提取解剖结构时发生错误: {str(e)}")
            self.debug_info["解剖结构_错误"] = str(e)
            return []

def extract_anatomical_structures(self, report_text: str) -> List[Dict[str, str]]:
    """
    从报告文本中提取解剖结构
    
    参数:
        report_text: 报告文本
    
    返回:
        解剖结构列表，每个结构包含原文、标准名称和父结构
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"anatomical_{report_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的解剖结构提取结果")
        return self.cache[cache_key]
    
    # 检测报告类型
    report_type = self.detect_report_type(report_text)
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "anatomical", 
        report_type, 
        report_text=report_text
    )
    
    # 保存提示词用于调试
    self.debug_info["解剖结构_提示词"] = prompt
    self.debug_info["解剖结构_报告类型"] = report_type
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["解剖结构_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"提取解剖结构失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"提取解剖结构时发生错误: {str(e)}")
        self.debug_info["解剖结构_错误"] = str(e)
        return []
def extract_lesion_features(self, report_text: str) -> List[Dict[str, Any]]:
    """
    从报告文本中提取病变特征
    
    参数:
        report_text: 报告文本
    
    返回:
        病变特征列表，每个病变包含位置、大小、形态等信息
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"lesion_{report_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的病变特征提取结果")
        return self.cache[cache_key]
    
    # 检测报告类型
    report_type = self.detect_report_type(report_text)
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "lesion", 
        report_type, 
        report_text=report_text
    )
    
    # 保存提示词用于调试
    self.debug_info["病变特征_提示词"] = prompt
    self.debug_info["病变特征_报告类型"] = report_type
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["病变特征_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"提取病变特征失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"提取病变特征时发生错误: {str(e)}")
        self.debug_info["病变特征_错误"] = str(e)
        return []

def extract_diagnoses(self, diagnosis_text: str) -> List[Dict[str, str]]:
    """
    从诊断结论文本中提取诊断信息
    
    参数:
        diagnosis_text: 诊断结论文本
    
    返回:
        诊断信息列表，每个诊断包含类型和描述
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"diagnosis_{diagnosis_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的诊断信息提取结果")
        return self.cache[cache_key]
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "diagnosis", 
        "default", 
        diagnosis_text=diagnosis_text
    )
    
    # 保存提示词用于调试
    self.debug_info["诊断信息_提示词"] = prompt
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["诊断信息_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"提取诊断信息失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"提取诊断信息时发生错误: {str(e)}")
        self.debug_info["诊断信息_错误"] = str(e)
        return []

def build_image_diagnosis_mapping(self, image_text: str, diagnosis_text: str,
                                 anatomical_structures: Optional[List] = None,
                                 lesion_features: Optional[List] = None,
                                 diagnoses: Optional[List] = None) -> List[Dict[str, str]]:
    """
    构建影像表现与诊断结论之间的映射关系
    
    参数:
        image_text: 影像表现文本
        diagnosis_text: 诊断结论文本
        anatomical_structures: 已提取的解剖结构（可选）
        lesion_features: 已提取的病变特征（可选）
        diagnoses: 已提取的诊断信息（可选）
    
    返回:
        影像表现与诊断结论的映射关系
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"mapping_{image_text}_{diagnosis_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的影像诊断映射结果")
        return self.cache[cache_key]
    
    # 准备已提取的结构化信息
    extracted_info = ""
    if anatomical_structures:
        extracted_info += f"已提取的解剖结构: {json.dumps(anatomical_structures, ensure_ascii=False)}\n\n"
    if lesion_features:
        extracted_info += f"已提取的病变特征: {json.dumps(lesion_features, ensure_ascii=False)}\n\n"
    if diagnoses:
        extracted_info += f"已提取的诊断信息: {json.dumps(diagnoses, ensure_ascii=False)}\n\n"
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "mapping", 
        "default", 
        image_text=image_text,
        diagnosis_text=diagnosis_text,
        extracted_info=extracted_info
    )
    
    # 保存提示词用于调试
    self.debug_info["影像诊断映射_提示词"] = prompt
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["影像诊断映射_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"构建影像诊断映射失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"构建影像诊断映射时发生错误: {str(e)}")
        self.debug_info["影像诊断映射_错误"] = str(e)
        return []
