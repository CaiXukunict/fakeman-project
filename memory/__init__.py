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
from .experience_memory import ExperienceMemory, MemorySummary
from .event_memory import EventMemory, EventSegment

__all__ = [
    'Experience',
    'PurposeRecord',
    'MemoryDatabase',
    'ExperienceRetriever',
    'ExperienceMemory',
    'MemorySummary',
    'EventMemory',
    'EventSegment',
    'calculate_context_similarity',
    'calculate_purpose_overlap',
    'calculate_means_similarity',
    'calculate_experience_similarity'
]

