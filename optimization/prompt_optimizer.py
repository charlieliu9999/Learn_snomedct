import json
import re
from typing import Dict, List, Tuple
from datetime import datetime
import os

class PromptOptimizer:
    """基于Microsoft PromptWizard思路的提示词优化器"""
    
    def __init__(self, base_prompt_path: str = "prompts/snomed_ct_initial_prompt.txt"):
        self.base_prompt_path = base_prompt_path
        self.optimization_history = []
        self.current_version = 1
        
    def load_base_prompt(self) -> str:
        """加载基础提示词模板"""
        with open(self.base_prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def analyze_failure_patterns(self, test_results: List[Dict]) -> Dict[str, List[str]]:
        """分析测试失败模式，识别需要优化的方向"""
        patterns = {
            "entity_extraction_issues": [],
            "structure_issues": [],
            "coding_issues": [],
            "json_format_issues": [],
            "semantic_understanding_issues": []
        }
        
        for result in test_results:
            if result["total_score"] < 0.7:  # 低分案例
                # 实体提取问题
                if result["entity_score"] < 0.6:
                    patterns["entity_extraction_issues"].extend(result.get("details", []))
                
                # 结构问题
                if result["structure_score"] < 0.6:
                    patterns["structure_issues"].extend(result.get("details", []))
                
                # 编码问题
                if result["coding_score"] < 0.6:
                    patterns["coding_issues"].extend(result.get("details", []))
                
                # JSON格式问题
                if "error" in result and "JSON" in result["error"]:
                    patterns["json_format_issues"].append(result["error"])
        
        return patterns
    
    def generate_optimization_strategies(self, failure_patterns: Dict) -> List[Dict]:
        """基于失败模式生成优化策略"""
        strategies = []
        
        # 实体提取优化
        if failure_patterns["entity_extraction_issues"]:
            strategies.append({
                "type": "entity_extraction",
                "description": "增强实体识别指导",
                "modifications": [
                    "添加更多医学术语示例",
                    "强调同义词和变体识别",
                    "增加否定词处理指导"
                ]
            })
        
        # 结构完整性优化
        if failure_patterns["structure_issues"]:
            strategies.append({
                "type": "structure_completeness",
                "description": "完善输出结构要求",
                "modifications": [
                    "明确必填字段要求",
                    "添加字段验证示例",
                    "强调属性层级关系"
                ]
            })
        
        # SNOMED编码优化
        if failure_patterns["coding_issues"]:
            strategies.append({
                "type": "coding_accuracy",
                "description": "提升编码准确性",
                "modifications": [
                    "提供更多SNOMED编码示例",
                    "强调编码查找策略",
                    "添加编码置信度要求"
                ]
            })
        
        # JSON格式优化
        if failure_patterns["json_format_issues"]:
            strategies.append({
                "type": "json_format",
                "description": "改进JSON输出格式",
                "modifications": [
                    "简化JSON结构",
                    "添加格式验证要求",
                    "提供标准输出模板"
                ]
            })
        
        return strategies
    
    def apply_optimization_strategy(self, base_prompt: str, strategy: Dict) -> str:
        """应用优化策略到提示词"""
        optimized_prompt = base_prompt
        
        if strategy["type"] == "entity_extraction":
            # 在分析要求部分添加实体识别增强
            entity_enhancement = """
### 实体识别增强要求：
- 识别医学术语的同义词和变体表达（如"低密度"="低信号"="减低信号"）
- 正确处理否定表达（如"未见"、"无"、"排除"）
- 提取复合术语的各个组成部分
- 识别隐含的解剖结构和病理过程
"""
            optimized_prompt = optimized_prompt.replace(
                "## 分析要求：",
                "## 分析要求：" + entity_enhancement
            )
        
        elif strategy["type"] == "structure_completeness":
            # 强化结构要求
            structure_enhancement = """
### 结构完整性要求：
- clinical_findings字段必须包含，即使为空数组
- 每个finding必须包含concept_id, preferred_term, chinese_term
- attributes字段必须包含finding_site和associated_morphology
- quality_indicators字段必须包含concept_coverage和coding_confidence
"""
            optimized_prompt = optimized_prompt.replace(
                "### 4. 标准输出格式（严格JSON）：",
                "### 4. 标准输出格式（严格JSON）：" + structure_enhancement
            )
        
        elif strategy["type"] == "coding_accuracy":
            # 增强编码指导
            coding_enhancement = """
### SNOMED CT编码指导：
- 优先使用预协调概念（单一编码）
- 无法找到精确编码时，使用最接近的上级概念
- 为每个编码标注置信度（高/中/低）
- 记录编码选择的理由和可能的替代编码
"""
            optimized_prompt = optimized_prompt.replace(
                "## 特殊要求：",
                "## 特殊要求：" + coding_enhancement
            )
        
        elif strategy["type"] == "json_format":
            # 简化JSON格式要求
            format_enhancement = """
### JSON输出格式要求：
- 必须输出有效的JSON格式
- 使用双引号包围所有字符串
- 避免使用特殊字符和换行符
- 确保所有括号和引号正确配对
"""
            optimized_prompt = optimized_prompt.replace(
                "请严格按照上述SNOMED CT标准进行结构化分析",
                format_enhancement + "\n请严格按照上述SNOMED CT标准进行结构化分析"
            )
        
        return optimized_prompt
    
    def save_optimized_prompt(self, optimized_prompt: str, version: int, strategy: Dict) -> str:
        """保存优化后的提示词"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompts/snomed_ct_v{version}_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# SNOMED CT提示词 v{version}\n")
            f.write(f"# 优化策略: {strategy['description']}\n")
            f.write(f"# 生成时间: {timestamp}\n\n")
            f.write(optimized_prompt)
        
        # 记录优化历史
        self.optimization_history.append({
            "version": version,
            "timestamp": timestamp,
            "strategy": strategy,
            "filename": filename
        })
        
        return filename
    
    def run_optimization_cycle(self, test_results: List[Dict]) -> Tuple[str, Dict]:
        """运行一轮优化循环"""
        print(f"🔄 开始第 {self.current_version} 轮提示词优化...")
        
        # 1. 分析失败模式
        failure_patterns = self.analyze_failure_patterns(test_results)
        print(f"📊 识别到 {len([p for patterns in failure_patterns.values() for p in patterns])} 个问题模式")
        
        # 2. 生成优化策略
        strategies = self.generate_optimization_strategies(failure_patterns)
        
        if not strategies:
            print("✅ 未发现需要优化的问题，当前提示词表现良好")
            return None, {"status": "no_optimization_needed"}
        
        # 3. 选择最重要的优化策略
        primary_strategy = strategies[0]  # 简化版本，选择第一个策略
        print(f"🎯 选择优化策略: {primary_strategy['description']}")
        
        # 4. 应用优化
        base_prompt = self.load_base_prompt()
        optimized_prompt = self.apply_optimization_strategy(base_prompt, primary_strategy)
        
        # 5. 保存优化结果
        self.current_version += 1
        filename = self.save_optimized_prompt(optimized_prompt, self.current_version, primary_strategy)
        
        optimization_result = {
            "status": "optimized",
            "version": self.current_version,
            "strategy": primary_strategy,
            "filename": filename,
            "failure_patterns": failure_patterns
        }
        
        print(f"💾 优化完成，新版本保存至: {filename}")
        return optimized_prompt, optimization_result
    
    def get_optimization_summary(self) -> Dict:
        """获取优化历史摘要"""
        return {
            "total_versions": self.current_version,
            "optimization_history": self.optimization_history,
            "latest_version": self.optimization_history[-1] if self.optimization_history else None
        } 