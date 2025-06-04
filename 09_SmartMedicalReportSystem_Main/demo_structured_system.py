"""
医学影像报告双向结构化知识体系 - 核心功能演示
基于华西胸部CT数据构建的双向转换系统演示
"""

import pandas as pd
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# 结构化数据模型定义
@dataclass
class PatientInfo:
    age: int
    gender: str
    chief_complaint: Optional[str] = None

@dataclass
class ExaminationInfo:
    exam_date: str
    exam_time: str
    exam_type: str
    referring_department: str

@dataclass
class StructuredFinding:
    anatomy: str
    finding: str
    location: str
    size: Optional[str] = None
    characteristics: Optional[str] = None
    snomed_codes: Optional[List[str]] = None

@dataclass
class StructuredDiagnosis:
    disease: str
    anatomy: str
    certainty: str
    severity: Optional[str] = None
    snomed_codes: Optional[List[str]] = None

@dataclass
class StructuredReport:
    report_id: str
    patient_info: PatientInfo
    examination_info: ExaminationInfo
    imaging_findings: List[StructuredFinding]
    diagnoses: List[StructuredDiagnosis]
    raw_imaging_text: str
    raw_diagnosis_text: str
    extraction_confidence: float
    created_at: str

class MedicalEntityExtractor:
    """医学实体抽取引擎（模拟LLM功能）"""
    
    def __init__(self):
        # 医学术语词典（简化版）
        self.anatomy_terms = {
            "双肺": ["双肺", "两肺", "肺部", "肺野"],
            "右肺": ["右肺", "右侧肺"],
            "左肺": ["左肺", "左侧肺"],
            "肺叶": ["上叶", "中叶", "下叶"],
            "胸膜": ["胸膜", "胸膜腔"],
            "纵隔": ["纵隔", "纵膈"],
            "肋骨": ["肋骨", "肋间"],
        }
        
        self.finding_terms = {
            "结节": ["结节", "结节影", "小结节"],
            "肿块": ["肿块", "占位"],
            "囊状影": ["囊状影", "囊肿"],
            "炎症": ["炎症", "感染"],
            "增厚": ["增厚", "厚"],
            "钙化": ["钙化", "钙化灶"],
        }
        
        self.disease_terms = {
            "肺炎": ["肺炎", "炎症"],
            "肿瘤": ["肿瘤", "瘤"],
            "结节": ["结节病"],
            "囊肿": ["囊肿"],
        }

    def extract_findings(self, imaging_text: str) -> List[StructuredFinding]:
        """从影像表现文本中抽取结构化信息"""
        findings = []
        
        # 简化的抽取逻辑（实际应用中会使用LLM）
        sentences = re.split('[。；]', imaging_text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # 抽取解剖部位
            anatomy = self._extract_anatomy(sentence)
            # 抽取影像表现
            finding = self._extract_finding(sentence)
            # 抽取位置信息
            location = self._extract_location(sentence)
            # 抽取大小信息
            size = self._extract_size(sentence)
            
            if anatomy and finding:
                structured_finding = StructuredFinding(
                    anatomy=anatomy,
                    finding=finding,
                    location=location,
                    size=size,
                    characteristics=sentence.strip(),
                    snomed_codes=[]  # 实际应用中会映射到SNOMED CT
                )
                findings.append(structured_finding)
        
        return findings

    def extract_diagnoses(self, diagnosis_text: str) -> List[StructuredDiagnosis]:
        """从诊断结论文本中抽取结构化信息"""
        diagnoses = []
        
        sentences = re.split('[。；]', diagnosis_text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # 抽取疾病名称
            disease = self._extract_disease(sentence)
            # 抽取病变部位
            anatomy = self._extract_anatomy(sentence)
            # 抽取确定性程度
            certainty = self._extract_certainty(sentence)
            
            if disease:
                structured_diagnosis = StructuredDiagnosis(
                    disease=disease,
                    anatomy=anatomy or "未指定",
                    certainty=certainty,
                    snomed_codes=[]
                )
                diagnoses.append(structured_diagnosis)
        
        return diagnoses

    def _extract_anatomy(self, text: str) -> Optional[str]:
        """抽取解剖部位"""
        for anatomy, synonyms in self.anatomy_terms.items():
            for synonym in synonyms:
                if synonym in text:
                    return anatomy
        return None

    def _extract_finding(self, text: str) -> Optional[str]:
        """抽取影像表现"""
        for finding, synonyms in self.finding_terms.items():
            for synonym in synonyms:
                if synonym in text:
                    return finding
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """抽取具体位置"""
        location_patterns = [
            r'(\w+叶)',
            r'(\w+段)',
            r'(\w+区)',
            r'(前|后|内|外|上|下)(\w*)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_size(self, text: str) -> Optional[str]:
        """抽取大小信息"""
        size_pattern = r'(\d+\.?\d*\s*[×*]\s*\d+\.?\d*\s*(?:[×*]\s*\d+\.?\d*)?\s*cm)'
        match = re.search(size_pattern, text)
        if match:
            return match.group(0)
        return None

    def _extract_disease(self, text: str) -> Optional[str]:
        """抽取疾病名称"""
        for disease, synonyms in self.disease_terms.items():
            for synonym in synonyms:
                if synonym in text:
                    return disease
        return None

    def _extract_certainty(self, text: str) -> str:
        """抽取诊断确定性"""
        if "？" in text or "性质？" in text:
            return "疑似"
        elif "可能" in text or "倾向" in text:
            return "可能"
        elif "考虑" in text:
            return "考虑"
        else:
            return "确定"

class ReportGenerator:
    """报告生成引擎"""
    
    def __init__(self):
        self.imaging_templates = {
            "结节": "{anatomy}见{size}的{finding}，{characteristics}。",
            "肿块": "{anatomy}见{finding}，{characteristics}。",
            "炎症": "{anatomy}见{finding}表现，{characteristics}。",
            "囊状影": "{anatomy}见{finding}，{characteristics}。",
        }
        
        self.diagnosis_templates = {
            "肺炎": "{anatomy}{disease}，{certainty}。",
            "肿瘤": "{anatomy}{disease}，{certainty}。",
            "结节": "{anatomy}{finding}，{certainty}。",
        }

    def generate_imaging_findings(self, findings: List[StructuredFinding]) -> str:
        """生成影像表现文本"""
        if not findings:
            return "影像表现未见明显异常。"
        
        sentences = []
        for finding in findings:
            template = self.imaging_templates.get(finding.finding, "{anatomy}见{finding}。")
            
            sentence = template.format(
                anatomy=finding.anatomy,
                finding=finding.finding,
                size=finding.size or "",
                characteristics=finding.characteristics or ""
            )
            sentences.append(sentence)
        
        return "".join(sentences)

    def generate_diagnosis(self, diagnoses: List[StructuredDiagnosis]) -> str:
        """生成诊断结论文本"""
        if not diagnoses:
            return "未见明显异常。"
        
        sentences = []
        for diagnosis in diagnoses:
            template = self.diagnosis_templates.get(diagnosis.disease, "{anatomy}{disease}，{certainty}。")
            
            sentence = template.format(
                anatomy=diagnosis.anatomy,
                disease=diagnosis.disease,
                certainty=diagnosis.certainty
            )
            sentences.append(sentence)
        
        return "".join(sentences)

    def generate_full_report(self, structured_report: StructuredReport) -> str:
        """生成完整报告"""
        imaging_text = self.generate_imaging_findings(structured_report.imaging_findings)
        diagnosis_text = self.generate_diagnosis(structured_report.diagnoses)
        
        report = f"""
患者信息：
年龄：{structured_report.patient_info.age}岁
性别：{structured_report.patient_info.gender}

检查信息：
检查日期：{structured_report.examination_info.exam_date}
检查项目：{structured_report.examination_info.exam_type}
开单科室：{structured_report.examination_info.referring_department}

影像表现：
{imaging_text}

诊断结论：
{diagnosis_text}
        """
        
        return report.strip()

class StructuredReportSystem:
    """双向结构化报告系统"""
    
    def __init__(self):
        self.extractor = MedicalEntityExtractor()
        self.generator = ReportGenerator()
        self.knowledge_base = []  # 结构化报告知识库

    def load_data(self, file_path: str):
        """加载华西CT报告数据"""
        self.raw_data = pd.read_excel(file_path, engine='openpyxl')
        print(f"加载数据：{len(self.raw_data)} 条报告")

    def extract_structured_report(self, row_index: int) -> StructuredReport:
        """将原始报告转换为结构化报告"""
        row = self.raw_data.iloc[row_index]
        
        # 基础信息
        patient_info = PatientInfo(
            age=int(row['年龄']),
            gender=str(row['性别'])
        )
        
        exam_info = ExaminationInfo(
            exam_date=str(row['检查日期']),
            exam_time=str(row['检查时间']),
            exam_type=str(row['检查项目']),
            referring_department=str(row['开单科室'])
        )
        
        # 抽取结构化信息
        imaging_text = str(row['影像表现']) if pd.notna(row['影像表现']) else ""
        diagnosis_text = str(row['诊断结论']) if pd.notna(row['诊断结论']) else ""
        
        findings = self.extractor.extract_findings(imaging_text)
        diagnoses = self.extractor.extract_diagnoses(diagnosis_text)
        
        structured_report = StructuredReport(
            report_id=f"report_{row_index}",
            patient_info=patient_info,
            examination_info=exam_info,
            imaging_findings=findings,
            diagnoses=diagnoses,
            raw_imaging_text=imaging_text,
            raw_diagnosis_text=diagnosis_text,
            extraction_confidence=0.85,  # 模拟置信度
            created_at=datetime.now().isoformat()
        )
        
        return structured_report

    def generate_new_report(self, patient_age: int, patient_gender: str, 
                          findings: List[Dict], diagnoses: List[Dict]) -> str:
        """基于结构化信息生成新报告"""
        
        # 构建结构化数据
        patient_info = PatientInfo(age=patient_age, gender=patient_gender)
        
        exam_info = ExaminationInfo(
            exam_date=datetime.now().strftime("%Y-%m-%d"),
            exam_time=datetime.now().strftime("%H:%M:%S"),
            exam_type="胸部CT平扫",
            referring_department="呼吸内科"
        )
        
        structured_findings = [
            StructuredFinding(**finding) for finding in findings
        ]
        
        structured_diagnoses = [
            StructuredDiagnosis(**diagnosis) for diagnosis in diagnoses
        ]
        
        structured_report = StructuredReport(
            report_id="generated_report",
            patient_info=patient_info,
            examination_info=exam_info,
            imaging_findings=structured_findings,
            diagnoses=structured_diagnoses,
            raw_imaging_text="",
            raw_diagnosis_text="",
            extraction_confidence=1.0,
            created_at=datetime.now().isoformat()
        )
        
        return self.generator.generate_full_report(structured_report)

    def demonstrate_bidirectional_system(self):
        """演示双向系统功能"""
        print("=== 医学影像报告双向结构化知识体系演示 ===\n")
        
        # 演示1：原始报告 → 结构化
        print("【演示1：原始报告 → 结构化】")
        print("-" * 50)
        
        if len(self.raw_data) > 0:
            # 选择第一条记录进行演示
            structured = self.extract_structured_report(0)
            
            print("原始报告:")
            print(f"年龄: {structured.patient_info.age}")
            print(f"性别: {structured.patient_info.gender}")
            print(f"影像表现: {structured.raw_imaging_text[:100]}...")
            print(f"诊断结论: {structured.raw_diagnosis_text[:100]}...")
            
            print("\n结构化抽取结果:")
            print(f"抽取的影像表现数量: {len(structured.imaging_findings)}")
            for i, finding in enumerate(structured.imaging_findings[:3]):
                print(f"  {i+1}. 部位:{finding.anatomy}, 表现:{finding.finding}, 位置:{finding.location}")
            
            print(f"抽取的诊断数量: {len(structured.diagnoses)}")
            for i, diagnosis in enumerate(structured.diagnoses[:3]):
                print(f"  {i+1}. 疾病:{diagnosis.disease}, 部位:{diagnosis.anatomy}, 确定性:{diagnosis.certainty}")
        
        print("\n" + "="*50)
        
        # 演示2：结构化 → 新报告生成
        print("\n【演示2：结构化 → 新报告生成】")
        print("-" * 50)
        
        # 模拟结构化输入
        sample_findings = [
            {
                "anatomy": "双肺",
                "finding": "结节",
                "location": "下叶",
                "size": "0.8cm",
                "characteristics": "边界清楚，密度均匀"
            },
            {
                "anatomy": "右肺",
                "finding": "炎症",
                "location": "上叶",
                "characteristics": "片状模糊影"
            }
        ]
        
        sample_diagnoses = [
            {
                "disease": "肺部结节",
                "anatomy": "双肺",
                "certainty": "考虑"
            },
            {
                "disease": "肺炎",
                "anatomy": "右肺",
                "certainty": "确定"
            }
        ]
        
        generated_report = self.generate_new_report(
            patient_age=55,
            patient_gender="男",
            findings=sample_findings,
            diagnoses=sample_diagnoses
        )
        
        print("基于结构化信息生成的报告:")
        print(generated_report)
        
        print("\n" + "="*50)
        print("演示完成！这展示了双向转换的核心功能：")
        print("1. 从原始文本报告抽取结构化信息")
        print("2. 基于结构化信息生成标准化报告")
        print("3. 支持知识库的持续学习和更新")

def main():
    """主函数演示"""
    system = StructuredReportSystem()
    
    try:
        # 加载华西CT数据
        system.load_data('08_data/华西_胸部CT_报告.xlsx')
        
        # 运行双向系统演示
        system.demonstrate_bidirectional_system()
        
    except Exception as e:
        print(f"演示运行出错: {e}")
        print("请确保数据文件路径正确")

if __name__ == "__main__":
    main() 