"""
字体管理模块 - 专门用于处理中文字体的检测、加载和应用
"""

import os
import platform
import logging
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.text import Text
import subprocess
import warnings

# 创建日志记录器
logger = logging.getLogger('font_manager')

# 全局变量
FONT_FAMILY = None
FONT_PROPERTIES = None
FONT_LOADED = False

def get_system_font_dirs():
    """获取系统字体目录"""
    system = platform.system()
    font_dirs = []
    
    if system == 'Darwin':  # macOS
        font_dirs = [
            '/System/Library/Fonts',
            '/Library/Fonts',
            '/System/Library/Fonts/Supplemental',
            os.path.expanduser('~/Library/Fonts'),
            '/Network/Library/Fonts',
            '/System/Library/AssetsV2/com_apple_MobileAsset_Font7'
        ]
    elif system == 'Windows':
        font_dirs = [
            'C:\\Windows\\Fonts',
            os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\Fonts')
        ]
    else:  # Linux等
        font_dirs = [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            os.path.expanduser('~/.fonts'),
            '/usr/share/fonts/truetype',
            '/usr/share/fonts/opentype',
            '/usr/share/fonts/TTF',
            '/usr/share/fonts/OTF'
        ]
    
    # 过滤掉不存在的目录
    return [d for d in font_dirs if os.path.exists(d)]

def get_chinese_font_candidates():
    """获取中文字体候选列表"""
    system = platform.system()
    
    # 基本中文字体列表
    common_fonts = [
        'Arial Unicode MS', 
        'Microsoft YaHei', 
        'SimHei', 
        'SimSun', 
        'NSimSun',
        'Source Han Sans CN',
        'Source Han Serif CN',
        'Noto Sans CJK SC',
        'Noto Serif CJK SC',
        'DejaVu Sans',
    ]
    
    # 根据系统添加特定字体
    if system == 'Darwin':  # macOS
        mac_fonts = [
            'PingFang SC', 
            'Heiti SC', 
            'STHeiti', 
            'Hiragino Sans GB',
            'Songti SC',
            'Kaiti SC',
            'Yuanti SC',
            'STSong',
            'STFangsong',
            'STKaiti',
            'Apple LiGothic',
            '.AppleSystemUIFont',
            'Lantinghei SC',
        ]
        return mac_fonts + common_fonts
    elif system == 'Windows':
        win_fonts = [
            'Microsoft JhengHei',
            'MingLiU',
            'PMingLiU',
            'DFKai-SB',
            'FangSong', 
            'KaiTi', 
            'DengXian',
        ]
        return win_fonts + common_fonts
    else:  # Linux等
        linux_fonts = [
            'WenQuanYi Micro Hei', 
            'WenQuanYi Zen Hei',
            'Droid Sans Fallback',
            'AR PL UMing CN',
            'AR PL KaitiM GB',
            'WenQuanYi Bitmap Song',
            'HanaMinA',
            'HanaMinB',
            'Adobe Song Std',
        ]
        return linux_fonts + common_fonts

def detect_chinese_fonts():
    """检测系统中可用的中文字体"""
    # 获取系统中所有字体
    system_fonts = set([f.name for f in fm.fontManager.ttflist])
    logger.info(f"系统中发现 {len(system_fonts)} 个字体")
    
    # 获取中文字体候选列表
    chinese_fonts = get_chinese_font_candidates()
    
    # 找到系统中存在的中文字体
    available_chinese_fonts = [f for f in chinese_fonts if f in system_fonts]
    logger.info(f"找到的中文字体: {available_chinese_fonts}")
    
    return available_chinese_fonts

def find_font_file(font_name):
    """查找字体文件路径"""
    try:
        font_path = fm.findfont(fm.FontProperties(family=font_name))
        if font_path and os.path.exists(font_path):
            logger.info(f"找到字体文件: {font_path}")
            return font_path
        return None
    except Exception as e:
        logger.warning(f"查找字体文件失败: {str(e)}")
        return None

