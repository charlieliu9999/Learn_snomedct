#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNOMED CT 结构化提取器 - 优化版
基于最终修复版测试脚本的优化方案
- 使用专业的SNOMED CT提示词
- 增加 num_predict 解决JSON截断
- 增加 keep_alive 解决模型重载延迟
- 稳健的JSON解析
"""

import json
import requests
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SnomedCTExtractor:
    """SNOMED CT 结构化提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化SNOMED CT提取器
        
        参数:
            config: 配置字典，包含model, api_base等
        """
        self.config = config
        self.model = config.get("model", "medgemma:latest")
        self.api_base = config.get("api_base", "http://localhost:11434")
        self.temperature = config.get("temperature", 0.1)
        self.num_predict = config.get("num_predict", 2048)
        self.keep_alive = config.get("keep_alive", "5m")
        self.timeout = config.get("timeout", 300)
        
        logger.info(f"已初始化SNOMED CT提取器，使用模型: {self.model}")
    
    def extract_structured_report(self, report_text: str, diagnosis_text: str = "") -> Dict[str, Any]:
        """
        从医学报告中提取SNOMED CT结构化信息
        
        参数:
            report_text: 影像表现文本
            diagnosis_text: 诊断结论文本
            
        返回:
            SNOMED CT结构化数据
        """
        # 合并报告文本
        full_report = f"{report_text}\n{diagnosis_text}".strip()
        
        # 构建SNOMED CT专业提示词
        prompt = self._build_snomed_prompt(full_report)
        
        logger.info(f"开始SNOMED CT结构化提取，报告长度: {len(full_report)} 字符")
        start_time = time.time()
        
        try:
            # 调用Ollama API
            result = self._call_ollama_api(prompt)
            
            if result:
                processing_time = time.time() - start_time
                logger.info(f"SNOMED CT提取完成，耗时: {processing_time:.2f}秒")
                
                # 添加处理信息
                result["processing_info"] = {
                    "processing_time_seconds": round(processing_time, 2),
                    "model": self.model,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "input_length": len(full_report)
                }
                
                return result
            else:
                logger.error("SNOMED CT提取失败")
                return self._create_error_result("提取失败", full_report)
                
        except Exception as e:
            logger.error(f"SNOMED CT提取过程出错: {str(e)}")
            return self._create_error_result(str(e), full_report)
    
    def _build_snomed_prompt(self, report_text: str) -> str:
        """
        构建SNOMED CT专业提示词
        
        参数:
            report_text: 报告文本
            
        返回:
            构建的提示词
        """
        prompt = f"""You are a radiologist and medical terminologist highly familiar with the SNOMED CT ontology.

## TASK
Analyse the following medical imaging report and convert it into a structured representation using:
• official SNOMED CT preferred English terms (2024‑07 release or later)
• their Chinese equivalents
• explicit SNOMED CT attribute relationships.

## STRICT RULES
1. NO numeric concept IDs are required. If you know them you may append in brackets, but it is optional.
2. Use these relationship keys exactly:
   - finding_site (解剖部位)
   - associated_morphology (病变形态)
   - laterality (侧性)
   - severity (严重程度)
   - has_measurement (数值／尺寸)
3. For each finding keep the original Chinese sentence in source_sentence for traceability.
4. Output ONE single JSON object that follows the template below—no extra commentary or Markdown.

### JSON TEMPLATE
{{
  "clinical_findings": [
    {{
      "concept_en": "",
      "concept_zh": "",
      "relationships": {{
        "finding_site": "",
        "associated_morphology": "",
        "laterality": "",
        "severity": "",
        "has_measurement": ""
      }},
      "source_sentence": ""
    }}
  ],
  "body_structures": [
    {{
      "concept_en": "",
      "concept_zh": "",
      "laterality": "",
      "description": "",
      "source_sentence": ""
    }}
  ],
  "diagnoses": [
    {{
      "concept_en": "",
      "concept_zh": "",
      "relationships": {{
        "finding_site": "",
        "associated_morphology": "",
        "laterality": "",
        "severity": ""
      }},
      "source_sentence": ""
    }}
  ],
  "overall_quality": {{
    "completeness": "",
    "clarity": "",
    "comment": ""
  }}
}}

