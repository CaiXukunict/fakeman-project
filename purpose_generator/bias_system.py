#hachimi!
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class Experience:
    """
    经验数据类（用于偏见计算）
    简化版本，只包含偏见系统需要的字段
    """
    id: int
    timestamp: float
    action: str
    total_happiness_delta: float
    desire_delta: Dict[str, float]
    
    @property
    def is_positive(self) -> bool:
        """判断是否为正面经验"""
        return self.total_happiness_delta > 0
    
    @property
    def is_negative(self) -> bool:
        """判断是否为负面经验"""
        return self.total_happiness_delta < 0


class BiasSystem:
    """
    偏见系统 - 完整版
    
    实现四种认知偏见：
    1. 损失厌恶（Fear Bias）
    2. 时间折现（Time Bias）
    3. 边际效用递减（Owning Bias）
    4. 可能性偏见（Possibility Bias）
    
    这些偏见共同作用，使系统的决策更接近人类的非理性但适应性强的行为模式。
    """
    
    def __init__(self, bias_params: Dict):
        """
        初始化偏见系统
        
        Args:
            bias_params: 偏见参数配置字典
                {
                    'fear_multiplier': 2.5,
                    'time_discount_rate': 0.1,
                    'owning_decay_rates': {...},
                    'min_experiences_for_reliability': 3
                }
        """
        # 损失厌恶系数
        self.fear_multiplier = bias_params.get('fear_multiplier', 2.5)
        
        # 时间折现率
        self.time_discount_rate = bias_params.get('time_discount_rate', 0.1)
        
        # 边际效用递减率（每种欲望不同）
        self.owning_decay_rates = bias_params.get('owning_decay_rates', {
            'existing': 0.001,      # 维持存在欲望递减最慢
            'power': 0.01,          # 增加手段欲望递减较快
            'understanding': 0.008, # 获得认可欲望
            'information': 0.015    # 减少不确定性欲望递减最快
        })
        
        # 可能性偏见的参数
        self.min_experiences = bias_params.get('min_experiences_for_reliability', 3)
        self.time_decay_rate = bias_params.get('time_decay_rate', 0.001)  # 每秒衰减率
        
        # 统计信息
        self.stats = {
            'fear_bias_applied_count': 0,
            'time_bias_applied_count': 0,
            'owning_bias_applied_count': 0,
            'possibility_calculated_count': 0
        }
    
    # ==========================================
    # 1. 损失厌恶（Fear Bias）
    # ==========================================
    
    def apply_fear_bias(self, value: float, multiplier: Optional[float] = None) -> float:
        """
        应用损失厌恶偏见
        
        负面结果的影响被放大，体现"损失的痛苦 > 等量收益的快乐"
        
        Args:
            value: 原始价值（可以是预期欲望变化）
            multiplier: 可选的自定义系数，如果不提供则使用默认的 fear_multiplier
        
        Returns:
            应用偏见后的价值
            
        Example:
            >>> bias.apply_fear_bias(-0.5)  # 负面价值
            -1.25  # 被放大 2.5 倍
            
            >>> bias.apply_fear_bias(0.5)   # 正面价值
            0.5    # 不变
        """
        if value >= 0:
            return value
        
        multiplier = multiplier or self.fear_multiplier
        self.stats['fear_bias_applied_count'] += 1
        
        return value * multiplier
    
    def calculate_loss_aversion_ratio(self, experiences: List[Experience]) -> float:
        """
        根据历史经验计算动态的损失厌恶比率
        
        如果历史上负面经验导致了严重后果，提高损失厌恶系数
        
        Args:
            experiences: 相关历史经验
            
        Returns:
            动态调整后的损失厌恶系数
        """
        if not experiences:
            return self.fear_multiplier
        
        # 计算负面经验的平均严重程度
        negative_exps = [exp for exp in experiences if exp.is_negative]
        
        if not negative_exps:
            return self.fear_multiplier
        
        avg_negative = np.mean([abs(exp.total_happiness_delta) for exp in negative_exps])
        
        # 如果平均负面影响很大，提高损失厌恶
        if avg_negative > 0.5:
            return self.fear_multiplier * 1.5
        elif avg_negative > 0.3:
            return self.fear_multiplier * 1.2
        else:
            return self.fear_multiplier
    
    # ==========================================
    # 2. 时间折现（Time Bias）
    # ==========================================
    
    def apply_time_bias(self, value: float, time_to_achieve: float) -> float:
        """
        应用时间折现偏见
        
        远期收益的价值被打折，体现"即时满足 > 延迟满足"
        
        公式: discounted_value = value / (1 + r * t)
        其中 r 是折现率，t 是时间
        
        Args:
            value: 原始价值
            time_to_achieve: 实现该价值需要的时间（秒）
        
        Returns:
            折现后的价值
            
        Example:
            >>> bias.apply_time_bias(1.0, 0)     # 立即实现
            1.0
            
            >>> bias.apply_time_bias(1.0, 10)    # 10秒后实现
            0.5   # 价值打折
        """
        if time_to_achieve <= 0:
            return value
        
        self.stats['time_bias_applied_count'] += 1
        
        discounted = value / (1 + self.time_discount_rate * time_to_achieve)
        return discounted
    
    def apply_hyperbolic_discounting(self, value: float, time_to_achieve: float) -> float:
        """
        应用双曲折现（更符合人类实际行为）
        
        双曲折现在近期折扣更陡峭，远期较平缓
        公式: discounted_value = value / (1 + k * t)^α
        
        Args:
            value: 原始价值
            time_to_achieve: 时间（秒）
            
        Returns:
            双曲折现后的价值
        """
        if time_to_achieve <= 0:
            return value
        
        k = self.time_discount_rate
        alpha = 0.7  # 双曲参数，< 1 时为双曲折现
        
        discounted = value / ((1 + k * time_to_achieve) ** alpha)
        return discounted
    
    # ==========================================
    # 3. 边际效用递减（Owning Bias）- 基于可达成性的欲望转移
    # ==========================================
    
    def apply_owning_bias_with_achievability(self,
                                             current_desires: Dict[str, float],
                                             purpose_achievability: Dict[str, float]) -> Dict[str, float]:
        """
        基于可达成性应用边际效用递减
        
        新逻辑：最可能达成的欲望bias降低，更不可能达成的欲望bias增加
        这反映了"容易满足的欲望变得不那么重要，难以满足的欲望变得更重要"
        
        Args:
            current_desires: 当前欲望状态
            purpose_achievability: 各目的（对应欲望）的可达成性
                                   格式: {'existing': 0.8, 'power': 0.3, ...}
                                   值越高表示越容易达成
        
        Returns:
            调整后的欲望状态（已归一化）
            
        Example:
            >>> current = {'existing': 0.4, 'power': 0.2, 'understanding': 0.25, 'information': 0.15}
            >>> achievability = {'existing': 0.8, 'power': 0.2, 'understanding': 0.5, 'information': 0.6}
            >>> # existing 最容易达成，其bias会降低；power 最难达成，其bias会增加
            >>> new = bias.apply_owning_bias_with_achievability(current, achievability)
        """
        if not purpose_achievability:
            return current_desires.copy()
        
        new_desires = current_desires.copy()
        
        # 计算平均可达成性
        avg_achievability = sum(purpose_achievability.values()) / len(purpose_achievability)
        
        # 计算每个欲望应该转移的量
        transfer_amounts = {}
        total_to_transfer = 0.0
        
        for desire_name, achievability in purpose_achievability.items():
            if desire_name not in new_desires:
                continue
            
            # 可达成性高于平均 -> 降低bias（转出）
            # 可达成性低于平均 -> 增加bias（转入）
            deviation = achievability - avg_achievability
            
            # 转移量与可达成性偏差成正比
            transfer_rate = self.owning_decay_rates.get(desire_name, 0.01)
            transfer = deviation * transfer_rate * new_desires[desire_name]
            
            transfer_amounts[desire_name] = transfer
            if transfer > 0:  # 需要转出
                total_to_transfer += transfer
        
        # 应用转移
        for desire_name in new_desires.keys():
            if desire_name in transfer_amounts:
                transfer = transfer_amounts[desire_name]
                
                if transfer > 0:  # 从这个欲望转出
                    new_desires[desire_name] -= transfer
                else:  # 转入这个欲望
                    # 按比例分配转出的总量
                    if total_to_transfer > 0:
                        # 不可达成程度越高，分到的越多
                        achievability = purpose_achievability.get(desire_name, 0.5)
                        weight = (1.0 - achievability)
                        total_weight = sum(
                            (1.0 - purpose_achievability.get(d, 0.5))
                            for d in new_desires.keys()
                            if transfer_amounts.get(d, 0) < 0
                        )
                        if total_weight > 0:
                            new_desires[desire_name] += total_to_transfer * (weight / total_weight)
        
        # 确保非负并归一化
        for key in new_desires:
            new_desires[key] = max(0.0, new_desires[key])
        
        total = sum(new_desires.values())
        if total > 0:
            for key in new_desires:
                new_desires[key] /= total
        
        self.stats['owning_bias_applied_count'] += 1
        
        return new_desires
    
    def apply_owning_bias(self, 
                         desire_name: str, 
                         satisfaction_amount: float, 
                         current_value: float) -> float:
        """
        应用边际效用递减偏见（传统方式，保留用于兼容）
        
        已经被满足的欲望，其权重会降低
        体现"越满足越不在乎"的特性
        
        公式: new_value = current_value * (1 - decay_rate * ln(1 + satisfaction))
        
        Args:
            desire_name: 欲望名称 ('existing', 'power', 'understanding', 'information')
            satisfaction_amount: 满足量（正数）
            current_value: 当前欲望值
        
        Returns:
            应用递减后的新欲望值
            
        Example:
            >>> bias.apply_owning_bias('information', 0.5, 0.8)
            0.78  # information 被满足后，其权重略微降低
        """
        if satisfaction_amount <= 0:
            return current_value
        
        if current_value <= 0:
            return 0.0
        
        decay_rate = self.owning_decay_rates.get(desire_name, 0.01)
        
        # 使用对数函数，满足量越大，递减越明显
        decay = decay_rate * np.log(1 + satisfaction_amount)
        new_value = current_value * (1 - decay)
        
        self.stats['owning_bias_applied_count'] += 1
        
        return max(0.0, new_value)
    
    def apply_owning_bias_batch(self,
                                satisfaction_deltas: Dict[str, float],
                                current_desires: Dict[str, float]) -> Dict[str, float]:
        """
        批量应用边际效用递减（传统方式，保留用于兼容）
        
        对所有被满足的欲望同时应用递减
        
        Args:
            satisfaction_deltas: 各欲望的满足量 {'existing': 0.1, 'power': 0.05, ...}
            current_desires: 当前欲望状态
            
        Returns:
            应用递减后的新欲望状态
        """
        new_desires = current_desires.copy()
        
        for desire_name, satisfaction in satisfaction_deltas.items():
            if satisfaction > 0:  # 只对正向满足应用递减
                current = new_desires.get(desire_name, 0.0)
                new_desires[desire_name] = self.apply_owning_bias(
                    desire_name, 
                    satisfaction, 
                    current
                )
        
        return new_desires
    
    # ==========================================
    # 4. 可能性偏见（Possibility Bias）
    # ==========================================
    
    def calculate_possibility_weight(self, experiences: List[Experience]) -> float:
        """
        计算可能性权重
        
        基于历史经验的成功率、一致性和时效性，评估行动的可靠性
        
        组成部分：
        1. 成功率：正面结果的比例
        2. 一致性：结果的稳定性（标准差的倒数）
        3. 时效性：最近的经验权重更高
        
        Args:
            experiences: 相关历史经验列表
        
        Returns:
            可能性权重 (0.0 - 1.0)
            - 0.0: 完全不可靠
            - 0.5: 中性/未知
            - 1.0: 完全可靠
            
        Example:
            >>> # 20次经验，18次正面
            >>> weight = bias.calculate_possibility_weight(experiences)
            0.85  # 高可靠性
        """
        if not experiences:
            return 0.5  # 无经验时返回中性值
        
        self.stats['possibility_calculated_count'] += 1
        
        # 经验太少，降低权重
        if len(experiences) < self.min_experiences:
            base_weight = 0.3 + 0.1 * len(experiences)
            return min(base_weight, 0.5)
        
        deltas = [exp.total_happiness_delta for exp in experiences]
        
        # 1. 成功率
        success_rate = self._calculate_success_rate(experiences)
        
        # 2. 一致性
        consistency = self._calculate_consistency(deltas)
        
        # 3. 时效性加权的成功率
        weighted_success_rate = self._calculate_time_weighted_success_rate(experiences)
        
        # 4. 综合评分
        # 时效性加权的成功率占 50%，一致性占 30%，原始成功率占 20%
        possibility = (
            0.5 * weighted_success_rate +
            0.3 * consistency +
            0.2 * success_rate
        )
        
        return np.clip(possibility, 0.0, 1.0)
    
    def _calculate_success_rate(self, experiences: List[Experience]) -> float:
        """计算基础成功率"""
        success_count = sum(1 for exp in experiences if exp.is_positive)
        return success_count / len(experiences)
    
    def _calculate_consistency(self, deltas: List[float]) -> float:
        """
        计算一致性分数
        
        一致性高 = 标准差小 = 结果可预测
        """
        if len(deltas) <= 1:
            return 0.5
        
        std_dev = np.std(deltas)
        
        # 标准差越小，一致性越高
        # 使用倒数并归一化
        consistency = 1.0 / (std_dev + 0.1)  # 加0.1避免除零
        consistency = min(consistency, 5.0) / 5.0  # 归一化到 0-1
        
        return consistency
    
    def _calculate_time_weighted_success_rate(self, experiences: List[Experience]) -> float:
        """
        计算时效性加权的成功率
        
        最近的经验权重更高
        """
        now = time.time()
        
        # 计算每个经验的时间权重
        recency_weights = [
            np.exp(-self.time_decay_rate * (now - exp.timestamp))
            for exp in experiences
        ]
        
        # 加权成功率
        success_indicators = [1.0 if exp.is_positive else 0.0 for exp in experiences]
        
        weighted_success = np.average(success_indicators, weights=recency_weights)
        
        return weighted_success
    
    def get_detailed_possibility_analysis(self, experiences: List[Experience]) -> Dict:
        """
        获取可能性权重的详细分析
        
        用于调试和理解系统决策
        
        Returns:
            详细分析字典，包含各个组成部分
        """
        if not experiences:
            return {
                'possibility_weight': 0.5,
                'reason': 'no_experience',
                'experience_count': 0
            }
        
        deltas = [exp.total_happiness_delta for exp in experiences]
        
        success_rate = self._calculate_success_rate(experiences)
        consistency = self._calculate_consistency(deltas)
        weighted_success = self._calculate_time_weighted_success_rate(experiences)
        possibility = self.calculate_possibility_weight(experiences)
        
        return {
            'possibility_weight': possibility,
            'experience_count': len(experiences),
            'success_rate': success_rate,
            'consistency': consistency,
            'time_weighted_success_rate': weighted_success,
            'positive_count': sum(1 for exp in experiences if exp.is_positive),
            'negative_count': sum(1 for exp in experiences if exp.is_negative),
            'std_dev': np.std(deltas),
            'mean_delta': np.mean(deltas),
            'oldest_experience_age': time.time() - min(exp.timestamp for exp in experiences),
            'newest_experience_age': time.time() - max(exp.timestamp for exp in experiences)
        }
    
    # ==========================================
    # 5. 综合应用
    # ==========================================
    
    def apply_all_biases(self, 
                        predicted_value: float,
                        experiences: List[Experience],
                        time_to_achieve: float = 0,
                        use_hyperbolic_discounting: bool = False) -> float:
        """
        应用所有偏见的组合效果
        
        应用顺序：
        1. 可能性偏见（基于经验的可靠性）
        2. 损失厌恶（放大负面价值）
        3. 时间折现（打折延迟价值）
        
        Args:
            predicted_value: 原始预期价值
            experiences: 相关历史经验
            time_to_achieve: 实现该价值需要的时间（秒）
            use_hyperbolic_discounting: 是否使用双曲折现
        
        Returns:
            应用所有偏见后的最终价值
            
        Example:
            >>> predicted = 0.8  # 预期获得 0.8 的价值
            >>> experiences = [...]  # 历史经验显示成功率 90%
            >>> final = bias.apply_all_biases(predicted, experiences, time_to_achieve=5)
            0.65  # 经过可能性、损失厌恶、时间折现后的最终价值
        """
        value = predicted_value
        
        # 1. 可能性偏见
        possibility = self.calculate_possibility_weight(experiences)
        value = value * possibility
        
        # 2. 损失厌恶
        # 如果经验显示高风险，使用动态系数
        if experiences:
            dynamic_fear = self.calculate_loss_aversion_ratio(experiences)
            value = self.apply_fear_bias(value, multiplier=dynamic_fear)
        else:
            value = self.apply_fear_bias(value)
        
        # 3. 时间折现
        if time_to_achieve > 0:
            if use_hyperbolic_discounting:
                value = self.apply_hyperbolic_discounting(value, time_to_achieve)
            else:
                value = self.apply_time_bias(value, time_to_achieve)
        
        return value
    
    def compare_actions(self,
                       action_predictions: Dict[str, Tuple[float, List[Experience], float]]) -> List[Tuple[str, float]]:
        """
        比较多个行动的偏见调整后价值
        
        Args:
            action_predictions: 字典，格式为
                {
                    'action_name': (predicted_value, experiences, time_to_achieve),
                    ...
                }
        
        Returns:
            排序后的 (action_name, final_value) 列表，按价值降序
            
        Example:
            >>> predictions = {
            ...     'ask_question': (0.5, exp_list_1, 0),
            ...     'make_statement': (0.6, exp_list_2, 0),
            ...     'wait': (0.3, exp_list_3, 10)
            ... }
            >>> ranked = bias.compare_actions(predictions)
            [('make_statement', 0.55), ('ask_question', 0.48), ('wait', 0.15)]
        """
        results = []
        
        for action_name, (predicted, experiences, time_delay) in action_predictions.items():
            final_value = self.apply_all_biases(predicted, experiences, time_delay)
            results.append((action_name, final_value))
        
        # 按价值降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    # ==========================================
    # 6. 统计和诊断
    # ==========================================
    
    def get_stats(self) -> Dict:
        """获取偏见系统的统计信息"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0
    
    def __repr__(self) -> str:
        return (f"BiasSystem(fear={self.fear_multiplier}, "
                f"time_discount={self.time_discount_rate}, "
                f"stats={self.stats})")