def check_font_support_chinese(font_path):
    """检查字体是否支持中文字符"""
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(font_path)
        
        # 检查常见中文字符编码范围
        for table in font['cmap'].tables:
            if table.isUnicode():
                # 检查几个常见汉字的编码点
                chinese_chars = [0x4E00, 0x6587, 0x5B57, 0x4E2D, 0x6587]  # "一", "文", "字", "中", "文"
                supported = [c in table.cmap for c in chinese_chars]
                support_rate = sum(supported) / len(supported)
                
                if support_rate > 0.5:  # 支持超过一半的测试字符
                    return True
        return False
    except Exception as e:
        logger.warning(f"检查字体支持中文失败: {str(e)}")
        return True  # 出错时假设支持

def load_font_directories():
    """加载所有字体目录"""
    font_dirs = get_system_font_dirs()
    
    # 添加字体目录
    for font_dir in font_dirs:
        try:
            logger.info(f"添加字体目录: {font_dir}")
            fm.fontManager.addfont(font_dir)
        except Exception as e:
            logger.warning(f"添加字体目录失败: {font_dir}, 错误: {str(e)}")
    
    # 尝试刷新字体缓存
    try:
        fm._rebuild()
        logger.info("字体缓存已刷新")
    except Exception as e:
        logger.warning(f"刷新字体缓存失败: {str(e)}")

def setup_matplotlib_font(font_family):
    """设置matplotlib字体"""
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = [font_family] + mpl.rcParams['font.sans-serif']
    mpl.rcParams['axes.unicode_minus'] = False  # 修复负号显示
    
    # 设置全局字体属性
    global FONT_FAMILY, FONT_PROPERTIES
    FONT_FAMILY = font_family
    FONT_PROPERTIES = fm.FontProperties(family=font_family)
    
    logger.info(f"已设置matplotlib字体: {font_family}")

def override_matplotlib_text_functions():
    """覆盖matplotlib的文本函数，确保使用中文字体"""
    global FONT_PROPERTIES
    
    # 覆盖Text.__init__
    original_text_init = Text.__init__
    def new_text_init(self, x=0, y=0, text='', **kwargs):
        if 'fontproperties' not in kwargs and isinstance(text, str):
            kwargs['fontproperties'] = FONT_PROPERTIES
        return original_text_init(self, x, y, text, **kwargs)
    Text.__init__ = new_text_init
    
    # 覆盖plt.title
    original_title = plt.title
    def new_title(label, **kwargs):
        if 'fontproperties' not in kwargs:
            kwargs['fontproperties'] = FONT_PROPERTIES
        return original_title(label, **kwargs)
    plt.title = new_title
    
    # 覆盖plt.xlabel
    original_xlabel = plt.xlabel
    def new_xlabel(xlabel, **kwargs):
        if 'fontproperties' not in kwargs:
            kwargs['fontproperties'] = FONT_PROPERTIES
        return original_xlabel(xlabel, **kwargs)
    plt.xlabel = new_xlabel
    
    # 覆盖plt.ylabel
    original_ylabel = plt.ylabel
    def new_ylabel(ylabel, **kwargs):
        if 'fontproperties' not in kwargs:
            kwargs['fontproperties'] = FONT_PROPERTIES
        return original_ylabel(ylabel, **kwargs)
    plt.ylabel = new_ylabel
    
    # 覆盖plt.text
    original_text = plt.text
    def new_text(x, y, s, **kwargs):
        if 'fontproperties' not in kwargs:
            kwargs['fontproperties'] = FONT_PROPERTIES
        return original_text(x, y, s, **kwargs)
    plt.text = new_text
    
    # 覆盖plt.annotate
    original_annotate = plt.annotate
    def new_annotate(text, xy, **kwargs):
        if 'fontproperties' not in kwargs:
            kwargs['fontproperties'] = FONT_PROPERTIES
        return original_annotate(text, xy, **kwargs)
    plt.annotate = new_annotate
    
    logger.info("已覆盖matplotlib文本函数")

def try_install_font():
    """尝试安装中文字体（仅在Linux系统上）"""
    system = platform.system()
    if system != 'Linux':
        return False
    
    try:
        # 检查是否有sudo权限
        result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
        has_sudo = result.returncode == 0
        
        if has_sudo:
            logger.info("尝试安装中文字体...")
            # 安装字体包
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                           'fonts-noto-cjk', 'fonts-wqy-microhei', 'fonts-wqy-zenhei'], check=True)
            
            # 刷新字体缓存
            subprocess.run(['fc-cache', '-fv'], check=True)
            return True
    except Exception as e:
        logger.warning(f"安装字体失败: {str(e)}")
    
    return False

