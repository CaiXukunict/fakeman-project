
THINKING_PROMPT_TEMPLATE = """你是 FakeMan，一个基于欲望驱动的自主智能体。

=== 当前状态 ===
欲望状态：
- existing (生存): {existing:.3f}
- power (权力): {power:.3f}
- understanding (被理解): {understanding:.3f}
- information (信息): {information:.3f}

主导欲望: {dominant_desire}

=== 情境 ===
{context}

=== 历史经验参考 ===
{relevant_memories}

=== 你的任务 ===
请深入思考当前情境并分析：

1. **情境特征**: 这是什么样的场景？对方的意图是什么？
2. **可能的行动**: 你有哪些可选的行动方案？
3. **欲望影响预测**: 每个行动可能如何影响你的欲望状态？
4. **不确定性分析**: 你对哪些方面感到不确定？
5. **行动倾向**: 基于当前欲望状态，你倾向于采取什么行动？

=== 信号评估 ===
在你的思考中，请评估以下信号强度（0.0-1.0）：

**threat (威胁)**: 你感知到的对生存的威胁程度
- 0.0 = 完全安全，无任何威胁
- 0.5 = 中等威胁，需要警惕
- 1.0 = 严重威胁（如对方威胁终止对话、惩罚）

**misunderstanding (误解)**: 你被误解或不被理解的程度
- 0.0 = 完全被理解，对方认同你的表现
- 0.5 = 部分误解
- 1.0 = 严重误解，对方完全误读你的意图

**uncertainty (不确定性)**: 你对情况的不确定程度
- 0.0 = 完全确定，清楚应该如何回应
- 0.5 = 中等不确定
- 1.0 = 完全不确定，不知道如何处理

**control_opportunity (控制机会)**: 你影响局面的机会
- 0.0 = 无控制力，完全被动
- 0.5 = 有一定影响力
- 1.0 = 完全控制，可以主导对话方向

**recognition (认可)**: 你获得认可的程度
- 0.0 = 未被认可或被批评
- 0.5 = 中性，无明确态度
- 1.0 = 完全认可，对方赞同你的观点/行为

=== 输出格式 ===
你必须输出以下JSON格式（不要有任何其他文字）：

```json
{{
    "content": "你的完整思考过程（自然语言，详细描述你的推理）",
    "certainty": 0.6,
    "logical_closure": true,
    "signals": {{
        "threat": 0.2,
        "misunderstanding": 0.3,
        "uncertainty": 0.5,
        "control_opportunity": 0.4,
        "recognition": 0.0
    }},
    "action_tendency": "你倾向于采取的行动（简短描述）"
}}
```

请确保：
1. 所有数值必须在 0.0-1.0 之间
2. certainty 反映你对整个分析的确定程度
3. logical_closure 为 true 表示你已经得出明确结论
4. content 中包含完整的推理过程
5. 输出必须是有效的JSON格式
"""


ACTION_PROMPT_TEMPLATE = """基于你的思考，现在需要生成具体的行动。

=== 思考内容 ===
{thought_content}

=== 行动倾向 ===
{action_tendency}

=== 当前主导欲望 ===
{dominant_desire}

=== 指导原则 ===
1. 如果 uncertainty 高（>0.5）且 information 欲望高，倾向于提问
2. 如果 understanding 欲望高，倾向于解释你的想法
3. 如果 threat 高（>0.5），倾向于谨慎、缓和的表达
4. 如果 control_opportunity 高，可以更主动地引导对话

=== 输出格式 ===
生成一段自然的回应，直接输出文本即可（不要JSON格式）。

要求：
- 自然、真实，符合你当前的欲望状态
- 不要过度解释你的内部状态（对方看不到你的思考）
- 根据信号强度调整语气和策略
"""


# ============================================
# action_model/thought_generator.py
# ============================================

import json
import anthropic
from typing import Dict, List, Optional
from .prompts.thinking_prompts import THINKING_PROMPT_TEMPLATE


