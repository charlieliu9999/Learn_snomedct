#!/usr/bin/env python3
"""
检查原始数据的实际内容
"""

import json
from pathlib import Path

def check_original_data():
    """检查原始数据的实际内容"""
    
    data_file = Path("data/processed/analyzed_reports_3_20250604_220917.json")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    report = data[2]
    features = report['结构化数据'].get('病变特征', [])
    
    print(f'原始病变特征数量: {len(features)}')
    print('原始病变特征内容:')
    
    for i, f in enumerate(features):
        print(f'{i+1}. {f}')
        
    print('\n映射关系:')
    mappings = report['结构化数据'].get('影像诊断映射', [])
    print(f'映射关系数量: {len(mappings)}')
    
    for i, m in enumerate(mappings):
        print(f'{i+1}. {m}')

if __name__ == "__main__":
    check_original_data() 