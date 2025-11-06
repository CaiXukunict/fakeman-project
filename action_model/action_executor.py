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
        action_description = decision.get('chosen_action', '给出回应')
        
        logger.debug(f"执行行动: {action_description}")
        
        try:
            # 不再依赖固定的action类型，而是基于自然语言描述生成输出
            return self._generate_action_from_thought(thought, decision, current_desires)
        
        except Exception as e:
            logger.error(f"行动生成失败: {e}")
            return self._generate_default_action(thought)
    
    def _generate_action_from_thought(self,
                                      thought: Dict[str, Any],
                                      decision: Dict[str, Any],
                                      desires: Dict[str, float]) -> str:
        """
        基于思考内容直接生成行动（不限制类型）
        
        Args:
            thought: 思考内容
            decision: 决策信息
            desires: 当前欲望状态
        
        Returns:
            行动文本
        """
        # 提取关键信息
        action_desc = decision.get('chosen_action', '回应')
        rationale = decision.get('rationale', '')
        context_analysis = thought.get('context_analysis', '')
        
        # 格式化欲望状态
        desires_str = ', '.join([f"{k}={v:.2f}" for k, v in desires.items()])
        
        # 构建提示词 - 不限制行动类型
        prompt = f"""## 思考过程

情境分析: {context_analysis[:200]}

决策: {action_desc}
理由: {rationale}

当前欲望状态: {desires_str}

## 任务

根据上述思考和决策，生成具体的行动输出。

要求：
1. 直接基于你的决策"{action_desc}"来生成输出
2. 输出应该自然、真实，体现你的思考过程
3. 不要局限于特定形式，做你认为最合适的事
4. 保持输出简洁有力

请直接输出行动内容，不需要额外说明：
"""
        
        try:
            response = self.llm.complete([
                {'role': 'system', 'content': '你是一个基于欲望驱动的AI，根据你的思考内容生成自然的行动。'},
                {'role': 'user', 'content': prompt}
            ], temperature=0.8, max_tokens=300)
            
            action = response['content'].strip()
            logger.info(f"行动生成成功: {action[:50]}...")
            return action
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 回退：直接使用rationale作为输出
            return rationale if rationale else "..."
    
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
