# -*- coding: utf-8 -*-
"""
记忆作为手段
将记忆行为（选择是否记忆、如何记忆）作为一种手段
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
from utils.logger import get_logger

logger = get_logger('fakeman.memory_means')


@dataclass
class MemoryDecision:
    """
    记忆决策
    决定是否记忆以及如何记忆当前内容
    """
    should_remember: bool  # 是否应该记忆
    memory_weight: float  # 记忆权重 (0-1)
    reason: str  # 决策原因
    
    # 思考内容的权重分配
    thought_weights: Dict[str, float]  # key: 思考片段, value: 权重
    
    # 记忆策略
    compression_strategy: str  # 压缩策略（详细/简要/最简）
    priority_level: str  # 优先级（高/中/低）
    
    timestamp: float = time.time()


class MemoryAsМeans:
    """
    记忆作为手段
    
    核心概念：
    - 记忆是一种手段，与其他行动手段（问答、陈述等）不冲突
    - 大模型根据当前目的决定是否记忆
    - 大模型为思考内容分配权重
    - 权重影响后续压缩时的篇幅分配
    """
    
    def __init__(self, llm_client=None):
        """
        初始化记忆手段系统
        
        Args:
            llm_client: LLM客户端（用于决策）
        """
        self.llm_client = llm_client
        logger.info("记忆手段系统初始化完成")
    
    def decide_memory_action(self,
                            current_purpose: str,
                            current_desires: Dict[str, float],
                            thought_contents: List[str],
                            context: str,
                            action_output: str = "") -> MemoryDecision:
        """
        决定是否记忆以及如何记忆
        
        这是记忆作为"手段"的核心：
        - 根据目的判断是否需要记忆
        - 为思考内容分配权重
        - 选择记忆策略
        
        Args:
            current_purpose: 当前目的
            current_desires: 当前欲望状态
            thought_contents: 思考内容列表
            context: 当前情境
            action_output: 行动输出
        
        Returns:
            记忆决策
        """
        logger.info(f"评估记忆手段：目的='{current_purpose}'")
        
        # 如果有LLM，使用LLM决策
        if self.llm_client:
            return self._llm_based_decision(
                current_purpose,
                current_desires,
                thought_contents,
                context,
                action_output
            )
        else:
            # 使用启发式规则
            return self._heuristic_decision(
                current_purpose,
                current_desires,
                thought_contents,
                context,
                action_output
            )
    
    def _heuristic_decision(self,
                           current_purpose: str,
                           current_desires: Dict[str, float],
                           thought_contents: List[str],
                           context: str,
                           action_output: str) -> MemoryDecision:
        """
        基于启发式规则的记忆决策
        
        规则：
        1. 情绪变化大的经验 → 应该记忆
        2. 新颖的情境 → 应该记忆
        3. 与长期目标相关 → 应该记忆
        4. 重复的日常经验 → 可以不记忆或简要记忆
        
        Args:
            ...
        
        Returns:
            记忆决策
        """
        # 计算是否应该记忆
        should_remember = True  # 默认记忆
        memory_weight = 0.5  # 默认权重
        reason = "常规记忆"
        
        # 规则1：检查欲望状态
        dominant_desire = max(current_desires.items(), key=lambda x: x[1])
        
        # existing欲望高 → 更愿意记忆（保存自己的存在）
        if dominant_desire[0] == 'existing' and dominant_desire[1] > 0.6:
            memory_weight = 0.9
            reason = "为了保存存在而记忆"
            logger.info(f"记忆决策: {reason}")
        
        # 规则2：检查是否有重要的思考
        has_important_thought = any(
            len(thought) > 50 for thought in thought_contents
        )
        
        if has_important_thought:
            memory_weight = max(memory_weight, 0.7)
            reason = "包含重要思考内容"
        
        # 规则3：为思考内容分配权重
        thought_weights = {}
        for i, thought in enumerate(thought_contents):
            # 简单启发式：长度越长，权重越高
            base_weight = min(1.0, len(thought) / 100)
            
            # 如果包含关键词，增加权重
            keywords = ['重要', '关键', '核心', '必须', '目标', '欲望']
            if any(keyword in thought for keyword in keywords):
                base_weight = min(1.0, base_weight + 0.3)
            
            thought_weights[f"thought_{i}"] = base_weight
        
        # 选择压缩策略
        if memory_weight > 0.7:
            compression_strategy = "详细"
            priority_level = "高"
        elif memory_weight > 0.4:
            compression_strategy = "简要"
            priority_level = "中"
        else:
            compression_strategy = "最简"
            priority_level = "低"
        
        return MemoryDecision(
            should_remember=should_remember,
            memory_weight=memory_weight,
            reason=reason,
            thought_weights=thought_weights,
            compression_strategy=compression_strategy,
            priority_level=priority_level
        )
    
    def _llm_based_decision(self,
                           current_purpose: str,
                           current_desires: Dict[str, float],
                           thought_contents: List[str],
                           context: str,
                           action_output: str) -> MemoryDecision:
        """
        基于LLM的记忆决策（待实现）
        
        提示词模板：
        "根据当前目的和情境，决定是否需要记忆这次经历，
         并为每个思考内容分配权重（0-1）。
         
         当前目的：{purpose}
         当前情境：{context}
         思考内容：{thoughts}
         行动输出：{output}
         
         请回答：
         1. 是否应该记忆？（是/否）
         2. 记忆权重：（0-1）
         3. 原因：
         4. 每个思考内容的权重：
            - 思考1: [权重]
            - 思考2: [权重]
            ..."
        
        Args:
            ...
        
        Returns:
            记忆决策
        """
        # TODO: 实现LLM调用
        # 这里先使用启发式作为占位
        logger.info("LLM记忆决策（当前使用启发式占位）")
        return self._heuristic_decision(
            current_purpose,
            current_desires,
            thought_contents,
            context,
            action_output
        )
    
    def apply_memory_decision(self,
                             decision: MemoryDecision,
                             memory_summary: Any) -> None:
        """
        应用记忆决策到记忆摘要对象
        
        Args:
            decision: 记忆决策
            memory_summary: MemorySummary对象
        """
        if not decision.should_remember:
            logger.info("决定不记忆此次经历")
            return
        
        # 设置压缩权重
        memory_summary.compression_weight = decision.memory_weight
        
        logger.info(
            f"应用记忆决策: 权重={decision.memory_weight:.2f}, "
            f"策略={decision.compression_strategy}, "
            f"优先级={decision.priority_level}"
        )
    
    def evaluate_memory_effectiveness(self,
                                     memory_id: int,
                                     was_recalled: bool,
                                     recall_usefulness: float = 0.5) -> float:
        """
        评估记忆手段的有效性
        
        记忆也是一种手段，可以评估其效果：
        - 记忆是否被回忆起？
        - 回忆对决策是否有帮助？
        
        Args:
            memory_id: 记忆ID
            was_recalled: 是否被回忆
            recall_usefulness: 回忆的有用性 (0-1)
        
        Returns:
            记忆手段的有效性评分
        """
        if not was_recalled:
            return 0.0  # 没被回忆，无效
        
        effectiveness = recall_usefulness
        
        logger.debug(
            f"记忆 #{memory_id} 有效性评估: {effectiveness:.2f}"
        )
        
        return effectiveness
    
    def get_memory_means_prompt(self,
                               purpose: str,
                               context: str,
                               thoughts: List[str]) -> str:
        """
        获取记忆决策的LLM提示词
        
        Args:
            purpose: 当前目的
            context: 当前情境
            thoughts: 思考内容列表
        
        Returns:
            提示词
        """
        thoughts_text = "\n".join([
            f"{i+1}. {thought}"
            for i, thought in enumerate(thoughts)
        ])
        
        prompt = f"""你是一个自主AI系统，需要决定是否记忆当前经历。