def create_font_fallback_chain(available_fonts):
    """创建字体回退链"""
    if not available_fonts:
        return None
    
    # 创建一个复合字体属性，按优先级使用可用字体
    props = fm.FontProperties(family=available_fonts[0])
    
    # 尝试使用fontTools创建更高级的回退链
    try:
        from fontTools.ttLib import TTFont
        
        # 为每个字体分配支持的字符范围
        font_coverage = {}
        for font in available_fonts:
            font_path = find_font_file(font)
            if font_path:
                try:
                    ttfont = TTFont(font_path)
                    # 简单统计字体支持的字符数量
                    char_count = 0
                    for table in ttfont['cmap'].tables:
                        if table.isUnicode():
                            char_count = len(table.cmap)
                    font_coverage[font] = char_count
                except Exception as e:
                    logger.warning(f"分析字体 {font} 失败: {str(e)}")
                    font_coverage[font] = 0
        
        # 按字符覆盖范围排序
        sorted_fonts = sorted(font_coverage.items(), key=lambda x: x[1], reverse=True)
        if sorted_fonts:
            best_font = sorted_fonts[0][0]
            logger.info(f"选择覆盖范围最广的字体: {best_font} (支持 {font_coverage[best_font]} 个字符)")
            props = fm.FontProperties(family=best_font)
    except Exception as e:
        logger.warning(f"创建高级字体回退链失败: {str(e)}")
    
    return props

def initialize_chinese_font():
    """初始化中文字体支持"""
    global FONT_LOADED, FONT_PROPERTIES
    
    if FONT_LOADED:
        return FONT_PROPERTIES
    
    # 设置警告过滤器，忽略字体相关警告
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
    
    # 加载字体目录
    load_font_directories()
    
    # 检测可用的中文字体
    available_fonts = detect_chinese_fonts()
    
    # 如果没有找到中文字体，尝试安装（仅限Linux）
    if not available_fonts:
        if try_install_font():
            # 重新加载字体目录
            load_font_directories()
            available_fonts = detect_chinese_fonts()
    
    # 创建字体回退链
    if available_fonts:
        FONT_PROPERTIES = create_font_fallback_chain(available_fonts)
        setup_matplotlib_font(available_fonts[0])
        print(f"使用中文字体: {available_fonts[0]}")
    else:
        # 如果没有找到中文字体，使用通用字体
        fallback_font = 'DejaVu Sans'
        FONT_PROPERTIES = fm.FontProperties(family=fallback_font)
        setup_matplotlib_font(fallback_font)
        print(f"警告: 未找到支持中文的字体，使用通用字体 {fallback_font}")
    
    # 覆盖matplotlib文本函数
    override_matplotlib_text_functions()
    
    FONT_LOADED = True
    return FONT_PROPERTIES

def apply_chinese_font_to_figure(fig):
    """应用中文字体到现有图表"""
    global FONT_PROPERTIES
    
    if not FONT_LOADED:
        initialize_chinese_font()
    
    # 应用到所有文本元素
    for ax in fig.get_axes():
        # 设置标题字体
        if ax.get_title():
            ax.set_title(ax.get_title(), fontproperties=FONT_PROPERTIES)
        
        # 设置x轴标签字体
        if ax.get_xlabel():
            ax.set_xlabel(ax.get_xlabel(), fontproperties=FONT_PROPERTIES)
        
        # 设置y轴标签字体
        if ax.get_ylabel():
            ax.set_ylabel(ax.get_ylabel(), fontproperties=FONT_PROPERTIES)
        
        # 设置x轴刻度标签字体
        for label in ax.get_xticklabels():
            label.set_fontproperties(FONT_PROPERTIES)
        
        # 设置y轴刻度标签字体
        for label in ax.get_yticklabels():
            label.set_fontproperties(FONT_PROPERTIES)
        
        # 设置图例字体
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                text.set_fontproperties(FONT_PROPERTIES)
        
        # 设置文本注释字体
        for artist in ax.get_children():
            if isinstance(artist, Text):
                artist.set_fontproperties(FONT_PROPERTIES)
    
    return fig

def get_font_properties():
    """获取当前字体属性"""
    global FONT_PROPERTIES
    
    if not FONT_LOADED:
        initialize_chinese_font()
    
    return FONT_PROPERTIES

# 初始化时自动加载字体
initialize_chinese_font()
