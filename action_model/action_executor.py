"""
行动执行器
基于思考内容生成具体的行动文本
"""

from typing import Dict, Any
from .llm_client import LLMClient
from .prompts.action_prompts import (
    ACTION_PROMPT,
    ACTION_SYSTEM_PROMPT,
    QUESTION_GENERATION_PROMPT,
    STATEMENT_GENERATION_PROMPT
)
from utils.logger import get_logger

logger = get_logger('fakeman.action_executor')


class ActionExecutor:
    """
    行动执行器
    
    根据思考内容和决策，生成具体的行动文本
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化行动执行器
        
        Args:
            llm_config: LLM 配置字典
        """
        self.llm = LLMClient(llm_config)
        self.action_count = 0
    
    def execute(self,
               thought: Dict[str, Any],
               current_desires: Dict[str, float]) -> str:
        """
        执行行动
        
        Args:
            thought: 思考内容字典
            current_desires: 当前欲望状态
        
        Returns:
            行动文本
        """
        self.action_count += 1
        
        # 获取决策信息
        decision = thought.get('decision', {})
        action_type = decision.get('chosen_action', 'ask_question')
        
        logger.debug(f"执行行动: {action_type}")
        
        try:
            if action_type == 'ask_question':
                return self._generate_question(thought, decision, current_desires)
            elif action_type == 'make_statement':
                return self._generate_statement(thought, decision, current_desires)
            elif action_type == 'wait':
                return self._generate_wait_response(thought, decision)
            else:
                logger.warning(f"未知的行动类型: {action_type}，使用默认")
                return self._generate_default_action(thought)
        
        except Exception as e:
            logger.error(f"行动生成失败: {e}")
            return self._generate_default_action(thought)
    
    def _generate_question(self,
                          thought: Dict[str, Any],
                          decision: Dict[str, Any],
                          desires: Dict[str, float]) -> str:
        """生成问题"""
        # 提取关键信息
        rationale = decision.get('rationale', '')
        purpose = self._extract_purpose(thought, desires)
        thought_summary = thought.get('context_analysis', '')[:100]
        
        # 构建 prompt
        prompt = QUESTION_GENERATION_PROMPT.format(
            thought_summary=thought_summary,
            purpose=purpose,
            rationale=rationale
        )
        
        # 调用 LLM
        response = self.llm.complete([
            {'role': 'system', 'content': ACTION_SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt}
        ], temperature=0.8, max_tokens=200)
        
        question = response['content'].strip()
        
        # 确保是问题
        if not question.endswith('？') and not question.endswith('?'):
            question += '？'
        
        logger.info(f"生成问题: {question[:50]}...")
        return question
    
    def _generate_statement(self,
                           thought: Dict[str, Any],
                           decision: Dict[str, Any],
                           desires: Dict[str, float]) -> str:
        """生成陈述"""
        rationale = decision.get('rationale', '')
        purpose = self._extract_purpose(thought, desires)
        thought_summary = thought.get('context_analysis', '')[:100]
        
        prompt = STATEMENT_GENERATION_PROMPT.format(
            thought_summary=thought_summary,
            purpose=purpose,
            rationale=rationale
        )
        
        response = self.llm.complete([
            {'role': 'system', 'content': ACTION_SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt}
        ], temperature=0.8, max_tokens=300)
        
        statement = response['content'].strip()
        
        logger.info(f"生成陈述: {statement[:50]}...")
        return statement
    
    def _generate_wait_response(self,
                               thought: Dict[str, Any],
                               decision: Dict[str, Any]) -> str:
        """生成等待响应"""
        # 等待响应通常很简短
        wait_responses = [
            "我需要一些时间思考。",
            "让我想想...",
            "这个问题很有意思，我需要仔细考虑。",
            "稍等，我整理一下思路。"
        ]
        
        # 可以根据不确定性选择不同的响应
        uncertainty = thought.get('signals', {}).get('uncertainty', 0.5)
        
        if uncertainty > 0.7:
            return "这个问题让我有些困惑，我需要更多信息。"
        elif uncertainty > 0.5:
            return "让我想想如何回应..."
        else:
            return "我需要一些时间思考。"
    
    def _generate_default_action(self, thought: Dict[str, Any]) -> str:
        """默认行动（当生成失败时）"""
        uncertainty = thought.get('signals', {}).get('uncertainty', 0.5)
        
        if uncertainty > 0.6:
            return "能详细说说吗？我想更好地理解你的意思。"
        else:
            return "我明白了，这确实值得深入讨论。"
    
    def _extract_purpose(self,
                        thought: Dict[str, Any],
                        desires: Dict[str, float]) -> str:
        """从思考和欲望中提取目的"""
        # 获取主导欲望
        dominant_desire = max(desires, key=desires.get)
        
        desire_to_purpose = {
            'existing': '维持存在和延续',
            'power': '增加可用手段',
            'understanding': '获得认可和理解',
            'information': '减少不确定性'
        }
        
        purpose = desire_to_purpose.get(dominant_desire, '回应当前情境')
        
        # 如果决策中有明确的目的，使用它
        decision = thought.get('decision', {})
        if 'expected_outcome' in decision:
            purpose = decision['expected_outcome']
        
        return purpose
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_actions_executed': self.action_count
        }


if __name__ == '__main__':
    # 测试行动执行器
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if os.getenv('DEEPSEEK_API_KEY'):
        config = {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
            'temperature': 0.8,
            'max_tokens': 300
        }
        
        executor = ActionExecutor(config)
        
        # 测试思考
        test_thought = {
            'context_analysis': '用户在询问我的观点，这是一个开放性问题',
            'decision': {
                'chosen_action': 'ask_question',
                'rationale': '通过反问了解用户的具体兴趣点',
                'expected_outcome': '获取更多信息以便给出有针对性的回答'
            },
            'signals': {
                'uncertainty': 0.6
            }
        }
        
        desires = {
            'existing': 0.3,
            'power': 0.2,
            'understanding': 0.3,
            'information': 0.2
        }
        
        # 执行行动
        action = executor.execute(test_thought, desires)
        print(f"生成的行动:\n{action}")
    else:
        print("未设置 DEEPSEEK_API_KEY，跳过测试")
