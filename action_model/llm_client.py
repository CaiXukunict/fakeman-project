"""
LLM 客户端
支持 DeepSeek, Anthropic (Claude), OpenAI (GPT)
"""

import json
from typing import Dict, List, Optional, Any
import httpx
from utils.logger import get_logger

logger = get_logger('fakeman.llm')


class LLMClient:
    """
    统一的 LLM 客户端接口
    支持多个提供商
    """
    
    def __init__(self, config):
        """
        初始化 LLM 客户端
        
        Args:
            config: Config对象或配置字典
        """
        # 兼容Config对象和字典
        if hasattr(config, 'llm'):
            # Config对象
            llm_config = config.llm
            self.provider = llm_config.provider
            self.model = llm_config.model
            self.api_key = llm_config.api_key
            self.base_url = llm_config.base_url
            self.temperature = llm_config.temperature
            self.max_tokens = llm_config.max_tokens
            self.timeout = llm_config.timeout
        else:
            # 字典
            self.provider = config.get('provider', 'deepseek')
            self.model = config.get('model', 'deepseek-chat')
            self.api_key = config.get('api_key')
            self.base_url = config.get('base_url')
            self.temperature = config.get('temperature', 0.7)
            self.max_tokens = config.get('max_tokens', 2000)
            self.timeout = config.get('timeout', 30)
        
        if not self.api_key:
            raise ValueError(f"未提供 API Key for {self.provider}")
        
        # 设置默认 base_url
        if not self.base_url:
            if self.provider == 'deepseek':
                self.base_url = 'https://api.deepseek.com'
            elif self.provider == 'openai':
                self.base_url = 'https://api.openai.com/v1'
            elif self.provider == 'anthropic':
                self.base_url = 'https://api.anthropic.com'
        
        # 初始化 HTTP 客户端
        self.http_client = httpx.Client(timeout=self.timeout)
        
        logger.info(f"LLM客户端初始化: {self.provider} / {self.model}")
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'http_client'):
            self.http_client.close()
    
    def complete(self, 
                 messages: List[Dict[str, str]],
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 **kwargs) -> Dict[str, Any]:
        """
        统一的补全接口
        
        Args:
            messages: 消息列表，格式为 [{'role': 'user'|'assistant'|'system', 'content': str}, ...]
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大token数（可选，覆盖默认值）
            **kwargs: 其他参数
        
        Returns:
            响应字典
                {
                    'content': str,  # 生成的文本
                    'usage': {...},  # token使用情况
                    'raw_response': {...}  # 原始响应
                }
        """
        if self.provider == 'deepseek':
            return self._complete_deepseek(messages, temperature, max_tokens, **kwargs)
        elif self.provider == 'anthropic':
            return self._complete_anthropic(messages, temperature, max_tokens, **kwargs)
        elif self.provider == 'openai':
            return self._complete_openai(messages, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")
    
    def _complete_deepseek(self,
                          messages: List[Dict[str, str]],
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        DeepSeek API 补全
        使用 OpenAI 兼容的接口
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature if temperature is not None else self.temperature,
            'max_tokens': max_tokens if max_tokens is not None else self.max_tokens,
            **kwargs
        }
        
        try:
            logger.debug(f"调用 DeepSeek API: {self.model}")
            response = self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'content': data['choices'][0]['message']['content'],
                'usage': data.get('usage', {}),
                'raw_response': data
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            raise
    
    def _complete_anthropic(self,
                           messages: List[Dict[str, str]],
                           temperature: Optional[float] = None,
                           max_tokens: Optional[int] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Anthropic Claude API 补全
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("请安装 anthropic 包: pip install anthropic")
        
        # 分离 system 消息
        system_msg = None
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_msg = msg['content']
            else:
                user_messages.append(msg)
        
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            logger.debug(f"调用 Claude API: {self.model}")
            
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system_msg if system_msg else anthropic.NOT_GIVEN,
                messages=user_messages,
                **kwargs
            )
            
            return {
                'content': response.content[0].text,
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Claude API 调用失败: {e}")
            raise
    
    def _complete_openai(self,
                        messages: List[Dict[str, str]],
                        temperature: Optional[float] = None,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> Dict[str, Any]:
        """
        OpenAI GPT API 补全
        """
        try:
            import openai
        except ImportError:
            raise ImportError("请安装 openai 包: pip install openai")
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            logger.debug(f"调用 OpenAI API: {self.model}")
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
                **kwargs
            )
            
            return {
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise
    
    def parse_json_response(self, content: str) -> Optional[Dict]:
        """
        从响应中解析 JSON
        
        尝试提取 ```json ... ``` 代码块中的 JSON
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取代码块
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试提取大括号内容
        brace_match = re.search(r'\{.*\}', content, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.warning("无法从响应中解析 JSON")
        return None
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None, **kwargs) -> str:
        """
        便捷方法：生成文本响应
        
        Args:
            prompt: 提示文本
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Returns:
            生成的文本
        """
        messages = [{'role': 'user', 'content': prompt}]
        response = self.complete(messages, max_tokens=max_tokens, **kwargs)
        return response.get('content', '')


if __name__ == '__main__':
    # 测试 LLM 客户端
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 测试 DeepSeek
    if os.getenv('DEEPSEEK_API_KEY'):
        print("测试 DeepSeek API...")
        client = LLMClient({
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
            'temperature': 0.7,
            'max_tokens': 100
        })
        
        response = client.complete([
            {'role': 'system', 'content': '你是一个有用的助手。'},
            {'role': 'user', 'content': '你好！'}
        ])
        
        print(f"响应: {response['content']}")
        print(f"Token使用: {response['usage']}")
    else:
        print("未设置 DEEPSEEK_API_KEY，跳过测试")

