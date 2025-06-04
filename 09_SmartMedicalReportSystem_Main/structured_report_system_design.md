# 医学影像报告双向结构化知识体系设计方案

## 一、数据分析总结

### 1.1 华西胸部CT报告数据（7755行）
- **基础信息**：年龄、性别、检查日期、检查时间、检查项目、开单科室
- **核心内容**：影像表现（平均129字符）、诊断结论（平均149字符）
- **特点**：真实临床数据，文本丰富，适合实体抽取和结构化

### 1.2 绥化报告模版数据（2534行）
- **结构化诊断**：2030种不同诊断类型，已分类整理
- **模版字段**：id、诊断、影像表现、诊断结论、分级标记等
- **特点**：结构化程度高，适合作为知识库和生成模版

## 二、结构化报告模版设计

### 2.1 核心结构化字段
```json
{
  "report_id": "报告唯一标识",
  "patient_info": {
    "age": "年龄",
    "gender": "性别",
    "chief_complaint": "主诉（如有）"
  },
  "examination_info": {
    "exam_date": "检查日期",
    "exam_time": "检查时间", 
    "exam_type": "检查项目",
    "referring_department": "开单科室"
  },
  "imaging_findings": {
    "raw_text": "原始影像表现文本",
    "structured_findings": [
      {
        "anatomy": "解剖部位",
        "finding": "影像表现",
        "location": "具体位置",
        "size": "大小/范围",
        "characteristics": "特征描述",
        "snomed_codes": ["SNOMED CT编码"]
      }
    ]
  },
  "diagnosis": {
    "raw_text": "原始诊断结论文本",
    "structured_diagnosis": [
      {
        "disease": "疾病名称",
        "anatomy": "病变部位", 
        "severity": "严重程度",
        "certainty": "确定性程度",
        "snomed_codes": ["SNOMED CT编码"]
      }
    ],
    "differential_diagnosis": ["鉴别诊断"],
    "recommendations": "建议和后续处理"
  },
  "metadata": {
    "extraction_confidence": "抽取置信度",
    "template_version": "模版版本",
    "last_updated": "最后更新时间"
  }
}
```

### 2.2 知识库结构设计
```json
{
  "anatomical_structures": {
    "lung": {
      "snomed_code": "39607008",
      "synonyms": ["肺", "肺部", "双肺"],
      "sub_structures": ["肺叶", "肺段", "支气管"]
    }
  },
  "findings_patterns": {
    "nodule": {
      "snomed_code": "27925004", 
      "synonyms": ["结节", "结节影", "小结节"],
      "modifiers": ["孤立性", "多发性", "钙化"]
    }
  },
  "diagnosis_templates": {
    "pneumonia": {
      "snomed_code": "233604007",
      "template": "{部位}{类型}肺炎",
      "synonyms": ["肺炎", "炎症"],
      "severity_levels": ["轻度", "中度", "重度"]
    }
  }
}
```

## 三、双向转换技术架构

### 3.1 报告→结构化（抽取方向）

#### 步骤1：LLM实体抽取引擎
```python
class MedicalEntityExtractor:
    def extract_findings(self, imaging_text):
        """从影像表现中抽取结构化信息"""
        prompt = f"""
        从以下影像表现中抽取结构化信息：
        文本：{imaging_text}
        
        请按以下格式输出：
        1. 解剖部位：
        2. 影像表现：
        3. 具体位置：
        4. 大小/范围：
        5. 特征描述：
        """
        return llm_call(prompt)
    
    def extract_diagnosis(self, diagnosis_text):
        """从诊断结论中抽取结构化信息"""
        prompt = f"""
        从以下诊断结论中抽取结构化信息：
        文本：{diagnosis_text}
        
        请按以下格式输出：
        1. 主要疾病：
        2. 病变部位：
        3. 严重程度：
        4. 确定性程度：
        5. 鉴别诊断：
        6. 建议处理：
        """
        return llm_call(prompt)
```

#### 步骤2：SNOMED CT映射引擎
```python
class SNOMEDMapper:
    def map_to_snomed(self, entity, entity_type):
        """将抽取的实体映射到SNOMED CT编码"""
        # 1. 精确匹配
        # 2. 模糊匹配
        # 3. 语义相似度匹配
        # 4. 人工审核机制
        pass
```

