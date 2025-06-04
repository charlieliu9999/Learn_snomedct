"""
结构提取器模块，负责从医学报告中提取结构化信息
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional

from .llm_client import LLMClient
from .prompt_templates import PromptTemplateManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def __init__(self, llm_client: LLMClient):
    """
    初始化结构提取器
    
    参数:
        llm_client: LLM客户端实例
    """
    self.llm_client = llm_client
    self.status_callback = None  # 状态回调函数
    
    # 添加提示词模板管理器
    self.prompt_manager = PromptTemplateManager()
    
    # 添加简单缓存
    self.cache = {}
    self.debug_info = {}
    
    # 默认报告类型
    self.report_type = "default"

    def detect_report_type(self, report_text: str) -> str:
        """
        检测报告类型
        
        参数:
            report_text: 报告文本
        
        返回:
            报告类型 (胸部CT, 腹部超声, 等)
        """
        # 简单的关键词匹配规则
        report_text_lower = report_text.lower()
        
        if "ct" in report_text_lower and ("胸" in report_text or "肺" in report_text):
            return "胸部CT"
        elif "超声" in report_text_lower and ("腹" in report_text or "肝" in report_text or "胆" in report_text):
            return "腹部超声"
        elif "mri" in report_text_lower:
            return "MRI"
        
        # 默认返回通用类型
        return "default"
def _get_cache_key(self, text: str) -> str:
    """
    生成缓存键
    
    参数:
        text: 文本内容
    
    返回:
        缓存键
    """
    # 使用MD5哈希作为缓存键
    return hashlib.md5(text.encode('utf-8')).hexdigest()

    def extract_anatomical_structures(self, report_text: str) -> List[Dict[str, str]]:
        """
        从报告文本中提取解剖结构
        
        参数:
            report_text: 报告文本
        
        返回:
            解剖结构列表，每个结构包含原文、标准名称和父结构
        """
        # 检查缓存
        cache_key = self._get_cache_key(f"anatomical_{report_text}")
        if cache_key in self.cache:
            logger.info("使用缓存的解剖结构提取结果")
            return self.cache[cache_key]
        
        # 检测报告类型
        report_type = self.detect_report_type(report_text)
        
        # 使用模板管理器获取提示词
        prompt = self.prompt_manager.get_prompt(
            "anatomical", 
            report_type, 
            report_text=report_text
        )
        
        # 保存提示词用于调试
        self.debug_info["解剖结构_提示词"] = prompt
        self.debug_info["解剖结构_报告类型"] = report_type
        
        try:
            result = self.llm_client.extract_json(prompt)
            # 保存模型响应用于调试
            self.debug_info["解剖结构_响应"] = result
            
            if isinstance(result, list):
                # 保存到缓存
                self.cache[cache_key] = result
                return result
            elif isinstance(result, dict) and "error" in result:
                logger.error(f"提取解剖结构失败: {result['error']}")
                return []
            else:
                return []
        except Exception as e:
            logger.error(f"提取解剖结构时发生错误: {str(e)}")
            self.debug_info["解剖结构_错误"] = str(e)
            return []

def extract_anatomical_structures(self, report_text: str) -> List[Dict[str, str]]:
    """
    从报告文本中提取解剖结构
    
    参数:
        report_text: 报告文本
    
    返回:
        解剖结构列表，每个结构包含原文、标准名称和父结构
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"anatomical_{report_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的解剖结构提取结果")
        return self.cache[cache_key]
    
    # 检测报告类型
    report_type = self.detect_report_type(report_text)
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "anatomical", 
        report_type, 
        report_text=report_text
    )
    
    # 保存提示词用于调试
    self.debug_info["解剖结构_提示词"] = prompt
    self.debug_info["解剖结构_报告类型"] = report_type
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["解剖结构_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"提取解剖结构失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"提取解剖结构时发生错误: {str(e)}")
        self.debug_info["解剖结构_错误"] = str(e)
        return []
def extract_lesion_features(self, report_text: str) -> List[Dict[str, Any]]:
    """
    从报告文本中提取病变特征
    
    参数:
        report_text: 报告文本
    
    返回:
        病变特征列表，每个病变包含位置、大小、形态等信息
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"lesion_{report_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的病变特征提取结果")
        return self.cache[cache_key]
    
    # 检测报告类型
    report_type = self.detect_report_type(report_text)
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "lesion", 
        report_type, 
        report_text=report_text
    )
    
    # 保存提示词用于调试
    self.debug_info["病变特征_提示词"] = prompt
    self.debug_info["病变特征_报告类型"] = report_type
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["病变特征_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"提取病变特征失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"提取病变特征时发生错误: {str(e)}")
        self.debug_info["病变特征_错误"] = str(e)
        return []

def extract_diagnoses(self, diagnosis_text: str) -> List[Dict[str, str]]:
    """
    从诊断结论文本中提取诊断信息
    
    参数:
        diagnosis_text: 诊断结论文本
    
    返回:
        诊断信息列表，每个诊断包含类型和描述
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"diagnosis_{diagnosis_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的诊断信息提取结果")
        return self.cache[cache_key]
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "diagnosis", 
        "default", 
        diagnosis_text=diagnosis_text
    )
    
    # 保存提示词用于调试
    self.debug_info["诊断信息_提示词"] = prompt
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["诊断信息_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"提取诊断信息失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"提取诊断信息时发生错误: {str(e)}")
        self.debug_info["诊断信息_错误"] = str(e)
        return []

