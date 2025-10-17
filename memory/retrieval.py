"""
经验检索引擎
提供基于多种策略的经验检索功能，包括成就感和无聊机制
"""

import time
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from .experience import Experience, PurposeRecord
from .database import MemoryDatabase
from .similarity import (
    calculate_context_similarity,
    calculate_purpose_overlap,
    calculate_means_similarity,
    calculate_experience_similarity,
    calculate_boredom_factor
)
from utils.logger import get_logger

logger = get_logger('fakeman.memory.retrieval')


class ExperienceRetriever:
    """
    经验检索引擎
    
    支持多种检索策略：
    1. 基于情境相似度
    2. 基于目的重合度
    3. 基于手段相似度
    4. 考虑时间衰减
    5. 考虑成就感加成
    6. 考虑无聊惩罚
    """
    
    def __init__(self, 
                 database: MemoryDatabase,
                 time_decay_rate: float = 0.001,
                 achievement_boost: float = 1.5,
                 boredom_penalty: float = 0.5):
        """
        初始化检索引擎
        
        Args:
            database: 记忆数据库
            time_decay_rate: 时间衰减率
            achievement_boost: 成就感加成系数
            boredom_penalty: 无聊惩罚系数
        """
        self.database = database
        self.time_decay_rate = time_decay_rate
        self.achievement_boost = achievement_boost
        self.boredom_penalty = boredom_penalty
    
    def retrieve_similar_experiences(self,
                                     context: str,
                                     purpose: str,
                                     purpose_desires: Dict[str, float],
                                     top_k: int = 5,
                                     min_similarity: float = 0.3,
                                     include_negative: bool = True) -> List[Experience]:
        """
        检索相似经验
        
        综合考虑情境、目的、手段的相似度，以及时间衰减和成就感
        
        Args:
            context: 当前情境
            purpose: 当前目的
            purpose_desires: 目的对应的欲望组成
            top_k: 返回前K个结果
            min_similarity: 最小相似度阈值
            include_negative: 是否包含负面经验
        
        Returns:
            相似经验列表，按相关性排序
        """
        if not self.database.experiences:
            return []
        
        current_time = time.time()
        scored_experiences = []
        
        for exp in self.database.experiences:
            # 过滤负面经验（如果不需要）
            if not include_negative and exp.is_negative:
                continue
            
            # 计算各维度相似度
            context_sim = calculate_context_similarity(context, exp.context)
            purpose_sim = calculate_purpose_overlap(purpose_desires, exp.purpose_desires)
            
            # 综合相似度（加权）
            similarity = 0.4 * context_sim + 0.6 * purpose_sim
            
            if similarity < min_similarity:
                continue
            
            # 时间衰减
            time_diff = current_time - exp.timestamp
            time_weight = np.exp(-self.time_decay_rate * time_diff)
            
            # 成就感加成
            achievement_weight = 1.0
            if exp.is_achievement:
                achievement_weight = self.achievement_boost
            
            # 无聊惩罚
            boredom_weight = 1.0 - exp.boredom_level * self.boredom_penalty
            
            # 综合得分
            score = similarity * time_weight * achievement_weight * boredom_weight
            
            scored_experiences.append((score, exp))
        
        # 排序并返回
        scored_experiences.sort(key=lambda x: x[0], reverse=True)
        results = [exp for _, exp in scored_experiences[:top_k]]
        
        logger.debug(f"检索到 {len(results)} 条相似经验")
        
        return results
    
    def retrieve_for_means_selection(self,
                                     purpose: str,
                                     purpose_desires: Dict[str, float],
                                     top_k: int = 5) -> List[Tuple[str, float, List[Experience]]]:
        """
        为手段选择检索经验
        
        按不同的手段分组，评估每种手段的效果
        
        Args:
            purpose: 当前目的
            purpose_desires: 目的对应的欲望
            top_k: 返回前K种手段
        
        Returns:
            (手段, 平均效果, 相关经验列表) 的列表
        """
        # 查找目的相关的经验
        relevant_exps = []
        for exp in self.database.experiences:
            purpose_overlap = calculate_purpose_overlap(purpose_desires, exp.purpose_desires)
            if purpose_overlap > 0.3:
                relevant_exps.append(exp)
        
        if not relevant_exps:
            logger.debug("没有找到相关经验，返回空列表")
            return []
        
        # 按手段分组
        means_groups: Dict[str, List[Experience]] = {}
        for exp in relevant_exps:
            means_key = exp.means_type  # 使用手段类型分组
            if means_key not in means_groups:
                means_groups[means_key] = []
            means_groups[means_key].append(exp)
        
        # 计算每种手段的效果
        means_scores = []
        current_time = time.time()
        
        for means, exps in means_groups.items():
            # 计算平均效果（考虑时间衰减和成就感）
            weighted_effectiveness = []
            
            for exp in exps:
                # 时间权重
                time_diff = current_time - exp.timestamp
                time_weight = np.exp(-self.time_decay_rate * time_diff)
                
                # 成就感加成
                achievement_mult = exp.achievement_multiplier if exp.is_achievement else 1.0
                
                # 无聊惩罚
                boredom_mult = 1.0 - exp.boredom_level * self.boredom_penalty
                
                # 加权效果
                weighted = exp.means_effectiveness * time_weight * achievement_mult * boredom_mult
                weighted_effectiveness.append(weighted)
            
            avg_effectiveness = np.mean(weighted_effectiveness) if weighted_effectiveness else 0.0
            means_scores.append((means, avg_effectiveness, exps))
        
        # 排序
        means_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"找到 {len(means_scores)} 种手段，推荐前 {min(top_k, len(means_scores))} 种")
        
        return means_scores[:top_k]
    
    def retrieve_for_prediction(self,
                                means: str,
                                means_type: str,
                                purpose_desires: Dict[str, float]) -> List[Experience]:
        """
        为结果预测检索经验
        
        查找使用类似手段、类似目的的历史经验，用于预测效果
        
        Args:
            means: 手段描述
            means_type: 手段类型
            purpose_desires: 目的对应的欲望
        
        Returns:
            相关经验列表
        """
        relevant_exps = []
        
        for exp in self.database.experiences:
            # 手段类型匹配
            if exp.means_type == means_type:
                # 目的相似度
                purpose_overlap = calculate_purpose_overlap(purpose_desires, exp.purpose_desires)
                
                # 手段相似度
                means_sim = calculate_means_similarity(means, exp.means)
                
                # 综合相关性
                relevance = 0.5 * purpose_overlap + 0.5 * means_sim
                
                if relevance > 0.3:
                    relevant_exps.append((relevance, exp))
        
        # 排序
        relevant_exps.sort(key=lambda x: x[0], reverse=True)
        
        return [exp for _, exp in relevant_exps[:10]]
    
    def detect_boredom(self, 
                      purpose: str,
                      means: str,
                      recent_window: int = 10) -> float:
        """
        检测对特定目的-手段组合的无聊程度
        
        Args:
            purpose: 目的
            means: 手段
            recent_window: 最近N次经验
        
        Returns:
            无聊程度 (0-1)
        """
        # 获取最近的经验
        recent_exps = self.database.get_recent_experiences(recent_window)
        
        # 过滤出相关的经验
        relevant_exps = []
        for exp in recent_exps:
            purpose_sim = calculate_means_similarity(purpose, exp.purpose)
            means_sim = calculate_means_similarity(means, exp.means)
            
            if purpose_sim > 0.5 and means_sim > 0.5:
                relevant_exps.append(exp)
        
        if len(relevant_exps) < 3:
            return 0.0
        
        # 使用相似度和效果计算无聊因子
        return calculate_boredom_factor(relevant_exps)
    
    def retrieve_achievements(self, top_k: int = 10) -> List[Experience]:
        """
        检索成就事件
        
        Args:
            top_k: 返回前K个成就
        
        Returns:
            成就事件列表，按成就感加成排序
        """
        achievements = self.database.query_achievements()
        
        # 按成就感加成排序
        achievements.sort(key=lambda x: x.achievement_multiplier, reverse=True)
        
        return achievements[:top_k]
    
    def calculate_means_bias(self,
                            means: str,
                            means_type: str,
                            purpose: str,
                            purpose_desires: Dict[str, float]) -> float:
        """
        计算手段的bias
        
        根据用户要求：手段的bias = 手段对目的可能性的影响 * 完成目的后欲望变化的程度
        
        Args:
            means: 手段描述
            means_type: 手段类型
            purpose: 目的
            purpose_desires: 目的对应的欲望组成
        
        Returns:
            手段bias (0-1+)
        """
        # 检索使用该手段的历史经验
        relevant_exps = self.retrieve_for_prediction(means, means_type, purpose_desires)
        
        if not relevant_exps:
            return 0.5  # 无经验时返回中性值
        
        # 计算手段对目的的可能性影响
        # 可能性 = 成功率 * 平均效果
        success_count = sum(1 for exp in relevant_exps if exp.purpose_achieved)
        success_rate = success_count / len(relevant_exps)
        
        avg_effectiveness = np.mean([exp.means_effectiveness for exp in relevant_exps])
        
        possibility_impact = success_rate * avg_effectiveness
        
        # 计算完成目的后欲望变化的程度
        # 使用加权幸福度变化（包含成就感）
        avg_desire_change = np.mean([
            abs(exp.weighted_happiness_delta) 
            for exp in relevant_exps 
            if exp.purpose_achieved
        ])
        
        if success_count == 0:
            avg_desire_change = 0.1  # 默认小值
        
        # 手段bias = 可能性影响 * 欲望变化程度
        means_bias = possibility_impact * avg_desire_change
        
        # 考虑无聊因子
        boredom = self.detect_boredom(purpose, means)
        means_bias *= (1.0 - boredom * self.boredom_penalty)
        
        logger.debug(f"手段 '{means}' 的bias: {means_bias:.3f} "
                    f"(可能性={possibility_impact:.3f}, 欲望变化={avg_desire_change:.3f}, 无聊={boredom:.3f})")
        
        return max(0.0, means_bias)
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """获取检索统计信息"""
        total_exps = len(self.database.experiences)
        
        if total_exps == 0:
            return {'total_experiences': 0}
        
        achievements = self.database.query_achievements()
        positive_exps = self.database.query_positive_experiences()
        
        # 计算平均无聊程度
        avg_boredom = np.mean([exp.boredom_level for exp in self.database.experiences])
        
        return {
            'total_experiences': total_exps,
            'achievements': len(achievements),
            'positive_rate': len(positive_exps) / total_exps,
            'avg_boredom_level': avg_boredom,
            'avg_achievement_multiplier': np.mean([
                exp.achievement_multiplier for exp in achievements
            ]) if achievements else 0.0
        }


