"""
FakeMan 思考压缩模块
提供思考内容的压缩、摘要和因果提取功能
"""

from .thought_compressor import ThoughtCompressor
from .weighted_compressor import WeightedMemoryCompressor

__all__ = ['ThoughtCompressor', 'WeightedMemoryCompressor']