def build_image_diagnosis_mapping(self, image_text: str, diagnosis_text: str,
                                 anatomical_structures: Optional[List] = None,
                                 lesion_features: Optional[List] = None,
                                 diagnoses: Optional[List] = None) -> List[Dict[str, str]]:
    """
    构建影像表现与诊断结论之间的映射关系
    
    参数:
        image_text: 影像表现文本
        diagnosis_text: 诊断结论文本
        anatomical_structures: 已提取的解剖结构（可选）
        lesion_features: 已提取的病变特征（可选）
        diagnoses: 已提取的诊断信息（可选）
    
    返回:
        影像表现与诊断结论的映射关系
    """
    # 检查缓存
    cache_key = self._get_cache_key(f"mapping_{image_text}_{diagnosis_text}")
    if cache_key in self.cache:
        logger.info("使用缓存的影像诊断映射结果")
        return self.cache[cache_key]
    
    # 准备已提取的结构化信息
    extracted_info = ""
    if anatomical_structures:
        extracted_info += f"已提取的解剖结构: {json.dumps(anatomical_structures, ensure_ascii=False)}\n\n"
    if lesion_features:
        extracted_info += f"已提取的病变特征: {json.dumps(lesion_features, ensure_ascii=False)}\n\n"
    if diagnoses:
        extracted_info += f"已提取的诊断信息: {json.dumps(diagnoses, ensure_ascii=False)}\n\n"
    
    # 使用模板管理器获取提示词
    prompt = self.prompt_manager.get_prompt(
        "mapping", 
        "default", 
        image_text=image_text,
        diagnosis_text=diagnosis_text,
        extracted_info=extracted_info
    )
    
    # 保存提示词用于调试
    self.debug_info["影像诊断映射_提示词"] = prompt
    
    try:
        result = self.llm_client.extract_json(prompt)
        # 保存模型响应用于调试
        self.debug_info["影像诊断映射_响应"] = result
        
        if isinstance(result, list):
            # 保存到缓存
            self.cache[cache_key] = result
            return result
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"构建影像诊断映射失败: {result['error']}")
            return []
        else:
            return []
    except Exception as e:
        logger.error(f"构建影像诊断映射时发生错误: {str(e)}")
        self.debug_info["影像诊断映射_错误"] = str(e)
        return []