if __name__ == '__main__':
    # 测试检索引擎
    from .database import MemoryDatabase
    
    # 创建测试数据库
    db = MemoryDatabase('data/test_retrieval.json')
    
    # 添加一些测试经验
    for i in range(5):
        exp = Experience(
            id=0,
            timestamp=time.time() - i * 100,
            cycle_id=i+1,
            context=f"测试情境{i}",
            context_hash=Experience.create_context_hash(f"测试情境{i}"),
            purpose="理解用户意图",
            purpose_desires={'understanding': 0.6, 'information': 0.4},
            means=f"询问用户{i}",
            means_type='ask_question',
            thought_count=i+1,
            total_happiness_delta=0.3 + i*0.1,
            means_effectiveness=0.5 + i*0.1,
            purpose_achieved=(i % 2 == 0),
            is_achievement=(i == 4)
        )
        
        if i == 4:
            exp.achievement_multiplier = exp.calculate_achievement_multiplier()
        
        db.insert_experience(exp)
    
    # 创建检索引擎
    retriever = ExperienceRetriever(db)
    
    # 测试检索
    print("测试检索相似经验:")
    results = retriever.retrieve_similar_experiences(
        context="测试情境0",
        purpose="理解用户意图",
        purpose_desires={'understanding': 0.7, 'information': 0.3},
        top_k=3
    )
    print(f"找到 {len(results)} 条相似经验")
    
    # 测试手段选择
    print("\n测试手段选择:")
    means_results = retriever.retrieve_for_means_selection(
        purpose="理解用户意图",
        purpose_desires={'understanding': 0.6, 'information': 0.4}
    )
    for means, score, exps in means_results:
        print(f"  手段: {means}, 得分: {score:.3f}, 经验数: {len(exps)}")
    
    # 测试手段bias计算
    print("\n测试手段bias:")
    bias = retriever.calculate_means_bias(
        means="询问用户",
        means_type='ask_question',
        purpose="理解用户意图",
        purpose_desires={'understanding': 0.6, 'information': 0.4}
    )
    print(f"手段bias: {bias:.3f}")
    
    # 统计信息
    print("\n检索统计:")
    stats = retriever.get_retrieval_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

