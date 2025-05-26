"""
诊断关联器 - 使用LLM建立病变特征与诊断之间的智能关联
"""

import logging
import json
import uuid
from typing import Dict, List, Any

from .llm_client import LLMClient

# 设置日志
logger = logging.getLogger(__name__)

class DiagnosisAssociator:
    """
    诊断关联器 - 使用LLM建立病变特征与诊断之间的智能关联
    
    特点:
    1. 双向关联：诊断关联到病变，病变关联到诊断
    2. 利用模型医学知识自动建立关联
    3. 提供关联强度评估
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化诊断关联器
        
        参数:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        # 简单内存缓存
        self.cache = {
            "诊断到病变": {},  # 缓存诊断到病变的映射
            "病变到诊断": {},  # 缓存病变到诊断的映射
            "关联强度": {}     # 缓存关联强度计算
        }
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _assign_ids(self, lesions: List[Dict], diagnoses: List[Dict]) -> None:
        """
        为病变和诊断分配唯一ID（如果尚未分配）
        
        参数:
            lesions: 病变特征列表
            diagnoses: 诊断信息列表
        """
        # 为病变分配ID
        for i, lesion in enumerate(lesions):
            if "病变ID" not in lesion:
                lesion["病变ID"] = f"lesion_{i+1:03d}"
            
            # 初始化相关诊断列表（如果不存在）
            if "相关诊断列表" not in lesion:
                lesion["相关诊断列表"] = []
                
        # 为诊断分配ID
        for i, diagnosis in enumerate(diagnoses):
            if "诊断ID" not in diagnosis:
                diagnosis["诊断ID"] = f"diagnosis_{i+1:03d}"
                
            # 初始化相关病变列表（如果不存在）
            if "相关病变列表" not in diagnosis:
                diagnosis["相关病变列表"] = []
                
    def _map_diagnoses_to_lesions(self, diagnoses: List[Dict], lesions: List[Dict]) -> Dict[str, Dict]:
        """
        使用LLM将诊断映射到相关病变
        
        参数:
            diagnoses: 诊断信息列表
            lesions: 病变特征列表
            
        返回:
            诊断ID到病变列表的映射
        """
        result = {}
        
        for diagnosis in diagnoses:
            diagnosis_id = diagnosis["诊断ID"]
            diagnosis_content = diagnosis.get("内容", "")
            
            # 检查缓存
            cache_key = f"{diagnosis_id}:{','.join([l['病变ID'] for l in lesions])}"
            if cache_key in self.cache["诊断到病变"]:
                self.cache_hits += 1
                result[diagnosis_id] = self.cache["诊断到病变"][cache_key]
                
                # 更新诊断对象
                diagnosis["相关病变列表"] = result[diagnosis_id]["相关病变列表"]
                diagnosis["关联理由"] = result[diagnosis_id]["关联理由"]
                continue
                
            self.cache_misses += 1
            
            # 如果没有诊断内容，跳过
            if not diagnosis_content:
                result[diagnosis_id] = {"相关病变列表": [], "关联理由": "无诊断内容"}
                continue
                
            # 准备提示词 - 简化版本，避免JSON解析错误
            prompt = f"""
            分析下面的诊断与哪些病变特征相关，输出最可能相关的病变ID列表。
            
            诊断: {diagnosis.get('内容', '')}
            诊断类型: {diagnosis.get('类型', '')}
            
            病变特征列表:
            """            
            
            # 添加简化的病变描述
            for i, lesion in enumerate(lesions):
                prompt += f"病变{i+1} (ID: {lesion['病变ID']}): 位置={lesion.get('解剖位置', '')}, "
                prompt += f"大小={lesion.get('大小', '')}, 特征={lesion.get('形态', '')} {lesion.get('密度', '')} {lesion.get('边界', '')} {lesion.get('其他特征', '')}\n"
            
            prompt += """
            请分析诊断与哪些病变相关，只输出两部分内容：
            1. 相关病变ID列表（用逗号分隔）
            2. 简短的关联理由
            
            格式示例：
            相关病变ID列表：lesion_001,lesion_002
            关联理由：位置匹配，且具有恶性特征
            """
            
            try:
                # 调用LLM进行关联分析
                response = self.llm_client.generate(prompt)
                
                # 解析普通文本格式而非JSON
                related_ids = []
                reason = ""
                
                try:
                    lines = response.strip().split('\n')
                    for line in lines:
                        if line.startswith("相关病变ID列表") and ":" in line:
                            id_part = line.split(":", 1)[1].strip()
                            related_ids = [id.strip() for id in id_part.split(",") if id.strip()]
                        elif line.startswith("关联理由") and ":" in line:
                            reason = line.split(":", 1)[1].strip()
                
                    # 存储关联结果
                    result[diagnosis_id] = {
                        "相关病变列表": related_ids,
                        "关联理由": reason
                    }
                except Exception as e:
                    logger.error(f"解析模型响应失败: {str(e)}，原始响应: {response}")
                    # 尝试简单提取任何包含lesion_的内容作为病变ID
                    import re
                    lesion_ids = re.findall(r'lesion_\d+', response)
                    result[diagnosis_id] = {
                        "相关病变列表": lesion_ids,
                        "关联理由": "解析失败，但从响应中提取了病变ID"
                    }
                
                # 更新诊断对象
                diagnosis["相关病变列表"] = result[diagnosis_id]["相关病变列表"]
                diagnosis["关联理由"] = result[diagnosis_id]["关联理由"]
                
                # 缓存结果
                self.cache["诊断到病变"][cache_key] = result[diagnosis_id]
                
            except Exception as e:
                logger.error(f"诊断关联失败: {str(e)}")
                result[diagnosis_id] = {"相关病变列表": [], "关联理由": f"关联分析失败: {str(e)}"}
        
        return result
    
    def _map_lesions_to_diagnoses(self, lesions: List[Dict], diagnoses: List[Dict]) -> Dict[str, Dict]:
        """
        根据已有的诊断到病变映射，计算病变到诊断的映射
        
        参数:
            lesions: 病变特征列表
            diagnoses: 诊断信息列表
            
        返回:
            病变ID到诊断列表的映射
        """
        result = {}
        
        # 通过反向映射构建病变到诊断的映射
        for diagnosis in diagnoses:
            diagnosis_id = diagnosis["诊断ID"]
            related_lesion_ids = diagnosis.get("相关病变列表", [])
            
            for lesion_id in related_lesion_ids:
                if lesion_id not in result:
                    result[lesion_id] = {"相关诊断列表": [], "关联理由": {}}
                
                result[lesion_id]["相关诊断列表"].append(diagnosis_id)
                result[lesion_id]["关联理由"][diagnosis_id] = diagnosis.get("关联理由", "")
                
                # 更新病变对象
                for lesion in lesions:
                    if lesion["病变ID"] == lesion_id and diagnosis_id not in lesion["相关诊断列表"]:
                        lesion["相关诊断列表"].append(diagnosis_id)
        
        return result
    
    def _calculate_association_strength(self, 
                                      diagnosis_to_lesions: Dict, 
                                      lesion_to_diagnoses: Dict,
                                      diagnoses: List[Dict],
                                      lesions: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        计算诊断与病变之间的关联强度
        
        参数:
            diagnosis_to_lesions: 诊断到病变的映射
            lesion_to_diagnoses: 病变到诊断的映射
            diagnoses: 诊断信息列表
            lesions: 病变特征列表
            
        返回:
            关联强度映射 {诊断ID: {病变ID: 强度}}
        """
        result = {}
        
        # 获取诊断和病变的查询字典
        diagnosis_dict = {d["诊断ID"]: d for d in diagnoses}
        lesion_dict = {l["病变ID"]: l for l in lesions}
        
        # 对每对诊断-病变关联计算强度
        for diagnosis_id, info in diagnosis_to_lesions.items():
            if diagnosis_id not in result:
                result[diagnosis_id] = {}
                
            diagnosis = diagnosis_dict.get(diagnosis_id, {})
            
            for lesion_id in info.get("相关病变列表", []):
                # 检查缓存
                cache_key = f"{diagnosis_id}:{lesion_id}"
                if cache_key in self.cache["关联强度"]:
                    self.cache_hits += 1
                    result[diagnosis_id][lesion_id] = self.cache["关联强度"][cache_key]
                    continue
                
                self.cache_misses += 1
                
                lesion = lesion_dict.get(lesion_id, {})
                
                if not diagnosis or not lesion:
                    result[diagnosis_id][lesion_id] = 0.0
                    continue
                
                # 准备提示词
                prompt = f"""
                请评估以下影像诊断与病变特征之间的关联强度(0-1.0之间的小数):
                
                诊断: {json.dumps(diagnosis, ensure_ascii=False)}
                病变特征: {json.dumps(lesion, ensure_ascii=False)}
                
                考虑以下因素:
                1. 位置匹配度 - 诊断涉及的解剖位置是否与病变位置一致
                2. 特征与诊断的医学一致性 - 病变特征是否符合诊断的典型表现
                3. 大小、形态等对诊断的支持程度 - 病变特点是否支持该诊断
                
                请直接返回一个0-1.0之间的小数表示关联强度。数字越大表示关联性越强。
                """
                
                try:
                    # 使用模型评估关联强度
                    response = self.llm_client.generate(prompt).strip()
                    strength = float(response)
                    
                    # 确保结果在0-1.0之间
                    strength = max(0.0, min(1.0, strength))
                    
                    result[diagnosis_id][lesion_id] = strength
                    
                    # 缓存结果
                    self.cache["关联强度"][cache_key] = strength
                    
                except Exception as e:
                    logger.error(f"关联强度计算失败: {str(e)}")
                    # 默认中等关联强度
                    result[diagnosis_id][lesion_id] = 0.5
        
        return result
        
    def associate_features_with_diagnoses(self, 
                                         lesions: List[Dict], 
                                         diagnoses: List[Dict],
                                         structures: List[Dict] = None) -> Dict:
        """
        建立病变特征与诊断之间的双向关联
        
        参数:
            lesions: 病变特征列表
            diagnoses: 诊断信息列表
            structures: 解剖结构列表(可选)
            
        返回:
            包含关联关系的字典
        """
        # 如果列表为空，返回空结果
        if not lesions or not diagnoses:
            return {
                "诊断到病变映射": {},
                "病变到诊断映射": {},
                "关联强度": {}
            }
        
        # 为所有元素生成唯一ID
        self._assign_ids(lesions, diagnoses)
        
        # 为每个诊断找到相关的病变
        diagnosis_to_lesions = self._map_diagnoses_to_lesions(diagnoses, lesions)

        # --- 修正：同步写入病变的相关诊断列表，确保双向关联 ---
        for diagnosis in diagnoses:
            diagnosis_id = diagnosis["诊断ID"]
            for lesion_id in diagnosis.get("相关病变列表", []):
                for lesion in lesions:
                    if lesion["病变ID"] == lesion_id:
                        if "相关诊断列表" not in lesion:
                            lesion["相关诊断列表"] = []
                        if diagnosis_id not in lesion["相关诊断列表"]:
                            lesion["相关诊断列表"].append(diagnosis_id)

        # 为每个病变找到相关的诊断
        lesion_to_diagnoses = self._map_lesions_to_diagnoses(lesions, diagnoses)
        
        # 计算关联强度
        association_strength = self._calculate_association_strength(
            diagnosis_to_lesions, 
            lesion_to_diagnoses,
            diagnoses,
            lesions
        )
        
        # 合并关联结果
        return {
            "诊断到病变映射": diagnosis_to_lesions,
            "病变到诊断映射": lesion_to_diagnoses,
            "关联强度": association_strength
        }
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "诊断到病变_缓存大小": len(self.cache["诊断到病变"]),
            "病变到诊断_缓存大小": len(self.cache["病变到诊断"]),
            "关联强度_缓存大小": len(self.cache["关联强度"])
        }
    
    def clear_cache(self):
        """清除缓存"""
        self.cache = {
            "诊断到病变": {},
            "病变到诊断": {},
            "关联强度": {}
        }
        self.cache_hits = 0
        self.cache_misses = 0
