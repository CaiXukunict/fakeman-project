"""
目的管理系统
管理原始目的和高级目的，包括目的的创建、正当性检查、bias计算
"""

import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class PurposeType(Enum):
    """目的类型"""
    PRIMARY = "primary"    # 原始目的（由基础欲望生成）
    ADVANCED = "advanced"  # 高级目的（由手段相关欲望生成）


class DesireType(Enum):
    """欲望类型"""
    # 基础欲望（不基于手段）
    EXISTING = "existing"        # 维持存在
    UNDERSTANDING = "understanding"  # 获得认可
    # 手段相关欲望
    INFORMATION = "information"   # 减少不确定性
    POWER = "power"              # 增加手段


@dataclass
class Purpose:
    """
    目的数据结构
    
    目的必须是可通过干涉达成的事件
    """
    id: str                              # 目的ID
    description: str                     # 目的描述
    type: PurposeType                    # 目的类型
    source_desires: List[DesireType]     # 来源欲望
    expected_desire_satisfaction: Dict[str, float]  # 预期满足的欲望值
    
    # Bias相关
    achievability: float = 0.5           # 可达成性 (0-1)
    time_required: float = 1.0           # 需要时间（相对单位）
    bias: float = 0.5                    # 综合bias
    
    # 高级目的特有
    parent_purpose_id: Optional[str] = None  # 父目的ID（高级目的）
    related_means: List[str] = field(default_factory=list)  # 相关手段
    
    # 状态
    created_time: float = field(default_factory=time.time)
    last_check_time: float = field(default_factory=time.time)
    is_legitimate: bool = True           # 是否正当
    check_count: int = 0                 # 检查次数
    
    def calculate_bias(self) -> float:
        """
        计算目的的bias
        bias = achievability * (1 / (1 + time_required))
        越不可能达成的bias越低，需要时间越长的bias越低
        """
        time_factor = 1.0 / (1.0 + self.time_required)
        self.bias = self.achievability * time_factor
        return self.bias
    
    def get_total_satisfaction(self) -> float:
        """获取总满足度（叠加计算）"""
        return sum(self.expected_desire_satisfaction.values())
    
    def is_expired(self, max_age: float = 3600.0) -> bool:
        """检查目的是否过期"""
        return (time.time() - self.created_time) > max_age