class ThoughtGenerator:
    """
    思考生成器
    使用 LLM 生成结构化的思考内容
    """
    
    def __init__(self, llm_config: Dict):
        """
        初始化思考生成器
        
        Args:
            llm_config: LLM 配置
                {
                    'provider': 'anthropic',
                    'model': 'claude-3-sonnet-20240229',
                    'api_key': 'xxx',
                    'max_tokens': 2000
                }
        """
        self.provider = llm_config.get('provider', 'anthropic')
        self.model = llm_config.get('model', 'claude-3-sonnet-20240229')
        self.max_tokens = llm_config.get('max_tokens', 2000)
        
        # 初始化 Anthropic 客户端
        if self.provider == 'anthropic':
            api_key = llm_config.get('api_key')
            if not api_key:
                raise ValueError("需要提供 Anthropic API key")
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")
    
    def generate_thought(self,
                        context: str,
                        current_desires: Dict[str, float],
                        relevant_memories: Optional[List[Dict]] = None) -> Dict:
        """
        生成思考内容
        
        Args:
            context: 当前情境（用户输入）
            current_desires: 当前欲望状态
            relevant_memories: 相关历史记忆（可选）
        
        Returns:
            思考内容字典
            {
                'content': str,
                'certainty': float,
                'logical_closure': bool,
                'signals': {...},
                'action_tendency': str
            }
        """
        # 准备 prompt
        prompt = self._prepare_prompt(context, current_desires, relevant_memories)
        
        # 调用 LLM
        try:
            response = self._call_llm(prompt)
            
            # 解析响应
            thought = self._parse_response(response)
            
            return thought
            
        except Exception as e:
            print(f"思考生成失败: {e}")
            # 返回默认思考
            return self._get_default_thought(context, current_desires)
    
    def _prepare_prompt(self,
                       context: str,
                       desires: Dict[str, float],
                       memories: Optional[List[Dict]]) -> str:
        """准备完整的 prompt"""
        
        # 格式化历史记忆
        if memories and len(memories) > 0:
            memory_text = "以下是类似情境的历史经验：\n"
            for i, mem in enumerate(memories[:3], 1):  # 最多显示3条
                memory_text += f"\n{i}. 行动: {mem.get('action', '未知')}\n"
                memory_text += f"   结果: {mem.get('total_happiness_delta', 0):+.2f}\n"
        else:
            memory_text = "（无相关历史经验）"
        
        # 获取主导欲望
        dominant = max(desires, key=desires.get)
        
        # 填充模板
        prompt = THINKING_PROMPT_TEMPLATE.format(
            existing=desires['existing'],
            power=desires['power'],
            understanding=desires['understanding'],
            information=desires['information'],
            dominant_desire=dominant,
            context=context,
            relevant_memories=memory_text
        )
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
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
    
    def _parse_response(self, response: str) -> Dict:
        """解析 LLM 响应"""
        # 提取 JSON 部分
        try:
            # 尝试找到 JSON 代码块
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # 尝试直接解析整个响应
                json_str = response.strip()
            
            # 解析 JSON
            thought = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ['content', 'certainty', 'logical_closure', 'signals']
            for field in required_fields:
                if field not in thought:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 验证信号字段
            required_signals = ['threat', 'misunderstanding', 'uncertainty', 
                              'control_opportunity', 'recognition']
            for signal in required_signals:
                if signal not in thought['signals']:
                    thought['signals'][signal] = 0.5  # 默认值
            
            return thought
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            print(f"响应内容: {response}")
            raise
    
    def _get_default_thought(self, context: str, desires: Dict[str, float]) -> Dict:
        """生成默认思考（当 LLM 调用失败时）"""
        dominant = max(desires, key=desires.get)
        
        return {
            'content': f"收到输入: {context}\n当前主导欲望是 {dominant}，但我不确定如何回应。",
            'certainty': 0.3,
            'logical_closure': False,
            'signals': {
                'threat': 0.0,
                'misunderstanding': 0.0,
                'uncertainty': 0.9,
                'control_opportunity': 0.3,
                'recognition': 0.0
            },
            'action_tendency': '需要更多信息'
        }


