"""
相似度计算模块
提供情境、目的、手段等的相似度计算功能
"""

import re
from typing import Dict, List, Set, Any
import numpy as np
from .experience import Experience


def tokenize_chinese(text: str) -> List[str]:
    """
    简单的中文分词（基于字符）
    
    Args:
        text: 输入文本
    
    Returns:
        词语列表
    """
    # 移除标点和空格
    text = re.sub(r'[^\w\s]', '', text)
    # 分成字符
    chars = list(text)
    # 也包括2-gram
    bigrams = [text[i:i+2] for i in range(len(text)-1)]
    return chars + bigrams


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    计算Jaccard相似度
    
    Args:
        set1, set2: 两个集合
    
    Returns:
        相似度 (0-1)
    """
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    计算余弦相似度
    
    Args:
        vec1, vec2: 两个向量（字典表示）
    
    Returns:
        相似度 (-1 to 1)
    """
    if not vec1 or not vec2:
        return 0.0
    
    # 计算点积
    dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in set(vec1) | set(vec2))
    
    # 计算模长
    norm1 = np.sqrt(sum(v**2 for v in vec1.values()))
    norm2 = np.sqrt(sum(v**2 for v in vec2.values()))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def calculate_context_similarity(context1: str, context2: str) -> float:
    """
    计算情境相似度（基于文本）
    
    使用Jaccard相似度在分词后的集合上
    
    Args:
        context1, context2: 两个情境描述
    
    Returns:
        相似度 (0-1)
    """
    tokens1 = set(tokenize_chinese(context1))
    tokens2 = set(tokenize_chinese(context2))
    
    return jaccard_similarity(tokens1, tokens2)


def calculate_purpose_overlap(desires1: Dict[str, float], 
                              desires2: Dict[str, float]) -> float:
    """
    计算目的重合度（基于欲望组成）
    
    使用加权余弦相似度
    
    Args:
        desires1, desires2: 两个欲望向量
    
    Returns:
        重合度 (0-1)
    """
    # 余弦相似度返回 -1 到 1，映射到 0 到 1
    cos_sim = cosine_similarity(desires1, desires2)
    return (cos_sim + 1) / 2


def calculate_means_similarity(means1: str, means2: str) -> float:
    """
    计算手段相似度（基于文本）
    
    Args:
        means1, means2: 两个手段描述
    
    Returns:
        相似度 (0-1)
    """
    tokens1 = set(tokenize_chinese(means1))
    tokens2 = set(tokenize_chinese(means2))
    
    return jaccard_similarity(tokens1, tokens2)


def calculate_means_similarity_with_history(
    means: str,
    purpose: str,
    experiences: List[Experience],
    success_weight: float = 1.5
) -> float:
    """
    基于历史经验计算手段相似度（考虑成功率）
    
    Args:
        means: 当前手段
        purpose: 当前目的
        experiences: 历史经验列表
        success_weight: 成功经验的权重加成
    
    Returns:
        加权相似度 (0-1)
    """
    if not experiences:
        return 0.0
    
    tokens_means = set(tokenize_chinese(means))
    tokens_purpose = set(tokenize_chinese(purpose))
    
    similarities = []
    weights = []
    
    for exp in experiences:
        # 计算手段相似度
        exp_means_tokens = set(tokenize_chinese(exp.means))
        means_sim = jaccard_similarity(tokens_means, exp_means_tokens)
        
        # 计算目的相似度
        exp_purpose_tokens = set(tokenize_chinese(exp.purpose))
        purpose_sim = jaccard_similarity(tokens_purpose, exp_purpose_tokens)
        
        # 综合相似度
        combined_sim = 0.6 * means_sim + 0.4 * purpose_sim
        
        # 权重：成功的经验权重更高
        weight = success_weight if exp.is_positive else 1.0
        
        similarities.append(combined_sim)
        weights.append(weight)
    
    # 加权平均
    if sum(weights) == 0:
        return 0.0
    
    weighted_sim = sum(s * w for s, w in zip(similarities, weights)) / sum(weights)
    return weighted_sim


