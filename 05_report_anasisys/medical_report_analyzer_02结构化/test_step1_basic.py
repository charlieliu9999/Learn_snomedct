#!/usr/bin/env python3
"""
测试步骤1: 基础配置和连接测试
"""
import sys
import os
sys.path.append('.')

print("🔧 步骤1: 基础配置和连接测试")
print("=" * 50)

try:
    # 测试配置加载
    print("1.1 测试配置文件加载...")
    import config
    print(f"✅ 配置加载成功")
    print(f"   - APP_TITLE: {config.APP_TITLE}")
    print(f"   - 数据目录: {config.DATA_DIR}")
    print(f"   - Neo4j配置: {config.NEO4J_CONFIG}")
    
    # 测试用户配置管理
    print("\n1.2 测试用户配置管理...")
    from utils.config_manager import config_manager
    user_config = config_manager.get_config()
    print(f"✅ 用户配置加载成功")
    print(f"   - LLM提供商: {user_config.get('llm_config', {}).get('provider', '未配置')}")
    print(f"   - LLM模型: {user_config.get('llm_config', {}).get('model', '未配置')}")
    
    # 测试LLM客户端初始化
    print("\n1.3 测试LLM客户端初始化...")
    from utils.llm_client import LLMClient
    llm_config = user_config.get('llm_config', config.LLM_CONFIG)
    llm_client = LLMClient(llm_config)
    print(f"✅ LLM客户端初始化成功")
    print(f"   - 提供商: {llm_client.provider}")
    print(f"   - 模型: {llm_client.model}")
    
    # 简单的LLM连接测试
    print("\n1.4 测试LLM连接...")
    try:
        test_response = llm_client.generate_text("请回答：1+1=?")
        print(f"✅ LLM连接测试成功")
        print(f"   - 测试响应: {test_response[:50]}...")
    except Exception as e:
        print(f"⚠️ LLM连接测试失败: {str(e)}")
    
    print("\n🎉 步骤1测试完成!")
    
except Exception as e:
    print(f"❌ 步骤1测试失败: {str(e)}")
    import traceback
    traceback.print_exc() 