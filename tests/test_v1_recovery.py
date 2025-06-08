#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一版本KnowledgeForge架构恢复验证测试
验证核心功能模块、数据库架构、分析流程是否正常工作
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_knowledgeforge_imports():
    """测试KnowledgeForge核心模块导入"""
    try:
        from knowledgeforge import (
            process as knowledgeforge_process,
            analyze_medical_report_with_snomed,
            display_snomed_visualization,
            KnowledgeDB,
            SNOMEDReportAnalyzer
        )
        print("✅ KnowledgeForge核心模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ KnowledgeForge模块导入失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接和基本操作"""
    try:
        from knowledgeforge.db_manager import KnowledgeDB
        
        # 使用测试数据库
        test_db_path = project_root / "data" / "test_recovery.db"
        
        # 如果存在则删除
        if test_db_path.exists():
            test_db_path.unlink()
        
        # 创建数据库连接
        db = KnowledgeDB(str(test_db_path))
        
        # 测试基本操作
        db.add_term(
            sct_id="123456789",
            term_en="Test Structure",
            term_zh="测试结构",
            category="Anatomy"
        )
        
        # 查找术语
        result = db.find_term_by_name("Test Structure")
        assert result is not None
        assert result["term_en"] == "Test Structure"
        
        db.close()
        
        # 清理测试数据库
        if test_db_path.exists():
            test_db_path.unlink()
        
        print("✅ 数据库连接和基本操作测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_snomed_analyzer_initialization():
    """测试SNOMED CT分析器初始化"""
    try:
        from knowledgeforge.snomed_report_analyzer import SNOMEDReportAnalyzer
        
        # 使用测试数据库
        test_db_path = project_root / "data" / "test_analyzer.db"
        
        # 创建分析器实例
        analyzer = SNOMEDReportAnalyzer(str(test_db_path))
        
        assert analyzer.db is not None
        assert analyzer.session_id is not None
        
        # 清理
        if test_db_path.exists():
            test_db_path.unlink()
        
        print("✅ SNOMED CT分析器初始化测试通过")
        return True
        
    except Exception as e:
        print(f"❌ SNOMED CT分析器测试失败: {e}")
        return False

def run_all_tests():
    """运行所有恢复验证测试"""
    print("🚀 开始第一版本KnowledgeForge架构恢复验证测试")
    print("=" * 60)
    
    tests = [
        ("模块导入测试", test_knowledgeforge_imports),
        ("数据库连接测试", test_database_connection),
        ("SNOMED分析器测试", test_snomed_analyzer_initialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 第一版本KnowledgeForge架构恢复验证 - 全部通过！")
        return True
    else:
        print("⚠️ 部分测试失败，需要检查相关模块")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 