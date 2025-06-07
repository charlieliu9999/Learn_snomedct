import json
import re
from typing import Dict, List, Tuple, Set

class SNOMEDCTEvaluator:
    def __init__(self):
        self.entity_weight = 0.4
        self.structure_weight = 0.3
        self.coding_weight = 0.3
    
    def evaluate_response(self, model_output: str, gold_standard: Dict) -> Dict:
        """评估模型输出质量"""
        try:
            # 尝试解析JSON
            parsed_output = self._parse_json_output(model_output)
            
            if not parsed_output:
                return {
                    "total_score": 0.0,
                    "entity_score": 0.0,
                    "structure_score": 0.0,
                    "coding_score": 0.0,
                    "error": "JSON解析失败",
                    "details": ["无法解析模型输出为有效JSON"]
                }
            
            # 1. 实体识别准确率
            entity_score = self._evaluate_entity_extraction(parsed_output, gold_standard)
            
            # 2. 结构完整性
            structure_score = self._evaluate_structure_completeness(parsed_output)
            
            # 3. SNOMED编码准确率
            coding_score = self._evaluate_coding_accuracy(parsed_output, gold_standard)
            
            # 综合评分
            total_score = (entity_score * self.entity_weight + 
                          structure_score * self.structure_weight + 
                          coding_score * self.coding_weight)
            
            return {
                "total_score": total_score,
                "entity_score": entity_score,
                "structure_score": structure_score,
                "coding_score": coding_score,
                "details": self._get_detailed_feedback(parsed_output, gold_standard)
            }
        except Exception as e:
            return {
                "total_score": 0.0,
                "entity_score": 0.0,
                "structure_score": 0.0,
                "coding_score": 0.0,
                "error": str(e),
                "details": [f"评估过程发生错误: {str(e)}"]
            }
    
    def _parse_json_output(self, output: str) -> Dict:
        """解析JSON输出，支持多种格式"""
        # 首先尝试直接解析
        try:
            return json.loads(output)
        except:
            pass
        
        # 尝试提取JSON代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 尝试提取花括号内容
        brace_match = re.search(r'\{.*\}', output, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except:
                pass
        
        return None
    
    def _evaluate_entity_extraction(self, output: Dict, gold: Dict) -> float:
        """评估实体提取准确率"""
        expected_entities = set(gold.get("expected_entities", []))
        
        # 从输出中提取所有实体
        extracted_entities = set()
        
        # 从clinical_findings中提取
        for finding in output.get("clinical_findings", []):
            extracted_entities.add(finding.get("preferred_term", ""))
            extracted_entities.add(finding.get("chinese_term", ""))
            
            # 从属性中提取
            for attr_name, attr_value in finding.get("attributes", {}).items():
                if isinstance(attr_value, dict):
                    extracted_entities.add(attr_value.get("term", ""))
        
        # 从body_structures中提取
        for structure in output.get("body_structures", []):
            extracted_entities.add(structure.get("preferred_term", ""))
            extracted_entities.add(structure.get("chinese_term", ""))
        
        # 移除空字符串
        extracted_entities = {e for e in extracted_entities if e.strip()}
        
        if not expected_entities:
            return 1.0
        
        # 计算匹配度（支持部分匹配）
        correct = 0
        for expected in expected_entities:
            for extracted in extracted_entities:
                if expected in extracted or extracted in expected:
                    correct += 1
                    break
        
        return correct / len(expected_entities)
    
    def _evaluate_structure_completeness(self, output: Dict) -> float:
        """评估结构完整性"""
        # 检查必要字段
        required_fields = ["clinical_findings", "body_structures", "procedures", "quality_indicators"]
        present_fields = sum(1 for field in required_fields if field in output and output[field])
        field_score = present_fields / len(required_fields)
        
        # 检查clinical_findings的属性完整性
        findings_quality = 0.0
        if "clinical_findings" in output and output["clinical_findings"]:
            total_attr_score = 0
            for finding in output["clinical_findings"]:
                attr_score = 0
                required_attrs = ["finding_site", "associated_morphology"]
                present_attrs = sum(1 for attr in required_attrs 
                                  if attr in finding.get("attributes", {}))
                attr_score = present_attrs / len(required_attrs)
                total_attr_score += attr_score
            
            findings_quality = total_attr_score / len(output["clinical_findings"])
        
        # JSON格式完整性
        json_quality = 1.0 if isinstance(output, dict) else 0.0
        
        return (field_score * 0.5 + findings_quality * 0.3 + json_quality * 0.2)
    
    def _evaluate_coding_accuracy(self, output: Dict, gold: Dict) -> float:
        """评估SNOMED编码准确率"""
        coded_findings = 0
        total_findings = 0
        
        # 检查clinical_findings的编码
        for finding in output.get("clinical_findings", []):
            total_findings += 1
            concept_id = finding.get("concept_id", "")
            if concept_id and concept_id != "SCTID" and len(concept_id) > 5:
                coded_findings += 1
        
        # 检查body_structures的编码
        for structure in output.get("body_structures", []):
            total_findings += 1
            concept_id = structure.get("concept_id", "")
            if concept_id and concept_id != "SCTID" and len(concept_id) > 5:
                coded_findings += 1
        
        return coded_findings / total_findings if total_findings > 0 else 0.0
    
    def _get_detailed_feedback(self, output: Dict, gold: Dict) -> List[str]:
        """生成详细反馈"""
        feedback = []
        
        # 检查缺失的实体
        expected_entities = set(gold.get("expected_entities", []))
        extracted_entities = set()
        
        for finding in output.get("clinical_findings", []):
            extracted_entities.add(finding.get("preferred_term", ""))
            extracted_entities.add(finding.get("chinese_term", ""))
        
        extracted_entities = {e for e in extracted_entities if e.strip()}
        
        missing_entities = expected_entities - extracted_entities
        if missing_entities:
            feedback.append(f"缺失关键实体: {', '.join(missing_entities)}")
        
        # 检查结构问题
        if "clinical_findings" not in output or not output["clinical_findings"]:
            feedback.append("缺少clinical_findings字段或内容为空")
        
        if "quality_indicators" not in output:
            feedback.append("缺少quality_indicators字段")
        
        # 检查编码问题
        uncodeed_findings = []
        for finding in output.get("clinical_findings", []):
            concept_id = finding.get("concept_id", "")
            if not concept_id or concept_id == "SCTID":
                term = finding.get("preferred_term", "未知")
                uncodeed_findings.append(term)
        
        if uncodeed_findings:
            feedback.append(f"以下实体缺少有效SNOMED编码: {', '.join(uncodeed_findings[:3])}")
        
        return feedback if feedback else ["输出质量良好"]

    def calculate_improvement_suggestions(self, results: List[Dict]) -> List[str]:
        """基于评估结果计算改进建议"""
        suggestions = []
        
        # 统计各项得分
        entity_scores = [r["entity_score"] for r in results]
        structure_scores = [r["structure_score"] for r in results]
        coding_scores = [r["coding_score"] for r in results]
        
        avg_entity = sum(entity_scores) / len(entity_scores) if entity_scores else 0
        avg_structure = sum(structure_scores) / len(structure_scores) if structure_scores else 0
        avg_coding = sum(coding_scores) / len(coding_scores) if coding_scores else 0
        
        if avg_entity < 0.7:
            suggestions.append("需要改进实体识别能力，特别是医学术语的提取")
        
        if avg_structure < 0.7:
            suggestions.append("需要完善输出结构，确保包含所有必要字段")
        
        if avg_coding < 0.7:
            suggestions.append("需要提升SNOMED CT编码的准确性和覆盖率")
        
        return suggestions 