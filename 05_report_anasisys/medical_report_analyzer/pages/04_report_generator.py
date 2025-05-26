"""
报告生成页面 - 实现双向驱动的医学影像报告生成
"""

import streamlit as st
import pandas as pd
import os
import sys
import json
import re

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和工具模块
import config
from utils.structure_extractor import StructureExtractor

st.set_page_config(
    page_title=f"{config.APP_TITLE} - 报告生成",
    page_icon="📝",
    layout="wide"
)

st.title("📝 双向驱动报告生成")
st.markdown("基于影像-诊断知识库，实现影像→诊断和诊断→描述双向驱动的报告生成。")

# 初始化状态
if "report_generator_mode" not in st.session_state:
    st.session_state.report_generator_mode = "影像→诊断"

if "current_report" not in st.session_state:
    st.session_state.current_report = {
        "影像表现": "",
        "影像结构": {},
        "推荐诊断": [],
        "选定诊断": [],
        "生成描述": ""
    }

# 侧边栏
st.sidebar.header("报告生成设置")

# 选择报告生成模式
report_mode = st.sidebar.radio(
    "报告生成模式",
    ["影像→诊断", "诊断→描述"]
)

st.session_state.report_generator_mode = report_mode

# 加载知识库
st.sidebar.header("知识库设置")

kb_files = list(config.PROCESSED_DATA_DIR.glob("knowledge_base_*.json")) + list(config.PROCESSED_DATA_DIR.glob("bidirectional_templates_*.json"))

if kb_files:
    kb_file_names = [file.name for file in kb_files]
    selected_kb = st.sidebar.selectbox("选择知识库文件", kb_file_names)
    
    if st.sidebar.button("加载知识库", key="load_kb_gen"):
        with st.spinner("正在加载知识库..."):
            kb_path = config.PROCESSED_DATA_DIR / selected_kb
            
            try:
                with open(kb_path, 'r', encoding='utf-8') as f:
                    if "knowledge_base" in selected_kb:
                        # 加载完整知识库
                        st.session_state.knowledge_base = json.load(f)
                        if "bidirectional_templates" in st.session_state.knowledge_base:
                            st.session_state.templates = st.session_state.knowledge_base["bidirectional_templates"]
                    else:
                        # 仅加载模板
                        st.session_state.templates = json.load(f)
                
                st.success("知识库加载成功！")
            except Exception as e:
                st.error(f"知识库加载失败: {str(e)}")
else:
    st.sidebar.warning("未找到知识库文件，请先构建并保存知识库")

