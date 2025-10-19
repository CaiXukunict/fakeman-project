"""
FakeMan 记忆系统模块
提供经验存储、检索和相似度计算功能
"""

from .experience import Experience, PurposeRecord
from .database import MemoryDatabase
from .similarity import (
    calculate_context_similarity,
    calculate_purpose_overlap,
    calculate_means_similarity,
    calculate_experience_similarity
)
from .retrieval import ExperienceRetriever
from .long_term_memory import LongTermMemory, MemorySummary

__all__ = [
    'Experience',
    'PurposeRecord',
    'MemoryDatabase',
    'ExperienceRetriever',
    'LongTermMemory',
    'MemorySummary',
    'calculate_context_similarity',
    'calculate_purpose_overlap',
    'calculate_means_similarity',
    'calculate_experience_similarity'
]

