"""
结构提取器模块，负责从医学报告中提取结构化信息
优化版：使用标准化提示词和知识库支持
"""

import logging
import time
import json
import re
import asyncio
from typing import Dict, List, Any, Callable

from .model_assist_processor import ModelAssistProcessor

from .llm_client import LLMClient
from .medical_terminology import (
    STANDARD_ANATOMICAL_TERMS,
    STANDARD_DIAGNOSIS_TYPES,
    CONFIDENCE_TERMS
)
from .knowledge_base import MedicalKnowledgeBase
from .knowledge_settings import knowledge_settings
from .diagnosis_associator import DiagnosisAssociator

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入SNOMED CT相关服务
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '03_Image_snomed_struction'))
try:
    from enhanced_terminology_services import enhanced_terminology_service
    SNOMED_AVAILABLE = True
    logger.info("SNOMED CT服务已加载")
except ImportError:
    SNOMED_AVAILABLE = False
    enhanced_terminology_service = None
    logger.warning("SNOMED CT服务不可用，将使用基础模式")

class StructureExtractor:
    """优化版医学报告结构提取器"""

    def __init__(self, llm_client: LLMClient, use_knowledge_base: bool = True):
        """
        初始化结构提取器

        参数:
            llm_client: LLM客户端实例
            use_knowledge_base: 是否使用知识库
        """
        self.llm_client = llm_client
        self.status_callback = None  # 状态回调函数
        self.debug_info = {}  # 调试信息

        # 初始化知识库
        self.use_knowledge_base = use_knowledge_base
        if use_knowledge_base:
            self.knowledge_base = MedicalKnowledgeBase()
            logger.info("已启用知识库支持")
        else:
            self.knowledge_base = None
            logger.info("未启用知识库支持")

        # 初始化模型辅助处理器
        self.model_assist = ModelAssistProcessor(llm_client)
        logger.info("已初始化模型辅助处理器")

        # SNOMED CT增强功能
        self.use_snomed = SNOMED_AVAILABLE and enhanced_terminology_service is not None
        self.snomed_service = enhanced_terminology_service if self.use_snomed else None

        if self.use_snomed:
            logger.info("结构提取器已启用SNOMED CT增强功能")
        else:
            logger.info("结构提取器使用基础模式")

    def set_status_callback(self, callback: Callable):
        """
        设置状态回调函数

        参数:
            callback: 回调函数，接受步骤名称和步骤索引
        """
        self.status_callback = callback

    def extract_core_information(self, report_text: str, diagnosis_text: str) -> Dict[str, Any]:
        """
        一次性提取核心信息，减少API调用

        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本

        返回:
            包含解剖结构、影像特征和诊断信息的字典
        """
        # 打印诊断文本内容以便调试
        logger.info(f"接收到的诊断文本: '{diagnosis_text}'")
        logger.info(f"诊断文本长度: {len(diagnosis_text)}字符")

        # 尝试次数
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"尝试提取核心信息(第{attempt}/{max_attempts}次)")

            try:
                # 第一次尝试：使用标准提示词
                if attempt == 1:
                    prompt = self._get_standard_prompt(report_text, diagnosis_text)
                    extraction_method = "标准提示词"
                # 第二次尝试：使用简化提示词
                elif attempt == 2:
                    prompt = self._get_simplified_prompt(report_text, diagnosis_text)
                    extraction_method = "简化提示词"
                # 第三次尝试：使用基本提示词
                else:
                    prompt = self._get_basic_prompt(report_text, diagnosis_text)
                    extraction_method = "基本提示词"

                # 记录提示词
                self.debug_info[f"核心信息提取_{extraction_method}_提示词"] = prompt

                # 提取信息
                result = self.llm_client.extract_json(prompt)
                self.debug_info[f"核心信息提取_{extraction_method}_响应"] = result
                logger.info(f"[DEBUG] LLM {extraction_method} 原始响应: {result}")

                # 确保结果包含所有必要字段
                for field in ["解剖结构", "病变特征", "诊断信息"]:
                    if field not in result or not isinstance(result[field], list):
                        result[field] = []

                # 记录提取到的各类信息数量
                logger.info(f"提取结果({extraction_method}): 解剖结构={len(result['解剖结构'])}项, 病变特征={len(result['病变特征'])}项, 诊断信息={len(result['诊断信息'])}项")

                # 如果提取结果有效，返回结果
                if self._is_valid_extraction_result(result, diagnosis_text):
                    logger.info(f"使用{extraction_method}成功提取核心信息")
                    return result
                else:
                    logger.warning(f"使用{extraction_method}提取的结果不完整，尝试其他方法")

            except Exception as e:
                error_msg = f"第{attempt}次提取核心信息时发生错误: {str(e)}"
                logger.error(error_msg)
                self.debug_info[f"核心信息提取_第{attempt}次_错误"] = error_msg

        # 所有尝试都失败，使用基本提取
        logger.warning("所有提取方法都失败，使用基本提取")
        return self._fallback_extraction(report_text, diagnosis_text)

    def _is_valid_extraction_result(self, result: Dict[str, Any], diagnosis_text: str) -> bool:
        """
        验证提取结果是否有效

        参数:
            result: 提取结果
            diagnosis_text: 诊断文本

        返回:
            结果是否有效
        """
        # 必须是字典类型
        if not isinstance(result, dict):
            return False

        # 必须包含所有必要字段
        for field in ["解剖结构", "病变特征", "诊断信息"]:
            if field not in result or not isinstance(result[field], list):
                return False

        # 如果诊断文本不为空，诊断信息也不应为空
        if diagnosis_text and diagnosis_text.strip() and len(result["诊断信息"]) == 0:
            logger.warning("诊断文本非空但未提取到诊断信息")
            logger.info(f"LLM返回的完整结果: {json.dumps(result, ensure_ascii=False)}")
            return False

        return True

    def _get_standard_prompt(self, report_text: str, diagnosis_text: str) -> str:
        """
        获取标准提示词

        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本

        返回:
            标准提示词
        """
        prompt = f"""
        请仔细分析以下医学影像报告，提取所有关键结构化信息：

        【影像表现】：
        {report_text}

        【诊断结论】：
        {diagnosis_text}

        请严格提取以下三类信息：

        1. 解剖结构：报告中提到的所有解剖部位，参照标准医学术语
           格式: {{"原文": "报告中的原始表述", "标准名": "标准解剖名称", "父结构": "所属的上级结构"}}

        2. 病变特征：各解剖部位观察到的影像学特征
           格式: {{"解剖位置": "具体部位", "大小": "尺寸描述", "形态": "形状特征", "密度": "密度特征",
                 "边界": "边界特征", "数量": "数量描述", "分布": "分布特点", "其他特征": "其他特征描述"}}

        3. 诊断信息：【特别重要】从诊断结论部分提取每一项诊断，将其分类为以下类型之一
           格式: {{"类型": "确诊", "描述": "具体诊断内容", "置信度": "高", "相关解剖结构": ["相关结构1", "相关结构2"]}}

           注意：
           - 必须从诊断结论中提取出所有诊断项，每个独立的诊断作为一个单独的条目
           - 诊断类型通常为"确诊"，除非有明确的不确定性表述
           - 默认置信度为"高"，除非有特殊说明
           - 疾病、异常发现、钙化、狭窄等均应视为诊断信息

        请按以下JSON格式返回结果：
        {{
          "解剖结构": [
            // 结构列表
          ],
          "病变特征": [
            // 特征列表
          ],
          "诊断信息": [
            // 诊断列表
          ]
        }}

        注意：
        1. 所有字段必须使用中文，不要使用英文术语
        2. 解剖结构应参考标准医学术语，确保父结构正确
        3. 对于诊断类型，根据表述确定其类型及置信度
        4. 如果某信息不存在，返回空列表
        """
        return prompt

    def _get_simplified_prompt(self, report_text: str, diagnosis_text: str) -> str:
        """
        获取简化提示词

        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本

        返回:
            简化提示词
        """
        prompt = f"""
        请分析以下医学影像报告，提取关键信息：

        【影像表现】：
        {report_text}

        【诊断结论】：
        {diagnosis_text}

        请提取以下信息：

        1. 解剖结构
        2. 病变特征
        3. 诊断信息

        请按以下JSON格式返回结果：
        {{
          "解剖结构": [
            // 结构列表
          ],
          "病变特征": [
            // 特征列表
          ],
          "诊断信息": [
            // 诊断列表
          ]
        }}
        """
        return prompt

    def _get_basic_prompt(self, report_text: str, diagnosis_text: str) -> str:
        """
        获取基本提示词

        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本

        返回:
            基本提示词
        """
        prompt = f"""
        请分析以下医学影像报告，提取信息：

        【影像表现】：
        {report_text}

        【诊断结论】：
        {diagnosis_text}

        请返回以下JSON格式结果：
        {{
          "解剖结构": [
            // 结构列表
          ],
          "病变特征": [
            // 特征列表
          ],
          "诊断信息": [
            // 诊断列表
          ]
        }}
        """
        return prompt

    def _fallback_extraction(self, report_text: str, diagnosis_text: str) -> Dict[str, Any]:
        """
        基本提取方法

        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本

        返回:
            提取结果
        """
        logger.info("使用基本提取方法")
        result = {
            "解剖结构": [],
            "病变特征": [],
            "诊断信息": []
        }

        # 基本的解剖结构提取
        anatomy_keywords = [
            ("头部", "头部", "身体"),
            ("脑", "脑", "头部"),
            ("大脑", "大脑", "脑"),
            ("小脑", "小脑", "脑"),
            ("胸部", "胸部", "身体"),
            ("胸腔", "胸腔", "胸部"),
            ("肺", "肺", "胸腔"),
            ("左肺", "左肺", "肺"),
            ("右肺", "右肺", "肺"),
            ("心脏", "心脏", "胸腔"),
            ("腋部", "腋部", "身体"),
            ("肝脏", "肝脏", "腋部"),
            ("肾脏", "肾脏", "腋部"),
            ("脱", "脱部", "身体"),
            ("骨骼", "骨骼", "脱部"),
            ("脊柱", "脊柱", "骨骼"),
            ("预孕囊", "预孕囊", "产科系统"),
            ("子宫", "子宫", "产科系统")
        ]

        # 扫描文本中的解剖结构
        for keyword, standard_name, parent in anatomy_keywords:
            if keyword in report_text or keyword in diagnosis_text:
                result["解剖结构"].append({
                    "原文": keyword,
                    "标准名": standard_name,
                    "父结构": parent
                })

        # 基本的病变提取
        # 如果文本中提到“未见异常”，创建一个正常病变特征
        if "未见异常" in report_text or "未发现异常" in report_text:
            for structure in result["解剖结构"]:
                result["病变特征"].append({
                    "解剖位置": structure["标准名"],
                    "大小": "",
                    "形态": "正常",
                    "密度": "",
                    "边界": "未描述边界",
                    "数量": "单发",
                    "分布": "",
                    "其他特征": "未见异常"
                })

        # 基本的诊断提取
        # 如果有诊断文本，至少创建一个诊断项
        if diagnosis_text and diagnosis_text.strip():
            # 尝试提取常见诊断模式
            diagnoses = []

            # 处理多个诊断的情况(以分号或句号分隔)
            if ";" in diagnosis_text or "；" in diagnosis_text:
                parts = re.split(r"[;;；]", diagnosis_text)
                diagnoses.extend([p.strip() for p in parts if p.strip()])
            elif "." in diagnosis_text or "。" in diagnosis_text:
                parts = re.split(r"[..。]", diagnosis_text)
                diagnoses.extend([p.strip() for p in parts if p.strip()])
            else:
                diagnoses.append(diagnosis_text.strip())

            # 处理提取的诊断
            for diag_text in diagnoses:
                # 确定诊断类型和置信度
                diag_type = "确诊"
                confidence = "高"

                # 如果包含“未见异常”等关键词，设置相应标记
                if any(kw in diag_text for kw in ["未见异常", "未见明显异常", "正常", "未发现异常"]):
                    logger.info(f"诊断内容正常: {diag_text}")

                if "考虑" in diag_text or "可能" in diag_text or "待排除" in diag_text:
                    diag_type = "待证"
                    confidence = "中"

                # 提取相关解剖结构
                related_structures = []
                for structure in result["解剖结构"]:
                    if structure["标准名"] in diag_text or structure["原文"] in diag_text:
                        related_structures.append(structure["标准名"])

                # 创建诊断项
                result["诊断信息"].append({
                    "类型": diag_type,
                    "内容": diag_text,
                    "可信度": confidence,
                    "相关解剖结构": related_structures if related_structures else ["未指定"]
                })

        logger.info(f"基本提取结果: 解剖结构={len(result['解剖结构'])}项, 病变特征={len(result['病变特征'])}项, 诊断信息={len(result['诊断信息'])}项")
        return result

    def validate_and_fix_structures(self, structures: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        验证解剖结构并修复常见错误

        参数:
            structures: 解剖结构列表

        返回:
            修复后的解剖结构列表
        """
        valid_structures = []

        for structure in structures:
            # 检查必要字段是否存在
            if not all(key in structure for key in ["原文", "标准名", "父结构"]):
                continue

            # 标准化解剖结构名称
            structure = self._standardize_anatomical_term(structure)

            # 使用知识库查找正确的父结构（如果启用）
            if self.use_knowledge_base and self.knowledge_base:
                parent_from_kb = self.knowledge_base.get_structure_parent(structure["标准名"])
                if parent_from_kb:
                    structure["父结构"] = parent_from_kb

            valid_structures.append(structure)

        # 如果启用SNOMED CT，进行术语验证和增强
        if self.use_snomed and self.snomed_service:
            valid_structures = asyncio.run(self._enhance_structures_with_snomed(valid_structures))

        return valid_structures

    async def _enhance_structures_with_snomed(self, structures: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        使用SNOMED CT增强解剖结构信息

        参数:
            structures: 解剖结构列表

        返回:
            增强后的解剖结构列表
        """
        enhanced_structures = []

        for structure in structures:
            try:
                # 验证术语
                validation_result = await self.snomed_service.validate_medical_term(
                    structure["标准名"],
                    context="anatomical structure"
                )

                # 如果找到有效的SNOMED CT术语，使用它
                if validation_result.is_valid and validation_result.snomed_entity:
                    structure["snomed_code"] = validation_result.snomed_entity.code
                    structure["snomed_term"] = validation_result.snomed_entity.term
                    structure["validation_confidence"] = validation_result.confidence

                    # 如果SNOMED CT提供了更好的父结构关系，使用它
                    if validation_result.snomed_entity.relationships.get("parent_codes"):
                        # 这里可以进一步查询父概念来更新父结构
                        pass

                # 如果验证失败但有建议，记录建议
                elif validation_result.suggestions:
                    structure["snomed_suggestions"] = validation_result.suggestions
                    structure["validation_confidence"] = validation_result.confidence

                enhanced_structures.append(structure)

            except Exception as e:
                logger.warning(f"SNOMED CT增强失败: {structure['标准名']}, 错误: {e}")
                enhanced_structures.append(structure)

        return enhanced_structures

    def _standardize_anatomical_term(self, structure: Dict[str, str]) -> Dict[str, str]:
        """
        标准化解剖结构术语

        参数:
            structure: 解剖结构数据

        返回:
            标准化后的解剖结构数据
        """
        # 尝试匹配标准术语
        std_name = structure["标准名"]
        parent = structure["父结构"]

        # 检查是否需要修正父结构
        for category, terms in STANDARD_ANATOMICAL_TERMS.items():
            if std_name in terms and parent != category:
                # 找到了匹配的标准术语，但父结构不正确
                structure["父结构"] = category
                break

        return structure

    def validate_and_enhance_diagnosis(self, diagnoses: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        验证诊断信息并增强内容

        参数:
            diagnoses: 诊断信息列表

        返回:
            增强后的诊断信息列表
        """
        valid_diagnoses = []

        for diagnosis in diagnoses:
            # 检查必要字段
            if not all(key in diagnosis for key in ["类型", "描述"]):
                continue

            # 确保类型是标准类型之一
            if diagnosis["类型"] not in STANDARD_DIAGNOSIS_TYPES:
                # 尝试匹配最接近的标准类型
                for std_type in STANDARD_DIAGNOSIS_TYPES:
                    if std_type in diagnosis["类型"]:
                        diagnosis["类型"] = std_type
                        break
                else:
                    # 如果无法匹配，设为"其他发现"
                    diagnosis["类型"] = "其他发现"

            # 如果没有置信度字段，尝试从描述中推断
            if "置信度" not in diagnosis or not diagnosis["置信度"]:
                diagnosis["置信度"] = self._infer_confidence_level(diagnosis["描述"])

            valid_diagnoses.append(diagnosis)

        # 如果启用SNOMED CT，进行诊断术语验证和增强
        if self.use_snomed and self.snomed_service:
            valid_diagnoses = asyncio.run(self._enhance_diagnoses_with_snomed(valid_diagnoses))

        return valid_diagnoses

    async def _enhance_diagnoses_with_snomed(self, diagnoses: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        使用SNOMED CT增强诊断信息

        参数:
            diagnoses: 诊断信息列表

        返回:
            增强后的诊断信息列表
        """
        enhanced_diagnoses = []

        for diagnosis in diagnoses:
            try:
                # 验证诊断术语
                validation_result = await self.snomed_service.validate_medical_term(
                    diagnosis.get("描述", diagnosis.get("内容", "")),
                    context="clinical finding"
                )

                # 如果找到有效的SNOMED CT术语，添加编码信息
                if validation_result.is_valid and validation_result.snomed_entity:
                    diagnosis["snomed_code"] = validation_result.snomed_entity.code
                    diagnosis["snomed_term"] = validation_result.snomed_entity.term
                    diagnosis["validation_confidence"] = validation_result.confidence
                    diagnosis["snomed_source"] = validation_result.validation_source

                    # 获取相关的父概念（疾病分类）
                    if validation_result.snomed_entity.relationships.get("parent_codes"):
                        diagnosis["disease_category"] = validation_result.snomed_entity.relationships.get("parent_codes", [])

                # 如果验证失败但有建议，记录建议
                elif validation_result.suggestions:
                    diagnosis["snomed_suggestions"] = validation_result.suggestions
                    diagnosis["validation_confidence"] = validation_result.confidence

                enhanced_diagnoses.append(diagnosis)

            except Exception as e:
                logger.warning(f"诊断SNOMED CT增强失败: {diagnosis.get('描述', diagnosis.get('内容', ''))}, 错误: {e}")
                enhanced_diagnoses.append(diagnosis)

        return enhanced_diagnoses

    def _infer_confidence_level(self, description: str) -> str:
        """
        从描述文本推断置信度级别

        参数:
            description: 描述文本

        返回:
            置信度级别（高/中/低）
        """
        for level, terms in CONFIDENCE_TERMS.items():
            for term in terms:
                if term in description:
                    return level

        # 默认置信度
        return "中"

    def _split_text_into_segments(self, text: str, max_length: int = 800) -> List[str]:
        """
        将长文本分割成更小的段落

        参数:
            text: 长文本
            max_length: 每段最大长度

        返回:
            文本段落列表
        """
        if not text or len(text) <= max_length:
            return [text]

        # 按句子分割
        sentences = text.split('。')
        segments = []
        current_segment = ""

        for sentence in sentences:
            # 如果句子结尾没有句号，添加回去
            if sentence:
                sentence = sentence + '。'

            # 如果添加这个句子会超过最大长度，则开始新段落
            if len(current_segment) + len(sentence) > max_length and current_segment:
                segments.append(current_segment)
                current_segment = sentence
            else:
                current_segment += sentence

        # 添加最后一个段落
        if current_segment:
            segments.append(current_segment)

        return segments

    def _merge_segment_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个段落的提取结果

        参数:
            results: 段落结果列表

        返回:
            合并后的结果
        """
        merged = {
            "解剖结构": [],
            "病变特征": [],
            "诊断信息": []
        }

        # 用于去重的集合
        structure_texts = set()
        feature_texts = set()
        diagnosis_texts = set()

        # 合并所有结果
        for result in results:
            # 合并解剖结构
            for structure in result.get("解剖结构", []):
                key = f"{structure.get('原文', '')}-{structure.get('标准名', '')}"
                if key and key not in structure_texts:
                    structure_texts.add(key)
                    merged["解剖结构"].append(structure)

            # 合并病变特征
            for feature in result.get("病变特征", []):
                key = f"{feature.get('解剖位置', '')}-{feature.get('形态', '')}-{feature.get('大小', '')}"
                if key and key not in feature_texts:
                    feature_texts.add(key)
                    merged["病变特征"].append(feature)

            # 合并诊断信息
            for diagnosis in result.get("诊断信息", []):
                key = f"{diagnosis.get('类型', '')}-{diagnosis.get('描述', '')}"
                if key and key not in diagnosis_texts:
                    diagnosis_texts.add(key)
                    merged["诊断信息"].append(diagnosis)

        return merged

    def build_image_diagnosis_mapping(self, image_text: str, diagnosis_text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        构建影像表现与诊断结论之间的映射关系

        参数:
            image_text: 影像表现文本
            diagnosis_text: 诊断结论文本

        返回:
            影像表现与诊断结论的映射关系
        """
        # 如果任一文本为空，返回空映射
        if not image_text or not diagnosis_text:
            return {"影像发现与诊断映射": []}

        prompt = f"""
        请分析以下医学影像报告的影像表现和诊断结论，建立它们之间的映射关系

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
        映射时应当找出诊断结论中的疾病与影像表现中的特征之间的最佳匹配
        """

        # 保存提示词用于调试
        self.debug_info["影像诊断映射_提示词"] = prompt

        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["影像诊断映射_响应"] = result

            if isinstance(result, dict) and "影像发现与诊断映射" in result:
                # 使用知识库验证映射关系（如果启用）
                if self.use_knowledge_base and self.knowledge_base:
                    mappings = result["影像发现与诊断映射"]
                    enhanced_mappings = []

                    for mapping in mappings:
                        if all(key in mapping for key in ["影像发现", "对应诊断"]):
                            # 保留有效映射
                            enhanced_mappings.append(mapping)

                    result["影像发现与诊断映射"] = enhanced_mappings

                return result
            else:
                logger.error("构建影像诊断映射失败: 返回格式不正确")
                return {"影像发现与诊断映射": []}
        except Exception as e:
            error_msg = f"构建影像诊断映射时发生错误: {str(e)}"
            logger.error(error_msg)
            self.debug_info["影像诊断映射_错误"] = error_msg
            return {"影像发现与诊断映射": []}

    def process_long_report(self, report_text: str, max_length: int = 800) -> Dict[str, Any]:
        """
        分段处理长报告文本

        参数:
            report_text: 报告文本
            max_length: 每段最大长度

        返回:
            合并后的处理结果
        """
        # 对长文本进行分段处理
        if len(report_text) > max_length:
            logger.info(f"报告文本较长({len(report_text)}字符)，进行分段处理")
            segments = self._split_text_into_segments(report_text, max_length)
            logger.info(f"分割为{len(segments)}个段落")

            results = []
            for i, segment in enumerate(segments):
                logger.info(f"处理段落 {i+1}/{len(segments)}")
                segment_result = self.extract_core_information(segment, "")  # 诊断文本为空
                results.append(segment_result)

            # 合并结果
            return self._merge_segment_results(results)
        else:
            # 短文本直接处理
            logger.info(f"报告文本较短({len(report_text)}字符)，直接处理")
            return self.extract_core_information(report_text, "")

    def _fix_anatomical_structures(self, structures: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        修复解剖结构数据

        参数:
            structures: 解剖结构列表

        返回:
            修复后的解剖结构列表
        """
        valid_structures = []

        for structure in structures:
            # 检查必要字段是否存在
            if not all(key in structure for key in ["原文"]):
                continue

            # 初始化标准名称和父结构字段（如果不存在）
            fixed_structure = structure.copy()

            # 如果没有标准名，使用原文
            if "标准名" not in fixed_structure or not fixed_structure["标准名"]:
                fixed_structure["标准名"] = fixed_structure["原文"]

            # 如果没有父结构，尝试推断
            if "父结构" not in fixed_structure or not fixed_structure["父结构"]:
                fixed_structure["父结构"] = self._infer_parent_structure(fixed_structure["原文"])

            valid_structures.append(fixed_structure)

        return valid_structures

    def _infer_parent_structure(self, structure_name: str) -> str:
        """推断解剖结构的父结构"""
        # 简单的推断规则
        if "右肺" in structure_name or "右侧" in structure_name:
            return "右肺"
        elif "左肺" in structure_name or "左侧" in structure_name:
            return "左肺"
        elif "肺" in structure_name:
            return "肺"
        elif "气管" in structure_name or "支气管" in structure_name:
            return "气管"
        elif "纵隙" in structure_name:
            return "纵隙"
        elif "胸膜" in structure_name:
            return "胸膜"
        elif "心" in structure_name:
            return "心脉"
        elif "主动脉" in structure_name or "动脉" in structure_name:
            return "主动脉"
        else:
            return ""

    def _fix_lesion_features(self, lesions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        修复病变特征数据

        参数:
            lesions: 病变特征列表

        返回:
            修复后的病变特征列表
        """
        valid_lesions = []

        for lesion in lesions:
            # 检查基本字段是否存在
            if not any(key in lesion for key in ["解剖位置", "大小", "形态", "密度", "边界"]):
                continue

            # 复制并完善缺失的字段
            fixed_lesion = lesion.copy()

            # 确保必要字段存在
            required_fields = ["解剖位置", "大小", "形态", "密度", "边界", "数量", "分布", "其他特征"]
            for field in required_fields:
                if field not in fixed_lesion:
                    fixed_lesion[field] = ""

            # 边界必须有值，如果缺失则新增默认值
            if not fixed_lesion["边界"]:
                if "模糊" in str(fixed_lesion) or "不清" in str(fixed_lesion):
                    fixed_lesion["边界"] = "边界不清"
                else:
                    fixed_lesion["边界"] = "边界未描述"

            # 修复数量字段
            if not fixed_lesion["数量"]:
                if "多发" in str(fixed_lesion) or "多个" in str(fixed_lesion):
                    fixed_lesion["数量"] = "多发"
                else:
                    fixed_lesion["数量"] = "单发"

            valid_lesions.append(fixed_lesion)

        return valid_lesions

    def _fix_diagnosis_information(self, diagnoses: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        修复诊断信息数据

        参数:
            diagnoses: 诊断信息列表

        返回:
            修复后的诊断信息列表
        """
        valid_diagnoses = []
        logger.info(f"修复诊断信息: 收到 {len(diagnoses)} 项诊断信息")

        for diagnosis in diagnoses:
            # 记录原始诊断信息内容以便调试
            logger.info(f"处理诊断项: {diagnosis}")

            # 复制并处理诊断信息
            fixed_diagnosis = diagnosis.copy()

            # 处理字段名兼容性问题 - LLM可能使用"描述"而不是"内容"字段
            if "描述" in fixed_diagnosis and ("内容" not in fixed_diagnosis or not fixed_diagnosis["内容"]):
                fixed_diagnosis["内容"] = fixed_diagnosis["描述"]
                logger.info(f"将'描述'字段映射到'内容'字段: {fixed_diagnosis['内容']}")

            # 处理字段名兼容性问题 - LLM可能使用"置信度"而不是"可信度"字段
            if "置信度" in fixed_diagnosis and ("可信度" not in fixed_diagnosis or not fixed_diagnosis["可信度"]):
                fixed_diagnosis["可信度"] = fixed_diagnosis["置信度"]

            # 检查必要字段 - 宽松验证，只要有内容就接受
            if ("内容" not in fixed_diagnosis or not fixed_diagnosis["内容"]) and \
               ("描述" not in fixed_diagnosis or not fixed_diagnosis["描述"]):
                logger.warning(f"跳过缺少内容的诊断: {diagnosis}")
                continue

            # 确保必要字段存在
            required_fields = ["类型", "内容", "相关解剖结构", "可信度"]
            for field in required_fields:
                if field not in fixed_diagnosis:
                    fixed_diagnosis[field] = ""

            # 修复类型字段
            if not fixed_diagnosis["类型"]:
                content = fixed_diagnosis["内容"].lower()
                if "考虑" in content or "可能" in content or "似" in content:
                    fixed_diagnosis["类型"] = "高度疑似"
                elif "建议" in content or "复查" in content:
                    fixed_diagnosis["类型"] = "建议"
                elif "除外" in content or "排除" in content:
                    fixed_diagnosis["类型"] = "待排除"
                else:
                    fixed_diagnosis["类型"] = "确诊"

            # 修复相关解剖结构字段
            if not fixed_diagnosis["相关解剖结构"]:
                # 从内容中提取可能的解剖结构
                content = fixed_diagnosis["内容"]

                # 处理胸部CT常见结构
                if "肺" in content:
                    if "右肺" in content:
                        fixed_diagnosis["相关解剖结构"] = ["右肺"]
                    elif "左肺" in content:
                        fixed_diagnosis["相关解剖结构"] = ["左肺"]
                    else:
                        fixed_diagnosis["相关解剖结构"] = ["肺"]
                # 处理脑部相关结构
                elif "脑" in content or "颅" in content:
                    fixed_diagnosis["相关解剖结构"] = self._extract_brain_structure(content)
                # 处理其他常见结构
                elif "心" in content:
                    fixed_diagnosis["相关解剖结构"] = ["心脏"]
                elif "肝" in content:
                    fixed_diagnosis["相关解剖结构"] = ["肝脏"]
                elif "肾" in content:
                    fixed_diagnosis["相关解剖结构"] = ["肾脏"]
                elif "脊椎" in content or "脊柱" in content:
                    fixed_diagnosis["相关解剖结构"] = ["脊柱"]
                else:
                    # 默认使用一个空列表而不是抛弃这条诊断
                    fixed_diagnosis["相关解剖结构"] = []

            logger.info(f"修复后的诊断: {fixed_diagnosis}")
            valid_diagnoses.append(fixed_diagnosis)

        return valid_diagnoses

    def process_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理提取的数据，包括修复缺失或不规范的数据

        参数:
            data: 提取的原始数据

        返回:
            处理后的数据
        """
        # --- 调试信息 ---
        self.debug_info["process_extracted_data_输入"] = data

        fixed_data = data.copy()

        # -------- 类型修正，防止list作为key --------
        # 修正解剖结构中的“标准名”为字符串
        for structure in fixed_data.get("解剖结构", []):
            if isinstance(structure.get("标准名"), list):
                structure["标准名"] = ",".join([str(x) for x in structure["标准名"]])
            if isinstance(structure.get("父结构"), list):
                structure["父结构"] = ",".join([str(x) for x in structure["父结构"]])
        # 修正病变特征中的“解剖位置”为字符串
        for lesion in fixed_data.get("病变特征", []):
            if isinstance(lesion.get("解剖位置"), list):
                lesion["解剖位置"] = ",".join([str(x) for x in lesion["解剖位置"]])
        # 修正诊断信息中的“相关解剖结构”为字符串
        for diag in fixed_data.get("诊断信息", []):
            if isinstance(diag.get("相关解剖结构"), list):
                diag["相关解剖结构"] = ",".join([str(x) for x in diag["相关解剖结构"]])
        # -------------------------------------

        # 修复解剖结构
        if "解剖结构" in fixed_data and fixed_data["解剖结构"]:
            fixed_data["解剖结构"] = self._fix_anatomical_structures(fixed_data["解剖结构"])

        # 修复病变特征
        if "病变特征" in fixed_data and fixed_data["病变特征"]:
            fixed_data["病变特征"] = self._fix_lesion_features(fixed_data["病变特征"])

            # 如果有模型辅助处理器，使用它标准化病变特征
            if hasattr(self, 'model_assist') and self.model_assist:
                fixed_data["病变特征"] = self.model_assist.batch_standardize_lesions(fixed_data["病变特征"])
                logger.info(f"完成病变特征标准化，共处理 {len(fixed_data['病变特征'])} 项")

        # 修复诊断信息
        if "诊断信息" in fixed_data and fixed_data["诊断信息"]:
            fixed_data["诊断信息"] = self._fix_diagnosis_information(fixed_data["诊断信息"])

        # 建立诊断与病变的关联关系
        if hasattr(self, 'model_assist') and self.model_assist and \
           "病变特征" in fixed_data and fixed_data["病变特征"] and \
           "诊断信息" in fixed_data and fixed_data["诊断信息"]:
            try:
                logger.info("建立诊断与病变的关联关系...")
                associator = DiagnosisAssociator(self.model_assist.llm_client)
                associations = associator.associate_features_with_diagnoses(
                    fixed_data["病变特征"],
                    fixed_data["诊断信息"],
                    fixed_data.get("解剖结构", [])
                )
                # 添加关联结果到返回数据
                fixed_data["关联关系"] = associations
                logger.info(f"完成诊断关联建立，关联了 {len(associations['诊断到病变映射'])} 个诊断项")
            except Exception as e:
                logger.error(f"诊断关联建立失败: {str(e)}")
                fixed_data["关联关系"] = {
                    "诊断到病变映射": {},
                    "病变到诊断映射": {},
                    "关联强度": {}
                }

        self.debug_info["process_extracted_data_输出"] = fixed_data
        return fixed_data

    def analyze_with_knowledge_base(self, core_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用知识库优化分析结果

        参数:
            core_result: 核心提取结果

        返回:
            优化后的结果
        """
        if not self.use_knowledge_base or not self.knowledge_base:
            return core_result

        try:
            # 优化解剖结构
            if "解剖结构" in core_result:
                core_result["解剖结构"] = self.validate_and_fix_structures(core_result["解剖结构"])

            # 优化诊断信息
            if "诊断信息" in core_result:
                core_result["诊断信息"] = self.validate_and_enhance_diagnosis(core_result["诊断信息"])

            return core_result
        except Exception as e:
            logger.error(f"使用知识库优化结果时出错: {str(e)}")
            return core_result

    def analyze_single_report(self, image_text: str, diagnosis_text: str) -> Dict[str, Any]:
        """
        全面分析单份报告（优化版）
        """
        # --- 调试信息 ---
        logger.info(f"[DEBUG] analyze_single_report 启动, image_text长度={len(image_text)}, diagnosis_text长度={len(diagnosis_text)}")
        self.debug_info = {}
        self.debug_info["输入_影像表现"] = image_text
        self.debug_info["输入_诊断结论"] = diagnosis_text

        # 记录输入文本信息
        logger.info(f"准备分析报告: 影像表现文本长度={len(image_text)}字符, 诊断结论文本长度={len(diagnosis_text)}字符")
        if diagnosis_text.strip():
            logger.info(f"诊断文本内容: '{diagnosis_text}'")
        else:
            logger.warning("警告: 诊断文本为空!")
        import config  # 导入配置模块

        logger.info("===== 开始分析报告（优化版） =====")
        logger.info(f"LLM客户端配置: 提供商={self.llm_client.provider}, 模型={self.llm_client.model}")

        # 初始化结果和调试信息
        result = {
            "原始文本": {
                "影像表现": image_text,
                "诊断结论": diagnosis_text
            },
            "结构化数据": {},
            "调试信息": {}
        }
        self.debug_info = {}

        try:
            # 步骤1: 提取核心结构化信息
            if self.status_callback:
                self.status_callback("提取核心信息", 1)

            logger.info("提取核心结构化信息...")
            start_time = time.time()
            core_data = self.extract_core_information(image_text, diagnosis_text)
            extraction_time = time.time() - start_time
            logger.info(f"核心信息提取完成 (用时: {extraction_time:.2f}秒)")
            self.debug_info["LLM_结构化响应"] = core_data

            # 步骤2: 处理提取的数据，包括修复和标准化
            if self.status_callback:
                self.status_callback("数据修复和标准化", 2)

            logger.info("修复和标准化提取的数据...")
            start_time = time.time()
            processed_data = self.process_extracted_data(core_data)
            processing_time = time.time() - start_time
            logger.info(f"数据处理完成 (用时: {processing_time:.2f}秒)")
            self.debug_info["最终结构化数据"] = processed_data

            # 保存处理后的结果
            result["结构化数据"] = processed_data
            self.debug_info["核心信息提取_时间"] = extraction_time
            self.debug_info["数据处理_时间"] = processing_time

            # 步骤3: 如果启用了知识库，使用知识库增强分析结果
            if self.use_knowledge_base and self.knowledge_base:
                if self.status_callback:
                    self.status_callback("知识库增强", 3)

                logger.info("使用知识库增强分析结果...")
                start_time = time.time()
                result["结构化数据"] = self.knowledge_base.enhance_analysis(result["结构化数据"])
                enhance_time = time.time() - start_time
                logger.info(f"知识库增强完成 (用时: {enhance_time:.2f}秒)")
                self.debug_info["知识库增强_时间"] = enhance_time

            # 步骤4: 如果有解剖结构和诊断信息，构建映射关系
            if image_text and diagnosis_text:
                if self.status_callback:
                    self.status_callback("构建映射关系", 4)

                logger.info("构建影像表现与诊断结论的映射关系...")
                start_time = time.time()
                mapping_result = self.build_image_diagnosis_mapping(image_text, diagnosis_text)
                mapping_time = time.time() - start_time
                logger.info(f"映射关系构建完成 (用时: {mapping_time:.2f}秒)")

                result["映射关系"] = mapping_result
                self.debug_info["映射关系构建_时间"] = mapping_time

            # 步骤5: 如果启用了诊断关联功能，构建诊断与病变的关联
            logger.info("检查是否执行诊断关联分析...")
            try:
                diagnosis_association_config = config.PROCESSING_CONFIG.get("diagnosis_association", {})
                is_enabled = diagnosis_association_config.get("enabled", True)
                has_model_assist = hasattr(self, 'model_assist') and self.model_assist is not None

                logger.info(f"诊断关联配置: 启用={is_enabled}, 模型辅助处理器存在={has_model_assist}")

                if is_enabled and has_model_assist:
                    if self.status_callback:
                        self.status_callback("诊断关联分析", 5)

                    # 检查结构化数据中是否有病变特征和诊断信息
                    structured_data = result.get("结构化数据", {})
                    lesions = structured_data.get("病变特征", [])
                    diagnoses = structured_data.get("诊断信息", [])

                    logger.info(f"数据检查: 病变特征={len(lesions)}项, 诊断信息={len(diagnoses)}项")

                    if lesions and diagnoses:
                        logger.info("构建诊断与病变的关联关系...")
                        start_time = time.time()

                        try:
                            # 创建诊断关联器并配置
                            associator = DiagnosisAssociator(self.model_assist.llm_client)

                            # 执行关联分析
                            associations = associator.associate_features_with_diagnoses(
                                lesions,
                                diagnoses,
                                structured_data.get("解剖结构", [])
                            )

                            # 添加关联结果到返回数据
                            result["关联关系"] = associations

                            association_time = time.time() - start_time
                            logger.info(f"诊断关联分析完成 (用时: {association_time:.2f}秒)")
                            logger.info(f"关联结果: 诊断到病变={len(associations.get('诊断到病变映射', {}))}项, 病变到诊断={len(associations.get('病变到诊断映射', {}))}项")
                            self.debug_info["诊断关联分析_时间"] = association_time
                        except Exception as e:
                            logger.error(f"诊断关联建立失败: {str(e)}")
                            result["关联关系"] = {
                                "诊断到病变映射": {},
                                "病变到诊断映射": {},
                                "关联强度": {}
                            }
                            self.debug_info["诊断关联分析_错误"] = str(e)
                    else:
                        logger.warning("缺少病变特征或诊断信息，跳过诊断关联分析")
                        # 为前端提供一个空的关联结构，避免前端显示错误
                        result["关联关系"] = {
                            "诊断到病变映射": {},
                            "病变到诊断映射": {},
                            "关联强度": {}
                        }
                else:
                    logger.info("跳过诊断关联分析: 功能已禁用或模型辅助处理器不可用")
            except Exception as e:
                logger.error(f"诊断关联检查出错: {str(e)}")

            # 更新知识库（如果启用）
            if self.use_knowledge_base and self.knowledge_base:
                # 评估结果质量
                result_quality = 0.8  # 默认质量评分

                # 如果有诊断信息，质量评分提高
                diagnoses_count = len(result.get("结构化数据", {}).get("诊断信息", []))
                if diagnoses_count > 0:
                    result_quality = min(0.7 + diagnoses_count * 0.1, 1.0)  # 每个诊断增加0.1分，最高1.0

                # 检查知识库设置是否允许更新
                if knowledge_settings.should_update_knowledge_base(result_quality):
                    self.knowledge_base.update_with_report(result)
                    logger.info(f"   知识库已更新 (质量评分: {result_quality:.2f})")
                else:
                    logger.info(f"   根据设置，此结果不更新知识库 (质量评分: {result_quality:.2f})")

            logger.info("===== 报告分析完成 =====\n")
        except Exception as e:
            error_msg = f"===== 报告分析出错: {str(e)} ====="
            logger.error(f"{error_msg}\n")
            self.debug_info["分析错误"] = str(e)
            # 出错时仍然返回部分结果

        # 将调试信息添加到结果中
        result["调试信息"] = self.debug_info

        return result

    def learn_from_user_correction(self, original_result: Dict[str, Any], corrected_result: Dict[str, Any]):
        """
        从用户修正中学习

        参数:
            original_result: 原始分析结果
            corrected_result: 用户修正后的结果
        """
        if not self.use_knowledge_base or not self.knowledge_base:
            logger.warning("知识库未启用，无法从用户修正中学习")
            return

        try:
            logger.info("记录用户修正到知识库...")
            self.knowledge_base.learn_from_user_correction(original_result, corrected_result)
            logger.info("用户修正已记录到知识库")
        except Exception as e:
            logger.error(f"记录用户修正时出错: {str(e)}")

    def extract_anatomical_descriptions(self, report_text: str, diagnosis_text: str = "") -> Dict[str, Any]:
        """
        提取报告中解剖结构的描述模式

        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本（可选）

        返回:
            解剖描述模式的结构化数据
        """
        # 合并文本以便分析
        full_text = f"影像表现：\n{report_text}\n\n诊断结论：\n{diagnosis_text}" if diagnosis_text else report_text

        prompt = f"""
        请从以下医学影像报告中提取每个解剖结构的描述模式：

        报告文本：
        {full_text}

        请按以下JSON格式返回结果：
        {{
          "解剖描述模式": [
            {{
              "解剖结构": "肺",
              "描述模式": "含气程度+密度特征+异常影类型",
              "标准表达": ["含气良好", "未见明确异常密度影", "密度增高"],
              "异常类型": ["结节", "肿块", "浸润", "磨玻璃影"]
            }},
            // 更多解剖结构...
          ]
        }}

        要求：
        1. 对每个出现的解剖结构提取描述模式
        2. 标准表达应包含常见的正常和异常描述短语
        3. 异常类型应列出该解剖结构可能出现的病变类型
        """

        try:
            result = self.llm_client.extract_json(prompt)
            # 保存提示词和响应到调试信息
            self.debug_info["解剖描述模式_提示词"] = prompt
            self.debug_info["解剖描述模式_响应"] = result
            return result
        except Exception as e:
            logger.error(f"提取解剖描述模式失败: {str(e)}")
            return {"解剖描述模式": []}