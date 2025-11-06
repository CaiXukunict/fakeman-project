"""
手段管理系统
根据目的生成手段，计算手段的重要性
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Means:
    """
    手段数据结构
    手段是达成目的的具体行动方案
    """
    id: str                              # 手段ID
    description: str                     # 手段描述
    target_purposes: List[str]           # 目标目的ID列表
    
    # 重要性计算
    # 手段重要性 = Σ(手段对目的i的重要性 × 目的i的bias)
    importance_to_purposes: Dict[str, float] = field(default_factory=dict)  # 对各目的的重要性
    total_importance: float = 0.0        # 总重要性
    
    # 状态
    created_time: float = field(default_factory=time.time)
    execution_count: int = 0             # 执行次数
    success_count: int = 0               # 成功次数
    
    # 预期效果
    expected_outcomes: Dict[str, float] = field(default_factory=dict)
    
    def calculate_total_importance(self, purposes: Dict) -> float:
        """
        计算手段的总重要性
        重要性 = Σ(对目的i的重要性 × 目的i的bias)
        同时满足多个目的的手段重要性会叠加
        """
        total = 0.0
        for purpose_id, importance in self.importance_to_purposes.items():
            if purpose_id in purposes:
                purpose = purposes[purpose_id]
                total += importance * purpose.bias
        
        self.total_importance = total
        return total
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.execution_count == 0:
            return 0.5  # 默认50%
        return self.success_count / self.execution_count
    
    def record_execution(self, success: bool):
        """记录执行结果"""
        self.execution_count += 1
        if success:
            self.success_count += 1


class MeansManager:
    """
    手段管理器
    负责生成和管理所有手段
    """
    
    def __init__(self, config):
        self.config = config
        self.means: Dict[str, Means] = {}  # 所有手段
        self.means_counter = 0
    
    def generate_means_for_purposes(
        self,
        purposes: List,  # Purpose对象列表
        llm_client,
        context: str = ""
    ) -> List[Means]:
        """
        为一组目的生成手段
        每次生成的手段必须包括对所有目的的满足
        可以有多个手段分别满足一部分目的
        
        Args:
            purposes: 目的列表
            llm_client: LLM客户端
            context: 当前情境
        
        Returns:
            生成的手段列表
        """
        if not purposes:
            return []
        
        # 构建prompt
        purposes_desc = []
        for i, purpose in enumerate(purposes, 1):
            purposes_desc.append(
                f"{i}. [{purpose.id}] {purpose.description}\n"
                f"   - 预期满足: {purpose.expected_desire_satisfaction}\n"
                f"   - Bias: {purpose.bias:.3f}"
            )
        
        prompt = f"""
请为以下目的生成具体的行动手段：

当前情境：
{context}

目的列表：
{''.join(purposes_desc)}

要求：
1. 生成的手段必须覆盖所有目的（可以一个手段满足多个目的，也可以多个手段分别满足）
2. 对每个手段，评估它对每个目的的重要性（0-1）
3. 手段必须是具体可执行的行动
4. 同时满足多个目的的手段会获得更高的总重要性

请按以下格式输出（每个手段一行）：
手段描述 | 目的ID列表（逗号分隔） | 对各目的的重要性（逗号分隔，对应目的列表）

