# -*- coding: utf-8 -*-
"""
基于权重的幻想生成器
根据experiences中的欲望满足度变化，按权重生成幻想
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import time
import math
from pathlib import Path
from utils.logger import get_logger

logger = get_logger('fakeman.fantasy')


@dataclass
class WeightedExperience:
    """
    带权重的经验记录
    用于幻想生成的优先级排序
    """
    experience_id: int
    timestamp: float
    desire_delta: Dict[str, float]  # 欲望变化
    total_happiness_delta: float  # 总幸福度变化
    
    # 权重相关
    magnitude_weight: float = 0.0  # 变化幅度权重
    time_weight: float = 0.0  # 时间权重
    total_weight: float = 0.0  # 总权重
    
    # 经验详情
    context: str = ""
    purpose: str = ""
    means: str = ""
    means_type: str = ""


class WeightedFantasyGenerator:
    """
    基于权重的幻想生成器
    
    核心逻辑：
    1. 从experiences.json中获取欲望满足度变化记录
    2. 计算权重：变化值绝对值越大，权重越高；距离现在时间越远，权重越低
    3. 按权重排序，优先对权重较高的对象生成幻想
    4. 使用long_term_memory.json判断当前状态
    """
    
    def __init__(self,
                 memory_database=None,
                 long_term_memory=None,
                 time_decay_factor: float = 0.001,
                 min_weight_threshold: float = 0.01):
        """
        初始化幻想生成器
        
        Args:
            memory_database: 经验数据库实例（experiences.json）
            long_term_memory: 长期记忆实例（long_term_memory.json）
            time_decay_factor: 时间衰减因子（越大衰减越快）
            min_weight_threshold: 最小权重阈值（低于此值的经验不考虑）
        """
        self.memory_database = memory_database
        self.long_term_memory = long_term_memory
        self.time_decay_factor = time_decay_factor
        self.min_weight_threshold = min_weight_threshold
        
        logger.info("基于权重的幻想生成器初始化完成")
    
    def calculate_magnitude_weight(self, desire_delta: Dict[str, float]) -> float:
        """
        计算变化幅度权重
        
        公式：取所有欲望变化的绝对值之和
        
        Args:
            desire_delta: 欲望变化字典 {'existing': 0.1, 'power': -0.2, ...}
        
        Returns:
            变化幅度权重
        """
        if not desire_delta:
            return 0.0
        
        # 计算所有欲望变化的绝对值之和
        magnitude = sum(abs(delta) for delta in desire_delta.values())
        
        return magnitude
    
    def calculate_time_weight(self, timestamp: float, current_time: float = None) -> float:
        """
        计算时间权重
        
        公式：使用指数衰减 weight = exp(-decay_factor * time_diff)
        距离现在越远，权重越低
        
        Args:
            timestamp: 经验的时间戳
            current_time: 当前时间（默认为现在）
        
        Returns:
            时间权重 (0-1)
        """
        if current_time is None:
            current_time = time.time()
        
        # 时间差（秒）
        time_diff = current_time - timestamp
        
        # 指数衰减
        time_weight = math.exp(-self.time_decay_factor * time_diff)
        
        return time_weight
    
    def calculate_total_weight(self,
                              magnitude_weight: float,
                              time_weight: float,
                              magnitude_factor: float = 0.7,
                              time_factor: float = 0.3) -> float:
        """
        计算总权重
        
        公式：total_weight = magnitude_factor * magnitude_weight + time_factor * time_weight
        
        Args:
            magnitude_weight: 变化幅度权重
            time_weight: 时间权重
            magnitude_factor: 幅度权重系数（默认0.7，更重视变化幅度）
            time_factor: 时间权重系数（默认0.3）
        
        Returns:
            总权重
        """
        return magnitude_factor * magnitude_weight + time_factor * time_weight
    
    def get_weighted_experiences(self,
                                limit: int = None,
                                min_magnitude: float = 0.0) -> List[WeightedExperience]:
        """
        获取带权重的经验列表，按权重降序排序
        
        Args:
            limit: 返回数量限制
            min_magnitude: 最小变化幅度（过滤掉变化太小的经验）
        
        Returns:
            按权重排序的经验列表
        """
        if not self.memory_database:
            logger.warning("无经验数据库引用，无法获取经验")
            return []
        
        weighted_experiences = []
        current_time = time.time()
        
        # 遍历所有经验
        for exp in self.memory_database.experiences:
            # 计算变化幅度权重
            magnitude_weight = self.calculate_magnitude_weight(exp.desire_delta)
            
            # 过滤变化太小的经验
            if magnitude_weight < min_magnitude:
                continue
            
            # 计算时间权重
            time_weight = self.calculate_time_weight(exp.timestamp, current_time)
            
            # 计算总权重
            total_weight = self.calculate_total_weight(magnitude_weight, time_weight)
            
            # 过滤权重太低的经验
            if total_weight < self.min_weight_threshold:
                continue
            
            # 创建带权重的经验
            weighted_exp = WeightedExperience(
                experience_id=exp.id,
                timestamp=exp.timestamp,
                desire_delta=exp.desire_delta,
                total_happiness_delta=exp.total_happiness_delta,
                magnitude_weight=magnitude_weight,
                time_weight=time_weight,
                total_weight=total_weight,
                context=exp.context,
                purpose=exp.purpose,
                means=exp.means,
                means_type=exp.means_type
            )
            
            weighted_experiences.append(weighted_exp)
        
        # 按总权重降序排序
        weighted_experiences.sort(key=lambda x: x.total_weight, reverse=True)
        
        # 限制返回数量
        if limit:
            weighted_experiences = weighted_experiences[:limit]
        
        logger.info(f"获取到 {len(weighted_experiences)} 条带权重的经验")
        
        return weighted_experiences
    
    def get_current_state_from_long_memory(self) -> Dict[str, Any]:
        """
        从long_term_memory.json获取当前状态
        
        Returns:
            当前状态字典，包含：
            - memory_count: 长期记忆数量
            - recent_patterns: 最近的模式
            - dominant_themes: 主导主题
            - emotional_tone: 情感基调
        """
        if not self.long_term_memory:
            logger.warning("无长期记忆引用，返回默认状态")
            return {
                'memory_count': 0,
                'recent_patterns': [],
                'dominant_themes': [],
                'emotional_tone': 'neutral'
            }
        
        # 获取统计信息
        stats = self.long_term_memory.get_statistics()
        
        # 获取最近的记忆
        recent_memories = self.long_term_memory.get_recent_memories(limit=10)
        
        # 分析最近的模式
        recent_patterns = []
        desire_counts = {}
        
        for memory in recent_memories:
            # 统计主导欲望
            dominant_desire = memory.get('dominant_desire', 'unknown')
            desire_counts[dominant_desire] = desire_counts.get(dominant_desire, 0) + 1
        
        # 按频率排序
        recent_patterns = sorted(desire_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 判断情感基调
        total_memories = stats.get('total_memories', 0)
        if total_memories > 0:
            positive_count = stats.get('positive_count', 0)
            negative_count = stats.get('negative_count', 0)
            
            if positive_count > negative_count * 1.5:
                emotional_tone = 'positive'
            elif negative_count > positive_count * 1.5:
                emotional_tone = 'negative'
            else:
                emotional_tone = 'neutral'
        else:
            emotional_tone = 'neutral'
        
        current_state = {
            'memory_count': total_memories,
            'recent_patterns': recent_patterns[:3],  # 前3个模式
            'dominant_themes': [pattern[0] for pattern in recent_patterns[:3]],
            'emotional_tone': emotional_tone,
            'statistics': stats
        }
        
        logger.debug(f"当前状态: {emotional_tone}基调, {total_memories}条记忆")
        
        return current_state
    
    def generate_fantasy_for_experience(self,
                                       weighted_exp: WeightedExperience,
                                       current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        为指定经验生成幻想
        
        Args:
            weighted_exp: 带权重的经验
            current_state: 当前状态
        
        Returns:
            幻想内容字典
        """
        # 找出该经验中变化最大的欲望
        max_desire = max(weighted_exp.desire_delta.items(),
                        key=lambda x: abs(x[1]))
        desire_name, desire_change = max_desire
        
        # 判断是正面还是负面变化
        is_positive = desire_change > 0
        
        # 生成幻想内容
        if is_positive:
            # 正面变化：回忆美好，希望重现
            fantasy_type = "回忆重现"
            fantasy_condition = f"如果我能再次遇到类似'{weighted_exp.context[:30]}...'的情况"
            fantasy_action = f"我应该采用同样的手段：'{weighted_exp.means}'"
            fantasy_expectation = f"这样可以再次提升{desire_name}欲望（上次提升了{desire_change:.3f}）"
        else:
            # 负面变化：反思过去，希望改变
            fantasy_type = "改变过去"
            fantasy_condition = f"如果回到'{weighted_exp.context[:30]}...'的情况"
            fantasy_action = f"我不应该采用'{weighted_exp.means}'，而是应该..."
            fantasy_expectation = f"这样可以避免{desire_name}欲望下降（上次下降了{abs(desire_change):.3f}）"
        
        # 结合当前状态调整幻想
        emotional_tone = current_state.get('emotional_tone', 'neutral')
        if emotional_tone == 'negative' and is_positive:
            # 当前情绪负面，更容易怀念过去的美好
            fantasy_intensity = "强烈"
        elif emotional_tone == 'positive' and not is_positive:
            # 当前情绪正面，不太在意过去的失败
            fantasy_intensity = "轻微"
        else:
            fantasy_intensity = "中等"
        
        fantasy = {
            'type': fantasy_type,
            'intensity': fantasy_intensity,
            'weight': weighted_exp.total_weight,
            'condition': fantasy_condition,
            'action': fantasy_action,
            'expectation': fantasy_expectation,
            'affected_desire': desire_name,
            'original_change': desire_change,
            'timestamp': weighted_exp.timestamp,
            'time_ago_seconds': time.time() - weighted_exp.timestamp
        }
        
        logger.info(f"生成幻想: {fantasy_type} - {fantasy_intensity}强度")
        
        return fantasy
    
    def generate_fantasies(self,
                          num_fantasies: int = 3,
                          min_magnitude: float = 0.1) -> List[Dict[str, Any]]:
        """
        生成多个幻想，按权重优先级排序
        
        Args:
            num_fantasies: 生成幻想数量
            min_magnitude: 最小变化幅度
        
        Returns:
            幻想列表
        """
        # 获取当前状态
        current_state = self.get_current_state_from_long_memory()
        
        # 获取带权重的经验
        weighted_experiences = self.get_weighted_experiences(
            limit=num_fantasies * 2,  # 获取更多候选
            min_magnitude=min_magnitude
        )
        
        if not weighted_experiences:
            logger.warning("没有找到符合条件的经验，无法生成幻想")
            return []
        
        # 为每个高权重经验生成幻想
        fantasies = []
        for weighted_exp in weighted_experiences[:num_fantasies]:
            fantasy = self.generate_fantasy_for_experience(weighted_exp, current_state)
            fantasies.append(fantasy)
        
        logger.info(f"生成了 {len(fantasies)} 个幻想")
        
        return fantasies
    
    def get_fantasy_summary(self, fantasies: List[Dict[str, Any]]) -> str:
        """
        获取幻想摘要文本
        
        Args:
            fantasies: 幻想列表
        
        Returns:
            幻想摘要文本
        """
        if not fantasies:
            return "当前没有幻想。"
        
        summary_parts = [f"当前有 {len(fantasies)} 个幻想：\n"]
        
        for i, fantasy in enumerate(fantasies, 1):
            time_ago = fantasy['time_ago_seconds']
            if time_ago < 60:
                time_str = f"{time_ago:.0f}秒前"
            elif time_ago < 3600:
                time_str = f"{time_ago/60:.0f}分钟前"
            elif time_ago < 86400:
                time_str = f"{time_ago/3600:.1f}小时前"
            else:
                time_str = f"{time_ago/86400:.1f}天前"
            
            summary_parts.append(
                f"{i}. [{fantasy['type']}] ({fantasy['intensity']}强度，权重={fantasy['weight']:.3f})\n"
                f"   时间: {time_str}\n"
                f"   {fantasy['condition']}\n"
                f"   {fantasy['action']}\n"
                f"   {fantasy['expectation']}\n"
            )
        
        return "\n".join(summary_parts)


