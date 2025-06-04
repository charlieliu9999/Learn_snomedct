"""
修复影像诊断映射问题的临时脚本
"""

import json
import os
import sys

# 获取structure_extractor.py的路径
script_dir = os.path.dirname(os.path.abspath(__file__))
extractor_path = os.path.join(script_dir, "structure_extractor.py")

# 读取原始文件
with open(extractor_path, "r", encoding="utf-8") as f:
    content = f.read()

# 修改_generate_mappings方法
old_method = """    def _generate_mappings(self, structures: List[Dict[str, str]], features: List[Dict[str, Any]], diagnoses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        \"\"\"
        自动生成影像发现和诊断的映射关系
        
        参数:
            structures: 解剖结构列表
            features: 病变特征列表
            diagnoses: 诊断信息列表
            
        返回:
            映射关系列表
        \"\"\"
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
            # 如果没有找到相关特征，但有诊断，创建一个带"低"置信度的映射
            elif features:
                mapping = {
                    "影像发现": "综合影像表现",
                    "对应诊断": diagnosis_text,
                    "映射置信度": "低"
                }
                mappings.append(mapping)
                
        return mappings"""

new_method = """    def _generate_mappings(self, structures: List[Dict[str, str]], features: List[Dict[str, Any]], diagnoses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        \"\"\"
        自动生成影像发现和诊断的映射关系
        
        参数:
            structures: 解剖结构列表
            features: 病变特征列表
            diagnoses: 诊断信息列表
            
        返回:
            映射关系列表
        \"\"\"
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
                
                # 获取特征的解剖位置和其他关键信息
                location = ""
                property_info = ""
                size_info = ""
                shape_info = ""
                
                if isinstance(feature_detail, dict):
                    location = feature_detail.get("解剖位置", "")
                    property_info = feature_detail.get("特性", "")
                    size_info = feature_detail.get("大小", "")
                    shape_info = feature_detail.get("形态", "")
                    
                # 判断是否相关(简单版：判断解剖位置或特征名称是否出现在诊断中)
                if location and location in diagnosis_text:
                    related_features.append(feature)
                elif feature_name and feature_name in diagnosis_text:
                    related_features.append(feature)
            
            # 如果找到相关特征，创建映射
            if related_features:
                for feature in related_features:
                    # 从特征中提取更具体的描述作为影像发现
                    feature_detail = feature.get("特征", {})
                    feature_name = feature.get("名称", "")
                    
                    # 构建更精确的影像发现描述
                    finding_description = ""
                    
                    if isinstance(feature_detail, dict):
                        # 提取关键信息
                        location = feature_detail.get("解剖位置", "")
                        property_info = feature_detail.get("特性", "")
                        size_info = feature_detail.get("大小", "")
                        shape_info = feature_detail.get("形态", "")
                        
                        # 组合关键信息
                        components = []
                        if location: components.append(location)
                        if property_info: components.append(property_info)
                        
                        # 如果有足够的组件，使用它们构建描述
                        if components:
                            finding_description = "，".join(components)
                    
                    # 如果无法从特征详情构建描述，使用特征名称但去掉不必要的后缀
                    if not finding_description and feature_name:
                        finding_description = feature_name.replace("-", "")
                    
                    # 确保有描述内容
                    if not finding_description:
                        finding_description = feature_name
                    
                    mapping = {
                        "影像发现": finding_description,  # 不再添加"的特征"后缀
                        "对应诊断": diagnosis_text,
                        "映射置信度": "高" if feature_name in diagnosis_text or \\
                                   (location and location in diagnosis_text) else "中"
                    }
                    mappings.append(mapping)
            # 如果没有找到相关特征，但有诊断，尝试从诊断文本中提取关键信息
            elif features:
                # 从诊断文本中提取关键术语作为影像发现
                finding_words = []
                
                # 遍历所有解剖结构，查看哪些出现在诊断中
                for structure in structures:
                    if not isinstance(structure, dict):
                        continue
                        
                    structure_name = structure.get("标准名", "")
                    if structure_name and structure_name in diagnosis_text:
                        finding_words.append(structure_name)
                
                # 如果找到解剖结构，使用它作为影像发现的一部分
                if finding_words:
                    finding_description = finding_words[0] + "相关影像表现"
                    mapping = {
                        "影像发现": finding_description,
                        "对应诊断": diagnosis_text,
                        "映射置信度": "中"
                    }
                else:
                    # 如果无法提取有意义的信息，使用更具体的描述而非"综合影像表现"
                    mapping = {
                        "影像发现": diagnosis_text.split("，")[0] if "，" in diagnosis_text else diagnosis_text,
                        "对应诊断": diagnosis_text,
                        "映射置信度": "低"
                    }
                mappings.append(mapping)
                
        return mappings"""

# 替换方法
new_content = content.replace(old_method, new_method)

# 保存修改后的文件
with open(extractor_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("影像诊断映射功能已修复")
