import streamlit as st
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# 导入配置和工具
from config import LLM_CONFIG, SUPPORTED_PROVIDERS, OPENAI_MODELS, OLLAMA_MODELS
from utils.llm_client import LLMClient
from utils.config_manager import config_manager, OllamaManager

# 页面配置
st.set_page_config(
    page_title="设置 - 医学影像报告分析工具",
    page_icon="⚙️",
    layout="wide"
)

# 页面标题
st.title("⚙️ 系统设置")

# 检查API密钥是否设置
if "llm_config" in st.session_state and st.session_state.llm_config.get("provider") == "openai":
    if not st.session_state.llm_config.get("api_key"):
        st.warning("❗ 警告：OpenAI API密钥未设置，请在下方表单中设置 API 密钥后才能正常使用分析功能。")

# 初始化会话状态
# 从配置文件加载配置，如果存在的话
user_config = config_manager.get_config()
if "llm_config" in user_config and user_config["llm_config"]:
    st.session_state.llm_config = user_config["llm_config"]
else:
    st.session_state.llm_config = LLM_CONFIG.copy()

# 初始化Ollama管理器
ollama_api_base = st.session_state.llm_config.get("api_base", "http://localhost:11434") \
    if st.session_state.llm_config.get("provider") == "ollama" else "http://localhost:11434"
ollama_manager = OllamaManager(api_base=ollama_api_base)

# 创建设置表单
with st.form("settings_form"):
    st.subheader("大模型配置")
    
    # 选择模型提供商
    provider_options = {p["name"]: p["value"] for p in SUPPORTED_PROVIDERS}
    selected_provider = st.selectbox(
        "选择模型提供商",
        options=list(provider_options.keys()),
        index=list(provider_options.values()).index(st.session_state.llm_config["provider"]) if st.session_state.llm_config["provider"] in provider_options.values() else 0
    )
    
    # 根据提供商显示不同的模型列表
    provider_value = provider_options[selected_provider]
    if provider_value == "openai":
        model_list = OPENAI_MODELS
        # 显示API密钥输入
        api_key = st.text_input(
            "OpenAI API密钥",
            value=st.session_state.llm_config.get("api_key", ""),
            type="password",
            help="请输入您的OpenAI API密钥，如果为空则尝试从环境变量OPENAI_API_KEY获取"
        )
        api_base = st.text_input(
            "API基础URL（可选）",
            value=st.session_state.llm_config.get("api_base", ""),
            help="如果使用OpenAI API代理，请输入基础URL，否则留空"
        )
    elif provider_value == "ollama":
        # 自动设置Ollama的API密钥为"nokey"
        api_key = "nokey"
        
        # 设置Ollama API地址
        api_base = st.text_input(
            "Ollama API地址",
            value=st.session_state.llm_config.get("api_base", "http://localhost:11434"),
            help="Ollama服务器地址，默认为http://localhost:11434"
        )
        
        # 检查Ollama服务器是否运行
        ollama_manager = OllamaManager(api_base=api_base)
        server_running = ollama_manager.is_server_running()
        
        if server_running:
            st.success("✅ Ollama服务器连接成功")
            
            # 获取可用模型列表
            with st.spinner("获取Ollama可用模型..."):
                available_models = ollama_manager.get_available_models()
                if available_models:
                    model_list = available_models
                    st.info(f"发现 {len(model_list)} 个Ollama模型")
                else:
                    model_list = OLLAMA_MODELS
                    st.warning("未找到已安装的Ollama模型，使用默认列表")
        else:
            st.error("❌ Ollama服务器连接失败，请确保Ollama服务器正在运行")
            model_list = OLLAMA_MODELS
            st.info("💡 提示: 如果未安装Ollama，请运行 `curl -fsSL https://ollama.com/install.sh | sh`")
    else:
        model_list = []
        api_key = ""
        api_base = ""
    
    # 选择模型
    default_model_index = 0
    current_model = st.session_state.llm_config["model"]
    if current_model in model_list:
        default_model_index = model_list.index(current_model)
    
    selected_model = st.selectbox(
        "选择模型",
        options=model_list,
        index=default_model_index,
        help="选择要使用的大模型"
    )
    
    # 高级参数
    with st.expander("高级参数"):
        temperature = st.slider(
            "温度参数",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.llm_config.get("temperature", 0.2),
            step=0.1,
            help="控制输出的随机性，值越高输出越多样化，值越低输出越确定性"
        )
        
        max_tokens = st.number_input(
            "最大输出标记数",
            min_value=100,
            max_value=8000,
            value=st.session_state.llm_config.get("max_tokens", 2000),
            step=100,
            help="控制模型最大输出的标记数量"
        )
    
    # 测试连接按钮和保存按钮
    col1, col2 = st.columns(2)
    with col1:
        test_connection = st.form_submit_button("测试连接")
    with col2:
        save_settings = st.form_submit_button("保存设置")

# 处理表单提交
if test_connection:
    # 创建临时配置
    temp_config = {
        "provider": provider_value,
        "model": selected_model,
        "api_key": api_key,
        "api_base": api_base,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # 测试连接
    with st.spinner("正在测试连接..."):
        try:
            client = LLMClient(temp_config)
            response = client.generate("请简短回复：你是什么模型？", "你是一个医学影像报告分析助手")
            if "错误" in response:
                st.error(f"连接测试失败: {response}")
            else:
                st.success(f"连接测试成功！模型响应: {response}")
        except Exception as e:
            st.error(f"连接测试失败: {str(e)}")

if save_settings:
    # 保存配置到会话状态
    new_config = {
        "provider": provider_value,
        "model": selected_model,
        "api_key": api_key,
        "api_base": api_base,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # 保存配置到配置文件
    if config_manager.update_config("llm_config", new_config):
        st.success("设置已保存到配置文件！")
        
        # 更新会话状态中的配置
        st.session_state.llm_config = new_config
        
        # 重新初始化LLM客户端
        with st.spinner("正在重新初始化LLM客户端..."):
            try:
                from utils.llm_client import LLMClient
                st.session_state.llm_client = LLMClient(new_config)
                st.success(f"✅ LLM客户端已更新：{new_config['provider']} - {new_config['model']}")
            except Exception as e:
                st.error(f"重新初始化LLM客户端失败: {str(e)}")
    else:
        st.warning("设置已保存到会话状态，但保存到配置文件失败")

# 显示当前配置
st.subheader("当前配置")
current_config = st.session_state.llm_config.copy()
# 不显示API密钥
if "api_key" in current_config and current_config["api_key"]:
    current_config["api_key"] = "******"

st.json(current_config)

# 添加说明
st.markdown("""
## 使用说明

### OpenAI
- 需要提供API密钥
- 支持标准OpenAI模型和兼容OpenAI API的服务

### Ollama
- 本地运行的开源大模型
- 默认地址为 http://localhost:11434
- 需要先在本地安装并运行Ollama服务
- 安装命令: `curl -fsSL https://ollama.com/install.sh | sh`
- 拉取模型命令: `ollama pull qwen2.5:14b`

### 配置保存
- 您的设置已自动保存到配置文件中
- 下次启动应用时会自动加载您的配置
- 如选择Ollama，将自动获取可用模型列表
- API密钥会保存在配置文件中，请确保系统安全
""")
