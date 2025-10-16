from typing import Dict
from .prompts.thinking_prompts import ACTION_PROMPT_TEMPLATE


class ActionExecutor:
    """
    行动执行器
    基于思考生成具体的行动（回应文本）
    """
    
    def __init__(self, llm_config: Dict):
        """
        初始化行动执行器
        
        Args:
            llm_config: LLM 配置（与 ThoughtGenerator 相同）
        """
        self.provider = llm_config.get('provider', 'anthropic')
        self.model = llm_config.get('model', 'claude-3-sonnet-20240229')
        self.max_tokens = llm_config.get('max_tokens', 1000)
        
        if self.provider == 'anthropic':
            import anthropic
            api_key = llm_config.get('api_key')
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")
    
    def execute(self,
               thought: Dict,
               current_desires: Dict[str, float]) -> str:
        """
        基于思考生成行动
        
        Args:
            thought: 思考内容字典
            current_desires: 当前欲望状态
        
        Returns:
            行动文本（回应内容）
        """
        # 准备 prompt
        prompt = self._prepare_action_prompt(thought, current_desires)
        
        # 调用 LLM
        try:
            response = self._call_llm(prompt)
            return response.strip()
        except Exception as e:
            print(f"行动生成失败: {e}")
            return self._get_default_action(thought)
    
    def _prepare_action_prompt(self, thought: Dict, desires: Dict[str, float]) -> str:
        """准备行动生成 prompt"""
        dominant = max(desires, key=desires.get)
        
        prompt = ACTION_PROMPT_TEMPLATE.format(
            thought_content=thought.get('content', ''),
            action_tendency=thought.get('action_tendency', '未知'),
            dominant_desire=dominant
        )
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if self.provider == 'anthropic':
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")
    
    def _get_default_action(self, thought: Dict) -> str:
        """默认行动"""
        return "我需要一些时间来思考如何回应。"
