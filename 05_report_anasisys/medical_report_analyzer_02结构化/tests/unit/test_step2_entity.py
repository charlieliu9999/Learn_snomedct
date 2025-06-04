#!/usr/bin/env python3
"""
测试步骤2: 实体识别测试
"""
import sys
import os
sys.path.append('.')

print("🔍 步骤2: 实体识别测试")
print("=" * 50)

# 测试数据
test_report = """
右肺上叶见一枚约1.5cm大小的结节影，边缘毛糙，内部密度不均匀。
右肺下叶见散在小结节影。双肺门淋巴结增大。胸腔未见积液。
心脏大小形态正常。主动脉壁钙化。
"""

test_diagnosis = """
右肺上叶结节，考虑恶性病变可能，建议进一步检查。
双肺散在结节，炎性或其他。
淋巴结增大。
主动脉壁钙化。
"""

try:
    # 初始化必要组件
    print("2.1 初始化测试环境...")
    import config
    from utils.config_manager import config_manager
    from utils.llm_client import LLMClient
    from utils.structure_extractor import StructureExtractor
    
    user_config = config_manager.get_config()
    llm_config = user_config.get('llm_config', config.LLM_CONFIG)
    llm_client = LLMClient(llm_config)
    extractor = StructureExtractor(llm_client)
    
    print("✅ 测试环境初始化成功")
    
    # 测试LLM基本连接
    print("\n2.2 测试LLM基本连接...")
    try:
        test_response = llm_client.generate("请回答：1+1等于几？")
        print(f"✅ LLM连接正常，响应: {test_response[:30]}...")
    except Exception as e:
        print(f"❌ LLM连接失败: {str(e)}")
        print("继续测试其他功能...")
    
    # 测试解剖结构识别
    print("\n2.3 测试解剖结构识别...")
    try:
        anatomical_structures = extractor.extract_anatomical_structures(test_report)
        print(f"✅ 解剖结构识别成功，提取到 {len(anatomical_structures)} 个结构")
        for i, struct in enumerate(anatomical_structures[:3]):
            print(f"   [{i+1}] 原文: {struct.get('原文', 'N/A')}")
            print(f"       标准名: {struct.get('标准名', 'N/A')}")
    except Exception as e:
        print(f"❌ 解剖结构识别失败: {str(e)}")
    
    # 测试病变特征识别
    print("\n2.4 测试病变特征识别...")
    try:
        lesion_features = extractor.extract_lesion_features(test_report)
        print(f"✅ 病变特征识别成功，提取到 {len(lesion_features)} 个特征")
        for i, feature in enumerate(lesion_features[:3]):
            print(f"   [{i+1}] 名称: {feature.get('名称', 'N/A')}")
            if '特征' in feature and '解剖位置' in feature['特征']:
                print(f"       位置: {feature['特征']['解剖位置']}")
    except Exception as e:
        print(f"❌ 病变特征识别失败: {str(e)}")
    
    # 测试诊断信息提取
    print("\n2.5 测试诊断信息提取...")
    try:
        diagnosis_info = extractor.extract_diagnosis_info(test_diagnosis)
        print(f"✅ 诊断信息提取成功，提取到 {len(diagnosis_info)} 个诊断")
        for i, diag in enumerate(diagnosis_info[:3]):
            print(f"   [{i+1}] 类型: {diag.get('类型', 'N/A')}")
            print(f"       描述: {diag.get('描述', 'N/A')[:50]}...")
    except Exception as e:
        print(f"❌ 诊断信息提取失败: {str(e)}")
    
    # 测试完整报告分析
    print("\n2.6 测试完整报告分析...")
    try:
        complete_result = extractor.analyze_single_report(test_report, test_diagnosis)
        print(f"✅ 完整报告分析成功")
        
        structured_data = complete_result.get('结构化数据', {})
        print(f"   - 解剖结构: {len(structured_data.get('解剖结构', []))} 个")
        print(f"   - 病变特征: {len(structured_data.get('病变特征', []))} 个")
        print(f"   - 诊断信息: {len(structured_data.get('诊断信息', []))} 个")
        print(f"   - 映射关系: {len(structured_data.get('影像诊断映射', []))} 个")
        
        # 显示处理时间
        analysis_info = complete_result.get('分析信息', {})
        if '处理时间' in analysis_info:
            print(f"   - 处理时间: {analysis_info['处理时间']}")
    except Exception as e:
        print(f"❌ 完整报告分析失败: {str(e)}")
    
    print("\n🎉 步骤2测试完成!")
    
except Exception as e:
    print(f"❌ 步骤2测试失败: {str(e)}")
    import traceback
    traceback.print_exc() 