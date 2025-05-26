"""
数据处理模块，负责Excel数据的读取和预处理
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_excel_data(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    从Excel文件加载数据
    
    参数:
        file_path: Excel文件路径
        sheet_name: 表格名称，默认为None（读取第一个表格）
    
    返回:
        加载的DataFrame
    """
    try:
        logger.info(f"正在从 {file_path} 加载数据...")
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
        logger.info(f"成功加载数据，共 {len(df)} 行")
        return df
    except Exception as e:
        logger.error(f"加载数据失败: {str(e)}")
        raise

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗DataFrame数据
    
    参数:
        df: 输入的DataFrame
    
    返回:
        清洗后的DataFrame
    """
    # 复制DataFrame以避免修改原始数据
    df_clean = df.copy()
    
    # 1. 处理缺失值
    null_counts = df_clean.isnull().sum()
    logger.info(f"缺失值统计: \n{null_counts}")
    
    # 2. 去除空行 (所有关键列都为空的行)
    key_columns = ['影像表现', '诊断结论']
    key_columns = [col for col in key_columns if col in df_clean.columns]
    if key_columns:
        before_len = len(df_clean)
        df_clean = df_clean.dropna(subset=key_columns, how='all')
        logger.info(f"去除空行后，从 {before_len} 行减少到 {len(df_clean)} 行")
    
    # 3. 文本数据清洗和标准化
    text_columns = ['影像表现', '诊断结论']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).apply(standardize_text)
    
    return df_clean

def standardize_text(text: str) -> str:
    """
    标准化文本内容
    
    参数:
        text: 输入文本
    
    返回:
        标准化后的文本
    """
    if pd.isna(text) or text == 'nan':
        return ""
    
    # 替换多个空格为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 统一全角标点为半角标点
    punctuation_map = {
        '，': ',', '。': '.', '：': ':', '；': ';',
        '"': '"', '"': '"', ''': "'", ''': "'",
        '（': '(', '）': ')', '【': '[', '】': ']',
        '！': '!', '？': '?'
    }
    for ch, en in punctuation_map.items():
        text = text.replace(ch, en)
    
    # 去除首尾空格
    text = text.strip()
    
    return text

def get_report_sections(text: str) -> Dict[str, str]:
    """
    尝试将报告文本分割为不同的部分
    
    参数:
        text: 报告文本
    
    返回:
        包含不同部分的字典
    """
    sections = {}
    
    # 常见的报告部分标题
    section_patterns = [
        (r'胸廓[与和及]?胸膜[:：]?(.*?)(?=肺部[:：]|气管[:：]|$)', '胸廓与胸膜'),
        (r'肺部[:：]?(.*?)(?=胸廓[:：]|气管[:：]|$)', '肺部'),
        (r'气管[与和及]?支气管[:：]?(.*?)(?=胸廓[:：]|肺部[:：]|$)', '气管与支气管'),
        (r'纵隔[与和及]?心脏[:：]?(.*?)(?=胸廓[:：]|肺部[:：]|气管[:：]|$)', '纵隔与心脏')
    ]
    
    for pattern, section_name in section_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sections[section_name] = match.group(1).strip()
    
    # 如果没有找到任何部分，则将整个文本作为"其他"部分
    if not sections:
        sections['完整描述'] = text
    
    return sections

def extract_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    提取数据集的基本统计信息
    
    参数:
        df: 输入的DataFrame
    
    返回:
        包含统计信息的字典
    """
    stats = {
        '报告总数': len(df),
        '列名列表': list(df.columns),
        '数据类型': {col: str(df[col].dtype) for col in df.columns},
        '缺失值统计': {col: int(df[col].isna().sum()) for col in df.columns},
    }
    
    # 计算诊断结论的分布情况
    if '诊断结论' in df.columns:
        # 简化诊断（提取第一个诊断条目作为主诊断）
        df['主要诊断'] = df['诊断结论'].apply(
            lambda x: x.split('.')[0].strip() if isinstance(x, str) and '.' in x else x
        )
        diagnosis_counts = df['主要诊断'].value_counts().head(10).to_dict()
        stats['前10位诊断分布'] = diagnosis_counts
    
    return stats

def save_processed_data(df: pd.DataFrame, save_path: str) -> None:
    """
    保存处理后的数据
    
    参数:
        df: 处理后的DataFrame
        save_path: 保存路径
    """
    try:
        logger.info(f"正在保存处理后的数据到 {save_path}")
        df.to_pickle(save_path)
        logger.info("数据保存成功")
    except Exception as e:
        logger.error(f"保存数据失败: {str(e)}")
        raise

def load_processed_data(file_path: str) -> pd.DataFrame:
    """
    加载处理后的数据
    
    参数:
        file_path: 数据文件路径
    
    返回:
        加载的DataFrame
    """
    try:
        logger.info(f"正在加载处理后的数据: {file_path}")
        df = pd.read_pickle(file_path)
        logger.info(f"成功加载数据，共 {len(df)} 行")
        return df
    except Exception as e:
        logger.error(f"加载处理后的数据失败: {str(e)}")
        raise