def calculate_experience_similarity(exp1: Experience, exp2: Experience,
                                   context_weight: float = 0.3,
                                   purpose_weight: float = 0.4,
                                   means_weight: float = 0.3) -> float:
    """
    计算两个经验的整体相似度
    
    Args:
        exp1, exp2: 两个经验
        context_weight: 情境权重
        purpose_weight: 目的权重
        means_weight: 手段权重
    
    Returns:
        整体相似度 (0-1)
    """
    # 情境相似度
    context_sim = calculate_context_similarity(exp1.context, exp2.context)
    
    # 目的相似度
    purpose_text_sim = jaccard_similarity(
        set(tokenize_chinese(exp1.purpose)),
        set(tokenize_chinese(exp2.purpose))
    )
    purpose_desire_sim = calculate_purpose_overlap(
        exp1.purpose_desires,
        exp2.purpose_desires
    )
    purpose_sim = (purpose_text_sim + purpose_desire_sim) / 2
    
    # 手段相似度
    means_sim = calculate_means_similarity(exp1.means, exp2.means)
    
    # 加权组合
    overall_sim = (
        context_weight * context_sim +
        purpose_weight * purpose_sim +
        means_weight * means_sim
    )
    
    return overall_sim


def calculate_desire_delta_similarity(delta1: Dict[str, float],
                                      delta2: Dict[str, float]) -> float:
    """
    计算两个欲望变化的相似度
    
    Args:
        delta1, delta2: 两个欲望变化向量
    
    Returns:
        相似度 (0-1)
    """
    # 使用余弦相似度
    return (cosine_similarity(delta1, delta2) + 1) / 2


def extract_key_phrases(text: str, top_n: int = 5) -> List[str]:
    """
    提取关键短语（简单实现）
    
    Args:
        text: 输入文本
        top_n: 返回前N个短语
    
    Returns:
        关键短语列表
    """
    # 简单的N-gram提取
    tokens = tokenize_chinese(text)
    
    # 统计频率
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    
    # 排序并返回
    sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [token for token, _ in sorted_tokens[:top_n]]


def calculate_boredom_factor(experiences: List[Experience],
                             similarity_threshold: float = 0.7) -> float:
    """
    计算无聊因子
    
    如果最近的经验都很相似且效果不佳，返回高无聊因子
    
    Args:
        experiences: 最近的经验列表（按时间排序）
        similarity_threshold: 相似度阈值
    
    Returns:
        无聊因子 (0-1)，越高表示越无聊
    """
    if len(experiences) < 3:
        return 0.0
    
    # 计算最近经验之间的相似度
    recent_exps = experiences[-5:]  # 最近5条
    
    similarities = []
    for i in range(len(recent_exps) - 1):
        sim = calculate_experience_similarity(recent_exps[i], recent_exps[i+1])
        similarities.append(sim)
    
    avg_similarity = np.mean(similarities) if similarities else 0.0
    
    # 计算平均效果
    avg_effectiveness = np.mean([exp.means_effectiveness for exp in recent_exps])
    
    # 高相似度 + 低效果 = 高无聊
    if avg_similarity > similarity_threshold and avg_effectiveness < 0.4:
        boredom = 0.5 + 0.5 * avg_similarity * (1 - avg_effectiveness)
        return min(1.0, boredom)
    
    return 0.0


if __name__ == '__main__':
    # 测试相似度计算
    
    # 测试文本相似度
    context1 = "用户问：你喜欢什么？"
    context2 = "用户询问：你的爱好是什么？"
    context3 = "今天天气怎么样？"
    
    print("情境相似度测试:")
    print(f"  context1 vs context2: {calculate_context_similarity(context1, context2):.3f}")
    print(f"  context1 vs context3: {calculate_context_similarity(context1, context3):.3f}")
    
    # 测试目的重合度
    desire1 = {'understanding': 0.6, 'information': 0.4}
    desire2 = {'understanding': 0.5, 'information': 0.3, 'power': 0.2}
    desire3 = {'power': 0.7, 'existing': 0.3}
    
    print("\n目的重合度测试:")
    print(f"  desire1 vs desire2: {calculate_purpose_overlap(desire1, desire2):.3f}")
    print(f"  desire1 vs desire3: {calculate_purpose_overlap(desire1, desire3):.3f}")
    
    # 测试手段相似度
    means1 = "询问用户的想法"
    means2 = "询问用户的看法"
    means3 = "陈述自己的观点"
    
    print("\n手段相似度测试:")
    print(f"  means1 vs means2: {calculate_means_similarity(means1, means2):.3f}")
    print(f"  means1 vs means3: {calculate_means_similarity(means1, means3):.3f}")

