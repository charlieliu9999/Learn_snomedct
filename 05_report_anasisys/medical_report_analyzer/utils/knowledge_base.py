"""
医学知识库模块，用于存储和检索结构化信息
"""

import os
import json
import logging
from typing import Dict, List, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicalKnowledgeBase:
    """医学知识库，用于存储和检索结构化信息"""
    
    def __init__(self, db_path=None):
        """
        初始化医学知识库
        
        参数:
            db_path: 知识库文件路径，默认在data目录下
        """
        if db_path is None:
            # 默认在项目data目录下
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(os.path.join(base_dir, "knowledge"), exist_ok=True)
            self.db_path = os.path.join(base_dir, "knowledge", "medical_knowledge_base.json")
        else:
            self.db_path = db_path
            
        self.knowledge = self._load_knowledge()
        logger.info(f"医学知识库初始化完成，路径: {self.db_path}")
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """加载知识库"""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 初始化空知识库
            return {
                "解剖结构关系": {},
                "常见诊断": {},
                "特征-诊断映射": {},
                "用户修正记录": {}
            }
    
    def update_with_report(self, report_result: Dict[str, Any]):
        """
        使用新报告结果更新知识库
        
        参数:
            report_result: 报告分析结果
        """
        # 更新解剖结构关系
        if "解剖结构" in report_result.get("结构化数据", {}):
            for structure in report_result["结构化数据"]["解剖结构"]:
                self._update_anatomical_relation(structure)
        
        # 更新诊断信息
        if "诊断信息" in report_result.get("结构化数据", {}):
            for diagnosis in report_result["结构化数据"]["诊断信息"]:
                self._update_diagnosis_stats(diagnosis)
        
        # 更新影像-诊断映射关系
        if "影像诊断映射" in report_result.get("结构化数据", {}):
            mapping = report_result["结构化数据"]["影像诊断映射"]
            if "影像发现与诊断映射" in mapping:
                for item in mapping["影像发现与诊断映射"]:
                    self._update_feature_diagnosis_mapping(item)
        
        # 保存更新后的知识库
        self._save_knowledge()
    
    def _update_anatomical_relation(self, structure: Dict[str, str]):
        """
        更新解剖结构关系
        
        参数:
            structure: 解剖结构数据
        """
        if "标准名" in structure and "父结构" in structure:
            std_name = structure["标准名"]
            parent = structure["父结构"]
            
            if std_name not in self.knowledge["解剖结构关系"]:
                self.knowledge["解剖结构关系"][std_name] = {"父结构": parent, "计数": 1}
            else:
                # 投票决定最常见的父结构关系
                current = self.knowledge["解剖结构关系"][std_name]
                if current["父结构"] == parent:
                    current["计数"] += 1
                else:
                    # 记录不同的父结构关系并计票
                    if "父结构映射" not in current:
                        current["父结构映射"] = {}
                    
                    if parent in current["父结构映射"]:
                        current["父结构映射"][parent] += 1
                    else:
                        current["父结构映射"][parent] = 1
                    
                    # 如果新的父结构出现次数更多，则更新主要父结构
                    if current["父结构映射"][parent] > current["计数"]:
                        current["父结构"] = parent
                        current["计数"] = current["父结构映射"][parent]
    
    def _update_diagnosis_stats(self, diagnosis: Dict[str, str]):
        """
        更新诊断统计信息
        
        参数:
            diagnosis: 诊断信息
        """
        if "类型" in diagnosis and "描述" in diagnosis:
            diag_type = diagnosis["类型"]
            description = diagnosis["描述"]
            
            if description not in self.knowledge["常见诊断"]:
                self.knowledge["常见诊断"][description] = {
                    "计数": 1,
                    "类型分布": {diag_type: 1}
                }
            else:
                current = self.knowledge["常见诊断"][description]
                current["计数"] += 1
                
                if diag_type in current["类型分布"]:
                    current["类型分布"][diag_type] += 1
                else:
                    current["类型分布"][diag_type] = 1
    
    def _update_feature_diagnosis_mapping(self, mapping_item: Dict[str, str]):
        """
        更新影像特征与诊断的映射关系
        
        参数:
            mapping_item: 映射项
        """
        if "影像发现" in mapping_item and "对应诊断" in mapping_item:
            feature = mapping_item["影像发现"]
            diagnosis = mapping_item["对应诊断"]
            
            # 使用影像发现作为键
            if feature not in self.knowledge["特征-诊断映射"]:
                self.knowledge["特征-诊断映射"][feature] = {
                    diagnosis: 1
                }
            else:
                current = self.knowledge["特征-诊断映射"][feature]
                if diagnosis in current:
                    current[diagnosis] += 1
                else:
                    current[diagnosis] = 1
    
    def learn_from_user_correction(self, original_result: Dict[str, Any], corrected_result: Dict[str, Any]):
        """
        从用户修正中学习
        
        参数:
            original_result: 原始分析结果
            corrected_result: 用户修正后的结果
        """
        try:
            # 记录修正的解剖结构
            if ("解剖结构" in original_result.get("结构化数据", {}) and 
                "解剖结构" in corrected_result.get("结构化数据", {})):
                
                orig_structures = {s.get("原文", ""): s for s in original_result["结构化数据"]["解剖结构"]}
                corr_structures = {s.get("原文", ""): s for s in corrected_result["结构化数据"]["解剖结构"]}
                
                for key, corr_struct in corr_structures.items():
                    if key and key in orig_structures and orig_structures[key] != corr_struct:
                        correction_key = f"解剖结构:{key}"
                        
                        if correction_key not in self.knowledge["用户修正记录"]:
                            self.knowledge["用户修正记录"][correction_key] = []
                        
                        self.knowledge["用户修正记录"][correction_key].append({
                            "原始": orig_structures[key],
                            "修正": corr_struct,
                            "计数": 1
                        })
            
            # 记录修正的诊断信息
            if ("诊断信息" in original_result.get("结构化数据", {}) and 
                "诊断信息" in corrected_result.get("结构化数据", {})):
                
                # 仅简单记录有修正的事实，不详细跟踪具体修改
                self.knowledge["用户修正记录"]["诊断修正次数"] = self.knowledge["用户修正记录"].get("诊断修正次数", 0) + 1
            
            # 保存修正记录
            self._save_knowledge()
            logger.info("用户修正已记录到知识库")
            
        except Exception as e:
            logger.error(f"记录用户修正时出错: {str(e)}")
    
    def get_structure_parent(self, structure_name: str) -> str:
        """
        获取解剖结构的父结构
        
        参数:
            structure_name: 解剖结构名称
            
        返回:
            父结构名称，未知则返回空字符串
        """
        if structure_name in self.knowledge["解剖结构关系"]:
            return self.knowledge["解剖结构关系"][structure_name]["父结构"]
        return ""
    
    def get_common_diagnosis_for_feature(self, feature: str) -> List[str]:
        """
        获取与特定影像特征相关的常见诊断
        
        参数:
            feature: 影像特征描述
            
        返回:
            相关诊断列表，按频率排序
        """
        if feature in self.knowledge["特征-诊断映射"]:
            # 按计数降序排列
            mapping = self.knowledge["特征-诊断映射"][feature]
            return sorted(mapping.keys(), key=lambda k: mapping[k], reverse=True)
        return []
    
    def update_anatomical_description_patterns(self, description_patterns: List[Dict[str, Any]]):
        """
        更新解剖结构描述模式
        
        参数:
            description_patterns: 描述模式列表
        """
        if "解剖描述模式" not in self.knowledge:
            self.knowledge["解剖描述模式"] = {}
        
        for pattern in description_patterns:
            structure = pattern.get("解剖结构", "")
            if not structure:
                continue
                
            if structure not in self.knowledge["解剖描述模式"]:
                self.knowledge["解剖描述模式"][structure] = {
                    "描述模式": pattern.get("描述模式", ""),
                    "标准表达": pattern.get("标准表达", []),
                    "异常类型": pattern.get("异常类型", []),
                    "计数": 1
                }
            else:
                # 更新现有条目
                current = self.knowledge["解剖描述模式"][structure]
                current["计数"] += 1
                
                # 合并标准表达和异常类型（去重）
                std_exprs = set(current["标准表达"])
                for expr in pattern.get("标准表达", []):
                    std_exprs.add(expr)
                current["标准表达"] = list(std_exprs)
                    
                abnormals = set(current["异常类型"])
                for abnormal in pattern.get("异常类型", []):
                    abnormals.add(abnormal)
                current["异常类型"] = list(abnormals)
        
        # 保存更新后的知识库
        self._save_knowledge()
    
    def get_description_patterns(self, structure_name: str = None) -> Dict[str, Any]:
        """
        获取解剖结构的描述模式
        
        参数:
            structure_name: 解剖结构名称，如果不指定则返回所有
        
        返回:
            描述模式数据
        """
        if "解剖描述模式" not in self.knowledge:
            return {}
            
        if structure_name:
            return self.knowledge["解剖描述模式"].get(structure_name, {})
        else:
            return self.knowledge["解剖描述模式"]
    
    def _save_knowledge(self):
        """保存知识库到文件"""
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
            logger.debug(f"知识库已保存到 {self.db_path}")
        except Exception as e:
            logger.error(f"保存知识库时发生错误: {str(e)}")
            
    def enhance_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用知识库增强分析结果
        
        参数:
            data: 原始分析数据
            
        返回:
            增强后的数据
        """
        try:
            logger.info("使用知识库增强分析结果...")
            enhanced_data = data.copy()
            
            # 1. 增强解剖结构信息
            if "解剖结构" in enhanced_data and enhanced_data["解剖结构"]:
                for structure in enhanced_data["解剖结构"]:
                    if "标准名" in structure:
                        # 如果知识库中有更好的父结构信息，使用它
                        parent = self.get_structure_parent(structure["标准名"])
                        if parent and ("父结构" not in structure or not structure["父结构"]):
                            structure["父结构"] = parent
                            structure["来源"] = "知识库增强"
            
            # 2. 增强病变特征信息（暂无具体逻辑）
            
            # 3. 增强诊断信息
            if "病变特征" in enhanced_data and enhanced_data["病变特征"] and \
               "诊断信息" in enhanced_data and not enhanced_data["诊断信息"]:
                # 如果有病变特征但没有诊断信息，尝试从知识库提供可能的诊断
                possible_diagnoses = set()
                for feature in enhanced_data["病变特征"]:
                    if "形态" in feature and feature["形态"]:
                        diagnoses = self.get_common_diagnosis_for_feature(feature["形态"])
                        for diag in diagnoses:
                            possible_diagnoses.add(diag)
                
                # 添加可能的诊断（如果有）
                if possible_diagnoses:
                    enhanced_data["知识库诊断建议"] = list(possible_diagnoses)
                    logger.info(f"知识库推荐了 {len(possible_diagnoses)} 项可能的诊断")
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"知识库增强分析结果失败: {str(e)}")
            return data  # 出错时返回原始数据