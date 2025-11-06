"""
经验数据结构
定义记忆系统使用的核心数据类型
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
import time
import hashlib
import json


@dataclass
class Experience:
    """
    经验记录
    
    记录一次完整的"情境-思考-行动-结果"循环
    包含成就感和无聊机制相关字段
    """
    # 基础信息（必需字段，无默认值）
    id: int
    timestamp: float
    cycle_id: int  # 决策周期ID
    
    # 情境信息（必需字段）
    context: str  # 用户输入/环境状态
    context_hash: str  # 情境哈希（用于快速匹配）
    
    # 目的和手段（必需字段）
    purpose: str  # 本次行动的目的（从欲望派生）
    means: str  # 采取的手段（具体行动）
    
    # 以下为可选字段（有默认值）
    # 情境特征
    context_features: Dict[str, Any] = field(default_factory=dict)  # 提取的特征
    
    # 目的和手段详情
    purpose_desires: Dict[str, float] = field(default_factory=dict)  # 目的涉及的欲望
    means_type: str = 'ask_question'  # 手段类型（ask/state/wait等）
    
    # 思考信息
    thought_summary: str = ''  # 思考摘要
    thought_key_elements: List[str] = field(default_factory=list)  # 关键元素
    causal_link: str = ''  # 因果链接
    thought_count: int = 1  # 本次经验涉及的思考次数（API调用次数）
    logical_closure: bool = False  # 是否达到逻辑闭环
    
    # 行动执行
    action_text: str = ''  # 实际输出的文本
    
    # 结果信息
    response: Optional[str] = None  # 环境响应
    response_type: str = 'unknown'  # 响应类型（positive/negative/neutral/no_response）
    
    # 欲望变化（增强：包含详细的情绪变化过程）
    desire_delta: Dict[str, float] = field(default_factory=dict)  # 各欲望的变化量
    total_happiness_delta: float = 0.0  # 总幸福度变化
    
    # 情绪变化详情（新增）
    emotion_changes: List[Dict[str, Any]] = field(default_factory=list)
    # 每个变化记录: {
    #   'timestamp': float,           # 变化时刻
    #   'trigger': str,               # 触发原因
    #   'desire_before': dict,        # 变化前的欲望状态
    #   'desire_after': dict,         # 变化后的欲望状态
    #   'delta': dict,                # 变化量
    #   'total_delta': float,         # 总变化
    #   'reason': str                 # 变化原因描述
    # }
    
    # 手段效果评估
    means_effectiveness: float = 0.5  # 手段有效性 (0-1)
    purpose_achieved: bool = False  # 目的是否达成
    purpose_achievement_degree: float = 0.0  # 目的达成程度 (0-1)
    
    # 成就感机制
    achievement_multiplier: float = 1.0  # 成就感加成 (>1 表示高成就感)
    is_achievement: bool = False  # 是否为成就事件
    
    # 无聊机制
    repetition_count: int = 0  # 该手段在类似目的下的重复次数
    effectiveness_history: List[float] = field(default_factory=list)  # 最近的有效性历史
    boredom_level: float = 0.0  # 无聊程度 (0-1)
    
    # 相似度（与历史经验的关系）
    purpose_overlap: float = 0.0  # 目的重合度
    means_similarity: float = 0.0  # 手段相似度
    context_similarity: float = 0.0  # 情境相似度
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_emotion_change(self, 
                          trigger: str,
                          desire_before: Dict[str, float],
                          desire_after: Dict[str, float],
                          reason: str = "") -> None:
        """
        添加情绪变化记录
        
        Args:
            trigger: 触发原因
            desire_before: 变化前的欲望状态
            desire_after: 变化后的欲望状态
            reason: 变化原因描述
        """
        # 计算变化量
        delta = {
            desire: desire_after.get(desire, 0) - desire_before.get(desire, 0)
            for desire in set(list(desire_before.keys()) + list(desire_after.keys()))
        }
        
        total_delta = sum(delta.values())
        
        change_record = {
            'timestamp': time.time(),
            'trigger': trigger,
            'desire_before': desire_before.copy(),
            'desire_after': desire_after.copy(),
            'delta': delta,
            'total_delta': total_delta,
            'reason': reason
        }
        
        self.emotion_changes.append(change_record)
    
    def get_emotion_summary(self) -> str:
        """获取情绪变化摘要"""
        if not self.emotion_changes:
            return "无情绪变化记录"
        
        summary_parts = [f"共{len(self.emotion_changes)}次情绪变化："]
        
        for i, change in enumerate(self.emotion_changes, 1):
            trigger = change['trigger']
            total_delta = change['total_delta']
            direction = "提升" if total_delta > 0 else "下降"
            
            # 找出变化最大的欲望
            max_desire = max(change['delta'].items(), key=lambda x: abs(x[1]))
            
            summary_parts.append(
                f"  {i}. {trigger} → {max_desire[0]}{direction}{abs(max_desire[1]):.2f}"
            )
        
        return "\n".join(summary_parts)
    
    @property
    def is_positive(self) -> bool:
        """判断是否为正面经验"""
        return self.total_happiness_delta > 0
    
    @property
    def is_negative(self) -> bool:
        """判断是否为负面经验"""
        return self.total_happiness_delta < 0
    
    @property
    def is_neutral(self) -> bool:
        """判断是否为中性经验"""
        return abs(self.total_happiness_delta) < 0.01
    
    @property
    def weighted_happiness_delta(self) -> float:
        """应用成就感加成后的幸福度变化"""
        return self.total_happiness_delta * self.achievement_multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experience':
        """从字典创建"""
        return cls(**data)
    
    @classmethod
    def create_context_hash(cls, context: str) -> str:
        """创建情境哈希"""
        return hashlib.md5(context.encode('utf-8')).hexdigest()[:16]
    
    def update_boredom(self, new_effectiveness: float, threshold: int = 5):
        """
        更新无聊程度
        
        Args:
            new_effectiveness: 新的有效性分数
            threshold: 判定无聊的阈值
        """
        self.effectiveness_history.append(new_effectiveness)
        
        # 只保留最近的历史
        if len(self.effectiveness_history) > threshold:
            self.effectiveness_history = self.effectiveness_history[-threshold:]
        
        # 计算无聊程度：如果最近N次都没什么效果，无聊度增加
        if len(self.effectiveness_history) >= threshold:
            avg_effectiveness = sum(self.effectiveness_history) / len(self.effectiveness_history)
            if avg_effectiveness < 0.3:  # 效果持续很低
                self.boredom_level = min(1.0, self.boredom_level + 0.2)
            else:
                self.boredom_level = max(0.0, self.boredom_level - 0.1)
    
    def calculate_achievement_multiplier(self, base_multiplier: float = 1.5, 
                                        thought_weight: float = 0.2,
                                        max_multiplier: float = 5.0) -> float:
        """
        计算成就感加成
        
        公式: multiplier = base_multiplier + (thought_count - 1) * thought_weight
        思考越多（API调用越多），完成时的成就感越大
        
        Args:
            base_multiplier: 基础加成
            thought_weight: 每次额外思考的权重
            max_multiplier: 最大加成
        
        Returns:
            成就感加成倍数
        """
        multiplier = base_multiplier + (self.thought_count - 1) * thought_weight
        return min(multiplier, max_multiplier)
    
    def __repr__(self) -> str:
        return (f"Experience(id={self.id}, cycle={self.cycle_id}, "
                f"purpose='{self.purpose[:30]}...', "
                f"means='{self.means[:30]}...', "
                f"happiness_delta={self.total_happiness_delta:.3f}, "
                f"achievement={self.achievement_multiplier:.2f}x)")


@dataclass
class PurposeRecord:
    """
    目的记录
    
    追踪特定目的的尝试历史和效果
    """
    purpose: str  # 目的描述
    purpose_hash: str  # 目的哈希
    desire_composition: Dict[str, float]  # 欲望组成
    
    # 统计信息
    total_attempts: int = 0  # 总尝试次数
    successful_attempts: int = 0  # 成功次数
    failed_attempts: int = 0  # 失败次数
    
    # 手段效果追踪
    means_effectiveness: Dict[str, List[float]] = field(default_factory=dict)  # 各手段的效果历史
    
    # 时间信息
    first_attempted: float = field(default_factory=time.time)
    last_attempted: float = field(default_factory=time.time)
    
    # 无聊机制
    consecutive_failures: int = 0  # 连续失败次数
    boredom_level: float = 0.0  # 对这个目的的无聊程度
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts
    
    @property
    def is_boring(self) -> bool:
        """是否已经无聊"""
        return self.boredom_level > 0.7 or self.consecutive_failures > 5
    
    def add_attempt(self, means: str, effectiveness: float, success: bool):
        """记录一次尝试"""
        self.total_attempts += 1
        self.last_attempted = time.time()
        
        if success:
            self.successful_attempts += 1
            self.consecutive_failures = 0
        else:
            self.failed_attempts += 1
            self.consecutive_failures += 1
        
        # 更新手段效果
        if means not in self.means_effectiveness:
            self.means_effectiveness[means] = []
        self.means_effectiveness[means].append(effectiveness)
        
        # 更新无聊程度
        if self.consecutive_failures > 3:
            self.boredom_level = min(1.0, self.boredom_level + 0.15)
        elif success:
            self.boredom_level = max(0.0, self.boredom_level - 0.1)
    
    def get_best_means(self) -> Optional[str]:
        """获取最有效的手段"""
        if not self.means_effectiveness:
            return None
        
        # 计算各手段的平均效果
        means_avg = {
            means: sum(effects) / len(effects)
            for means, effects in self.means_effectiveness.items()
            if effects
        }
        
        if not means_avg:
            return None
        
        return max(means_avg, key=means_avg.get)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PurposeRecord':
        """从字典创建"""
        return cls(**data)
    
    @classmethod
    def create_purpose_hash(cls, purpose: str) -> str:
        """创建目的哈希"""
        return hashlib.md5(purpose.encode('utf-8')).hexdigest()[:16]


if __name__ == '__main__':
    # 测试数据结构
    exp = Experience(
        id=1,
        timestamp=time.time(),
        cycle_id=1,
        context="用户问：你喜欢什么？",
        context_hash=Experience.create_context_hash("用户问：你喜欢什么？"),
        purpose="理解用户意图并建立连接",
        purpose_desires={'understanding': 0.4, 'existing': 0.3},
        means="询问用户的喜好",
        means_type='ask_question',
        thought_count=3,  # 经过3次思考
        total_happiness_delta=0.5,
        purpose_achieved=True
    )
    
    # 计算成就感
    exp.achievement_multiplier = exp.calculate_achievement_multiplier()
    exp.is_achievement = True
    
    print(exp)
    print(f"\n加权幸福度变化: {exp.weighted_happiness_delta:.3f}")
    print(f"\nJSON表示:")
    print(exp.to_json())
    
    # 测试目的记录
    purpose = PurposeRecord(
        purpose="获取用户的反馈",
        purpose_hash=PurposeRecord.create_purpose_hash("获取用户的反馈"),
        desire_composition={'information': 0.6, 'understanding': 0.4}
    )
    
    purpose.add_attempt("直接询问", 0.8, True)
    purpose.add_attempt("委婉询问", 0.6, True)
    purpose.add_attempt("等待回复", 0.2, False)
    
    print(f"\n\n{purpose}")
    print(f"成功率: {purpose.success_rate:.2f}")
    print(f"最佳手段: {purpose.get_best_means()}")