class PurposeManager:
    """
    目的管理器
    负责管理所有原始目的和高级目的
    """
    
    def __init__(self, config):
        self.config = config
        self.purposes: Dict[str, Purpose] = {}  # 所有目的
        self.purpose_counter = 0
        
        # 基础欲望列表
        self.base_desires = {DesireType.EXISTING, DesireType.UNDERSTANDING}
        # 手段相关欲望列表
        self.means_desires = {DesireType.INFORMATION, DesireType.POWER}
    
    def create_primary_purpose(
        self,
        description: str,
        source_desires: List[DesireType],
        expected_satisfaction: Dict[str, float],
        achievability: float = 0.5,
        time_required: float = 1.0
    ) -> Purpose:
        """
        创建原始目的
        由基础欲望（existing, understanding）生成
        作为长期规划存在
        """
        # 验证来源欲望必须是基础欲望
        for desire in source_desires:
            if desire not in self.base_desires:
                raise ValueError(f"原始目的只能由基础欲望生成: {desire}")
        
        purpose_id = f"primary_{self.purpose_counter}"
        self.purpose_counter += 1
        
        purpose = Purpose(
            id=purpose_id,
            description=description,
            type=PurposeType.PRIMARY,
            source_desires=source_desires,
            expected_desire_satisfaction=expected_satisfaction,
            achievability=achievability,
            time_required=time_required
        )
        
        purpose.calculate_bias()
        self.purposes[purpose_id] = purpose
        
        return purpose
    
    def create_advanced_purpose(
        self,
        description: str,
        source_desire: DesireType,
        parent_purpose_id: str,
        related_means: List[str],
        expected_satisfaction: Dict[str, float],
        achievability: float = 0.5,
        time_required: float = 1.0
    ) -> Purpose:
        """
        创建高级目的
        由手段相关欲望（information, power）基于原始目的生成
        """
        # 验证来源欲望必须是手段相关欲望
        if source_desire not in self.means_desires:
            raise ValueError(f"高级目的只能由手段相关欲望生成: {source_desire}")
        
        # 验证父目的存在
        if parent_purpose_id not in self.purposes:
            raise ValueError(f"父目的不存在: {parent_purpose_id}")
        
        purpose_id = f"advanced_{self.purpose_counter}"
        self.purpose_counter += 1
        
        purpose = Purpose(
            id=purpose_id,
            description=description,
            type=PurposeType.ADVANCED,
            source_desires=[source_desire],
            expected_desire_satisfaction=expected_satisfaction,
            parent_purpose_id=parent_purpose_id,
            related_means=related_means,
            achievability=achievability,
            time_required=time_required
        )
        
        purpose.calculate_bias()
        self.purposes[purpose_id] = purpose
        
        return purpose
    
    def check_legitimacy(
        self,
        purpose_id: str,
        current_desires: Dict[str, float],
        llm_client
    ) -> bool:
        """
        检查目的的正当性
        只有当判断确定目的不会给欲望带来正反馈时，才会取消
        
        Args:
            purpose_id: 目的ID
            current_desires: 当前欲望状态
            llm_client: LLM客户端用于判断
        
        Returns:
            是否正当
        """
        if purpose_id not in self.purposes:
            return False
        
        purpose = self.purposes[purpose_id]
        purpose.last_check_time = time.time()
        purpose.check_count += 1
        
        # 构建检查prompt
        prompt = f"""
请判断以下目的是否正当（是否能给欲望带来正反馈）：

目的描述: {purpose.description}
目的类型: {purpose.type.value}
来源欲望: {[d.value for d in purpose.source_desires]}
预期满足: {purpose.expected_desire_satisfaction}

当前欲望状态:
{current_desires}

判断标准：
1. 这个目的是否可能让相关欲望得到满足？
2. 这个目的是否有明显的负面影响？
3. 这个目的在当前情况下是否仍然有意义？

请只回答"正当"或"不正当"，并简要说明理由。
"""
        
        response = llm_client.generate(prompt, max_tokens=200)
        
        # 解析响应
        is_legitimate = "正当" in response and "不正当" not in response
        purpose.is_legitimate = is_legitimate
        
        # 如果父目的不正当，高级目的也不正当
        if purpose.type == PurposeType.ADVANCED and purpose.parent_purpose_id:
            parent = self.purposes.get(purpose.parent_purpose_id)
            if parent and not parent.is_legitimate:
                purpose.is_legitimate = False
        
        return purpose.is_legitimate
    
    def remove_illegitimate_purposes(self) -> List[str]:
        """
        移除所有非正当的目的
        返回被移除的目的ID列表
        """
        removed = []
        for purpose_id, purpose in list(self.purposes.items()):
            if not purpose.is_legitimate:
                # 同时移除依赖此目的的高级目的
                self._remove_dependent_purposes(purpose_id)
                del self.purposes[purpose_id]
                removed.append(purpose_id)
        
        return removed
    
    def _remove_dependent_purposes(self, parent_id: str):
        """移除依赖某个目的的所有高级目的"""
        for purpose_id, purpose in list(self.purposes.items()):
            if (purpose.type == PurposeType.ADVANCED and 
                purpose.parent_purpose_id == parent_id):
                del self.purposes[purpose_id]
    
    def get_all_purposes(self, only_legitimate: bool = True) -> List[Purpose]:
        """获取所有目的"""
        purposes = list(self.purposes.values())
        if only_legitimate:
            purposes = [p for p in purposes if p.is_legitimate]
        return purposes
    
    def get_primary_purposes(self, only_legitimate: bool = True) -> List[Purpose]:
        """获取所有原始目的"""
        purposes = [p for p in self.purposes.values() 
                   if p.type == PurposeType.PRIMARY]
        if only_legitimate:
            purposes = [p for p in purposes if p.is_legitimate]
        return purposes
    
    def get_advanced_purposes(self, only_legitimate: bool = True) -> List[Purpose]:
        """获取所有高级目的"""
        purposes = [p for p in self.purposes.values() 
                   if p.type == PurposeType.ADVANCED]
        if only_legitimate:
            purposes = [p for p in purposes if p.is_legitimate]
        return purposes
    
    def get_purposes_by_desire(
        self, 
        desire: DesireType,
        only_legitimate: bool = True
    ) -> List[Purpose]:
        """获取与特定欲望相关的目的"""
        purposes = [p for p in self.purposes.values() 
                   if desire in p.source_desires]
        if only_legitimate:
            purposes = [p for p in purposes if p.is_legitimate]
        return purposes
    
    def update_purpose_bias(self, purpose_id: str, 
                           achievability: Optional[float] = None,
                           time_required: Optional[float] = None):
        """更新目的的bias"""
        if purpose_id not in self.purposes:
            return
        
        purpose = self.purposes[purpose_id]
        if achievability is not None:
            purpose.achievability = achievability
        if time_required is not None:
            purpose.time_required = time_required
        
        purpose.calculate_bias()
    
    def get_total_satisfaction_by_desires(
        self,
        purposes: List[Purpose]
    ) -> Dict[str, float]:
        """
        计算一组目的对各个欲望的总满足度
        支持叠加计算
        """
        total = {}
        for purpose in purposes:
            for desire, value in purpose.expected_desire_satisfaction.items():
                total[desire] = total.get(desire, 0.0) + value * purpose.bias
        
        return total
    
    def cleanup_old_purposes(self, max_age: float = 3600.0):
        """清理过期的目的"""
        for purpose_id, purpose in list(self.purposes.items()):
            if purpose.is_expired(max_age):
                self._remove_dependent_purposes(purpose_id)
                del self.purposes[purpose_id]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total': len(self.purposes),
            'primary': len([p for p in self.purposes.values() 
                          if p.type == PurposeType.PRIMARY]),
            'advanced': len([p for p in self.purposes.values() 
                           if p.type == PurposeType.ADVANCED]),
            'legitimate': len([p for p in self.purposes.values() 
                             if p.is_legitimate]),
            'illegitimate': len([p for p in self.purposes.values() 
                               if not p.is_legitimate])
        }

