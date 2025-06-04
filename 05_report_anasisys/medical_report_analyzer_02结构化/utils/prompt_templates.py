"""
提示词模板管理模块 - 用于管理结构化分析中使用的提示词
"""

import os
import json
import logging
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PromptTemplateManager:
    """提示词模板管理器"""
    
    def __init__(self):
        """初始化提示词模板管理器"""
        self.templates = self._load_default_templates()
        self.template_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "data", 
            "prompt_templates.json"
        )
        self._load_custom_templates()
    
    def _load_default_templates(self) -> Dict[str, Dict[str, str]]:
        """加载默认模板"""
        return {
            "anatomical": {
                "胸部CT": """
                从以下胸部CT报告文本中提取所有提到的解剖结构，包括肺叶、气管、支气管、胸膜、纵隔等。
                
                报告文本:
                {report_text}
                
                请按以下JSON格式返回结果:
                [
                  {{"原文": "原文描述", "标准名": "标准术语", "父结构": "上级结构"}}
                ]
                
                仅返回报告中明确提到的解剖结构，不要添加推测的结构。
                所有标准名和父结构必须使用中文名称。
                """,
                
                "腹部超声": """
                从以下腹部超声报告文本中提取所有提到的解剖结构，包括肝脏、胆囊、胰腺、脾脏、肾脏等。
                
                报告文本:
                {report_text}
                
                请按以下JSON格式返回结果:
                [
                  {{"原文": "原文描述", "标准名": "标准术语", "父结构": "上级结构"}}
                ]
                
                仅返回报告中明确提到的解剖结构，不要添加推测的结构。
                所有标准名和父结构必须使用中文名称。
                """,
                
                "default": """
                从以下医学影像报告文本中提取所有提到的解剖结构。
                
                报告文本:
                {report_text}
                
                请按以下JSON格式返回结果:
                [
                  {{"原文": "原文描述", "标准名": "标准术语", "父结构": "上级结构"}}
                ]
                
                仅返回报告中明确提到的解剖结构，不要添加推测的结构。
                所有标准名和父结构必须使用中文名称。
                """
            },
            
            "lesion": {
                "胸部CT": """
                从以下胸部CT报告文本中提取所有病变特征信息。
                
                常见形态描述: 结节, 肿块, 磨玻璃, 实变, 条索, 蜂窝
                常见密度描述: 软组织密度, 液体密度, 脂肪密度, 钙化, 高密度, 低密度
                常见边界描述: 边界清晰, 边界模糊, 分叶, 毛刺, 胸膜凹陷
                
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
                
                以JSON格式返回，每个病变为数组中的一个对象:
                [
                  {{
                    "解剖位置": "位置描述",
                    "大小": "尺寸描述",
                    "形态": "形态描述",
                    "密度": "密度描述",
                    "边界": "边界描述",
                    "数量": "数量描述",
                    "分布": "分布描述",
                    "其他特征": "其他描述"
                  }}
                ]
                
                如果报告中没有明确描述某项特征，则对应字段返回空字符串。
                """,
                
                "腹部超声": """
                从以下腹部超声报告文本中提取所有病变特征信息。
                
                常见形态描述: 结节, 肿块, 囊肿, 钙化, 占位
                常见回声描述: 高回声, 低回声, 无回声, 混合回声
                常见边界描述: 边界清晰, 边界模糊, 光整, 不规则
                
                报告文本:
                {report_text}
                
                请分析文本中描述的每个病变，提取以下特征：
                1. 解剖位置 - 病变所在的具体解剖结构
                2. 大小 - 病变的尺寸描述
                3. 形态 - 病变的形状特征
                4. 回声 - 病变的回声特征
                5. 边界 - 病变边界的描述
                6. 数量 - 病变的数量
                7. 分布 - 病变的分布特征
                8. 其他特征 - 其他相关描述
                
                以JSON格式返回，每个病变为数组中的一个对象。
                如果报告中没有明确描述某项特征，则对应字段返回空字符串。
                """,
                
                "default": """
                从以下医学影像报告文本中提取所有病变特征信息。
                
                报告文本:
                {report_text}
                
                请分析文本中描述的每个病变，提取以下特征：
                1. 解剖位置 - 病变所在的具体解剖结构
                2. 大小 - 病变的尺寸描述
                3. 形态 - 病变的形状特征
                4. 特性 - 病变的特性描述
                5. 边界 - 病变边界的描述
                6. 数量 - 病变的数量
                7. 分布 - 病变的分布特征
                8. 其他特征 - 其他相关描述
                
                以JSON格式返回，每个病变为数组中的一个对象。
                如果报告中没有明确描述某项特征，则对应字段返回空字符串。
                """
            },
            
            "diagnosis": {
                "default": """
                从以下医学影像诊断结论文本中提取结构化的诊断信息:
                
                诊断结论:
                {diagnosis_text}
                
                请严格按照以下JSON格式要求返回，不要添加任何解释或额外文本:
                [
                  {{"类型": "分类", "描述": "具体描述"}}
                ]
                
                类型分类参考:
                1. 肿瘤相关: 良性肿瘤, 恶性肿瘤, 肿瘤可能, 转移
                2. 感染相关: 感染, 炎症, 肺炎
                3. 解剖异常: 增生, 囊肿, 结节, 钙化, 粘连, 积液
                4. 变性病变: 纤维化, 硬化
                5. 血管相关: 栓塞, 血管瘤
                6. 其他发现: 其他
                7. 正常: 未见异常
                
                请确保提取的诊断信息准确反映原始文本内容，不要添加不存在的信息。
                """
            },
            
            "mapping": {
                "default": """
                请从以下提供的数据中，建立精确的影像发现与诊断结论的直接映射关系。
                
                解剖结构列表：
                {structures}
                
                病变特征列表：
                {features}
                
                诊断信息列表：
                {diagnoses}
                
                请遵循以下原则构建映射：
                1. 影像发现应直接描述具体影像特征，不要添加"的特征"等多余后缀
                2. 每个诊断应对应至少一个具体的影像发现，避免使用"综合影像表现"这类模糊描述
                3. 映射应基于文本中明确的证据，而非推测
                
                请按以下JSON格式返回结果：
                [
                  {
                    "影像发现": "主动脉瓣钙化、增厚",
                    "对应诊断": "主动脉瓣钙化、增厚,开放受限",
                    "映射置信度": "高"
                  }
                ]
                
                映射置信度说明:
                - 高: 影像发现和诊断之间有明确的因果关系
                - 中: 影像发现和诊断之间可能有关联
                - 低: 影像发现和诊断之间关系不确定
                
                请基于文本内容和已提取的结构化信息进行映射，避免信息丢失或错配。
                """
            }
        }
    
    def _load_custom_templates(self):
        """从文件加载自定义模板"""
        try:
            if os.path.exists(self.template_file):
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    custom_templates = json.load(f)
                
                # 合并自定义模板
                for category, templates in custom_templates.items():
                    if category not in self.templates:
                        self.templates[category] = {}
                    
                    for report_type, template in templates.items():
                        self.templates[category][report_type] = template
                
                logger.info(f"已加载自定义提示词模板: {self.template_file}")
        except Exception as e:
            logger.error(f"加载自定义提示词模板失败: {str(e)}")
    
    def save_custom_templates(self):
        """保存自定义模板到文件"""
        try:
            os.makedirs(os.path.dirname(self.template_file), exist_ok=True)
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存自定义提示词模板: {self.template_file}")
            return True
        except Exception as e:
            logger.error(f"保存自定义提示词模板失败: {str(e)}")
            return False
    
    def get_prompt(self, prompt_type: str, report_type: str = "default", **kwargs) -> str:
        """
        获取特定类型的提示词
        
        参数:
            prompt_type: 提示词类型（anatomical, lesion, diagnosis, mapping）
            report_type: 报告类型（胸部CT, 腹部超声, default等）
            **kwargs: 格式化提示词所需的参数
        
        返回:
            格式化后的提示词
        """
        # 获取指定类型和报告类型的模板
        template = self.templates.get(prompt_type, {}).get(report_type)
        
        # 如果没有找到特定报告类型的模板，使用默认模板
        if not template:
            template = self.templates.get(prompt_type, {}).get("default", "")
        
        # 如果仍然没有找到模板，返回空字符串
        if not template:
            logger.warning(f"未找到提示词模板: {prompt_type}, {report_type}")
            return ""
        
        # 格式化模板
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"格式化提示词模板失败，缺少参数: {str(e)}")
            return template  # 返回未格式化的模板
    
    def save_template(self, prompt_type: str, report_type: str, template: str) -> bool:
        """
        保存自定义模板
        
        参数:
            prompt_type: 提示词类型
            report_type: 报告类型
            template: 模板内容
        
        返回:
            保存是否成功
        """
        if not prompt_type or not report_type:
            logger.error("保存模板失败: 提示词类型和报告类型不能为空")
            return False
        
        # 确保分类存在
        if prompt_type not in self.templates:
            self.templates[prompt_type] = {}
        
        # 保存模板
        self.templates[prompt_type][report_type] = template
        
        # 保存到文件
        return self.save_custom_templates()
    
    def get_available_types(self) -> Dict[str, list]:
        """
        获取所有可用的提示词类型和报告类型
        
        返回:
            包含所有提示词类型和对应报告类型的字典
        """
        result = {}
        for prompt_type, report_types in self.templates.items():
            result[prompt_type] = list(report_types.keys())
        return result
