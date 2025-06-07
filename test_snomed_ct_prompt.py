#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNOMED CT提示词测试和优化系统
基于Microsoft PromptWizard思路实现
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.medical_test_dataset import load_test_dataset
from evaluation.metrics import SNOMEDCTEvaluator
from optimization.prompt_optimizer import PromptOptimizer

class MedGEMMAClient:
    """MedGEMMA模型客户端（通过ollama调用）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "medgemma:latest"):
        self.base_url = base_url
        self.model = model
        
    def generate_response(self, prompt: str, max_retries: int = 3) -> str:
        """调用MedGEMMA生成响应"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # 降低随机性，提高一致性
                            "top_p": 0.9,
                            "num_predict": 2048
                        }
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    print(f"⚠️ API调用失败 (状态码: {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 第 {attempt + 1} 次调用失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    
        return ""

class SNOMEDCTTester:
    """SNOMED CT提示词测试器"""
    
    def __init__(self):
        self.client = MedGEMMAClient()
        self.evaluator = SNOMEDCTEvaluator()
        self.optimizer = PromptOptimizer()
        
    def run_single_test(self, report: str, prompt_template: str) -> Tuple[str, float]:
        """运行单个测试案例"""
        # 构造完整提示词
        full_prompt = prompt_template.replace("{{REPORT}}", report)
        
        # 调用模型
        print(f"📤 调用MedGEMMA模型...")
        response = self.client.generate_response(full_prompt)
        
        if not response:
            print("❌ 模型调用失败")
            return "", 0.0
            
        print(f"📥 收到响应 ({len(response)} 字符)")
        return response, 1.0
    
    def run_batch_test(self, test_dataset: List[Dict], prompt_template: str) -> List[Dict]:
        """运行批量测试"""
        results = []
        
        print(f"🚀 开始批量测试，共 {len(test_dataset)} 个案例")
        
        for i, test_case in enumerate(test_dataset, 1):
            print(f"\n--- 测试案例 {i}/{len(test_dataset)} ---")
            print(f"📋 报告: {test_case['report'][:50]}...")
            
            # 运行测试
            response, success = self.run_single_test(test_case["report"], prompt_template)
            
            if success:
                # 评估结果
                evaluation = self.evaluator.evaluate_response(response, test_case["gold_standard"])
                
                result = {
                    "test_id": test_case["id"],
                    "report": test_case["report"],
                    "model_response": response,
                    "evaluation": evaluation,
                    "total_score": evaluation["total_score"],
                    "entity_score": evaluation["entity_score"],
                    "structure_score": evaluation["structure_score"],
                    "coding_score": evaluation["coding_score"],
                    "details": evaluation["details"]
                }
                
                print(f"📊 评分: 总分={evaluation['total_score']:.2f}, "
                      f"实体={evaluation['entity_score']:.2f}, "
                      f"结构={evaluation['structure_score']:.2f}, "
                      f"编码={evaluation['coding_score']:.2f}")
                
            else:
                result = {
                    "test_id": test_case["id"],
                    "report": test_case["report"],
                    "model_response": "",
                    "evaluation": {"total_score": 0.0, "error": "模型调用失败"},
                    "total_score": 0.0,
                    "entity_score": 0.0,
                    "structure_score": 0.0,
                    "coding_score": 0.0,
                    "details": ["模型调用失败"]
                }
                print("❌ 测试失败")
            
            results.append(result)
            
            # 短暂延迟，避免过于频繁的API调用
            time.sleep(1)
        
        return results
    
    def save_test_results(self, results: List[Dict], version: str = "v1") -> str:
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/test_results_{version}_{timestamp}.json"
        
        os.makedirs("results", exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 测试结果已保存至: {filename}")
        return filename
    
    def generate_test_report(self, results: List[Dict]) -> Dict:
        """生成测试报告"""
        total_tests = len(results)
        successful_tests = len([r for r in results if r["total_score"] > 0])
        
        # 计算平均分数
        avg_total = sum(r["total_score"] for r in results) / total_tests if total_tests > 0 else 0
        avg_entity = sum(r["entity_score"] for r in results) / total_tests if total_tests > 0 else 0
        avg_structure = sum(r["structure_score"] for r in results) / total_tests if total_tests > 0 else 0
        avg_coding = sum(r["coding_score"] for r in results) / total_tests if total_tests > 0 else 0
        
        # 识别问题案例
        low_score_cases = [r for r in results if r["total_score"] < 0.7]
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "average_scores": {
                    "total": avg_total,
                    "entity": avg_entity,
                    "structure": avg_structure,
                    "coding": avg_coding
                }
            },
            "performance_analysis": {
                "high_score_cases": len([r for r in results if r["total_score"] >= 0.8]),
                "medium_score_cases": len([r for r in results if 0.5 <= r["total_score"] < 0.8]),
                "low_score_cases": len(low_score_cases),
                "failed_cases": len([r for r in results if r["total_score"] == 0])
            },
            "improvement_suggestions": self.evaluator.calculate_improvement_suggestions(results),
            "problematic_cases": [
                {
                    "test_id": case["test_id"],
                    "score": case["total_score"],
                    "issues": case["details"]
                }
                for case in low_score_cases[:3]  # 只显示前3个问题案例
            ]
        }
        
        return report
    
    def run_optimization_cycle(self, max_iterations: int = 3) -> Dict:
        """运行完整的测试-优化循环"""
        print("🎯 开始SNOMED CT提示词优化循环")
        
        # 加载测试数据
        test_dataset = load_test_dataset()
        print(f"📚 加载测试数据集: {len(test_dataset)} 个案例")
        
        optimization_results = []
        current_prompt = self.optimizer.load_base_prompt()
        
        for iteration in range(max_iterations):
            print(f"\n{'='*60}")
            print(f"🔄 第 {iteration + 1} 轮优化循环")
            print(f"{'='*60}")
            
            # 运行测试
            test_results = self.run_batch_test(test_dataset, current_prompt)
            
            # 生成测试报告
            test_report = self.generate_test_report(test_results)
            
            # 保存测试结果
            results_file = self.save_test_results(test_results, f"v{iteration + 1}")
            
            # 显示测试摘要
            print(f"\n📊 第 {iteration + 1} 轮测试摘要:")
            print(f"   成功率: {test_report['summary']['success_rate']:.1%}")
            print(f"   平均总分: {test_report['summary']['average_scores']['total']:.2f}")
            print(f"   实体识别: {test_report['summary']['average_scores']['entity']:.2f}")
            print(f"   结构完整: {test_report['summary']['average_scores']['structure']:.2f}")
            print(f"   编码准确: {test_report['summary']['average_scores']['coding']:.2f}")
            
            # 检查是否需要优化
            if test_report['summary']['average_scores']['total'] >= 0.8:
                print("✅ 提示词性能已达到目标，无需进一步优化")
                break
            
            # 运行优化
            optimized_prompt, optimization_result = self.optimizer.run_optimization_cycle(test_results)
            
            if optimization_result["status"] == "no_optimization_needed":
                print("✅ 未发现明显问题，优化循环结束")
                break
            
            # 更新当前提示词
            current_prompt = optimized_prompt
            
            optimization_results.append({
                "iteration": iteration + 1,
                "test_report": test_report,
                "optimization_result": optimization_result,
                "results_file": results_file
            })
        
        # 生成最终报告
        final_report = {
            "optimization_summary": {
                "total_iterations": len(optimization_results),
                "final_performance": optimization_results[-1]["test_report"]["summary"] if optimization_results else None,
                "optimization_history": self.optimizer.get_optimization_summary()
            },
            "iteration_details": optimization_results
        }
        
        # 保存最终报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_report_file = f"results/optimization_report_{timestamp}.json"
        with open(final_report_file, "w", encoding="utf-8") as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 优化循环完成！最终报告保存至: {final_report_file}")
        return final_report