示例：
主动询问用户需求 | primary_0,advanced_1 | 0.8,0.6
"""
        
        response = llm_client.generate(prompt, max_tokens=800)
        
        # 解析响应生成手段
        generated_means = []
        purpose_dict = {p.id: p for p in purposes}
        
        for line in response.strip().split('\n'):
            if '|' not in line:
                continue
            
            try:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 3:
                    continue
                
                description = parts[0]
                purpose_ids = [pid.strip() for pid in parts[1].split(',')]
                importances = [float(imp.strip()) for imp in parts[2].split(',')]
                
                # 验证目的ID有效
                valid_purpose_ids = [pid for pid in purpose_ids if pid in purpose_dict]
                if not valid_purpose_ids:
                    continue
                
                # 创建手段
                means = self.create_means(
                    description=description,
                    target_purposes=valid_purpose_ids,
                    importance_to_purposes=dict(zip(valid_purpose_ids, importances[:len(valid_purpose_ids)])),
                    purpose_objects=purpose_dict
                )
                
                generated_means.append(means)
                
            except Exception as e:
                # 解析失败，跳过这一行
                continue
        
        return generated_means
    
    def create_means(
        self,
        description: str,
        target_purposes: List[str],
        importance_to_purposes: Dict[str, float],
        purpose_objects: Dict
    ) -> Means:
        """
        创建手段
        
        Args:
            description: 手段描述
            target_purposes: 目标目的ID列表
            importance_to_purposes: 对各目的的重要性
            purpose_objects: 目的对象字典
        """
        means_id = f"means_{self.means_counter}"
        self.means_counter += 1
        
        means = Means(
            id=means_id,
            description=description,
            target_purposes=target_purposes,
            importance_to_purposes=importance_to_purposes
        )
        
        # 计算总重要性
        means.calculate_total_importance(purpose_objects)
        
        self.means[means_id] = means
        return means
    
    def get_all_means(self) -> List[Means]:
        """获取所有手段"""
        return list(self.means.values())
    
    def get_means_for_purpose(self, purpose_id: str) -> List[Means]:
        """获取满足特定目的的所有手段"""
        return [m for m in self.means.values() 
                if purpose_id in m.target_purposes]
    
    def get_top_means(self, n: int = 5) -> List[Means]:
        """获取重要性最高的N个手段"""
        sorted_means = sorted(
            self.means.values(),
            key=lambda m: m.total_importance,
            reverse=True
        )
        return sorted_means[:n]
    
    def update_means_importance(self, purpose_objects: Dict):
        """
        更新所有手段的重要性
        当目的的bias变化时需要调用
        """
        for means in self.means.values():
            means.calculate_total_importance(purpose_objects)
    
    def remove_means_for_purpose(self, purpose_id: str) -> List[str]:
        """
        移除与某个目的相关的手段
        返回被移除的手段ID列表
        """
        removed = []
        for means_id, means in list(self.means.items()):
            # 如果手段只为这一个目的服务，则删除
            if purpose_id in means.target_purposes and len(means.target_purposes) == 1:
                del self.means[means_id]
                removed.append(means_id)
            # 如果手段为多个目的服务，只移除对这个目的的关联
            elif purpose_id in means.target_purposes:
                means.target_purposes.remove(purpose_id)
                if purpose_id in means.importance_to_purposes:
                    del means.importance_to_purposes[purpose_id]
        
        return removed
    
    def check_coverage(self, purposes: List) -> Dict[str, bool]:
        """
        检查手段是否覆盖所有目的
        
        Returns:
            {purpose_id: 是否被覆盖}
        """
        coverage = {}
        for purpose in purposes:
            purpose_id = purpose.id
            covered = any(purpose_id in means.target_purposes 
                         for means in self.means.values())
            coverage[purpose_id] = covered
        
        return coverage
    
    def get_uncovered_purposes(self, purposes: List) -> List:
        """获取未被手段覆盖的目的"""
        coverage = self.check_coverage(purposes)
        return [p for p in purposes if not coverage.get(p.id, False)]
    
    def cleanup_invalid_means(self, valid_purpose_ids: set):
        """清理指向无效目的的手段"""
        for means_id, means in list(self.means.items()):
            # 移除无效的目的引用
            means.target_purposes = [
                pid for pid in means.target_purposes 
                if pid in valid_purpose_ids
            ]
            
            # 如果手段不再指向任何目的，删除它
            if not means.target_purposes:
                del self.means[means_id]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.means:
            return {
                'total': 0,
                'avg_importance': 0.0,
                'avg_success_rate': 0.0,
                'total_executions': 0
            }
        
        return {
            'total': len(self.means),
            'avg_importance': sum(m.total_importance for m in self.means.values()) / len(self.means),
            'avg_success_rate': sum(m.get_success_rate() for m in self.means.values()) / len(self.means),
            'total_executions': sum(m.execution_count for m in self.means.values())
        }