# 主要内容区域
if report_mode == "影像→诊断":
    st.markdown("### 从影像表现推导诊断")
    
    # 分两列显示内容
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 输入影像表现")
        
        # 区域选择
        anatomy_section = st.selectbox(
            "选择解剖区域", 
            ["胸廓与胸膜", "肺部", "气管与支气管", "纵隔与心脏", "自定义"]
        )
        
        if anatomy_section == "自定义":
            custom_section = st.text_input("输入自定义区域")
            current_section = custom_section
        else:
            current_section = anatomy_section
        
        # 特征输入框
        section_text = st.text_area(
            f"{current_section}描述", 
            height=200, 
            key=f"section_{current_section}",
            value=st.session_state.current_report.get("影像结构", {}).get(current_section, "")
        )
        
        # 保存到状态
        if current_section and section_text:
            if "影像结构" not in st.session_state.current_report:
                st.session_state.current_report["影像结构"] = {}
            
            st.session_state.current_report["影像结构"][current_section] = section_text
        
        # 合并所有区域的文本
        all_sections_text = ""
        if "影像结构" in st.session_state.current_report:
            for section, text in st.session_state.current_report["影像结构"].items():
                if text.strip():
                    all_sections_text += f"{section}：{text}\n\n"
        
        st.session_state.current_report["影像表现"] = all_sections_text
        
        # 分析按钮
        if st.button("分析影像描述", key="analyze_image"):
            with st.spinner("正在分析影像描述..."):
                # 检查是否有LLM客户端
                if st.session_state.get("llm_client") is None:
                    st.error("LLM客户端未初始化")
                else:
                    # 提取结构和推断诊断
                    extractor = StructureExtractor(st.session_state.llm_client)
                    
                    # 提取影像特征
                    try:
                        features = extractor.extract_lesion_features(all_sections_text)
                        st.session_state.current_report["提取特征"] = features
                        
                        # 使用知识库推断诊断
                        prompt = f"""
                        基于以下胸部CT的影像特征，推断可能的诊断:
                        
                        影像表现:
                        {all_sections_text}
                        
                        提取的特征:
                        {json.dumps(features, ensure_ascii=False, indent=2)}
                        
                        请提供最可能的诊断，包括诊断名称、可能性评估和依据，以JSON格式返回:
                        [
                          {{"诊断名称": "肺腺癌", "可能性": "高", "依据": "右肺上叶可见边缘毛刺的结节影，伴分叶征，符合肺腺癌的典型影像学表现"}},
                          {{"诊断名称": "肺错构瘤", "可能性": "中", "依据": "结节密度较低，可能含有脂肪成分，考虑错构瘤可能"}},
                          ...
                        ]
                        
                        最多提供5个可能的诊断，按可能性从高到低排序。
                        """
                        
                        diagnoses = st.session_state.llm_client.extract_json(prompt)
                        
                        if isinstance(diagnoses, list):
                            st.session_state.current_report["推荐诊断"] = diagnoses
                            st.success("影像分析完成，已生成推荐诊断！")
                        else:
                            st.error("诊断推断失败")
                    except Exception as e:
                        st.error(f"影像分析过程出错: {str(e)}")
    
    with col2:
        st.markdown("#### 诊断推荐")
        
        # 显示推荐诊断
        if "推荐诊断" in st.session_state.current_report and st.session_state.current_report["推荐诊断"]:
            for i, diag in enumerate(st.session_state.current_report["推荐诊断"]):
                if "诊断名称" in diag and "可能性" in diag:
                    with st.expander(f"{diag['诊断名称']} (可能性: {diag['可能性']})", expanded=(i == 0)):
                        st.write(f"**依据**: {diag.get('依据', '未提供')}")
                        
                        # 添加选择按钮
                        if st.button(f"选择该诊断", key=f"select_diag_{i}"):
                            if "选定诊断" not in st.session_state.current_report:
                                st.session_state.current_report["选定诊断"] = []
                            
                            # 检查是否已添加
                            if diag['诊断名称'] not in [d.get('诊断名称') for d in st.session_state.current_report["选定诊断"]]:
                                st.session_state.current_report["选定诊断"].append(diag)
                                st.success(f"已选择 {diag['诊断名称']} 作为诊断！")
        else:
            st.info("请先分析影像描述以获取推荐诊断")
        
        # 显示已选诊断
        st.markdown("#### 已选诊断")
        
        if "选定诊断" in st.session_state.current_report and st.session_state.current_report["选定诊断"]:
            for i, diag in enumerate(st.session_state.current_report["选定诊断"]):
                col_diag, col_remove = st.columns([4, 1])
                
                with col_diag:
                    st.write(f"{i+1}. **{diag.get('诊断名称', '未知诊断')}** (可能性: {diag.get('可能性', '未知')})")
                
                with col_remove:
                    if st.button("移除", key=f"remove_diag_{i}"):
                        st.session_state.current_report["选定诊断"].pop(i)
                        st.experimental_rerun()
        else:
            st.info("尚未选择任何诊断")
        
        # 生成报告按钮
        if "选定诊断" in st.session_state.current_report and st.session_state.current_report["选定诊断"]:
            st.markdown("#### 生成完整报告")
            
            if st.button("生成标准报告", key="generate_report"):
                with st.spinner("正在生成标准报告..."):
                    # 准备诊断文本
                    diag_texts = []
                    for i, diag in enumerate(st.session_state.current_report["选定诊断"]):
                        diag_texts.append(f"{i+1}. {diag.get('诊断名称')}" + (f"，{diag.get('依据')}" if "依据" in diag else ""))
                    
                    diagnosis_text = "。".join(diag_texts) + "。"
                    
                    prompt = f"""
                    请基于以下影像表现和诊断，生成一份标准化的医学影像报告。

                    影像表现:
                    {st.session_state.current_report['影像表现']}

                    诊断结论:
                    {diagnosis_text}

                    请按以下格式生成完整报告:
                    ```
                    【影像表现】
                    (标准化、完整的影像表现描述，组织合理，包含所有重要发现)

                    【诊断结论】
                    (规范的诊断结论，包括主要诊断、鉴别诊断和建议)
                    ```
                    """
                    
                    try:
                        report = st.session_state.llm_client.generate(prompt)
                        
                        # 提取影像表现和诊断结论
                        image_part = re.search(r"【影像表现】\s*(.*?)\s*【诊断结论】", report, re.DOTALL)
                        diagnosis_part = re.search(r"【诊断结论】\s*(.*?)\s*(?:```|$)", report, re.DOTALL)
                        
                        if image_part and diagnosis_part:
                            st.session_state.current_report["生成报告"] = {
                                "影像表现": image_part.group(1).strip(),
                                "诊断结论": diagnosis_part.group(1).strip()
                            }
                            st.success("报告生成完成！")
                        else:
                            st.error("报告格式解析失败")
                    except Exception as e:
                        st.error(f"报告生成失败: {str(e)}")
    
    # 显示生成的完整报告
    if "生成报告" in st.session_state.current_report:
        st.markdown("---")
        st.markdown("### 生成的标准报告")
        
        report = st.session_state.current_report["生成报告"]
        
        st.markdown("#### 影像表现")
        st.write(report["影像表现"])
        
        st.markdown("#### 诊断结论")
        st.write(report["诊断结论"])
        
        # 导出报告
        st.download_button(
            label="导出报告 (TXT)",
            data=f"【影像表现】\n{report['影像表现']}\n\n【诊断结论】\n{report['诊断结论']}",
            file_name=f"医学影像报告_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

elif report_mode == "诊断→描述":
    st.markdown("### 从诊断生成标准化描述")
    
    # 分两列显示内容
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 选择诊断")
        
        # 诊断选择
        if "templates" in st.session_state and "诊断描述模板" in st.session_state.templates and "诊断列表" in st.session_state.templates["诊断描述模板"]:
            diag_list = st.session_state.templates["诊断描述模板"]["诊断列表"]
            diag_names = [d["诊断"] for d in diag_list if "诊断" in d]
            
            selected_diag = st.selectbox("选择诊断", diag_names)
            
            # 诊断详情
            selected_template = None
            for diag_template in diag_list:
                if diag_template.get("诊断") == selected_diag:
                    selected_template = diag_template
                    break
            
            if selected_template:
                st.markdown("#### 诊断详情")
                
                if "描述模板" in selected_template:
                    for i, template in enumerate(selected_template["描述模板"]):
                        st.markdown(f"{i+1}. `{template}`")
                
                # 保存选择的诊断
                if st.button("使用该诊断", key="use_diagnosis"):
                    st.session_state.current_report["选定诊断"] = [{"诊断名称": selected_diag, "模板": selected_template}]
                    st.success(f"已选择 {selected_diag} 作为诊断！")
        else:
            st.warning("未找到诊断模板，请先加载有效的知识库")
        
        # 自定义诊断
        st.markdown("#### 或输入自定义诊断")
        custom_diag = st.text_input("自定义诊断")
        
        if custom_diag and st.button("使用自定义诊断", key="use_custom_diag"):
            st.session_state.current_report["选定诊断"] = [{"诊断名称": custom_diag, "模板": None}]
            st.success(f"已选择自定义诊断: {custom_diag}！")
    
    with col2:
        st.markdown("#### 生成影像描述")
        
        # 显示已选诊断
        if "选定诊断" in st.session_state.current_report and st.session_state.current_report["选定诊断"]:
            diag = st.session_state.current_report["选定诊断"][0]
            st.write(f"当前诊断: **{diag['诊断名称']}**")
            
            # 特征参数输入
            st.markdown("##### 填写影像特征参数")
            
            params = {}
            
            # 基本参数输入
            col_params1, col_params2 = st.columns(2)
            
            with col_params1:
                params["解剖位置"] = st.text_input("解剖位置", "右肺上叶")
                params["大小"] = st.text_input("大小", "2.5cm×1.8cm")
                params["形态"] = st.selectbox("形态", ["结节状", "肿块", "团片状", "条索状", "磨玻璃", "实变", "网格状"])
            
            with col_params2:
                params["密度"] = st.selectbox("密度", ["软组织密度", "高密度", "低密度", "混合密度", "脂肪密度"])
                params["边界"] = st.selectbox("边界", ["边缘清晰", "边缘模糊", "毛刺征", "分叶状", "平滑", "锯齿状"])
                params["增强方式"] = st.selectbox("增强方式", ["明显强化", "轻度强化", "不均匀强化", "环形强化", "无明显强化"])
            
            # 其他特征
            params["其他特征"] = st.text_area("其他特征", "可见钙化")
            
            # 生成描述按钮
            if st.button("生成影像描述", key="generate_description"):
                with st.spinner("正在生成影像描述..."):
                    # 如果有模板，使用模板生成
                    if diag["模板"] and "描述模板" in diag["模板"]:
                        description = []
                        
                        for template in diag["模板"]["描述模板"]:
                            # 替换模板中的参数
                            temp_desc = template
                            for param, value in params.items():
                                temp_desc = temp_desc.replace(f"{{{{{param}}}}}", value)
                            
                            description.append(temp_desc)
                        
                        full_description = "。".join(description) + "。"
                        st.session_state.current_report["生成描述"] = full_description
                    else:
                        # 使用LLM生成描述
                        prompt = f"""
                        请基于以下诊断和参数，生成一段符合医学标准的影像描述。

                        诊断: {diag['诊断名称']}

                        参数:
                        - 解剖位置: {params['解剖位置']}
                        - 大小: {params['大小']}
                        - 形态: {params['形态']}
                        - 密度: {params['密度']}
                        - 边界: {params['边界']}
                        - 增强方式: {params['增强方式']}
                        - 其他特征: {params['其他特征']}

                        生成一段完整、专业的医学影像描述文本，符合放射科医生的表达习惯。
                        """
                        
                        try:
                            description = st.session_state.llm_client.generate(prompt)
                            
                            # 保存生成的描述
                            st.session_state.current_report["生成描述"] = description
                            st.success("影像描述生成完成！")
                        except Exception as e:
                            st.error(f"描述生成失败: {str(e)}")
        else:
            st.info("请先选择一个诊断")
    
    # 显示生成的描述
    if "生成描述" in st.session_state.current_report and st.session_state.current_report["生成描述"]:
        st.markdown("---")
        st.markdown("### 生成的影像描述")
        
        st.write(st.session_state.current_report["生成描述"])
        
        # 生成完整报告
        st.markdown("#### 生成完整报告")
        
        if st.button("生成标准报告", key="generate_full_report"):
            with st.spinner("正在生成标准报告..."):
                # 准备诊断文本
                diag_name = st.session_state.current_report["选定诊断"][0]["诊断名称"]
                
                prompt = f"""
                请基于以下影像描述和诊断，生成一份标准化的医学影像报告。

                影像描述:
                {st.session_state.current_report['生成描述']}

                诊断:
                {diag_name}

                请按以下格式生成完整报告:
                ```
                【影像表现】
                (完整的影像表现描述，组织合理，可适当扩充相关内容)

                【诊断结论】
                (规范的诊断结论，包括主要诊断、可能的鉴别诊断和建议)
                ```
                """
                
                try:
                    report = st.session_state.llm_client.generate(prompt)
                    
                    # 提取影像表现和诊断结论
                    image_part = re.search(r"【影像表现】\s*(.*?)\s*【诊断结论】", report, re.DOTALL)
                    diagnosis_part = re.search(r"【诊断结论】\s*(.*?)\s*(?:```|$)", report, re.DOTALL)
                    
                    if image_part and diagnosis_part:
                        st.session_state.current_report["生成报告"] = {
                            "影像表现": image_part.group(1).strip(),
                            "诊断结论": diagnosis_part.group(1).strip()
                        }
                        st.success("报告生成完成！")
                    else:
                        st.error("报告格式解析失败")
                except Exception as e:
                    st.error(f"报告生成失败: {str(e)}")
        
        # 显示生成的完整报告
        if "生成报告" in st.session_state.current_report:
            st.markdown("#### 完整报告")
            
            report = st.session_state.current_report["生成报告"]
            
            tab1, tab2 = st.tabs(["影像表现", "诊断结论"])
            
            with tab1:
                st.write(report["影像表现"])
            
            with tab2:
                st.write(report["诊断结论"])
            
            # 导出报告
            st.download_button(
                label="导出报告 (TXT)",
                data=f"【影像表现】\n{report['影像表现']}\n\n【诊断结论】\n{report['诊断结论']}",
                file_name=f"医学影像报告_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# 清除状态按钮
st.sidebar.markdown("---")
if st.sidebar.button("清除当前报告", key="clear_report"):
    st.session_state.current_report = {
        "影像表现": "",
        "影像结构": {},
        "推荐诊断": [],
        "选定诊断": [],
        "生成描述": ""
    }
    st.sidebar.success("已清除当前报告状态")
    st.experimental_rerun()
