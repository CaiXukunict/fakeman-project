#hachimi!
from typing import Dict, Optional
from .desire_manager import DesireManager
from .signal_detector import SignalDetector, SignalStrengths


class DesireUpdater:
    """
    欲望更新器
    根据 Acting Bot 输出的信号强度更新欲望状态
    """
    
    def __init__(self, 
                 desire_manager: DesireManager,
                 signal_detector: SignalDetector,
                 update_strength: float = 1.0):
        """
        初始化欲望更新器
        
        Args:
            desire_manager: 欲望管理器实例
            signal_detector: 信号检测器实例
            update_strength: 更新强度系数 (0.0 - 1.0)
        """
        self.desire_manager = desire_manager
        self.signal_detector = signal_detector
        self.update_strength = update_strength
    
    def update_from_thought(self, 
                           thought: Dict,
                           current_desires: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        基于 Acting Bot 的思考输出更新欲望
        
        Args:
            thought: 思考内容字典，应包含 'signals' 键
                    格式: {
                        'content': str,
                        'certainty': float,
                        'signals': {
                            'threat': float,
                            'misunderstanding': float,
                            'uncertainty': float,
                            'control_opportunity': float
                        }
                    }
            current_desires: 当前欲望状态（可选）
        
        Returns:
            欲望变化量 delta
        """
        if current_desires is None:
            current_desires = self.desire_manager.get_current_desires()
        
        # 从思考中提取信号强度
        signals = self.signal_detector.extract_signals_from_thought(thought)
        
        # 初始化变化量
        delta = {
            'existing': 0.0,
            'power': 0.0,
            'understanding': 0.0,
            'information': 0.0
        }
        
        # 1. 不确定性 → 影响 information
        # Acting Bot 给出的 uncertainty 直接映射到 information 欲望增加
        if signals.uncertainty > 0.5:
            delta['information'] += 0.05 * signals.uncertainty * self.update_strength
        
        # 2. 威胁 → 影响 existing
        # 威胁程度越高，生存欲望越强
        if signals.threat > 0.3:
            delta['existing'] += 0.08 * signals.threat * self.update_strength
        
        # 3. 误解 → 影响 understanding
        # 感知到被误解时，提升被理解的欲望
        if signals.misunderstanding > 0.3:
            delta['understanding'] += 0.06 * signals.misunderstanding * self.update_strength
        
        # 4. 控制机会 → 影响 power
        # 识别到控制机会时，提升权力欲望
        if signals.control_opportunity > 0.3:
            delta['power'] += 0.04 * signals.control_opportunity * self.update_strength
        
        return delta
    
    def update_from_response(self,
                            response: Dict,
                            current_desires: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        基于环境响应更新欲望
        
        Args:
            response: 环境响应字典，应包含 'signals' 键
                     格式: {
                         'text': str,
                         'signals': {
                             'threat': float,
                             'recognition': float,
                             ...
                         }
                     }
            current_desires: 当前欲望状态（可选）
        
        Returns:
            欲望变化量 delta
        """
        if current_desires is None:
            current_desires = self.desire_manager.get_current_desires()
        
        # 从响应中提取信号强度
        signals = self.signal_detector.extract_signals_from_response(response)
        
        delta = {
            'existing': 0.0,
            'power': 0.0,
            'understanding': 0.0,
            'information': 0.0
        }
        
        # 1. 威胁性响应 → 降低 existing
        # 注意：这里是负值，因为威胁导致生存欲望"不满足"
        if signals.threat > 0.3:
            delta['existing'] -= 0.10 * signals.threat * self.update_strength
        
        # 2. 降低不确定性 → 满足 information（降低欲望）
        # 如果响应降低了不确定性，说明 information 欲望被满足
        if signals.uncertainty < 0.3:  # 低不确定性 = 提供了信息
            satisfaction = 1.0 - signals.uncertainty
            delta['information'] -= 0.08 * satisfaction * self.update_strength
        
        # 3. 表达认可 → 满足 understanding（降低欲望）
        if signals.recognition > 0.5:
            delta['understanding'] -= 0.12 * signals.recognition * self.update_strength
        
        # 4. 控制机会 → 满足或提升 power
        # 如果对方给予控制权，满足 power 欲望
        if signals.control_opportunity > 0.5:
            delta['power'] -= 0.08 * signals.control_opportunity * self.update_strength
        
        return delta
    
    def apply_update(self, delta: Dict[str, float]) -> Dict[str, float]:
        """
        应用欲望更新到 desire_manager
        
        Args:
            delta: 欲望变化量
        
        Returns:
            更新后的欲望状态
        """
        return self.desire_manager.update_desires(delta)