#### 步骤3：质量控制与验证
```python
class QualityController:
    def validate_extraction(self, original_text, structured_data):
        """验证抽取质量"""
        # 1. 完整性检查
        # 2. 一致性检查  
        # 3. 置信度评估
        pass
```

### 3.2 结构化→报告（生成方向）

#### 步骤1：模版选择引擎
```python
class TemplateSelector:
    def select_template(self, structured_data):
        """根据结构化数据选择合适的报告模版"""
        # 1. 基于检查类型
        # 2. 基于主要诊断
        # 3. 基于复杂程度
        pass
```

#### 步骤2：智能文本生成
```python
class ReportGenerator:
    def generate_imaging_findings(self, structured_findings):
        """生成影像表现文本"""
        template = self.get_findings_template()
        return template.format(**structured_findings)
    
    def generate_diagnosis(self, structured_diagnosis):
        """生成诊断结论文本"""
        template = self.get_diagnosis_template()
        return template.format(**structured_diagnosis)
```

#### 步骤3：个性化调整
```python
class PersonalizationEngine:
    def adjust_for_context(self, generated_text, patient_info):
        """根据患者信息和科室偏好调整报告"""
        # 1. 年龄相关调整
        # 2. 科室习惯用词
        # 3. 报告风格优化
        pass
```

## 四、知识库持续更新机制

### 4.1 自动学习机制
```python
class KnowledgeUpdater:
    def learn_from_new_reports(self, reports):
        """从新报告中学习更新知识库"""
        # 1. 新实体发现
        # 2. 表达方式学习
        # 3. 模版优化
        pass
    
    def update_templates(self, feedback):
        """基于反馈更新模版"""
        # 1. 医生修正反馈
        # 2. 质量评估结果
        # 3. 使用频率统计
        pass
```

### 4.2 质量监控
```python
class QualityMonitor:
    def monitor_extraction_quality(self):
        """监控抽取质量"""
        # 1. 准确率统计
        # 2. 异常检测
        # 3. 人工校验
        pass
    
    def monitor_generation_quality(self):
        """监控生成质量"""
        # 1. 医生满意度
        # 2. 修改频率
        # 3. 临床适用性
        pass
```

## 五、实施路线图

### 阶段1：基础结构化抽取（1-2月）
1. 基于华西数据训练LLM抽取模型
2. 构建基础SNOMED CT映射库
3. 实现影像表现和诊断结论的结构化抽取
4. 建立质量评估机制

### 阶段2：知识库构建（2-3月）
1. 整合绥化模版数据构建诊断知识库
2. 建立解剖结构和影像表现知识库
3. 实现知识库的增量更新机制
4. 构建Web界面进行人工校验

### 阶段3：自动生成引擎（3-4月）
1. 设计报告生成模版体系
2. 实现基于结构化数据的报告生成
3. 加入个性化调整功能
4. 建立反馈机制

### 阶段4：闭环优化（4-6月）
1. 实现双向转换的完整闭环
2. 持续优化抽取和生成质量
3. 扩展到更多检查类型
4. 产品化和部署

## 六、技术选型建议

### 6.1 核心技术栈
- **LLM引擎**：GPT-4/Claude或开源医学LLM
- **数据库**：Neo4j（知识图谱）+ PostgreSQL（关系数据）
- **后端框架**：FastAPI + Python
- **前端界面**：React + TypeScript
- **SNOMED CT服务**：SNOMED CT Browser API

### 6.2 关键依赖
- **医学NLP库**：scispaCy, BioBERT
- **文本相似度**：sentence-transformers
- **质量控制**：自定义验证规则引擎

## 七、预期效果

### 7.1 量化指标
- 结构化抽取准确率：≥90%
- 报告生成质量满意度：≥85%
- 处理效率提升：10倍以上
- 知识库覆盖率：≥95%

### 7.2 业务价值
- 医生工作效率显著提升
- 报告质量标准化
- 知识积累和复用
- 临床决策支持

这个双向知识体系将实现从"个案报告"到"结构化知识"再到"智能生成"的完整闭环，为医学影像报告的智能化奠定坚实基础。 