def analyze_single_report(self, image_text: str, diagnosis_text: str) -> Dict[str, Any]:
    """
    全面分析单份报告
    
    参数:
        image_text: 影像表现文本
        diagnosis_text: 诊断结论文本
    
    返回:
        完整的分析结果
    """
    steps = ["提取报告部分", "提取解剖结构", "提取病变特征", "提取诊断信息", "构建映射关系"]
    
    # 重置调试信息
    self.debug_info = {
        "分析开始时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "LLM配置": {
            "供应商": self.llm_client.provider,
            "模型": self.llm_client.model,
            "温度": getattr(self.llm_client, 'temperature', '默认'),
            "最大输出标记": getattr(self.llm_client, 'max_tokens', '默认')
        },
        "分析耗时": {}
    }
    
    result = {
        "原始数据": {
            "影像表现": image_text,
            "诊断结论": diagnosis_text
        },
        "结构化数据": {}
    }
    
    try:
        # 检测报告类型
        self.report_type = self.detect_report_type(image_text)
        self.debug_info["报告类型"] = self.report_type
        
        # 1. 提取报告部分
        if self.status_callback:
            self.status_callback(steps[0], 0)
                
        step_start_time = time.time()
        logger.info("1. 提取报告部分...")
        report_sections = self.extract_report_sections(image_text)
        result["结构化数据"]["报告部分"] = report_sections
        step_time = time.time() - step_start_time
        self.debug_info["分析耗时"]["提取报告部分"] = f"{step_time:.2f}秒"
        logger.info(f"   提取到 {len(report_sections)} 个报告部分 (耗时: {step_time:.2f}秒)")
            
        # 2. 提取解剖结构
        if self.status_callback:
            self.status_callback(steps[1], 1)
                
        step_start_time = time.time()
        logger.info("2. 提取解剖结构...")
        anatomical_structures = self.extract_anatomical_structures(image_text)
        result["结构化数据"]["解剖结构"] = anatomical_structures
        step_time = time.time() - step_start_time
        self.debug_info["分析耗时"]["提取解剖结构"] = f"{step_time:.2f}秒"
        logger.info(f"   提取到 {len(anatomical_structures)} 个解剖结构 (耗时: {step_time:.2f}秒)")
            
        # 3. 提取病变特征
        if self.status_callback:
            self.status_callback(steps[2], 2)
                
        step_start_time = time.time()
        logger.info("3. 提取病变特征...")
        lesion_features = self.extract_lesion_features(image_text)
        result["结构化数据"]["病变特征"] = lesion_features
        step_time = time.time() - step_start_time
        self.debug_info["分析耗时"]["提取病变特征"] = f"{step_time:.2f}秒"
        logger.info(f"   提取到 {len(lesion_features)} 个病变特征 (耗时: {step_time:.2f}秒)")
            
        # 4. 提取诊断信息
        if self.status_callback:
            self.status_callback(steps[3], 3)
                
        step_start_time = time.time()
        logger.info("4. 提取诊断信息...")
        diagnoses = self.extract_diagnoses(diagnosis_text)
        result["结构化数据"]["诊断信息"] = diagnoses
        step_time = time.time() - step_start_time
        self.debug_info["分析耗时"]["提取诊断信息"] = f"{step_time:.2f}秒"
        logger.info(f"   提取到 {len(diagnoses)} 个诊断信息 (耗时: {step_time:.2f}秒)")
            
        # 5. 构建映射关系
        if self.status_callback:
            self.status_callback(steps[4], 4)
                
        step_start_time = time.time()
        logger.info("5. 构建映射关系...")
        mapping = self.build_image_diagnosis_mapping(
            image_text, 
            diagnosis_text,
            anatomical_structures,
            lesion_features,
            diagnoses
        )
        result["结构化数据"]["影像诊断映射"] = mapping
        step_time = time.time() - step_start_time
        self.debug_info["分析耗时"]["构建映射关系"] = f"{step_time:.2f}秒"
        logger.info(f"   映射关系构建完成 (耗时: {step_time:.2f}秒)")
            
        logger.info("===== 报告分析完成 =====\n")
    except Exception as e:
        logger.error(f"===== 报告分析出错: {str(e)} =====\n")
        self.debug_info["分析错误"] = str(e)
        # 出错时仍然返回部分结果
        
    # 将调试信息添加到结果中
    result["调试信息"] = self.debug_info
        
    return result
# 添加提示词模板设置
with st.expander("🔧 高级提示词设置", expanded=False):
    st.markdown("### 提示词模板配置")
    st.info("提示词模板用于指导LLM从报告中提取结构化信息。优化提示词可以提高提取精度。")
    
    # 如果结构提取器未初始化，进行初始化
    if "structure_extractor" not in st.session_state:
        if st.session_state.get("llm_client") is not None:
            from utils.structure_extractor import StructureExtractor
            st.session_state.structure_extractor = StructureExtractor(st.session_state.llm_client)
    
    # 获取提示词管理器
    if "structure_extractor" in st.session_state:
        extractor = st.session_state.structure_extractor
        prompt_manager = extractor.prompt_manager
        
        # 获取可用的提示词类型
        available_types = prompt_manager.get_available_types()
        
        # 创建提示词编辑界面
        prompt_type_names = {
            "anatomical": "解剖结构提取",
            "lesion": "病变特征提取",
            "diagnosis": "诊断信息提取",
            "mapping": "影像诊断映射"
        }
        
        # 选择提示词类型
        prompt_type = st.selectbox(
            "提示词类型", 
            list(prompt_type_names.keys()),
            format_func=lambda x: prompt_type_names.get(x, x)
        )
        
        # 选择报告类型
        if prompt_type in available_types:
            report_types = available_types[prompt_type]
            report_type = st.selectbox("报告类型", report_types)
            
            # 获取当前模板
            current_template = prompt_manager.get_prompt(prompt_type, report_type)
            
            # 编辑模板
            edited_template = st.text_area(
                "编辑提示词模板", 
                current_template, 
                height=300
            )
            
            # 保存模板
            if st.button("保存模板"):
                if prompt_manager.save_template(prompt_type, report_type, edited_template):
                    st.success(f"已保存 {prompt_type_names.get(prompt_type, prompt_type)} - {report_type} 模板")
                else:
                    st.error("保存模板失败")
        else:
            st.warning("未找到可用的提示词类型")
    else:
        st.warning("请先在上方配置并初始化LLM客户端")
        
