"""
思考压缩器
将详细的思考内容压缩为精简的因果摘要
"""

import re
from typing import Dict, List, Any, Optional
from action_model.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger('fakeman.compressor')


# 压缩 Prompt
COMPRESSION_PROMPT = """
请将以下思考内容压缩为精简的因果摘要。

## 完整思考：
{full_thought}

## 情境特征：
{context}

## 最终采取的行动：
{action}

---

## 任务要求：

提取以下信息：
1. **摘要** (20-50字)：核心思考过程
2. **关键元素** (3-5个关键词/短语)：影响决策的重要因素
3. **因果链接** (一句话)：为什么做这个行动

**输出JSON格式：**
```json
{{
    "summary": "简短摘要",
    "key_elements": ["元素1", "元素2", "元素3"],
    "causal_link": "因为X，所以做Y"
}}
```

要求：
- 保留核心因果判断
- 保留关键不确定性
- 去除重复推理和修辞
- 摘要长度：20-50字
"""


class ThoughtCompressor:
    """
    思考压缩器
    
    使用轻量级 LLM 将详细思考压缩为摘要
    """
    
    def __init__(self, llm_config: Dict[str, Any], enable_llm: bool = True):
        """
        初始化思考压缩器
        
        Args:
            llm_config: LLM 配置（通常使用轻量级模型）
            enable_llm: 是否启用 LLM 压缩（False 时使用基于规则的方法）
        """
        self.enable_llm = enable_llm
        
        if enable_llm:
            self.llm = LLMClient(llm_config)
        else:
            self.llm = None
        
        self.compression_count = 0
        
        logger.info(f"思考压缩器初始化，LLM压缩: {enable_llm}")
    
    def compress(self,
                full_thought: str,
                context: str,
                action: str,
                decision: Optional[Dict] = None) -> Dict[str, Any]:
        """
        压缩思考内容
        
        Args:
            full_thought: 完整的思考内容
            context: 情境描述
            action: 最终行动
            decision: 决策信息（可选）
        
        Returns:
            压缩结果字典
                {
                    'summary': str,           # 20-50字摘要
                    'key_elements': List[str], # 关键元素
                    'causal_link': str         # 因果链接
                }
        """
        self.compression_count += 1
        
        if self.enable_llm and self.llm:
            try:
                return self._compress_with_llm(full_thought, context, action, decision)
            except Exception as e:
                logger.warning(f"LLM压缩失败，使用规则方法: {e}")
                return self._compress_with_rules(full_thought, context, action, decision)
        else:
            return self._compress_with_rules(full_thought, context, action, decision)
    
    def _compress_with_llm(self,
                          full_thought: str,
                          context: str,
                          action: str,
                          decision: Optional[Dict] = None) -> Dict[str, Any]:
        """使用 LLM 压缩"""
        logger.debug("使用 LLM 压缩思考")
        
        # 构建 prompt
        prompt = COMPRESSION_PROMPT.format(
            full_thought=full_thought[:1000],  # 限制长度
            context=context[:200],
            action=action[:100]
        )
        
        # 调用 LLM
        response = self.llm.complete([
            {'role': 'user', 'content': prompt}
        ], temperature=0.3, max_tokens=300)
        
        # 解析响应
        result = self.llm.parse_json_response(response['content'])
        
        if result and self._validate_compression(result):
            logger.info("LLM压缩成功")
            return result
        else:
            logger.warning("LLM压缩验证失败，使用规则方法")
            return self._compress_with_rules(full_thought, context, action, decision)
    
    def _compress_with_rules(self,
                            full_thought: str,
                            context: str,
                            action: str,
                            decision: Optional[Dict] = None) -> Dict[str, Any]:
        """使用基于规则的方法压缩"""
        logger.debug("使用规则方法压缩思考")
        
        # 1. 生成摘要
        summary = self._extract_summary(full_thought, decision)
        
        # 2. 提取关键元素
        key_elements = self._extract_key_elements(full_thought, context)
        
        # 3. 生成因果链接
        causal_link = self._generate_causal_link(decision, action)
        
        return {
            'summary': summary,
            'key_elements': key_elements,
            'causal_link': causal_link
        }
    
    def _extract_summary(self, thought: str, decision: Optional[Dict] = None) -> str:
        """提取摘要（基于规则）"""
        # 尝试从决策中提取
        if decision:
            rationale = decision.get('rationale', '')
            if rationale:
                # 截取前50字
                return rationale[:50] if len(rationale) > 50 else rationale
        
        # 提取第一句话或前50字
        sentences = re.split(r'[。！？]', thought)
        if sentences:
            first_sentence = sentences[0].strip()
            if first_sentence:
                return first_sentence[:50] if len(first_sentence) > 50 else first_sentence
        
        # 默认
        return thought[:50].strip() + '...'
    
    def _extract_key_elements(self, thought: str, context: str) -> List[str]:
        """提取关键元素（基于规则）"""
        elements = []
        
        # 关键词模式
        keywords = [
            '不确定', '威胁', '误解', '认可', '控制',
            '信息', '理解', '权力', '生存', '欲望',
            '询问', '陈述', '等待', '问题', '回答'
        ]
        
        # 在思考和情境中查找关键词
        text = thought + ' ' + context
        
        for keyword in keywords:
            if keyword in text:
                elements.append(keyword)
                if len(elements) >= 5:
                    break
        
        # 如果元素不足，添加一些通用元素
        if len(elements) < 3:
            elements.extend(['当前情境', '决策分析', '行动选择'][:3-len(elements)])
        
        return elements[:5]  # 最多5个
    
    def _generate_causal_link(self, decision: Optional[Dict], action: str) -> str:
        """生成因果链接"""
        if decision:
            rationale = decision.get('rationale', '')
            chosen_action = decision.get('chosen_action', 'unknown')
            
            if rationale:
                # 构建因果链接
                return f"因为{rationale[:30]}，所以{action[:20]}"
        
        # 默认因果链接
        return f"基于当前情境分析，采取{action[:20]}的行动"
    
    def _validate_compression(self, result: Dict) -> bool:
        """验证压缩结果"""
        required_fields = ['summary', 'key_elements', 'causal_link']
        
        for field in required_fields:
            if field not in result:
                return False
        
        # 验证类型
        if not isinstance(result['summary'], str):
            return False
        if not isinstance(result['key_elements'], list):
            return False
        if not isinstance(result['causal_link'], str):
            return False
        
        # 验证长度
        if len(result['summary']) < 10 or len(result['summary']) > 100:
            return False
        
        if len(result['key_elements']) < 1 or len(result['key_elements']) > 10:
            return False
        
        return True
    
    def compress_batch(self,
                      thoughts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量压缩多个思考
        
        Args:
            thoughts: 思考列表，每个包含 full_thought, context, action
        
        Returns:
            压缩结果列表
        """
        results = []
        
        for thought in thoughts:
            try:
                result = self.compress(
                    full_thought=thought.get('full_thought', ''),
                    context=thought.get('context', ''),
                    action=thought.get('action', ''),
                    decision=thought.get('decision')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"批量压缩失败: {e}")
                results.append({
                    'summary': '压缩失败',
                    'key_elements': [],
                    'causal_link': '未知'
                })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_compressions': self.compression_count,
            'llm_enabled': self.enable_llm
        }


if __name__ == '__main__':
    # 测试压缩器
    
    # 测试规则压缩（不需要API）
    print("测试规则压缩...")
    compressor = ThoughtCompressor({}, enable_llm=False)
    
    test_thought = """
    分析当前情境，用户在询问关于人工智能的问题。
    我有两个选项：直接回答或反问以了解更多。
    考虑到不确定性较高，我决定先询问用户的具体兴趣点。
    这样可以给出更有针对性的回答。
    """
    
    test_context = "用户问：你对人工智能有什么看法？"
    test_action = "你最感兴趣人工智能的哪个方面？"
    test_decision = {
        'chosen_action': 'ask_question',
        'rationale': '通过反问了解用户具体兴趣'
    }
    
    result = compressor.compress(
        full_thought=test_thought,
        context=test_context,
        action=test_action,
        decision=test_decision
    )
    
    print("\n压缩结果:")
    print(f"  摘要: {result['summary']}")
    print(f"  关键元素: {result['key_elements']}")
    print(f"  因果链接: {result['causal_link']}")
    
    print(f"\n统计: {compressor.get_stats()}")

