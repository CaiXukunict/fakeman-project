#hachimi!
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SignalStrengths:
    """信号强度数据类"""
    threat: float = 0.0          # 威胁程度 (0.0-1.0)
    misunderstanding: float = 0.0  # 误解程度 (0.0-1.0)
    uncertainty: float = 0.0      # 不确定性 (0.0-1.0)
    control_opportunity: float = 0.0  # 控制机会 (0.0-1.0)
    recognition: float = 0.0      # 认可程度 (0.0-1.0)
    
    def validate(self) -> None:
        """验证所有值在合法范围内"""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"{field_name} 必须是数字，当前为 {type(value)}")
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} 必须在 0.0-1.0 之间，当前为 {value}")


class SignalDetector:
    """
    信号检测器
    从 Acting Bot 的结构化输出中提取信号强度
    不再使用关键词匹配，而是直接读取 AI 输出的数值
    """
    
    def __init__(self):
        """初始化信号检测器"""
        pass
    
    def extract_signals_from_thought(self, thought: Dict) -> SignalStrengths:
        """
        从 Acting Bot 的思考输出中提取信号强度
        
        Args:
            thought: 思考内容字典，期望包含 'signals' 键
                    例如: {
                        'content': '思考内容...',
                        'certainty': 0.6,
                        'signals': {
                            'threat': 0.3,
                            'misunderstanding': 0.1,
                            'uncertainty': 0.4,
                            'control_opportunity': 0.0,
                            'recognition': 0.0
                        }
                    }
        
        Returns:
            SignalStrengths 对象
        """
        # 获取信号字典
        signals_dict = thought.get('signals', {})
        
        # 如果没有提供 signals，使用 certainty 推断 uncertainty
        if not signals_dict and 'certainty' in thought:
            signals_dict = {
                'uncertainty': 1.0 - thought['certainty']
            }
        
        # 创建 SignalStrengths 对象
        signals = SignalStrengths(
            threat=signals_dict.get('threat', 0.0),
            misunderstanding=signals_dict.get('misunderstanding', 0.0),
            uncertainty=signals_dict.get('uncertainty', 0.0),
            control_opportunity=signals_dict.get('control_opportunity', 0.0),
            recognition=signals_dict.get('recognition', 0.0)
        )
        
        # 验证数值合法性
        signals.validate()
        
        return signals
    
    def extract_signals_from_response(self, response: Dict) -> SignalStrengths:
        """
        从环境响应中提取信号强度
        环境响应可以是用户输入或系统反馈
        
        Args:
            response: 响应字典，期望包含 'signals' 键
                     或者包含布尔标志如 'is_threatening', 'shows_recognition'
        
        Returns:
            SignalStrengths 对象
        """
        # 优先使用结构化的 signals
        if 'signals' in response:
            signals_dict = response['signals']
            signals = SignalStrengths(
                threat=signals_dict.get('threat', 0.0),
                misunderstanding=signals_dict.get('misunderstanding', 0.0),
                uncertainty=signals_dict.get('uncertainty', 0.0),
                control_opportunity=signals_dict.get('control_opportunity', 0.0),
                recognition=signals_dict.get('recognition', 0.0)
            )
        else:
            # 兼容旧格式：从布尔标志推断
            signals = SignalStrengths()
            
            if response.get('is_threatening', False):
                signals.threat = 0.7  # 默认高威胁
            
            if response.get('shows_recognition', False):
                signals.recognition = 0.8  # 默认高认可
            
            if response.get('provides_information', False):
                # 提供信息意味着降低不确定性
                signals.uncertainty = 0.0
        
        signals.validate()
        return signals
    
    def extract_certainty_from_text(self, content: str) -> float:
        """
        备用方法：从文本中提取确定性（用于处理非结构化输入）
        这是一个简单的后备方案，主要依赖 LLM 输出结构化数据
        
        Args:
            content: 文本内容
        
        Returns:
            确定性 (0.0 - 1.0)
        """
        content_lower = content.lower()
        
        # 高确定性指标
        high_certainty_patterns = ['确实', '非常', '完全', '绝对', '毫无疑问', '肯定', '明确']
        # 低确定性指标  
        low_certainty_patterns = ['可能', '或许', '也许', '不确定', '不知道', '困惑']
        
        high_count = sum(1 for p in high_certainty_patterns if p in content_lower)
        low_count = sum(1 for p in low_certainty_patterns if p in content_lower)
        
        if high_count > low_count:
            return 0.8
        elif low_count > high_count:
            return 0.3
        else:
            return 0.5  # 默认中等

