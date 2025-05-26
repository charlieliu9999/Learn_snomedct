"""
双向驱动的报告模版引擎
支持影像→诊断和诊断→描述两种工作流
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import os

from .llm_client import LLMClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TemplateField:
    """模版字段"""
    name: str
    field_type: str  # 'text', 'select', 'multiselect', 'number'
    required: bool
    options: List[str] = None
    default_value: str = ""
    description: str = ""
    snomed_mapping: str = ""

@dataclass
class DiagnosisTemplate:
    """诊断模版"""
    diagnosis_name: str
    snomed_code: str
    description_templates: List[str]
    required_findings: List[str]
    optional_findings: List[str]
    differential_diagnoses: List[str]

class BidirectionalTemplateEngine:
    """双向驱动的报告模版引擎"""

    def __init__(self, llm_client: LLMClient, template_dir: str = None):
        self.llm_client = llm_client

        # 设置模版存储目录
        if template_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            self.template_dir = os.path.join(base_dir, "templates")
        else:
            self.template_dir = template_dir

        os.makedirs(self.template_dir, exist_ok=True)

        # 加载模版
        self.diagnosis_templates = {}
        self._load_templates()

        logger.info(f"双向模版引擎初始化完成，加载了 {len(self.diagnosis_templates)} 个诊断模版")

    def _load_templates(self):
        """加载模版"""
        try:
            # 加载诊断模版
            diagnosis_template_file = os.path.join(self.template_dir, "diagnosis_templates.json")
            if os.path.exists(diagnosis_template_file):
                with open(diagnosis_template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for diag_data in data.get("diagnoses", []):
                        diagnosis = DiagnosisTemplate(**diag_data)
                        self.diagnosis_templates[diagnosis.diagnosis_name] = diagnosis

            # 如果没有模版，创建默认模版
            if not self.diagnosis_templates:
                self._create_default_templates()

        except Exception as e:
            logger.error(f"加载模版失败: {e}")
            self._create_default_templates()

    def _create_default_templates(self):
        """创建默认模版"""
        # 创建默认诊断模版
        default_diagnoses = [
            DiagnosisTemplate(
                diagnosis_name="肺癌",
                snomed_code="363358000",
                description_templates=[
                    "{解剖位置}可见约{大小}大小的{形态}软组织密度影，边缘{边界}",
                    "增强扫描后呈{增强方式}",
                    "周围可见{其他特征}"
                ],
                required_findings=["结节", "肿块"],
                optional_findings=["毛刺征", "胸膜牵拉", "淋巴结肿大"],
                differential_diagnoses=["肺炎", "结核", "转移瘤"]
            ),
            DiagnosisTemplate(
                diagnosis_name="肺炎",
                snomed_code="233604007",
                description_templates=[
                    "{解剖位置}可见{形态}影",
                    "密度{密度特征}，边界{边界特征}",
                    "可伴有{其他特征}"
                ],
                required_findings=["炎性浸润"],
                optional_findings=["胸腔积液", "淋巴结肿大"],
                differential_diagnoses=["肺癌", "结核", "肺栓塞"]
            )
        ]

        for diagnosis in default_diagnoses:
            self.diagnosis_templates[diagnosis.diagnosis_name] = diagnosis

        # 保存默认模版
        self._save_templates()

    def _save_templates(self):
        """保存模版到文件"""
        try:
            # 保存诊断模版
            diagnosis_data = {
                "diagnoses": [asdict(diagnosis) for diagnosis in self.diagnosis_templates.values()]
            }
            diagnosis_file = os.path.join(self.template_dir, "diagnosis_templates.json")
            with open(diagnosis_file, 'w', encoding='utf-8') as f:
                json.dump(diagnosis_data, f, ensure_ascii=False, indent=2)

            logger.info("模版保存成功")

        except Exception as e:
            logger.error(f"保存模版失败: {e}")

    def get_diagnosis_template(self, diagnosis_name: str) -> Optional[DiagnosisTemplate]:
        """获取诊断模版"""
        return self.diagnosis_templates.get(diagnosis_name)

    async def imaging_to_diagnosis(self, imaging_findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        影像→诊断工作流

        Args:
            imaging_findings: 影像发现

        Returns:
            诊断建议
        """
        try:
            # 构建推理提示词
            findings_text = self._format_findings(imaging_findings)

            prompt = f"""
            基于以下影像发现，请推荐可能的诊断：

            影像发现：
            {findings_text}

            请按以下JSON格式返回诊断建议：
            {{
              "primary_diagnosis": {{
                "name": "主要诊断",
                "confidence": 0.0-1.0,
                "reasoning": "推理依据"
              }},
              "differential_diagnoses": [
                {{
                  "name": "鉴别诊断1",
                  "confidence": 0.0-1.0,
                  "reasoning": "推理依据"
                }}
              ],
              "recommended_actions": ["建议的后续行动"]
            }}
            """

            result = self.llm_client.extract_json(prompt)
            return result

        except Exception as e:
            logger.error(f"影像→诊断推理失败: {e}")
            return {"error": str(e)}

    def _format_findings(self, findings: Dict[str, Any]) -> str:
        """格式化影像发现"""
        formatted = []
        for key, value in findings.items():
            if value:
                formatted.append(f"{key}: {value}")
        return "\n".join(formatted)

    def diagnosis_to_description(self, diagnosis_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        诊断→描述工作流

        Args:
            diagnosis_name: 诊断名称
            parameters: 描述参数

        Returns:
            生成的影像描述
        """
        diagnosis_template = self.get_diagnosis_template(diagnosis_name)
        if not diagnosis_template:
            return {"error": f"未找到诊断模版: {diagnosis_name}"}

        try:
            # 使用模版生成描述
            descriptions = []
            for template in diagnosis_template.description_templates:
                description = self._fill_template(template, parameters)
                descriptions.append(description)

            # 生成完整的影像描述
            full_description = "。".join(descriptions) + "。"

            result = {
                "diagnosis": diagnosis_name,
                "snomed_code": diagnosis_template.snomed_code,
                "generated_description": full_description,
                "individual_descriptions": descriptions,
                "required_findings": diagnosis_template.required_findings,
                "optional_findings": diagnosis_template.optional_findings,
                "differential_diagnoses": diagnosis_template.differential_diagnoses,
                "parameters_used": parameters
            }

            return result

        except Exception as e:
            logger.error(f"诊断→描述生成失败: {e}")
            return {"error": str(e)}

    def _fill_template(self, template: str, parameters: Dict[str, Any]) -> str:
        """填充模版参数"""
        filled_template = template

        # 替换模版中的参数
        for param, value in parameters.items():
            placeholder = f"{{{param}}}"
            if placeholder in filled_template:
                filled_template = filled_template.replace(placeholder, str(value))

        # 清理未填充的参数
        filled_template = re.sub(r'\{[^}]+\}', '', filled_template)

        return filled_template.strip()

    def get_diagnosis_list(self) -> List[Dict[str, Any]]:
        """获取诊断列表"""
        diagnosis_list = []
        for diagnosis in self.diagnosis_templates.values():
            diagnosis_info = {
                "diagnosis_name": diagnosis.diagnosis_name,
                "snomed_code": diagnosis.snomed_code,
                "required_findings": diagnosis.required_findings,
                "optional_findings": diagnosis.optional_findings,
                "differential_diagnoses": diagnosis.differential_diagnoses
            }
            diagnosis_list.append(diagnosis_info)

        return diagnosis_list

    def add_diagnosis_template(self, diagnosis_template: DiagnosisTemplate) -> bool:
        """添加诊断模版"""
        try:
            self.diagnosis_templates[diagnosis_template.diagnosis_name] = diagnosis_template
            self._save_templates()
            logger.info(f"诊断模版 {diagnosis_template.diagnosis_name} 添加成功")
            return True
        except Exception as e:
            logger.error(f"添加诊断模版失败: {e}")
            return False

    def update_diagnosis_template(self, diagnosis_name: str, updates: Dict[str, Any]) -> bool:
        """更新诊断模版"""
        if diagnosis_name not in self.diagnosis_templates:
            return False

        try:
            template = self.diagnosis_templates[diagnosis_name]

            # 更新模版属性
            if "snomed_code" in updates:
                template.snomed_code = updates["snomed_code"]
            if "description_templates" in updates:
                template.description_templates = updates["description_templates"]
            if "required_findings" in updates:
                template.required_findings = updates["required_findings"]
            if "optional_findings" in updates:
                template.optional_findings = updates["optional_findings"]
            if "differential_diagnoses" in updates:
                template.differential_diagnoses = updates["differential_diagnoses"]

            self._save_templates()
            logger.info(f"诊断模版 {diagnosis_name} 更新成功")
            return True

        except Exception as e:
            logger.error(f"更新诊断模版失败: {e}")
            return False

    def delete_diagnosis_template(self, diagnosis_name: str) -> bool:
        """删除诊断模版"""
        if diagnosis_name in self.diagnosis_templates:
            del self.diagnosis_templates[diagnosis_name]
            self._save_templates()
            logger.info(f"诊断模版 {diagnosis_name} 删除成功")
            return True
        return False

    def validate_template_parameters(self, diagnosis_name: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证模版参数

        Args:
            diagnosis_name: 诊断名称
            parameters: 参数字典

        Returns:
            (是否有效, 错误信息列表)
        """
        diagnosis_template = self.get_diagnosis_template(diagnosis_name)
        if not diagnosis_template:
            return False, [f"未找到诊断模版: {diagnosis_name}"]

        errors = []

        # 检查必需的发现是否在参数中
        for required_finding in diagnosis_template.required_findings:
            if required_finding not in parameters:
                errors.append(f"缺少必需的发现: {required_finding}")

        # 检查参数值是否有效
        for param, value in parameters.items():
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"参数 {param} 的值不能为空")

        return len(errors) == 0, errors

    def get_template_suggestions(self, findings: List[str]) -> List[Dict[str, Any]]:
        """
        根据发现获取模版建议

        Args:
            findings: 发现列表

        Returns:
            模版建议列表
        """
        suggestions = []

        for diagnosis_name, template in self.diagnosis_templates.items():
            # 计算匹配度
            required_matches = sum(1 for finding in template.required_findings if finding in findings)
            optional_matches = sum(1 for finding in template.optional_findings if finding in findings)

            total_required = len(template.required_findings)
            total_optional = len(template.optional_findings)

            # 计算匹配分数
            required_score = required_matches / total_required if total_required > 0 else 1.0
            optional_score = optional_matches / total_optional if total_optional > 0 else 0.0

            # 综合分数
            overall_score = required_score * 0.8 + optional_score * 0.2

            if overall_score > 0.3:  # 只返回匹配度较高的建议
                suggestion = {
                    "diagnosis_name": diagnosis_name,
                    "snomed_code": template.snomed_code,
                    "match_score": overall_score,
                    "required_matches": required_matches,
                    "total_required": total_required,
                    "optional_matches": optional_matches,
                    "missing_required": [f for f in template.required_findings if f not in findings]
                }
                suggestions.append(suggestion)

        # 按匹配分数排序
        suggestions.sort(key=lambda x: x["match_score"], reverse=True)

        return suggestions[:5]  # 返回前5个建议

    def export_templates(self, file_path: str) -> bool:
        """
        导出模版到文件

        Args:
            file_path: 导出文件路径

        Returns:
            是否导出成功
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "template_count": len(self.diagnosis_templates),
                "templates": [asdict(template) for template in self.diagnosis_templates.values()]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"模版导出成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"模版导出失败: {e}")
            return False

    def import_templates(self, file_path: str, overwrite: bool = False) -> bool:
        """
        从文件导入模版

        Args:
            file_path: 导入文件路径
            overwrite: 是否覆盖现有模版

        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            imported_count = 0
            skipped_count = 0

            for template_data in import_data.get("templates", []):
                diagnosis_name = template_data["diagnosis_name"]

                if diagnosis_name in self.diagnosis_templates and not overwrite:
                    skipped_count += 1
                    continue

                template = DiagnosisTemplate(**template_data)
                self.diagnosis_templates[diagnosis_name] = template
                imported_count += 1

            if imported_count > 0:
                self._save_templates()

            logger.info(f"模版导入完成: 导入 {imported_count} 个，跳过 {skipped_count} 个")
            return True

        except Exception as e:
            logger.error(f"模版导入失败: {e}")
            return False
