"""
FakeMan Prompts 模块
包含所有 LLM 提示词模板
"""

from .thinking_prompts import THINKING_PROMPT, THINKING_SYSTEM_PROMPT
from .action_prompts import ACTION_PROMPT, ACTION_SYSTEM_PROMPT

__all__ = [
    'THINKING_PROMPT',
    'THINKING_SYSTEM_PROMPT',
    'ACTION_PROMPT',
    'ACTION_SYSTEM_PROMPT'
]

