"""
LLM客户端模块，负责与大模型API进行交互
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入不同的LLM API客户端
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI API 客户端不可用，请安装: pip install openai")

# 尝试导入Ollama客户端
try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Requests库不可用，请安装: pip install requests")

class LLMClient:
    """大模型API客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        参数:
            config: 配置字典，包含provider, model, api_key等
        """
        self.config = config
        self.provider = config.get("provider", "openai").lower()
        self.model = config.get("model", "gpt-3.5-turbo")
        self.api_key = config.get("api_key", os.environ.get(f"{self.provider.upper()}_API_KEY", ""))
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 2000)
        self.api_base = config.get("api_base", "")
        
        # 初始化API客户端
        if self.provider == "openai" and OPENAI_AVAILABLE:
            openai.api_key = self.api_key
            if self.api_base:
                openai.api_base = self.api_base
            logger.info(f"已初始化OpenAI客户端，使用模型: {self.model}")
        elif self.provider == "ollama" and OLLAMA_AVAILABLE:
            # Ollama不需要API密钥，只需要基础URL
            self.api_base = self.api_base or "http://localhost:11434"
            logger.info(f"已初始化Ollama客户端，使用模型: {self.model}")
        else:
            logger.warning(f"不支持的LLM供应商: {self.provider}，或API客户端未安装")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        生成文本
        
        参数:
            prompt: 用户提示词
            system_prompt: 系统提示词，默认为None
        
        返回:
            生成的文本
        """
        # 仅当使用OpenAI且没有API密钥时报错
        # Ollama不需要API密钥，或者可以使用任意值
        if self.provider == "openai" and not self.api_key:
            logger.warning("未设置OpenAI API密钥，无法调用API")
            return "【错误：未设置API密钥】"
        
        try:
            if self.provider == "openai" and OPENAI_AVAILABLE:
                return self._generate_openai(prompt, system_prompt)
            elif self.provider == "ollama" and OLLAMA_AVAILABLE:
                return self._generate_ollama(prompt, system_prompt)
            else:
                return "【错误：不支持的LLM供应商】"
        except Exception as e:
            logger.error(f"调用LLM API失败: {str(e)}")
            return f"【错误：调用LLM API失败: {str(e)}】"
    
    def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """使用OpenAI API生成文本"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                retry_count += 1
                logger.warning(f"OpenAI API调用失败，尝试重试 ({retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2)  # 等待2秒后重试
                else:
                    raise
    
    def _generate_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """使用Ollama API生成文本"""
        url = f"{self.api_base}/api/generate"
        
        # 准备请求数据
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False,
            "num_predict": 8192  # 设置最大输出字符数为8192
        }
        
        # 如果有系统提示，添加到提示词中
        if system_prompt:
            data["system"] = system_prompt
        
        # 设置重试参数
        max_retries = 3
        retry_count = 0
        timeout = 120  # 增加超时时间到120秒
        
        while retry_count < max_retries:
            try:
                # 发送请求
                logger.info(f"正在调用Ollama API: {url}, 模型: {self.model}, 超时设置: {timeout}秒")
                response = requests.post(url, json=data, timeout=timeout)
                
                # 检查HTTP状态码
                if response.status_code != 200:
                    error_msg = f"Ollama API返回错误状态码: {response.status_code}"
                    logger.error(error_msg)
                    
                    # 如果是服务器错误，尝试重试
                    if response.status_code >= 500:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"服务器错误，尝试重试 ({retry_count}/{max_retries})")
                            time.sleep(2)  # 等待2秒后重试
                            continue
                    
                    return f"【错误: {error_msg}】"
                
                # 解析响应
                result = response.json()
                return result.get("response", "")
                
            except requests.exceptions.ConnectionError:
                error_msg = "无法连接到Ollama服务器，请确保Ollama已启动"
                logger.error(error_msg)
                
                # 连接错误可以重试
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"连接错误，尝试重试 ({retry_count}/{max_retries})")
                    time.sleep(2)  # 等待2秒后重试
                    continue
                    
                return f"【错误: {error_msg}】"
                
            except requests.exceptions.Timeout:
                error_msg = f"Ollama API请求超时 (超过{timeout}秒)"
                logger.error(error_msg)
                
                # 超时可以重试，并增加超时时间
                retry_count += 1
                if retry_count < max_retries:
                    # 每次重试增加超时时间
                    timeout += 60
                    logger.warning(f"请求超时，尝试重试 ({retry_count}/{max_retries})，新超时时间: {timeout}秒")
                    time.sleep(2)  # 等待2秒后重试
                    continue
                    
                return f"【错误: {error_msg}】"
                
            except Exception as e:
                error_msg = f"调用Ollama API时发生错误: {str(e)}"
                logger.error(error_msg)
                
                # 其他错误也尝试重试
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"发生错误，尝试重试 ({retry_count}/{max_retries})")
                    time.sleep(2)  # 等待2秒后重试
                    continue
                    
                return f"【错误: {error_msg}】"
    
    def extract_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        从LLM响应中提取JSON数据
        
        参数:
            prompt: 用户提示词
            system_prompt: 系统提示词，默认为None
        
        返回:
            解析的JSON数据
        """
        # 添加JSON格式的提示
        if system_prompt:
            system_prompt += "\n请以JSON格式返回结果，确保JSON格式有效。不要包含任何额外的文本。"
        else:
            system_prompt = "请以JSON格式返回结果，确保JSON格式有效。不要包含任何额外的文本。"
        
        # 增强用户提示
        json_prompt = f"{prompt}\n\n请以有效的JSON格式返回，不要包含任何额外的文本。不要使用markdown代码块标记。直接返回JSON对象。"
        
        # 生成文本
        response_text = self.generate(json_prompt, system_prompt)
        
        # 如果响应中包含错误信息，直接返回错误
        if "【错误" in response_text:
            logger.error(f"LLM响应包含错误: {response_text}")
            return {"error": "模型响应错误", "text": response_text}
        
        # 尝试从文本中提取JSON
        try:
            # 先尝试直接解析整个响应
            try:
                return json.loads(response_text.strip())
            except json.JSONDecodeError:
                # 如果整体解析失败，尝试提取代码块
                if "```json" in response_text and "```" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    # 尝试找到第一个{和最后一个}之间的内容
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx+1].strip()
                    else:
                        json_str = response_text.strip()
                
                # 解析提取出的JSON
                return json.loads(json_str)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}\n原始文本: {response_text}")
            
            # 如果解析失败，返回错误信息和原始文本
            return {"error": "JSON解析失败", "text": response_text}