## MEDICAL REPORT (CHINESE)
{report_text}
"""
        return prompt
    
    def _call_ollama_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        调用Ollama API进行结构化提取
        
        参数:
            prompt: 提示词
            
        返回:
            解析的JSON结果或None
        """
        url = f"{self.api_base}/api/generate"
        
        # 优化的配置参数
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,  # 解决JSON截断问题
                "top_p": 0.8
            },
            "keep_alive": self.keep_alive  # 解决模型重载延迟
        }
        
        logger.info(f"调用Ollama API: {url}")
        logger.info(f"配置: num_predict={self.num_predict}, keep_alive={self.keep_alive}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                model_response = response_data.get("response", "")
                
                logger.info(f"API响应长度: {len(model_response)} 字符")
                
                # 解析JSON
                parsed_result = self._extract_json_from_response(model_response)
                
                if parsed_result:
                    logger.info("✅ JSON解析成功")
                    return parsed_result
                else:
                    logger.error("❌ JSON解析失败")
                    # 保存调试信息
                    self._save_debug_info("json_parse_failed", model_response)
                    return None
            else:
                logger.error(f"API请求失败: {response.status_code}, {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"API请求超时 (超过 {self.timeout} 秒)")
            return None
        except Exception as e:
            logger.error(f"API调用异常: {str(e)}")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从模型响应中稳健地提取JSON对象
        
        参数:
            response: 模型响应文本
            
        返回:
            解析的JSON对象或None
        """
        # 优先寻找被```json ... ```包裹的代码块
        try:
            if "```json" in response:
                start_index = response.find("```json") + len("```json")
                end_index = response.rfind("```")
                if end_index > start_index:
                    json_str = response[start_index:end_index].strip()
                    return json.loads(json_str)
        except Exception:
            pass

        # 其次，寻找从'{'开始到'}'结束的完整字符串
        try:
            start_index = response.find('{')
            end_index = response.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_str = response[start_index:end_index + 1]
                # 清理换行符和多余空格
                json_str = json_str.replace('\n', '').replace('\r', '').strip()
                return json.loads(json_str)
        except Exception:
            pass

        # 最后尝试直接解析整个响应
        try:
            return json.loads(response.strip())
        except Exception:
            pass

        return None
    
    def _create_error_result(self, error_msg: str, report_text: str) -> Dict[str, Any]:
        """
        创建错误结果
        
        参数:
            error_msg: 错误信息
            report_text: 原始报告文本
            
        返回:
            错误结果字典
        """
        return {
            "error": error_msg,
            "clinical_findings": [],
            "body_structures": [],
            "diagnoses": [],
            "overall_quality": {
                "completeness": "failed",
                "clarity": "failed",
                "comment": f"处理失败: {error_msg}"
            },
            "processing_info": {
                "status": "failed",
                "error": error_msg,
                "input_length": len(report_text),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    def _save_debug_info(self, prefix: str, response: str):
        """
        保存调试信息
        
        参数:
            prefix: 文件名前缀
            response: 响应内容
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_dir = os.path.join(os.path.dirname(__file__), "..", "data", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            filename = os.path.join(debug_dir, f"{prefix}_{timestamp}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"--- 调试信息 ---\n")
                f.write(f"时间: {timestamp}\n")
                f.write(f"模型: {self.model}\n")
                f.write(f"响应长度: {len(response)}\n")
                f.write("\n--- 原始响应 ---\n")
                f.write(response)
            
            logger.info(f"调试文件已保存: {filename}")
        except Exception as e:
            logger.error(f"保存调试信息失败: {str(e)}")
    
    def analyze_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析提取结果的质量
        
        参数:
            result: 提取结果
            
        返回:
            质量分析结果
        """
        if "error" in result:
            return {
                "status": "failed",
                "score": 0,
                "issues": [result["error"]]
            }
        
        issues = []
        score = 100
        
        # 检查各个部分的完整性
        sections = ["clinical_findings", "body_structures", "diagnoses"]
        for section in sections:
            if section not in result or not result[section]:
                issues.append(f"缺少{section}部分")
                score -= 20
        
        # 检查SNOMED CT术语的完整性
        for finding in result.get("clinical_findings", []):
            if not finding.get("concept_en") or not finding.get("concept_zh"):
                issues.append("临床发现缺少SNOMED CT术语")
                score -= 10
                break
        
        # 检查关系的完整性
        for finding in result.get("clinical_findings", []):
            relationships = finding.get("relationships", {})
            if not any(relationships.values()):
                issues.append("临床发现缺少关系信息")
                score -= 10
                break
        
        return {
            "status": "success" if score >= 70 else "warning",
            "score": max(0, score),
            "issues": issues,
            "total_findings": len(result.get("clinical_findings", [])),
            "total_structures": len(result.get("body_structures", [])),
            "total_diagnoses": len(result.get("diagnoses", []))
        }

# 兼容性函数，用于与现有系统集成
def extract_snomed_structure(report_text: str, diagnosis_text: str = "", config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    提取SNOMED CT结构化信息的便捷函数
    
    参数:
        report_text: 影像表现文本
        diagnosis_text: 诊断结论文本
        config: 配置字典
        
    返回:
        SNOMED CT结构化数据
    """
    if config is None:
        config = {
            "model": "medgemma:latest",
            "api_base": "http://localhost:11434",
            "temperature": 0.1,
            "num_predict": 2048,
            "keep_alive": "5m",
            "timeout": 300
        }
    
    extractor = SnomedCTExtractor(config)
    return extractor.extract_structured_report(report_text, diagnosis_text)

if __name__ == "__main__":
    # 测试代码
    test_report = """影像所见：双侧大脑半球、脑干及小脑形态正常，脑实质内未见明显异常密度影，脑室系统未及异常，脑沟﹑裂无增宽，中线结构居中。骨窗示颅骨未见明显骨质异常。
影像诊断：颅脑CT平扫未见明显异常。"""
    
    print("🚀 SNOMED CT提取器测试")
    print("=" * 60)
    
    config = {
        "model": "medgemma:latest",
        "api_base": "http://localhost:11434",
        "temperature": 0.1,
        "num_predict": 2048,
        "keep_alive": "5m",
        "timeout": 300
    }
    
    extractor = SnomedCTExtractor(config)
    result = extractor.extract_structured_report(test_report)
    
    print("\n📊 提取结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n📈 质量分析:")
    quality = extractor.analyze_quality(result)
    print(json.dumps(quality, ensure_ascii=False, indent=2)) 