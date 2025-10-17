"""
FakeMan 工具模块
提供配置、日志、指标计算等通用功能
"""

from .config import Config
from .logger import setup_logger, get_logger

__all__ = ['Config', 'setup_logger', 'get_logger']