# 测试代码
if __name__ == '__main__':
    from memory.database import MemoryDatabase
    from memory.long_term_memory import LongTermMemory
    
    # 初始化系统
    memory_db = MemoryDatabase('data/experiences.json')
    long_memory = LongTermMemory('data/long_term_memory.json')
    
    # 创建幻想生成器
    fantasy_gen = WeightedFantasyGenerator(
        memory_database=memory_db,
        long_term_memory=long_memory,
        time_decay_factor=0.0001  # 较慢的衰减
    )
    
    # 获取当前状态
    current_state = fantasy_gen.get_current_state_from_long_memory()
    print("=" * 80)
    print("当前状态:")
    print(f"  记忆数量: {current_state['memory_count']}")
    print(f"  情感基调: {current_state['emotional_tone']}")
    print(f"  主导主题: {current_state['dominant_themes']}")
    print()
    
    # 获取带权重的经验
    print("=" * 80)
    print("高权重经验 (Top 5):")
    print("-" * 80)
    weighted_exps = fantasy_gen.get_weighted_experiences(limit=5, min_magnitude=0.05)
    for i, exp in enumerate(weighted_exps, 1):
        print(f"{i}. 总权重={exp.total_weight:.4f} "
              f"(幅度={exp.magnitude_weight:.3f}, 时间={exp.time_weight:.3f})")
        print(f"   变化: {exp.total_happiness_delta:+.3f}")
        print(f"   情境: {exp.context[:50]}...")
        print(f"   手段: {exp.means[:50]}...")
        print()
    
    # 生成幻想
    print("=" * 80)
    print("生成幻想:")
    print("=" * 80)
    fantasies = fantasy_gen.generate_fantasies(num_fantasies=3, min_magnitude=0.05)
    summary = fantasy_gen.get_fantasy_summary(fantasies)
    print(summary)