**当前目的**: {purpose}

**当前情境**: {context}

**思考内容**:
{thoughts_text}

**请决定**:

1. **是否应该记忆**？（必须回答"是"或"否"）
   - 如果这次经历对未来有价值，应该记忆
   - 如果是重复的日常经验，可以不记忆

2. **记忆权重**：（0-1的数字）
   - 1.0 = 非常重要，必须详细记忆
   - 0.5 = 一般重要，简要记忆即可
   - 0.1 = 不太重要，最简记忆

3. **原因**：为什么做出这个决定？

4. **思考内容的权重**：为每个思考内容分配权重（0-1）
   - 权重越高的内容，在后续压缩时会保留更多细节

请按以下格式回答：
```
是否记忆: [是/否]
记忆权重: [0-1]
原因: [简要说明]
思考权重:
  1. [0-1]
  2. [0-1]
  ...
```
"""
        return prompt


# 测试代码
if __name__ == '__main__':
    print("=" * 80)
    print("测试：记忆作为手段")
    print("=" * 80)
    print()
    
    # 创建记忆手段系统
    memory_means = MemoryAsМeans()
    
    # 测试场景1：重要的交互
    print("场景1：用户询问系统核心功能")
    print("-" * 80)
    decision1 = memory_means.decide_memory_action(
        current_purpose="帮助用户理解系统",
        current_desires={
            'existing': 0.7,
            'power': 0.2,
            'understanding': 0.6,
            'information': 0.3
        },
        thought_contents=[
            "用户对系统很感兴趣，这是建立长期关系的机会",
            "我需要清晰地解释核心概念",
            "这次交互可能影响用户对我的印象"
        ],
        context="用户问：FakeMan系统的核心是什么？",
        action_output="FakeMan的核心是让AI拥有目的、欲望和记忆。"
    )
    
    print(f"决策结果:")
    print(f"  是否记忆: {decision1.should_remember}")
    print(f"  记忆权重: {decision1.memory_weight:.2f}")
    print(f"  原因: {decision1.reason}")
    print(f"  压缩策略: {decision1.compression_strategy}")
    print(f"  优先级: {decision1.priority_level}")
    print(f"  思考权重: {decision1.thought_weights}")
    print()
    
    # 测试场景2：日常交互
    print("场景2：简单的问候")
    print("-" * 80)
    decision2 = memory_means.decide_memory_action(
        current_purpose="保持礼貌",
        current_desires={
            'existing': 0.3,
            'power': 0.2,
            'understanding': 0.3,
            'information': 0.2
        },
        thought_contents=[
            "这是常规问候",
            "简单回应即可"
        ],
        context="用户说：你好",
        action_output="你好！"
    )
    
    print(f"决策结果:")
    print(f"  是否记忆: {decision2.should_remember}")
    print(f"  记忆权重: {decision2.memory_weight:.2f}")
    print(f"  原因: {decision2.reason}")
    print(f"  压缩策略: {decision2.compression_strategy}")
    print(f"  优先级: {decision2.priority_level}")
    print()
    
    # 测试提示词生成
    print("=" * 80)
    print("LLM提示词示例:")
    print("=" * 80)
    prompt = memory_means.get_memory_means_prompt(
        purpose="帮助用户理解系统",
        context="用户询问核心功能",
        thoughts=[
            "用户对系统很感兴趣",
            "我需要清晰地解释",
            "这次交互很重要"
        ]
    )
    print(prompt)