def main():
    """主函数"""
    print("🏥 SNOMED CT医学影像报告结构化分析提示词测试系统")
    print("基于Microsoft PromptWizard思路实现")
    print("-" * 60)
    
    # 检查ollama服务
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama服务未运行，请先启动ollama")
            return
    except:
        print("❌ 无法连接到Ollama服务，请确保ollama正在运行")
        return
    
    # 创建测试器并运行
    tester = SNOMEDCTTester()
    
    # 首先生成测试数据集
    from data.medical_test_dataset import save_test_dataset
    save_test_dataset()
    
    # 运行优化循环
    final_report = tester.run_optimization_cycle(max_iterations=3)
    
    # 显示最终结果
    if final_report["optimization_summary"]["final_performance"]:
        final_perf = final_report["optimization_summary"]["final_performance"]
        print(f"\n🎯 最终性能指标:")
        print(f"   总体成功率: {final_perf['success_rate']:.1%}")
        print(f"   平均总分: {final_perf['average_scores']['total']:.2f}")
        print(f"   实体识别: {final_perf['average_scores']['entity']:.2f}")
        print(f"   结构完整: {final_perf['average_scores']['structure']:.2f}")
        print(f"   编码准确: {final_perf['average_scores']['coding']:.2f}")

if __name__ == "__main__":
    main() 