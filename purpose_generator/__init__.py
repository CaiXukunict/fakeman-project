"""
FakeMan 目的生成器模块
包含欲望管理、偏见系统、信号检测和欲望更新等功能
"""

from .desire_manager import DesireManager
from .bias_system import BiasSystem, Experience
from .signal_detector import SignalDetector, SignalStrengths
from .desire_updater import DesireUpdater

__all__ = [
    'DesireManager',
    'BiasSystem',
    'Experience',
    'SignalDetector',
    'SignalStrengths',
    'DesireUpdater'
]

