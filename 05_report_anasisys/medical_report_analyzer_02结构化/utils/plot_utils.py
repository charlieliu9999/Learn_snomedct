"""
绘图工具模块，处理中文显示和图表样式
"""

import matplotlib.pyplot as plt
import seaborn as sns
from . import font_manager

def configure_chinese_font():
    """
    配置matplotlib支持中文显示 - 使用更可靠的方法
    """
    # 使用新的font_manager模块
    font_manager.initialize_chinese_font()
    
    # 设置全局样式
    sns.set_style("whitegrid")
    
    return True

def create_bar_chart(x_data, y_data, title='', xlabel='', ylabel='', figsize=(10, 6), rotation=45):
    """
    创建条形图
    
    参数:
        x_data: x轴数据
        y_data: y轴数据
        title: 图表标题
        xlabel: x轴标签
        ylabel: y轴标签
        figsize: 图表大小
        rotation: x轴标签旋转角度
    
    返回:
        fig, ax: 图表对象
    """
    # 确保中文正确显示
    configure_chinese_font()
    
    # 创建图表
    fig, ax = plt.subplots(figsize=figsize)
    
    # 绘制条形图
    ax.bar(x_data, y_data)
    
    # 设置标题和标签
    font_props = font_manager.get_font_properties()
    ax.set_title(title, fontsize=14, fontproperties=font_props)
    ax.set_xlabel(xlabel, fontsize=12, fontproperties=font_props)
    ax.set_ylabel(ylabel, fontsize=12, fontproperties=font_props)
    
    # 处理x轴标签，确保中文显示正确
    if hasattr(x_data, '__len__') and len(x_data) > 0:
        # 如果标签过长，自动换行
        if any(isinstance(x, str) and len(x) > 10 for x in x_data):
            plt.xticks(rotation=rotation, ha='right', fontproperties=font_props)
            # 增加底部空间
            plt.subplots_adjust(bottom=0.2)
        else:
            plt.xticks(rotation=rotation, ha='right', fontproperties=font_props)
    
    # 设置刻度标签字体
    for label in ax.get_xticklabels():
        label.set_fontproperties(font_props)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_props)
    
    # 应用中文字体到所有文本元素
    font_manager.apply_chinese_font_to_figure(fig)
    
    # 自动调整布局
    plt.tight_layout()
    
    return fig, ax

def create_pie_chart(data, labels, title='', figsize=(10, 8)):
    """
    创建饼图
    
    参数:
        data: 数据
        labels: 标签
        title: 图表标题
        figsize: 图表大小
    
    返回:
        fig, ax: 图表对象
    """
    # 确保中文正确显示
    configure_chinese_font()
    
    # 创建图表
    fig, ax = plt.subplots(figsize=figsize)
    
    # 获取字体属性
    font_props = font_manager.get_font_properties()
    
    # 绘制饼图
    wedges, texts, autotexts = ax.pie(
        data, 
        labels=labels, 
        autopct='%1.1f%%',
        textprops={'fontsize': 12, 'fontproperties': font_props}
    )
    
    # 设置标题
    ax.set_title(title, fontsize=14, fontproperties=font_props)
    
    # 确保饼图是圆形的
    ax.axis('equal')
    
    # 应用中文字体到所有文本元素
    font_manager.apply_chinese_font_to_figure(fig)
    
    # 自动调整布局
    plt.tight_layout()
    
    return fig, ax
