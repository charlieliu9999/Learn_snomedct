"""
结果验证器 - 用于检查和修正结构化分析结果的质量问题
"""

import logging
from typing import Dict, List, Any, Tuple
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StructuredResultValidator:
    """结构化结果验证器"""
    
    def __init__(self):
        """初始化验证器"""
        # 诊断分类映射
        self.diagnosis_category_map = {
            '脑萎缩': '变性病变',
            '脑梗塞': '血管相关',
            '脑出血': '血管相关',
            '脑肿瘤': '肿瘤相关',
            '脑炎': '感染相关',
            '脑积水': '解剖异常',
            '钙化': '解剖异常',
            '囊肿': '解剖异常',
            '纤维化': '变性病变',
            '硬化': '变性病变'
        }
        
        # 禁用的映射描述
        self.forbidden_mapping_terms = [
            '综合影像表现',
            '整体影像表现', 
            '总体表现',
            '全部影像发现'
        ]
    
    def validate_structured_result(self, result: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        验证结构化分析结果的质量
        
        参数:
            result: 结构化分析结果
            
        返回:
            (是否通过验证, 问题列表, 修正后的结果)
        """
        issues = []
        corrected_result = result.copy()
        
        try:
            # 验证解剖结构
            if "结构化数据" in result and "解剖结构" in result["结构化数据"]:
                structures = result["结构化数据"]["解剖结构"]
                corrected_structures, structure_issues = self._validate_anatomical_structures(structures)
                issues.extend(structure_issues)
                corrected_result["结构化数据"]["解剖结构"] = corrected_structures
            
            # 验证诊断信息
            if "结构化数据" in result and "诊断信息" in result["结构化数据"]:
                diagnoses = result["结构化数据"]["诊断信息"]
                corrected_diagnoses, diagnosis_issues = self._validate_diagnosis_info(diagnoses)
                issues.extend(diagnosis_issues)
                corrected_result["结构化数据"]["诊断信息"] = corrected_diagnoses
            
            # 验证病变特征缺失
            if "结构化数据" in result and "原始文本" in result:
                features = result["结构化数据"].get("病变特征", [])
                image_text = result["原始文本"].get("影像表现", "")
                feature_issues, reconstructed_features = self._validate_features_missing(features, image_text)
                issues.extend(feature_issues)
                if reconstructed_features:
                    corrected_result["结构化数据"]["病变特征"] = reconstructed_features
            
            # 验证影像诊断映射
            if "结构化数据" in result:
                mappings = result["结构化数据"].get("影像诊断映射", [])
                features = corrected_result["结构化数据"].get("病变特征", [])  # 使用修正后的病变特征
                diagnoses = corrected_result["结构化数据"].get("诊断信息", [])
                corrected_mappings, mapping_issues = self._validate_mappings(mappings, features, diagnoses)
                issues.extend(mapping_issues)
                corrected_result["结构化数据"]["影像诊断映射"] = corrected_mappings
            
            # 添加验证信息
            corrected_result["验证信息"] = {
                "验证通过": len(issues) == 0,
                "发现问题数": len(issues),
                "问题列表": issues,
                "验证时间": "2025-01-06T13:30:00+00:00"
            }
            
            return len(issues) == 0, issues, corrected_result
            
        except Exception as e:
            error_msg = f"验证过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg], result
    
    def _validate_anatomical_structures(self, structures: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[str]]:
        """验证解剖结构"""
        issues = []
        corrected_structures = []
        seen_original_texts = set()
        
        for structure in structures:
            original_text = structure.get("原文", "")
            standard_name = structure.get("标准名", "")
            parent_structure = structure.get("父结构", "")
            
            # 检查重复 - 修复：不跳过重复项，而是只记录一次
            if original_text in seen_original_texts:
                issues.append(f"解剖结构重复: '{original_text}'")
                # 不跳过，保留第一个并记录问题
            else:
                seen_original_texts.add(original_text)
            
            # 检查信息丢失
            corrected_structure = structure.copy()
            
            # 保持重要的修饰词
            if "双侧" in original_text and "双侧" not in standard_name:
                corrected_structure["标准名"] = f"双侧{standard_name}"
                issues.append(f"修正标准名以保留位置信息: '{original_text}' -> '{corrected_structure['标准名']}'")
            
            if "幕上" in original_text and "幕上" not in standard_name:
                corrected_structure["标准名"] = f"幕上{standard_name}"
                issues.append(f"修正标准名以保留位置信息: '{original_text}' -> '{corrected_structure['标准名']}'")
            
            # 检查是否是重复的"脑沟、裂"拆分问题
            if original_text == "脑沟、裂" and (standard_name == "脑沟" or standard_name == "脑裂"):
                if standard_name == "脑裂":
                    # 跳过"脑裂"重复项
                    issues.append(f"错误拆分: '{original_text}'被拆分为脑沟和脑裂，应保持为一个整体")
                    continue
                else:
                    # 修正为完整概念
                    corrected_structure["标准名"] = "脑沟脑裂"
                    issues.append(f"修正拆分问题: '{original_text}' -> '{corrected_structure['标准名']}'")
            
            corrected_structures.append(corrected_structure)
        
        return corrected_structures, issues
    
    def _validate_diagnosis_info(self, diagnoses: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[str]]:
        """验证诊断信息"""
        issues = []
        corrected_diagnoses = []
        
        for diagnosis in diagnoses:
            diagnosis_type = diagnosis.get("类型", "")
            description = diagnosis.get("描述", "")
            
            corrected_diagnosis = diagnosis.copy()
            
            # 检查诊断分类是否准确
            for condition, correct_category in self.diagnosis_category_map.items():
                if condition in description and diagnosis_type != correct_category:
                    corrected_diagnosis["类型"] = correct_category
                    issues.append(f"修正诊断分类: '{description}' 从 '{diagnosis_type}' 改为 '{correct_category}'")
                    break
            
            corrected_diagnoses.append(corrected_diagnosis)
        
        return corrected_diagnoses, issues
    
    def _validate_features_missing(self, features: List[Dict[str, Any]], image_text: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """验证病变特征缺失"""
        issues = []
        reconstructed_features = features.copy() if features else []
        
        # 定义病变特征关键词
        pathology_keywords = [
            '低密度影', '高密度影', '密度影', '占位', '肿块', '结节', 
            '钙化', '出血', '水肿', '强化', '移位', '受压', '扩大', 
            '增宽', '变窄', '狭窄', '积液', '囊肿', '病变', '异常',
            '梗塞', '栓塞', '斑片', '片状', '团状', '条状'
        ]
        
        # 检查是否病变特征为空但影像表现中包含病变描述
        if len(features) == 0 and image_text:
            # 检查是否包含病变特征关键词
            contains_pathology = any(keyword in image_text for keyword in pathology_keywords)
            
            if contains_pathology:
                issues.append("严重问题：检测到影像表现中包含病变描述，但病变特征为空")
                
                # 尝试基于关键词重构基本的病变特征
                reconstructed_features = self._reconstruct_features_from_text(image_text)
                
                if reconstructed_features:
                    issues.append(f"自动重构了 {len(reconstructed_features)} 个病变特征")
                else:
                    issues.append("自动重构病变特征失败，需要重新分析")
        
        # 检查现有病变特征的合理性
        elif len(features) > 0:
            for feature in features:
                feature_name = feature.get("名称", "")
                # 检查特征名称是否与影像文本相关
                if feature_name and not any(keyword in feature_name for keyword in pathology_keywords):
                    issues.append(f"病变特征可能不准确：'{feature_name}' 缺少病理描述")
        
        return issues, reconstructed_features
    
    def _reconstruct_features_from_text(self, image_text: str) -> List[Dict[str, Any]]:
        """从影像表现文本中重构基本的病变特征"""
        reconstructed = []
        
        # 基于常见模式进行简单的病变特征提取
        import re
        
        # 模式1: 解剖位置 + 见 + 特征描述
        pattern1 = r'([^，。]+?)见([^，。]*?(?:密度影|占位|肿块|结节|钙化|病变)[^，。]*?)(?:[，。]|$)'
        matches1 = re.findall(pattern1, image_text)
        
        for i, (location, description) in enumerate(matches1):
            location = location.strip()
            description = description.strip()
            if location and description:
                reconstructed.append({
                    "名称": f"{location}-{description}",
                    "特征": {
                        "解剖位置": location,
                        "大小": "",
                        "形态": "",
                        "特性": description,
                        "边界": "",
                        "数量": "",
                        "分布": "",
                        "其他特征": "自动重构"
                    }
                })
        
        # 模式2: 结构 + 形容词（如：移位、受压、扩大等）
        pattern2 = r'([^，。]+?)(移位|受压|扩大|增宽|变窄|狭窄)(?:[，。]|$)'
        matches2 = re.findall(pattern2, image_text)
        
        for location, change in matches2:
            location = location.strip()
            if location and change:
                reconstructed.append({
                    "名称": f"{location}-{change}",
                    "特征": {
                        "解剖位置": location,
                        "大小": "",
                        "形态": "",
                        "特性": change,
                        "边界": "",
                        "数量": "",
                        "分布": "",
                        "其他特征": "自动重构"
                    }
                })
        
        # 模式3: 强化模式
        pattern3 = r'(.*?)呈([^，。]*?强化[^，。]*?)(?:[，。]|$)'
        matches3 = re.findall(pattern3, image_text)
        
        for location, enhancement in matches3:
            location = location.strip() if location else "病变"
            enhancement = enhancement.strip()
            if enhancement:
                reconstructed.append({
                    "名称": f"{location}-{enhancement}",
                    "特征": {
                        "解剖位置": location,
                        "大小": "",
                        "形态": "",
                        "特性": enhancement,
                        "边界": "",
                        "数量": "",
                        "分布": "",
                        "其他特征": "自动重构-强化特征"
                    }
                })
        
        return reconstructed
    
    def _validate_mappings(self, mappings: List[Dict[str, str]], features: List[Dict[str, Any]], diagnoses: List[Dict[str, Any]] = None) -> Tuple[List[Dict[str, str]], List[str]]:
        """验证影像诊断映射"""
        issues = []
        corrected_mappings = []
        
        # 获取所有病变特征名称
        feature_names = [f.get("名称", "") for f in features if f.get("名称")]
        
        for mapping in mappings:
            finding = mapping.get("影像发现", "")
            diagnosis = mapping.get("对应诊断", "")
            confidence = mapping.get("映射置信度", "")
            
            # 检查是否使用了禁用的模糊描述
            if finding in self.forbidden_mapping_terms:
                issues.append(f"使用了禁用的模糊描述: '{finding}'")
                
                # 尝试用具体的病变特征替换
                if feature_names:
                    for feature_name in feature_names:
                        corrected_mapping = {
                            "影像发现": feature_name,
                            "对应诊断": diagnosis,
                            "映射置信度": "高"
                        }
                        corrected_mappings.append(corrected_mapping)
                    issues.append(f"已替换为具体的影像发现: {feature_names}")
                else:
                    # 如果没有具体特征，保留原映射但标记问题
                    corrected_mappings.append(mapping)
            else:
                corrected_mappings.append(mapping)
        
        return corrected_mappings, issues
    
    def generate_quality_report(self, result: Dict[str, Any]) -> str:
        """生成质量评估报告"""
        is_valid, issues, corrected_result = self.validate_structured_result(result)
        
        report = f"""
# 结构化分析质量评估报告

## 总体评估
- 验证状态: {'✅ 通过' if is_valid else '❌ 未通过'}
- 发现问题: {len(issues)} 个

## 问题详情
"""
        
        if issues:
            for i, issue in enumerate(issues, 1):
                report += f"{i}. {issue}\n"
        else:
            report += "✅ 未发现质量问题\n"
        
        report += f"""
## 数据统计
- 解剖结构数量: {len(result.get('结构化数据', {}).get('解剖结构', []))}
- 病变特征数量: {len(result.get('结构化数据', {}).get('病变特征', []))}
- 诊断信息数量: {len(result.get('结构化数据', {}).get('诊断信息', []))}
- 映射关系数量: {len(result.get('结构化数据', {}).get('影像诊断映射', []))}

## 建议
{'需要根据上述问题进行修正' if issues else '结果质量良好，可以直接使用'}
"""
        
        return report

# 使用示例
if __name__ == "__main__":
    validator = StructuredResultValidator()
    
    # 测试示例
    sample_result = {
        "结构化数据": {
            "解剖结构": [
                {"原文": "双侧大脑半球", "标准名": "大脑半球", "父结构": "脑"}
            ],
            "诊断信息": [
                {"类型": "其他发现", "描述": "脑萎缩"}
            ],
            "影像诊断映射": [
                {"影像发现": "综合影像表现", "对应诊断": "脑萎缩", "映射置信度": "低"}
            ]
        }
    }
    
    is_valid, issues, corrected = validator.validate_structured_result(sample_result)
    print(f"验证结果: {is_valid}")
    print(f"问题: {issues}")
    print("\n质量报告:")
    print(validator.generate_quality_report(sample_result)) 