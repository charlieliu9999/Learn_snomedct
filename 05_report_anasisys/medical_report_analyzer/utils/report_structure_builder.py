"""
报告结构生成器模块，基于解剖描述模式构建标准化报告结构
"""

import logging
from typing import Dict, List, Any, Optional

from .knowledge_base import MedicalKnowledgeBase
from .llm_client import LLMClient
from .model_assist_processor import ModelAssistProcessor

logger = logging.getLogger(__name__)

class ReportStructureBuilder:
    """报告结构生成器，基于解剖描述模式构建标准化报告结构"""
    
    def __init__(self, knowledge_base: MedicalKnowledgeBase, llm_client: LLMClient):
        self.kb = knowledge_base
        self.llm = llm_client
        # 初始化模型辅助处理器
        self.model_processor = ModelAssistProcessor(llm_client)
        logger.info("已初始化报告结构生成器的模型辅助处理器")
    
    def build_report_structure(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于结构化数据构建报告结构
        
        参数:
            structured_data: 结构化的解剖、病变和诊断数据
            
        返回:
            标准化的报告结构
        """
        report_structure = {
            "影像表现": {},
            "诊断结论": []
        }
        
        # 解析解剖结构和病变特征
        anatomical = structured_data.get("解剖结构", [])
        lesions = structured_data.get("病变特征", [])
        diagnoses = structured_data.get("诊断信息", [])
        
        # 1. 组织解剖结构
        structure_map = self._organize_structures(anatomical)
        
        # 2. 将病变特征与解剖结构关联
        lesion_map = self._map_lesions_to_structures(lesions, structure_map)
        
        # 3. 为每个解剖结构生成描述
        for structure, info in structure_map.items():
            structure_lesions = lesion_map.get(structure, [])
            description = self._generate_structure_description(structure, structure_lesions)
            report_structure["影像表现"][structure] = description
        
        # 4. 组织诊断结论
        for diagnosis in diagnoses:
            report_structure["诊断结论"].append(
                self._format_diagnosis(diagnosis)
            )
        
        return report_structure
    
    def _organize_structures(self, anatomical: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """组织解剖结构"""
        result = {}
        
        # 1. 收集所有结构及其关系
        for structure in anatomical:
            std_name = structure.get("标准名", "")
            if not std_name:
                continue
                
            result[std_name] = {
                "原文": structure.get("原文", ""),
                "父结构": structure.get("父结构", ""),
                "子结构": []
            }
        
        # 2. 建立父子关系
        for name, info in result.items():
            parent = info["父结构"]
            if parent and parent in result:
                if name not in result[parent]["子结构"]:
                    result[parent]["子结构"].append(name)
        
        return result
    
    def _map_lesions_to_structures(self, lesions: List[Dict[str, str]], 
                           structure_map: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
        """将病变特征映射到解剖结构"""
        # 使用模型辅助处理器进行智能映射
        return self.model_processor.map_lesions_to_structures(lesions, structure_map)
    
    def _generate_structure_description(self, structure: str, lesions: List[Dict[str, str]]) -> str:
        """为特定解剖结构生成描述"""
        # 1. 获取描述模式
        description_patterns = self.kb.get_description_patterns(structure)
        
        # 2. 如果没有病变，使用正常描述
        if not lesions:
            normal_exprs = description_patterns.get("标准表达", [])
            normal_exprs = [e for e in normal_exprs if "正常" in e or "良好" in e or "未见" in e]
            
            if normal_exprs:
                return " ".join(normal_exprs[:3])  # 使用前3个正常表达
            else:
                return f"{structure}未见异常"
        
        # 3. 有病变，使用异常描述模板
        descriptions = []
        
        for lesion in lesions:
            # 从病变特征构建描述
            desc_parts = []
            
            # 添加位置
            if "解剖位置" in lesion and lesion["解剖位置"]:
                desc_parts.append(f"{lesion['解剖位置']}可见")
            
            # 添加数量
            if "数量" in lesion and lesion["数量"]:
                desc_parts.append(lesion["数量"])
            
            # 添加大小
            if "大小" in lesion and lesion["大小"]:
                desc_parts.append(f"大小约{lesion['大小']}")
            
            # 添加密度
            if "密度" in lesion and lesion["密度"]:
                desc_parts.append(lesion["密度"])
            
            # 添加形态
            if "形态" in lesion and lesion["形态"]:
                desc_parts.append(f"呈{lesion['形态']}")
            
            # 添加边界
            if "边界" in lesion and lesion["边界"]:
                desc_parts.append(f"边界{lesion['边界']}")
            
            # 添加分布
            if "分布" in lesion and lesion["分布"]:
                desc_parts.append(f"{lesion['分布']}")
            
            # 添加其他特征
            if "其他特征" in lesion and lesion["其他特征"]:
                desc_parts.append(lesion["其他特征"])
            
            descriptions.append(" ".join(desc_parts))
        
        return "。".join(descriptions) + "。"
    
    def _format_diagnosis(self, diagnosis: Dict[str, str]) -> Dict[str, str]:
        """格式化诊断信息"""
        result = {
            "类型": diagnosis.get("类型", "其他"),
            "内容": diagnosis.get("描述", ""),
            "置信度": diagnosis.get("置信度", "中")
        }
        
        return result
        
    def improve_report_structure_with_llm(self, report_structure: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM优化报告结构"""
        # 准备优化影像表现部分
        description_text = ""
        for structure, desc in report_structure["影像表现"].items():
            description_text += f"{structure}: {desc}\n"
        
        # 准备诊断结论部分
        diagnosis_text = ""
        for diag in report_structure["诊断结论"]:
            diagnosis_text += f"[{diag['类型']}] {diag['内容']}\n"
        
        # 使用LLM优化
        prompt = f"""
        请优化以下医学影像报告，使其更加专业、简洁和符合标准格式：
        
        【影像表现】
        {description_text}
        
        【诊断结论】
        {diagnosis_text}
        
        要求：
        1. 保留所有医学信息和发现
        2. 使用标准医学术语和格式
        3. 让描述更流畅连贯
        4. 保持简洁，去除冗余
        5. 返回结果格式：
        ```
        【影像表现】
        (优化后的影像表现)
        
        【诊断结论】
        (优化后的诊断结论)
        ```
        """
        
        try:
            response = self.llm.generate(prompt)
            
            # 提取优化后的内容
            import re
            image_part = re.search(r"【影像表现】\s*(.*?)\s*【诊断结论】", response, re.DOTALL)
            diagnosis_part = re.search(r"【诊断结论】\s*(.*?)\s*(?:```|$)", response, re.DOTALL)
            
            if image_part and diagnosis_part:
                return {
                    "影像表现": image_part.group(1).strip(),
                    "诊断结论": diagnosis_part.group(1).strip()
                }
            else:
                # 如果匹配失败，返回原始结构
                return {
                    "影像表现": description_text,
                    "诊断结论": diagnosis_text
                }
        except Exception as e:
            logger.error(f"优化报告结构失败: {str(e)}")
            # 返回原始结构
            return {
                "影像表现": description_text,
                "诊断结论": diagnosis_text
            }
