"""
结构提取器模块，负责从医学报告中提取结构化信息
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable

from .llm_client import LLMClient
from .prompt_templates import PromptTemplateManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructureExtractor:
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

    def analyze_single_report(self, report_text: str, diagnosis_text: str = "") -> Dict[str, Any]:
        """
        分析单份医学影像报告
        
        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本
            
        返回:
            包含结构化数据和分析信息的字典
        """
        logger.info(f"开始分析单份报告：{report_text[:30]}...，诊断：{diagnosis_text[:30]}...")
        
        try:
            # 提取结构化数据
            logger.info("调用extract_report_structure开始提取结构化数据")
            structured_data = self.extract_report_structure(report_text, diagnosis_text)
            logger.info(f"extract_report_structure返回结果类型: {type(structured_data)}")
            
            # 组织返回结果
            result = {
                "结构化数据": {
                    "解剖结构": structured_data.get("解剖结构", []),
                    "病变特征": structured_data.get("病变特征", []),
                    "诊断信息": structured_data.get("诊断信息", []),
                    "影像诊断映射": structured_data.get("映射关系", [])
                },
                "原始文本": {
                    "影像表现": report_text,
                    "诊断结论": diagnosis_text
                },
                "分析信息": {
                    "处理时间": structured_data.get("处理时间", ""),
                    "处理状态": "成功"
                }
            }
            
            # 如果有调试信息，添加到结果中
            if "调试信息" in structured_data:
                result["调试信息"] = structured_data["调试信息"]
                
            logger.info(f"单份报告分析完成，结果: {result.keys()}")
            # 打印更详细的结果信息
            logger.info(f"解剖结构数量: {len(result['结构化数据']['解剖结构'])}")
            logger.info(f"病变特征数量: {len(result['结构化数据']['病变特征'])}")
            logger.info(f"诊断信息数量: {len(result['结构化数据']['诊断信息'])}")
            logger.info(f"影像诊断映射数量: {len(result['结构化数据']['影像诊断映射'])}")
            return result
            
        except Exception as e:
            logger.error(f"单份报告分析失败: {str(e)}")
            # 返回错误信息
            return {
                "原始文本": {
                    "影像表现": report_text,
                    "诊断结论": diagnosis_text
                },
                "分析信息": {
                    "处理状态": "失败"
                },
                "分析错误": str(e)
            }

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
        logger.info("开始提取解剖结构")
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
            # 调用LLM进行提取
            logger.info("调用LLM进行解剖结构提取")
            result = self.llm_client.extract_json(prompt)
            logger.info(f"LLM返回结果类型: {type(result)}")
            
            # 提取结构列表 - 处理多种格式
            if isinstance(result, dict) and "解剖结构" in result:
                structures = result["解剖结构"]
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "原文" in result[0]:
                # 如果直接返回了解剖结构列表
                structures = result
                logger.info(f"兼容处理：直接从列表提取解剖结构，找到 {len(structures)} 个结构")
            else:
                logger.warning(f"解剖结构提取结果格式错误: {result}")
                return []
                
            # 保存到缓存
            self.cache[cache_key] = structures
            return structures
                
        except Exception as e:
            logger.error(f"解剖结构提取失败: {str(e)}")
            return []
            
    def extract_lesion_features(self, report_text: str, structures: List[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        从报告文本中提取病变特征
        
        参数:
            report_text: 报告文本
            structures: 可选的解剖结构列表，如果提供，将提高提取质量
            
        返回:
            病变特征列表
        """
        # 检查缓存
        cache_key = self._get_cache_key(f"lesion_{report_text}")
        if cache_key in self.cache:
            logger.info("使用缓存的病变特征提取结果")
            return self.cache[cache_key]
            
        # 检测报告类型
        report_type = self.detect_report_type(report_text)
        
        # 构建提示词
        prompt_args = {
            "report_text": report_text
        }
        
        # 如果有解剖结构，添加到提示词中
        if structures:
            prompt_args["structures"] = json.dumps(structures, ensure_ascii=False)
            
        # 获取提示词
        prompt = self.prompt_manager.get_prompt(
            "lesion",
            report_type,
            **prompt_args
        )
        
        # 保存提示词用于调试
        self.debug_info["病变特征_提示词"] = prompt
        
        try:
            # 调用LLM进行提取
            result = self.llm_client.extract_json(prompt)
            
            # 提取特征列表 - 增加格式兼容性处理并改进结构
            if isinstance(result, dict):
                if "病变特征" in result:
                    features = result["病变特征"]
                elif "病变" in result:  # 兼容"病变"字段
                    raw_features = result["病变"]
                    logger.info(f"兼容处理：从'病变'字段提取特征，找到 {len(raw_features)} 个特征")
                    
                    # 改进病变特征的结构，添加名称字段
                    features = []
                    for i, feature in enumerate(raw_features):
                        # 根据解剖位置和特性生成名称
                        name = ""
                        if "\u89e3\u5256\u4f4d\u7f6e" in feature and feature["\u89e3\u5256\u4f4d\u7f6e"]:
                            name += feature["\u89e3\u5256\u4f4d\u7f6e"]
                        if "\u7279\u6027" in feature and feature["\u7279\u6027"]:
                            if name: name += "-"
                            name += feature["\u7279\u6027"]
                        if not name:
                            name = f"病变{i+1}"
                            
                        # 创建新结构
                        new_feature = {
                            "名称": name,
                            "特征": feature
                        }
                        features.append(new_feature)
                    
                    logger.info(f"结构化后共 {len(features)} 个病变特征")
                else:
                    logger.warning(f"病变特征提取结果格式错误: {result}")
                    return []
                
                # 保存到缓存
                self.cache[cache_key] = features
                return features
            else:
                logger.warning(f"病变特征提取结果格式错误，不是字典类型: {result}")
                return []
                
        except Exception as e:
            logger.error(f"病变特征提取失败: {str(e)}")
            return []
            
    def extract_diagnosis_info(self, diagnosis_text: str) -> List[Dict[str, str]]:
        """
        从诊断结论中提取诊断信息
        
        参数:
            diagnosis_text: 诊断结论文本
            
        返回:
            诊断信息列表
        """
        # 检查缓存
        cache_key = self._get_cache_key(f"diagnosis_{diagnosis_text}")
        if cache_key in self.cache:
            logger.info("使用缓存的诊断信息提取结果")
            return self.cache[cache_key]
            
        # 如果诊断文本为空，返回空列表
        if not diagnosis_text or diagnosis_text.strip() == "":
            logger.warning("诊断文本为空，跳过提取")
            return []
            
        # 使用通用诊断提示词
        prompt = self.prompt_manager.get_prompt(
            "diagnosis",
            "default",
            diagnosis_text=diagnosis_text
        )
        
        # 保存提示词用于调试
        self.debug_info["诊断信息_提示词"] = prompt
        
        try:
            # 调用LLM进行提取
            result = self.llm_client.extract_json(prompt)
            
            # 提取诊断列表 - 增加格式兼容性处理
            if isinstance(result, dict) and "诊断信息" in result:
                diagnoses = result["诊断信息"]
            elif isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):  # 直接返回了列表
                diagnoses = result
                logger.info(f"兼容处理：直接从列表提取诊断，找到 {len(diagnoses)} 个诊断")
            else:
                logger.warning(f"诊断信息提取结果格式错误: {result}")
                return []
                
            # 保存到缓存
            self.cache[cache_key] = diagnoses
            return diagnoses
                
        except Exception as e:
            logger.error(f"诊断信息提取失败: {str(e)}")
            return []
            
    def map_findings_to_diagnosis(self, 
                                structures: List[Dict[str, str]], 
                                features: List[Dict[str, Any]],
                                diagnoses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        将影像发现映射到诊断结论
        
        参数:
            structures: 解剖结构列表
            features: 病变特征列表
            diagnoses: 诊断信息列表
            
        返回:
            映射关系列表
        """
        # 如果任一输入为空，返回空列表
        if not structures or not features or not diagnoses:
            logger.warning("影像发现或诊断为空，无法建立映射")
            return []
            
        # 构建提示词
        prompt = self.prompt_manager.get_prompt(
            "mapping",
            "default",
            structures=json.dumps(structures, ensure_ascii=False),
            features=json.dumps(features, ensure_ascii=False),
            diagnoses=json.dumps(diagnoses, ensure_ascii=False)
        )
        
        # 保存提示词用于调试
        self.debug_info["影像诊断映射_提示词"] = prompt
        
        try:
            # 调用LLM进行映射
            result = self.llm_client.extract_json(prompt)
            
            # 提取映射列表 - 增加格式兼容性处理
            if isinstance(result, dict) and "映射关系" in result:
                mappings = result["映射关系"]
                return mappings
            elif isinstance(result, list):
                # 如果返回的是示例格式，则自动生成有意义的映射
                if len(result) == 1 and '影像发现' in result[0] and result[0]['影像发现'] == '具体影像表现描述':
                    logger.info("检测到示例格式，自动生成映射关系")
                    
                    # 生成影像发现和诊断的映射关系
                    mappings = self._generate_mappings(structures, features, diagnoses)
                    logger.info(f"自动生成了 {len(mappings)} 个映射关系")
                    return mappings
                # 对于正常的列表结果，直接返回
                elif len(result) > 0 and isinstance(result[0], dict):
                    # 验证是否是有效的映射关系
                    valid_mappings = []
                    for mapping in result:
                        if '影像发现' in mapping and '对应诊断' in mapping:
                            valid_mappings.append(mapping)
                    
                    if valid_mappings:
                        logger.info(f"兼容处理：直接从列表提取映射关系，找到 {len(valid_mappings)} 个有效映射")
                        return valid_mappings
            
            # 如果没有找到有效映射，自动生成
            logger.warning(f"影像诊断映射结果格式错误，尝试自动生成: {result}")
            mappings = self._generate_mappings(structures, features, diagnoses)
            logger.info(f"自动生成了 {len(mappings)} 个映射关系")
            return mappings
                
        except Exception as e:
            logger.error(f"影像诊断映射失败: {str(e)}")
            return []
            
    def extract_report_structure(self, report_text: str, diagnosis_text: str = "") -> Dict[str, Any]:
        """
        从报告中提取完整的结构化信息
        
        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本
            
        返回:
            结构化报告数据
        """
        start_time = time.time()
        result = {
            "解剖结构": [],
            "病变特征": [],
            "诊断信息": [],
            "映射关系": [],
            "调试信息": {}
        }
        
        try:
            # 提取解剖结构
            if self.status_callback:
                self.status_callback("提取解剖结构", 1)
                
            structures = self.extract_anatomical_structures(report_text)
            result["解剖结构"] = structures
            
            # 提取病变特征
            if self.status_callback:
                self.status_callback("提取病变特征", 2)
                
            features = self.extract_lesion_features(report_text, structures)
            result["病变特征"] = features
            
            # 提取诊断信息
            if diagnosis_text:
                if self.status_callback:
                    self.status_callback("提取诊断信息", 3)
                    
                diagnoses = self.extract_diagnosis_info(diagnosis_text)
                result["诊断信息"] = diagnoses
                
                # 建立映射关系
                if structures and features and diagnoses:
                    if self.status_callback:
                        self.status_callback("建立映射关系", 4)
                        
                    mappings = self.map_findings_to_diagnosis(structures, features, diagnoses)
                    result["映射关系"] = mappings
            
            # 添加调试信息
            result["调试信息"] = self.debug_info
            
            # 添加性能指标
            end_time = time.time()
            result["处理时间"] = f"{end_time - start_time:.2f}秒"
            
            return result
            
        except Exception as e:
            logger.error(f"结构化提取过程出错: {str(e)}")
            
            # 添加错误信息
            result["错误信息"] = str(e)
            result["调试信息"] = self.debug_info
            
            return result
            
    def _generate_mappings(self, structures: List[Dict[str, str]], features: List[Dict[str, Any]], diagnoses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        自动生成影像发现和诊断的映射关系
        
        参数:
            structures: 解剖结构列表
            features: 病变特征列表
            diagnoses: 诊断信息列表
            
        返回:
            映射关系列表
        """
        mappings = []
        
        # 如果没有诊断或特征，返回空列表
        if not features or not diagnoses:
            return mappings
            
        # 对每个诊断，查找相关的影像特征
        for diagnosis in diagnoses:
            if not isinstance(diagnosis, dict) or "描述" not in diagnosis:
                continue
                
            diagnosis_text = diagnosis.get("描述", "")
            if not diagnosis_text:
                continue
                
            # 找到相关的特征
            related_features = []
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                    
                # 获取特征信息
                feature_name = feature.get("名称", "")
                feature_detail = feature.get("特征", {})
                
                # 获取特征的解剖位置
                location = ""
                if isinstance(feature_detail, dict) and "解剖位置" in feature_detail:
                    location = feature_detail["解剖位置"]
                    
                # 判断是否相关(简单版：判断解剖位置或特征名称是否出现在诊断中)
                if location and location in diagnosis_text:
                    related_features.append(feature)
                elif feature_name and feature_name in diagnosis_text:
                    related_features.append(feature)
            
            # 如果找到相关特征，创建映射
            if related_features:
                for feature in related_features:
                    mapping = {
                        "影像发现": feature.get("名称", "") + "的特征",
                        "对应诊断": diagnosis_text,
                        "映射置信度": "高" if feature.get("名称", "") in diagnosis_text else "中"
                    }
                    mappings.append(mapping)
            # 如果没有找到相关特征，但有诊断，创建一个带“低”置信度的映射
            elif features:
                mapping = {
                    "影像发现": "综合影像表现",
                    "对应诊断": diagnosis_text,
                    "映射置信度": "低"
                }
                mappings.append(mapping)
                
        return mappings
        
    def set_status_callback(self, callback: Callable):
        """
        设置状态回调函数
        
        参数:
            callback: 回调函数，接受步骤名称和步骤索引
        """
        self.status_callback = callback