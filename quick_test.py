#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNOMED CT快速测试脚本
用于验证系统基本功能
"""

import json
import requests
from datetime import datetime

def test_ollama_connection():
    """测试Ollama连接"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("✅ Ollama服务正常运行")
            print(f"📋 可用模型: {[m['name'] for m in models]}")
            
            # 检查medgemma模型
            medgemma_available = any("medgemma" in m['name'] for m in models)
            if medgemma_available:
                print("✅ MedGEMMA模型可用")
                return True
            else:
                print("⚠️ MedGEMMA模型未找到，请先下载: ollama pull medgemma:latest")
                return False
        else:
            print(f"❌ Ollama服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接Ollama服务: {str(e)}")
        print("请确保Ollama正在运行: ollama serve")
        return False

def test_simple_prompt():
    """测试简单提示词"""
    simple_prompt = """
请对以下医学影像报告进行结构化分析，提取关键信息：

报告: "左侧额叶见椭圆形低密度灶，直径约2.5cm，边界清楚。"

请以JSON格式输出，包含以下字段：
- findings: 发现列表
- locations: 部位列表  
- characteristics: 特征列表

"""
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "medgemma:latest",
                "prompt": simple_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 512
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            model_response = result.get("response", "")
            print("✅ 模型调用成功")
            print(f"📤 响应长度: {len(model_response)} 字符")
            print(f"📋 响应预览: {model_response[:200]}...")
            return True
        else:
            print(f"❌ 模型调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 模型调用异常: {str(e)}")
        return False

def test_file_structure():
    """测试文件结构"""
    required_files = [
        "prompts/snomed_ct_initial_prompt.txt",
        "data/medical_test_dataset.json",
        "evaluation/metrics.py",
        "optimization/prompt_optimizer.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✅ {file_path} 存在 ({len(content)} 字符)")
        except FileNotFoundError:
            print(f"❌ {file_path} 不存在")
            all_exist = False
        except Exception as e:
            print(f"⚠️ {file_path} 读取异常: {str(e)}")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("🧪 SNOMED CT系统快速测试")
    print("=" * 50)
    
    # 1. 测试文件结构
    print("\n1️⃣ 测试文件结构...")
    file_test = test_file_structure()
    
    # 2. 测试Ollama连接
    print("\n2️⃣ 测试Ollama连接...")
    ollama_test = test_ollama_connection()
    
    # 3. 测试模型调用
    if ollama_test:
        print("\n3️⃣ 测试模型调用...")
        model_test = test_simple_prompt()
    else:
        print("\n3️⃣ 跳过模型测试（Ollama不可用）")
        model_test = False
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 测试总结:")
    print(f"   文件结构: {'✅ 通过' if file_test else '❌ 失败'}")
    print(f"   Ollama连接: {'✅ 通过' if ollama_test else '❌ 失败'}")
    print(f"   模型调用: {'✅ 通过' if model_test else '❌ 失败'}")
    
    if file_test and ollama_test and model_test:
        print("\n🎉 所有测试通过！系统准备就绪")
        print("💡 可以运行完整测试: python test_snomed_ct_prompt.py")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")
        if not ollama_test:
            print("   - 请确保Ollama服务正在运行")
            print("   - 请确保已安装medgemma模型")

if __name__ == "__main__":
    main() 