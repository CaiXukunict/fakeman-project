"""
逻辑闭环判定
判断思考是否达到逻辑闭环（充分考虑了各方面因素）
"""

import re
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger('fakeman.logical_closure')


def check_logical_closure(thought: Dict[str, Any]) -> bool:
    """
    检查思考是否达到逻辑闭环
    
    Args:
        thought: 思考内容字典
    
    Returns:
        是否达到逻辑闭环
    """
    # 1. LLM 自己的判断（如果有）
    if 'logical_closure' in thought:
        llm_judgment = thought['logical_closure']
        if isinstance(llm_judgment, bool):
            return llm_judgment
    
    # 2. 基于模式匹配的判断
    return check_logical_closure_pattern(thought)


def check_logical_closure_pattern(thought: Dict[str, Any]) -> bool:
    """
    基于模式匹配判断逻辑闭环
    
    检查思考是否包含：
    1. 问题识别
    2. 多方考虑
    3. 明确结论
    
    Args:
        thought: 思考内容字典
    
    Returns:
        是否达到逻辑闭环
    """
    content = thought.get('content', '')
    
    # 关键要素
    has_analysis = False  # 是否有分析
    has_options = False   # 是否考虑了多个选项
    has_decision = False  # 是否有明确决策
    
    # 1. 检查是否有分析性语言
    analysis_patterns = [
        r'(分析|考虑|思考|评估|判断)',
        r'(因为|由于|所以|因此)',
        r'(可能|也许|或者|另一方面)'
    ]
    
    for pattern in analysis_patterns:
        if re.search(pattern, content):
            has_analysis = True
            break
    
    # 2. 检查是否有多个选项的考虑
    if 'action_options' in thought and len(thought['action_options']) > 1:
        has_options = True
    
    # 检查文本中是否提到多个选项
    options_patterns = [
        r'(选项|方案|可以|或者)',
        r'(一方面.*另一方面)',
        r'(第一|第二|其次)'
    ]
    
    if not has_options:
        for pattern in options_patterns:
            if re.search(pattern, content):
                has_options = True
                break
    
    # 3. 检查是否有明确决策
    if 'decision' in thought and thought['decision'].get('chosen_action'):
        has_decision = True
    
    decision_patterns = [
        r'(决定|选择|倾向于|最终)',
        r'(因此.*应该|所以.*要)',
    ]
    
    if not has_decision:
        for pattern in decision_patterns:
            if re.search(pattern, content):
                has_decision = True
                break
    
    # 4. 检查确定性
    certainty = thought.get('certainty', 0.5)
    is_certain_enough = certainty > 0.6
    
    # 综合判断
    # 需要满足：有分析 + 有决策 + 确定性足够
    # 或者：有分析 + 考虑了多个选项 + 有决策
    closure = (has_analysis and has_decision and is_certain_enough) or \
              (has_analysis and has_options and has_decision)
    
    logger.debug(f"逻辑闭环判定: 分析={has_analysis}, 选项={has_options}, "
                f"决策={has_decision}, 确定性={certainty:.2f} -> 闭环={closure}")
    
    return closure


def check_logical_closure_llm(thought_content: str, llm_client) -> Dict[str, Any]:
    """
    使用 LLM 判定逻辑闭环（可选，更准确但更慢）
    
    Args:
        thought_content: 思考内容文本
        llm_client: LLM 客户端
    
    Returns:
        判定结果
            {
                'closure': bool,
                'reason': str
            }
    """
    prompt = f"""
请判断以下思考内容是否达到了逻辑闭环。

逻辑闭环的标准：
1. 识别了问题/情境的关键特征
2. 考虑了多种可能性或选项
3. 进行了利弊分析
4. 得出了明确的结论或行动倾向

思考内容：
{thought_content}

请以JSON格式输出：
{{
    "closure": true/false,
    "reason": "判断理由"
}}
"""
    
    try:
        response = llm_client.complete([
            {'role': 'user', 'content': prompt}
        ], temperature=0.3, max_tokens=200)
        
        result = llm_client.parse_json_response(response['content'])
        
        if result and 'closure' in result:
            return result
        else:
            logger.warning("LLM 逻辑闭环判定失败，使用默认值")
            return {'closure': False, 'reason': '无法解析LLM响应'}
    
    except Exception as e:
        logger.error(f"LLM 逻辑闭环判定出错: {e}")
        return {'closure': False, 'reason': f'出错: {e}'}


def calculate_thought_depth(thought: Dict[str, Any]) -> float:
    """
    计算思考深度
    
    基于多个因素：
    - 内容长度
    - 选项数量
    - 不确定性识别
    - 信号评估的完整性
    
    Args:
        thought: 思考内容字典
    
    Returns:
        思考深度分数 (0-1)
    """
    score = 0.0
    
    # 1. 内容长度（最多0.3分）
    content_length = len(thought.get('content', ''))
    if content_length > 500:
        score += 0.3
    elif content_length > 200:
        score += 0.2
    elif content_length > 100:
        score += 0.1
    
    # 2. 考虑的选项数量（最多0.3分）
    options_count = len(thought.get('action_options', []))
    if options_count >= 3:
        score += 0.3
    elif options_count == 2:
        score += 0.2
    elif options_count == 1:
        score += 0.1
    
    # 3. 不确定性识别（最多0.2分）
    uncertainties = thought.get('uncertainties', [])
    if len(uncertainties) > 0:
        score += 0.2
    
    # 4. 信号评估（最多0.2分）
    signals = thought.get('signals', {})
    if len(signals) >= 4:  # 至少4个信号被评估
        score += 0.2
    elif len(signals) >= 2:
        score += 0.1
    
    return min(1.0, score)


if __name__ == '__main__':
    # 测试逻辑闭环判定
    
    # 测试1：完整的思考
    thought1 = {
        'content': '分析当前情境，我有两个选项：一是直接回答，二是询问更多信息。'
                  '考虑到不确定性较高，我决定先询问。',
        'action_options': [
            {'option': '直接回答', 'expected_desire_impact': {}},
            {'option': '询问信息', 'expected_desire_impact': {}}
        ],
        'decision': {'chosen_action': 'ask_question'},
        'certainty': 0.7,
        'signals': {'uncertainty': 0.6}
    }
    
    result1 = check_logical_closure(thought1)
    depth1 = calculate_thought_depth(thought1)
    print(f"测试1 - 逻辑闭环: {result1}, 思考深度: {depth1:.2f}")
    
    # 测试2：不完整的思考
    thought2 = {
        'content': '嗯，不太确定。',
        'certainty': 0.3
    }
    
    result2 = check_logical_closure(thought2)
    depth2 = calculate_thought_depth(thought2)
    print(f"测试2 - 逻辑闭环: {result2}, 思考深度: {depth2:.2f}")

