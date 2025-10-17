"""
思考生成器
使用 LLM 生成结构化的思考内容，支持DeepSeek, Anthropic, OpenAI
"""

from typing import Dict, List, Optional, Any
import json
from .llm_client import LLMClient
from .prompts.thinking_prompts import THINKING_PROMPT, THINKING_SYSTEM_PROMPT
from utils.logger import get_logger

logger = get_logger('fakeman.thought_generator')


class ThoughtGenerator:
    """
    思考生成器
    
    负责调用 LLM 生成结构化的思考内容
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化思考生成器
        
        Args:
            llm_config: LLM 配置字典
        """
        self.llm = LLMClient(llm_config)
        self.thought_count = 0  # 统计调用次数
    
    def generate_thought(self,
                        context: str,
                        current_desires: Dict[str, float],
                        relevant_memories: Optional[List[Dict]] = None,
                        max_retries: int = 3) -> Dict[str, Any]:
        """
        生成思考内容
        
        Args:
            context: 当前情境（用户输入）
            current_desires: 当前欲望状态
            relevant_memories: 相关历史经验
            max_retries: 最大重试次数
        
        Returns:
            思考内容字典
                {
                    'content': str,  # 完整思考内容
                    'context_analysis': str,
                    'action_options': List[Dict],
                    'decision': Dict,
                    'signals': Dict[str, float],
                    'certainty': float,
                    'logical_closure': bool,
                    'raw_response': str
                }
        """
        self.thought_count += 1
        
        # 格式化欲望状态
        desires_str = self._format_desires(current_desires)
        
        # 格式化记忆
        memories_str = self._format_memories(relevant_memories) if relevant_memories else "（无相关历史经验）"
        
        # 构建 prompt
        prompt = THINKING_PROMPT.format(
            desires=desires_str,
            context=context,
            memories=memories_str
        )
        
        # 调用 LLM
        for attempt in range(max_retries):
            try:
                logger.debug(f"生成思考（尝试 {attempt + 1}/{max_retries}）")
                
                response = self.llm.complete([
                    {'role': 'system', 'content': THINKING_SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt}
                ])
                
                content = response['content']
                
                # 解析 JSON 响应
                thought_data = self.llm.parse_json_response(content)
                
                if thought_data:
                    # 验证必需字段
                    if self._validate_thought_data(thought_data):
                        result = {
                            'content': content,
                            'context_analysis': thought_data.get('context_analysis', ''),
                            'action_options': thought_data.get('action_options', []),
                            'decision': thought_data.get('decision', {}),
                            'signals': thought_data.get('signals', {}),
                            'certainty': thought_data.get('certainty', 0.5),
                            'logical_closure': thought_data.get('logical_closure', False),
                            'raw_response': content,
                            'usage': response.get('usage', {})
                        }
                        
                        logger.info(f"思考生成成功，决策：{result['decision'].get('chosen_action')}")
                        return result
                    else:
                        logger.warning("思考数据验证失败，重试...")
                else:
                    logger.warning("无法解析 JSON，重试...")
                
            except Exception as e:
                logger.error(f"思考生成失败（尝试 {attempt + 1}）: {e}")
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，返回默认值
                    return self._get_default_thought(context)
        
        # 所有重试失败，返回默认值
        return self._get_default_thought(context)
    
    def _format_desires(self, desires: Dict[str, float]) -> str:
        """格式化欲望状态为可读字符串"""
        lines = []
        for name, value in sorted(desires.items(), key=lambda x: x[1], reverse=True):
            percentage = value * 100
            bar = '█' * int(percentage / 5) + '░' * (20 - int(percentage / 5))
            
            name_cn = {
                'existing': '维持存在',
                'power': '增加手段',
                'understanding': '获得认可',
                'information': '减少不确定性'
            }.get(name, name)
            
            lines.append(f"  {name_cn:10s} [{bar}] {percentage:5.1f}%")
        
        return '\n'.join(lines)
    
    def _format_memories(self, memories: List[Dict]) -> str:
        """格式化历史记忆为可读字符串"""
        if not memories:
            return "（无相关历史经验）"
        
        lines = []
        for i, mem in enumerate(memories[:5], 1):  # 最多显示5条
            summary = mem.get('thought_summary', '未知')
            means = mem.get('means', '未知')
            outcome = mem.get('total_happiness_delta', 0)
            outcome_str = '✓成功' if outcome > 0 else '✗失败'
            
            lines.append(f"  {i}. {summary[:40]}...")
            lines.append(f"     手段: {means[:30]}, 结果: {outcome_str}")
        
        return '\n'.join(lines)
    
    def _validate_thought_data(self, data: Dict) -> bool:
        """验证思考数据是否包含必需字段"""
        required_fields = ['decision', 'signals', 'certainty']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"缺少必需字段: {field}")
                return False
        
        # 验证 decision
        if 'chosen_action' not in data['decision']:
            logger.warning("decision 缺少 chosen_action")
            return False
        
        # 验证 action 类型
        valid_actions = ['ask_question', 'make_statement', 'wait']
        if data['decision']['chosen_action'] not in valid_actions:
            logger.warning(f"无效的 action 类型: {data['decision']['chosen_action']}")
            return False
        
        return True
    
    def _get_default_thought(self, context: str) -> Dict[str, Any]:
        """返回默认思考内容（当生成失败时）"""
        logger.warning("使用默认思考内容")
        
        return {
            'content': f"对于情境 '{context}'，我选择询问以获取更多信息。",
            'context_analysis': "无法生成详细分析",
            'action_options': [],
            'decision': {
                'chosen_action': 'ask_question',
                'rationale': '默认策略：通过提问获取更多信息',
                'expected_outcome': '增加对情境的理解'
            },
            'signals': {
                'threat': 0.0,
                'misunderstanding': 0.0,
                'uncertainty': 0.8,
                'control_opportunity': 0.0,
                'recognition': 0.0
            },
            'certainty': 0.3,
            'logical_closure': False,
            'raw_response': '（默认响应）',
            'usage': {}
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_thoughts_generated': self.thought_count
        }
