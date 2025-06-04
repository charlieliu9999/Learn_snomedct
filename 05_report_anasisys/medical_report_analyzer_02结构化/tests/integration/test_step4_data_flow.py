#!/usr/bin/env python3
"""
测试步骤4: 数据处理流程测试
"""
import sys
import os
sys.path.append('.')

print("📊 步骤4: 数据处理流程测试")
print("=" * 50)

try:
    # 初始化核心组件
    print("4.1 初始化核心组件...")
    import config
    import pandas as pd
    from utils.config_manager import config_manager
    from utils.data_processor import DataProcessor
    from utils.state_manager import state_manager
    
    print("✅ 核心组件导入成功")
    
    # 测试配置管理
    print("\n4.2 测试配置管理...")
    try:
        user_config = config_manager.get_config()
        print(f"✅ 配置管理正常")
        print(f"   - 配置文件存在: {'llm_config' in user_config}")
        
        # 测试配置保存
        test_config = {"test_key": "test_value"}
        config_manager.save_config(test_config)
        loaded_config = config_manager.get_config()
        
        if "test_key" in loaded_config:
            print(f"✅ 配置保存/加载功能正常")
        else:
            print(f"⚠️ 配置保存功能异常")
    except Exception as e:
        print(f"❌ 配置管理测试失败: {str(e)}")
    
    # 测试数据处理器
    print("\n4.3 测试数据处理器...")
    try:
        processor = DataProcessor()
        
        # 创建测试数据
        test_data = pd.DataFrame({
            '影像表现': [
                '右肺上叶见一枚约1.5cm大小的结节影，边缘毛糙',
                '双肺门淋巴结增大，胸腔未见积液',
                '心脏大小形态正常，主动脉壁钙化'
            ],
            '诊断结论': [
                '右肺上叶结节，考虑恶性病变可能',
                '双肺门淋巴结增大',
                '主动脉壁钙化'
            ]
        })
        
        print(f"✅ 数据处理器初始化成功")
        print(f"   - 测试数据行数: {len(test_data)}")
        print(f"   - 数据列: {list(test_data.columns)}")
        
        # 测试数据验证
        validation_result = processor.validate_data(test_data)
        print(f"   - 数据验证结果: {validation_result}")
        
    except Exception as e:
        print(f"❌ 数据处理器测试失败: {str(e)}")
    
    # 测试状态管理
    print("\n4.4 测试状态管理...")
    try:
        # 保存测试状态
        test_state = {
            "test_data": {"processed_count": 3, "timestamp": "2025-06-04"},
            "test_config": {"version": "1.0"}
        }
        
        # 临时更新会话状态
        import streamlit as st
        # 由于不在streamlit环境中，我们直接测试状态管理的基本功能
        success = state_manager.save_state("test_state", "测试状态", state_data=test_state)
        
        if success:
            print(f"✅ 状态保存成功")
            
            # 测试状态列表
            state_list = state_manager.get_state_list()
            print(f"   - 状态数量: {len(state_list)}")
            
            # 测试状态加载
            load_success = state_manager.load_state("test_state")
            if load_success:
                print(f"✅ 状态加载成功")
            else:
                print(f"⚠️ 状态加载失败")
        else:
            print(f"⚠️ 状态保存失败")
            
    except Exception as e:
        print(f"❌ 状态管理测试失败: {str(e)}")
    
    # 测试现有处理结果加载
    print("\n4.5 测试现有处理结果...")
    try:
        processed_dir = config.PROCESSED_DATA_DIR
        
        # 查找已处理的文件
        import glob
        json_files = glob.glob(str(processed_dir / "analyzed_reports_*.json"))
        
        if json_files:
            print(f"✅ 发现已处理文件: {len(json_files)} 个")
            
            # 读取最新的一个文件作为示例
            latest_file = max(json_files, key=os.path.getctime)
            print(f"   - 最新文件: {os.path.basename(latest_file)}")
            
            import json
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                sample = data[0]
                print(f"   - 文件包含记录数: {len(data)}")
                print(f"   - 样本结构: {list(sample.keys())}")
                
                if "结构化数据" in sample:
                    structured = sample["结构化数据"]
                    print(f"   - 解剖结构: {len(structured.get('解剖结构', []))} 个")
                    print(f"   - 病变特征: {len(structured.get('病变特征', []))} 个")
                    print(f"   - 诊断信息: {len(structured.get('诊断信息', []))} 个")
                    
        else:
            print(f"⚠️ 未发现已处理文件")
            
    except Exception as e:
        print(f"❌ 处理结果加载测试失败: {str(e)}")
    
    # 测试可视化组件
    print("\n4.6 测试可视化组件...")
    try:
        from utils.plot_utils import create_bar_chart, create_pie_chart
        
        # 测试数据
        categories = ["肺癌", "肺炎", "钙化", "结节"]
        values = [15, 8, 12, 6]
        
        # 这里只测试函数是否可以调用，不实际显示图表
        print(f"✅ 可视化组件导入成功")
        print(f"   - 图表数据准备: {len(categories)} 个类别")
        
    except Exception as e:
        print(f"❌ 可视化组件测试失败: {str(e)}")
    
    # 测试网络可视化
    print("\n4.7 测试网络可视化...")
    try:
        from utils.network_visualizer import create_relationship_graph
        
        # 准备测试节点和边
        test_nodes = [
            {"id": "肺癌", "label": "肺癌", "group": 1},
            {"id": "结节", "label": "结节", "group": 2},
            {"id": "毛糙边界", "label": "毛糙边界", "group": 2}
        ]
        
        test_edges = [
            {"from": "结节", "to": "肺癌", "label": "提示"},
            {"from": "毛糙边界", "to": "肺癌", "label": "支持"}
        ]
        
        print(f"✅ 网络可视化组件导入成功")
        print(f"   - 测试节点: {len(test_nodes)} 个")
        print(f"   - 测试边: {len(test_edges)} 个")
        
    except Exception as e:
        print(f"❌ 网络可视化测试失败: {str(e)}")
    
    # 测试Pipeline管理器
    print("\n4.8 测试Pipeline管理器...")
    try:
        from utils.pipeline_manager import PipelineManager
        
        pipeline = PipelineManager()
        print(f"✅ Pipeline管理器初始化成功")
        
        # 测试步骤注册
        steps = pipeline.get_available_steps()
        print(f"   - 可用步骤: {len(steps)} 个")
        for step in steps:
            print(f"     - {step}")
            
    except Exception as e:
        print(f"❌ Pipeline管理器测试失败: {str(e)}")
    
    print("\n🎉 步骤4测试完成!")
    
except Exception as e:
    print(f"❌ 步骤4测试失败: {str(e)}")
    import traceback
    traceback.print_exc() 