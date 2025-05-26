"""
关系建模模块，负责构建影像与诊断之间的关联关系模型
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from .llm_client import LLMClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RelationshipBuilder:
    """影像-诊断关系建模器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化关系建模器
        
        参数:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        self.feature_diagnosis_pairs = []
        self.knowledge_base = {}
    
    def add_mapping(self, mapping: Dict[str, Any]) -> None:
        """
        添加一个影像-诊断映射到数据集
        
        参数:
            mapping: 映射字典，包含诊断列表、影像特征列表和映射关系
        """
        if not mapping or not isinstance(mapping, dict):
            return
        
        # 确保mapping包含必要的键
        if not all(k in mapping for k in ["诊断列表", "影像特征列表", "映射关系"]):
            logger.warning("映射数据格式不正确，缺少必要的字段")
            return
        
        # 提取映射关系
        for relation in mapping.get("映射关系", []):
            diagnosis = relation.get("诊断", "")
            if not diagnosis:
                continue
            
            for feature in relation.get("支持特征", []):
                self.feature_diagnosis_pairs.append({
                    "feature": feature,
                    "diagnosis": diagnosis,
                    "support_level": relation.get("支持程度", "中"),
                    "explanation": relation.get("解释", "")
                })
    
    def build_probability_model(self) -> Dict[str, Any]:
        """
        基于已添加的映射构建概率模型
        
        返回:
            概率模型字典
        """
        if not self.feature_diagnosis_pairs:
            logger.warning("没有足够的数据来构建概率模型")
            return {}
        
        # 基本统计信息
        diagnosis_counter = Counter([pair["diagnosis"] for pair in self.feature_diagnosis_pairs])
        features_by_diagnosis = defaultdict(list)
        
        for pair in self.feature_diagnosis_pairs:
            features_by_diagnosis[pair["diagnosis"]].append(pair["feature"])
        
        # 构建简单的概率模型
        model = {
            "诊断频率": {k: v/len(self.feature_diagnosis_pairs) for k, v in diagnosis_counter.items()},
            "诊断特征关联": {}
        }
        
        # 使用LLM总结每种诊断的关键特征
        for diagnosis, features in features_by_diagnosis.items():
            # 过滤掉出现次数少于2的诊断（可能是噪声）
            if diagnosis_counter[diagnosis] < 2:
                continue
            
            prompt = f"""
            基于以下与"{diagnosis}"相关的影像特征，总结该诊断的关键影像学特征和关联强度。
            
            影像特征:
            {json.dumps(features, ensure_ascii=False, indent=2)}
            
            请分析这些特征，确定对该诊断最具鉴别意义的特征，并按以下JSON格式返回:
            {{
              "诊断": "{diagnosis}",
              "关键特征": [
                {{"特征": "特征1描述", "关联强度": "强/中/弱", "出现频率": "高/中/低"}},
                {{"特征": "特征2描述", "关联强度": "强/中/弱", "出现频率": "高/中/低"}},
                ...
              ],
              "特征组合": [
                {{"组合描述": "特征1+特征2", "诊断价值": "高/中/低"}}
              ],
              "鉴别要点": "该诊断的关键鉴别要点..."
            }}
            """
            
            try:
                result = self.llm_client.extract_json(prompt)
                if isinstance(result, dict) and "关键特征" in result:
                    model["诊断特征关联"][diagnosis] = result
            except Exception as e:
                logger.error(f"为诊断 '{diagnosis}' 构建特征关联时出错: {str(e)}")
        
        return model
    
    def extract_diagnostic_guidelines(self) -> Dict[str, Any]:
        """
        根据已有的映射关系，提取诊断指南
        
        返回:
            诊断指南字典
        """
        if not self.feature_diagnosis_pairs:
            logger.warning("没有足够的数据来提取诊断指南")
            return {}
        
        # 收集所有诊断
        all_diagnoses = list(set([pair["diagnosis"] for pair in self.feature_diagnosis_pairs]))
        
        # 使用LLM生成诊断指南
        prompt = f"""
        基于胸部CT的影像特征和诊断数据，为以下诊断生成诊断指南。
        
        诊断列表:
        {json.dumps(all_diagnoses, ensure_ascii=False, indent=2)}
        
        请为每个诊断提供以下信息：
        1. 典型的影像学表现
        2. 关键的鉴别诊断特征
        3. 容易混淆的疾病
        4. 诊断的置信度评估标准
        
        请按以下JSON格式返回:
        {{
          "诊断指南": [
            {{
              "诊断名称": "肺腺癌",
              "典型影像表现": "...",
              "鉴别诊断特征": "...",
              "容易混淆疾病": ["肺结核", "肺转移瘤"],
              "置信度评估": "..."
            }},
            ...
          ]
        }}
        """
        
        try:
            result = self.llm_client.extract_json(prompt)
            if isinstance(result, dict) and "诊断指南" in result:
                return result
            else:
                return {"诊断指南": []}
        except Exception as e:
            logger.error(f"提取诊断指南时出错: {str(e)}")
            return {"诊断指南": []}
    
    def generate_bidirectional_templates(self) -> Dict[str, Any]:
        """
        生成双向驱动的模板
        
        返回:
            模板字典
        """
        # 收集所有诊断和特征对
        all_diagnoses = list(set([pair["diagnosis"] for pair in self.feature_diagnosis_pairs]))
        all_features = []
        for pair in self.feature_diagnosis_pairs:
            all_features.append(pair["feature"])
        
        # 使用LLM生成模板
        prompt = f"""
        基于胸部CT的影像特征和诊断数据，生成双向驱动的报告模板。这些模板将支持两种工作流：
        
        1. 医生先描述影像特征，系统推荐可能的诊断
        2. 医生先选择诊断，系统生成标准化的影像描述
        
        诊断列表样例:
        {json.dumps(all_diagnoses[:5], ensure_ascii=False, indent=2)}
        
        请生成以下两种模板：
        
        1. 影像→诊断模板：如何从输入的影像特征推导出可能的诊断
        2. 诊断→描述模板：如何从选定的诊断生成标准化的影像描述
        
        请按以下JSON格式返回:
        {{
          "影像诊断模板": {{
            "输入字段": ["解剖位置", "大小", "形态", "密度", "边界", "增强方式", "其他特征"],
            "特征组合规则": [...],
            "诊断推理规则": [...]
          }},
          "诊断描述模板": {{
            "诊断列表": [
              {{
                "诊断": "肺腺癌",
                "描述模板": [
                  "{{解剖位置}}可见一枚约{{大小}}大小的{{形态}}软组织密度影，边缘{{边界}}{{其他特征}}",
                  "增强扫描后呈{{增强方式}}"
                ]
              }},
              ...
            ]
          }}
        }}
        """
        
        try:
            result = self.llm_client.extract_json(prompt)
            if isinstance(result, dict):
                return result
            else:
                return {"影像诊断模板": {}, "诊断描述模板": {}}
        except Exception as e:
            logger.error(f"生成双向驱动模板时出错: {str(e)}")
            return {"影像诊断模板": {}, "诊断描述模板": {}}
    
    def save_knowledge_base(self, file_path: str) -> None:
        """
        保存知识库到文件
        
        参数:
            file_path: 保存路径
        """
        knowledge_base = {
            "feature_diagnosis_pairs": self.feature_diagnosis_pairs,
            "probability_model": self.build_probability_model(),
            "diagnostic_guidelines": self.extract_diagnostic_guidelines(),
            "bidirectional_templates": self.generate_bidirectional_templates()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
            logger.info(f"知识库已保存到 {file_path}")
        except Exception as e:
            logger.error(f"保存知识库失败: {str(e)}")
    
    def load_knowledge_base(self, file_path: str) -> bool:
        """
        从文件加载知识库
        
        参数:
            file_path: 文件路径
        
        返回:
            是否成功加载
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
            
            self.feature_diagnosis_pairs = knowledge_base.get("feature_diagnosis_pairs", [])
            self.knowledge_base = knowledge_base
            
            logger.info(f"已从 {file_path} 加载知识库")
            return True
        except Exception as e:
            logger.error(f"加载知识库失败: {str(e)}")
            return False
