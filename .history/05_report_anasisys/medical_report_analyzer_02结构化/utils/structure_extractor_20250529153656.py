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
logger = logging.getLogger(__name__)"""
结构提取器模块，负责从医学报告中提取结构化信息
"""

import logging
import time
from typing import Dict, List, Any

from .llm_client import LLMClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructureExtractor:
    """医学报告结构提取器"""
    
    # 添加调试信息记录
    debug_info = {}
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化结构提取器
        
        参数:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        self.status_callback = None  # 状态回调函数
    
    def extract_anatomical_structures(self, report_text: str) -> List[Dict[str, str]]:
        """
        从报告文本中提取解剖结构
        
        参数:
            report_text: 报告文本
        
        返回:
            解剖结构列表，每个结构包含原文、标准名称和父结构
        """
        prompt = f"""
        从以下胸部CT报告文本中提取所有提到的解剖结构，包括器官、组织和位置

        报告文本:
        {report_text}
        
        请按以下JSON格式返回结果，注意所有标准名和父结构必须使用中文名称，不要使用英文:
        [
          {{"原文": "右肺中叶", "标准名": "右肺中叶", "父结构": "右肺"}},
          {{"原文": "胸膜", "标准名": "胸膜", "父结构": "胸腔"}},
          ...
        ]
        
        仅返回报告中明确提到的解剖结构，不要添加推测的结构
        所有标准名和父结构必须使用中文名称，不要使用英文
        """
        
        # 保存提示词用于调试
        self.debug_info["解剖结构_提示词"] = prompt
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["解剖结构_响应"] = result
            
            if isinstance(result, list):
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
        prompt = f"""
        从以下胸部CT报告文本中提取所有病变特征信息

        报告文本:
        {report_text}
        
        请分析文本中描述的每个病变，提取以下特征：
        1. 解剖位置 - 病变所在的具体解剖结构
        2. 大小 - 病变的尺寸描述
        3. 形态 - 病变的形状特征
        4. 密度 - 病变的密度特征
        5. 边界 - 病变边界的描述
        6. 数量 - 病变的数量
        7. 分布 - 病变的分布特征
        8. 其他特征 - 其他相关描述
        
        请按以下JSON格式返回结果，所有字段必须使用中文名称和描述，不要使用英文:
        [
          {{
            "解剖位置": "右肺上叶",
            "大小": "2.5cm×1.8cm",
            "形态": "结节状",
            "密度": "软组织密度",
            "边界": "边界清晰",
            "数量": "单发",
            "分布": "周围型",
            "其他特征": "无钥化"
          }},
          ...
        ]
        
        如果报告中没有明确描述某项特征，则对应字段返回空字符串
        """
        
        # 保存提示词用于调试
        self.debug_info["病变特征_提示词"] = prompt
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["病变特征_响应"] = result
            
            if isinstance(result, list):
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
        prompt = f"""
        从以下胸部CT报告的诊断结论文本中提取诊断信息

        诊断结论文本:
        {diagnosis_text}
        
        请分析文本中的诊断信息，提取以下内容：
        1. 主要诊断 - 报告中的主要诊断结论
        2. 鉴别诊断 - 可能的鉴别诊断
        3. 建议 - 医生的建议或随访计划
        
        请按以下JSON格式返回结果，所有字段必须使用中文名称和描述，不要使用英文：
        [
          {
            "类型": "主要诊断",
            "描述": "右肺上叶周围型肺癌"
          },
          {
            "类型": "鉴别诊断",
            "描述": "肺结核球"
          },
          {
            "类型": "建议",
            "描述": "建议进一步PET-CT检查"
          },
          ...
        ]
        
        请确保所有诊断名称和描述都使用中文表达，不要使用英文术语
        
        如果报告中没有某类信息，则不要在结果中包含该类型
        """
        
        # 保存提示词用于调试
        self.debug_info["诊断信息_提示词"] = prompt
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["诊断信息_响应"] = result
            
            if isinstance(result, list):
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
    
    def extract_report_sections(self, report_text: str) -> Dict[str, str]:
        """
        将报告文本分解为不同的部分
        
        参数:
            report_text: 报告文本
        
        返回:
            报告各部分的字典
        """
        prompt = f"""
        请将以下胸部CT报告的影像表现文本分解为不同的解剖部分
        
        报告文本:
        {report_text}
        
        请按以下JSON格式返回结果:
        {{
          "胸廓与胸膜": "胸廓对称，未见明显骨质破坏...",
          "肺部": "双肺纹理清晰，分布均匀...",
          "纵隔": "纵隔居中，未见肿大淋巴结...",
          "心脏与大血管": "心脏大小正常，主动脉走形正常..."
        }}
        
        根据报告内容提取相关解剖部位的描述，如果某部分在报告中未提及，则不要包含该部分
        """
        
        # 保存提示词用于调试
        self.debug_info["报告部分_提示词"] = prompt
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["报告部分_响应"] = result
            
            if isinstance(result, dict):
                # 移除空字段
                return {k: v for k, v in result.items() if v.strip()}
            elif isinstance(result, dict) and "error" in result:
                error_msg = f"分解报告部分失败: {result['error']}"
                logger.error(error_msg)
                self.debug_info["报告部分_错误"] = error_msg
                return {"完整文本": report_text}
            else:
                self.debug_info["报告部分_错误"] = "返回结果不是字典格式"
                return {"完整文本": report_text}
        except Exception as e:
            error_msg = f"分解报告部分时发生错误: {str(e)}"
            logger.error(error_msg)
            self.debug_info["报告部分_错误"] = error_msg
            return {"完整文本": report_text}
    
    def build_image_diagnosis_mapping(self, image_text: str, diagnosis_text: str) -> Dict[str, List[str]]:
        """
        构建影像表现与诊断结论之间的映射关系
        
        参数:
            image_text: 影像表现文本
            diagnosis_text: 诊断结论文本
        
        返回:
            影像表现与诊断结论的映射关系
        """
        prompt = f"""
        请分析以下胸部CT报告的影像表现和诊断结论，建立它们之间的映射关系
        
        影像表现:
        {image_text}
        
        诊断结论:
        {diagnosis_text}
        
        请按以下JSON格式返回结果:
        {{
          "影像发现与诊断映射": [
            {{
              "影像发现": "右肺上叶可见一枚约3cm大小的结节状软组织密度影，边缘毛糙，可见毛刺征、分叶征",
              "对应诊断": "右肺上叶周围型肺癌"
            }},
            {{
              "影像发现": "双肺散在多发小结节",
              "对应诊断": "肺内多发转移"
            }},
            ...
          ]
        }}
        
        请确保每个映射都有明确的证据支持，不要添加推测的映射关系
        """
        
        # 保存提示词用于调试
        self.debug_info["影像诊断映射_提示词"] = prompt
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["影像诊断映射_响应"] = result
            
            if isinstance(result, dict) and "影像发现与诊断映射" in result:
                return result
            elif isinstance(result, dict) and "error" in result:
                logger.error(f"构建影像诊断映射失败: {result['error']}")
                return {"影像发现与诊断映射": []}
            else:
                return {"影像发现与诊断映射": []}
        except Exception as e:
            logger.error(f"构建影像诊断映射时发生错误: {str(e)}")
            self.debug_info["影像诊断映射_错误"] = str(e)
            return {"影像发现与诊断映射": []}
    
    def analyze_single_report(self, image_text: str, diagnosis_text: str) -> Dict[str, Any]:
        """
        全面分析单份报告
        
        参数:
            image_text: 影像表现文本
            diagnosis_text: 诊断结论文本
        
        返回:
            完整的分析结果
        """
        logger.info("===== 开始分析报告 =====")
        logger.info(f"LLM客户端配置: 提供商={self.llm_client.provider}, 模型={self.llm_client.model}")
        
        # 分析步骤列表
        steps = [
            "提取报告部分",
            "提取解剖结构",
            "提取病变特征",
            "提取诊断信息",
            "构建映射关系"
        ]
        
        # 清空调试信息
        self.debug_info = {
            "原始数据": {
                "影像表现": image_text,
                "诊断结论": diagnosis_text
            },
            "模型信息": {
                "提供商": self.llm_client.provider,
                "模型": self.llm_client.model,
                "温度": getattr(self.llm_client, 'temperature', '默认'),
                "最大输出标记": getattr(self.llm_client, 'max_tokens', '默认')
            },
            "分析耗时": {}
        }
        
        result = {
            "原始数据": {
                "影像表现": image_text,
                "诊断结论": diagnosis_text
            },
            "结构化数据": {}
        }
        
        try:
            # 1. 提取报告部分
            if self.status_callback:
                self.status_callback(steps[0], 0)
                
            step_start_time = time.time()
            logger.info("1. 提取报告部分...")
            report_sections = self.extract_report_sections(image_text)
            result["结构化数据"]["报告部分"] = report_sections
            step_time = time.time() - step_start_time
            self.debug_info["分析耗时"]["提取报告部分"] = f"{step_time:.2f}秒"
            logger.info(f"   提取到 {len(report_sections)} 个报告部分 (耗时: {step_time:.2f}秒)")
            
            # 2. 提取解剖结构
            if self.status_callback:
                self.status_callback(steps[1], 1)
                
            step_start_time = time.time()
            logger.info("2. 提取解剖结构...")
            anatomical_structures = self.extract_anatomical_structures(image_text)
            result["结构化数据"]["解剖结构"] = anatomical_structures
            step_time = time.time() - step_start_time
            self.debug_info["分析耗时"]["提取解剖结构"] = f"{step_time:.2f}秒"
            logger.info(f"   提取到 {len(anatomical_structures)} 个解剖结构 (耗时: {step_time:.2f}秒)")
            
            # 3. 提取病变特征
            if self.status_callback:
                self.status_callback(steps[2], 2)
                
            step_start_time = time.time()
            logger.info("3. 提取病变特征...")
            lesion_features = self.extract_lesion_features(image_text)
            result["结构化数据"]["病变特征"] = lesion_features
            step_time = time.time() - step_start_time
            self.debug_info["分析耗时"]["提取病变特征"] = f"{step_time:.2f}秒"
            logger.info(f"   提取到 {len(lesion_features)} 个病变特征 (耗时: {step_time:.2f}秒)")
            
            # 4. 提取诊断信息
            if self.status_callback:
                self.status_callback(steps[3], 3)
                
            step_start_time = time.time()
            logger.info("4. 提取诊断信息...")
            diagnoses = self.extract_diagnoses(diagnosis_text)
            result["结构化数据"]["诊断信息"] = diagnoses
            step_time = time.time() - step_start_time
            self.debug_info["分析耗时"]["提取诊断信息"] = f"{step_time:.2f}秒"
            logger.info(f"   提取到 {len(diagnoses)} 个诊断信息 (耗时: {step_time:.2f}秒)")
            
            # 5. 构建映射关系
            if self.status_callback:
                self.status_callback(steps[4], 4)
                
            step_start_time = time.time()
            logger.info("5. 构建映射关系...")
            mapping = self.build_image_diagnosis_mapping(image_text, diagnosis_text)
            result["结构化数据"]["影像诊断映射"] = mapping
            step_time = time.time() - step_start_time
            self.debug_info["分析耗时"]["构建映射关系"] = f"{step_time:.2f}秒"
            logger.info(f"   映射关系构建完成 (耗时: {step_time:.2f}秒)")
            
            logger.info("===== 报告分析完成 =====\n")
        except Exception as e:
            logger.error(f"===== 报告分析出错: {str(e)} =====\n")
            self.debug_info["分析错误"] = str(e)
            # 出错时仍然返回部分结果
        
        # 将调试信息添加到结果中
        result["调试信息"] = self.debug_info
        
        return result
