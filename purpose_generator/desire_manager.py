#hachimi!
from typing import Dict, List
from copy import deepcopy
import time


class DesireManager:
    """
    欲望管理器
    负责维护和更新四种基础欲望的状态
    """
    
    def __init__(self, config_or_desires):
        """
        初始化欲望管理器
        
        Args:
            config_or_desires: Config对象或初始欲望字典
        """
        # 兼容Config对象和字典
        if hasattr(config_or_desires, 'desire'):
            # Config对象
            initial_desires = config_or_desires.desire.initial_desires
        else:
            # 字典
            initial_desires = config_or_desires
        
        self.desires = deepcopy(initial_desires)
        self.history = [{'timestamp': time.time(), 'desires': deepcopy(initial_desires)}]
        
        # 验证初始配置
        self._validate_desires(self.desires)
        self.normalize()
    
    def _validate_desires(self, desires: Dict[str, float]) -> None:
        """验证欲望配置是否合法"""
        required_keys = {'existing', 'power', 'understanding', 'information'}
        
        if set(desires.keys()) != required_keys:
            raise ValueError(f"欲望必须包含且仅包含这些键: {required_keys}")
        
        for key, value in desires.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"欲望值必须是数字，但 {key} 是 {type(value)}")
            if value < 0:
                raise ValueError(f"欲望值不能为负数，但 {key} = {value}")
    
    def get_current_desires(self) -> Dict[str, float]:
        """获取当前欲望状态的副本"""
        return deepcopy(self.desires)
    
    def update_desires(self, delta: Dict[str, float]) -> Dict[str, float]:
        """
        更新欲望值
        
        Args:
            delta: 欲望变化量，如 {'existing': -0.1, 'information': +0.05}
        
        Returns:
            更新并归一化后的欲望状态
        """
        # 应用变化
        for key, value in delta.items():
            if key in self.desires:
                self.desires[key] += value
            else:
                print(f"警告: 尝试更新不存在的欲望 '{key}'")
        
        # 确保非负
        for key in self.desires:
            self.desires[key] = max(0.0, self.desires[key])
        
        # 归一化
        self.normalize()
        
        # 记录历史
        self.history.append({
            'timestamp': time.time(),
            'desires': deepcopy(self.desires)
        })
        
        return self.get_current_desires()
    
    def normalize(self) -> None:
        """归一化欲望值，使其总和为 1"""
        total = sum(self.desires.values())
        
        if total == 0:
            # 如果所有欲望都是0，重置为初始状态
            print("警告: 所有欲望都为0，重置为均匀分布")
            for key in self.desires:
                self.desires[key] = 0.25
        else:
            for key in self.desires:
                self.desires[key] /= total
    
    def get_dominant_desire(self) -> str:
        """获取当前主导欲望（值最大的欲望）"""
        return max(self.desires, key=self.desires.get)
    
    def get_desire_value(self, desire_name: str) -> float:
        """获取特定欲望的当前值"""
        return self.desires.get(desire_name, 0.0)
    
    def get_history(self) -> List[Dict]:
        """获取欲望变化历史"""
        return self.history
    
    def get_history_range(self, start_time: float, end_time: float) -> List[Dict]:
        """获取指定时间范围内的欲望历史"""
        return [
            entry for entry in self.history
            if start_time <= entry['timestamp'] <= end_time
        ]
    
    def __repr__(self) -> str:
        desires_str = ", ".join(f"{k}={v:.3f}" for k, v in self.desires.items())
        return f"DesireManager({desires_str})"

