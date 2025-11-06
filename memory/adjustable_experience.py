"""
可审视调整的经验系统
记录手段干涉后的效果，可以根据情况变化被AI审视调整
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Experience:
    """
    经验记录
    记录手段的执行和效果
    """
    id: str                              # 经验ID
    timestamp: float                     # 时间戳
    
    # 手段信息
    means_id: str                        # 手段ID
    means_description: str               # 手段描述
    target_purposes: List[str]           # 目标目的
    
    # 执行情境
    context: str                         # 执行时的情境
    desires_before: Dict[str, float]     # 执行前的欲望状态
    
    # 执行结果
    action_taken: str                    # 实际采取的行动
    outcome: str                         # 结果描述
    desires_after: Dict[str, float]      # 执行后的欲望状态
    desire_changes: Dict[str, float]     # 欲望变化
    
    # 评估
    is_beneficial: bool                  # 是否对欲望有利
    total_satisfaction_delta: float      # 总满足度变化
    
    # 可调整性
    context_factors: List[str] = field(default_factory=list)  # 影响结果的情境因素
    adjustments: List[Dict] = field(default_factory=list)     # 历史调整记录
    adjustment_count: int = 0            # 调整次数
    
    # 验证
    validation_count: int = 0            # 被验证次数
    successful_validations: int = 0      # 成功验证次数
    
    def calculate_satisfaction_delta(self) -> float:
        """计算总满足度变化"""
        total = sum(self.desire_changes.values())
        self.total_satisfaction_delta = total
        self.is_beneficial = total > 0
        return total
    
    def add_adjustment(
        self,
        reason: str,
        factor: str,
        impact: float,
        adjusted_by: str = "AI"
    ):
        """
        添加调整记录
        
        Args:
            reason: 调整原因
            factor: 影响因素
            impact: 影响程度（-1到1）
            adjusted_by: 调整者
        """
        adjustment = {
            'timestamp': time.time(),
            'reason': reason,
            'factor': factor,
            'impact': impact,
            'adjusted_by': adjusted_by
        }
        
        self.adjustments.append(adjustment)
        self.adjustment_count += 1
        
        # 根据调整重新计算满足度
        # 这里简化处理：将影响因素的影响加到总满足度上
        self.total_satisfaction_delta += impact
        self.is_beneficial = self.total_satisfaction_delta > 0
    
    def record_validation(self, success: bool):
        """记录验证结果"""
        self.validation_count += 1
        if success:
            self.successful_validations += 1
    
    def get_reliability(self) -> float:
        """获取可靠性（基于验证结果）"""
        if self.validation_count == 0:
            return 0.5  # 未验证，默认50%
        return self.successful_validations / self.validation_count
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'Experience':
        """从字典创建"""
        return Experience(**data)


class AdjustableExperienceSystem:
    """
    可审视调整的经验系统
    """
    
    def __init__(self, storage_path: str = "data/adjustable_experiences.json"):
        self.storage_path = Path(storage_path)
        self.experiences: Dict[str, Experience] = {}
        self.experience_counter = 0
        
        # 确保存储目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载已有经验
        self.load()
    
    def record_experience(
        self,
        means_id: str,
        means_description: str,
        target_purposes: List[str],
        context: str,
        desires_before: Dict[str, float],
        action_taken: str,
        outcome: str,
        desires_after: Dict[str, float],
        context_factors: List[str] = None
    ) -> Experience:
        """
        记录一次手段执行的经验
        
        Args:
            means_id: 手段ID
            means_description: 手段描述
            target_purposes: 目标目的列表
            context: 执行情境
            desires_before: 执行前欲望
            action_taken: 实际行动
            outcome: 结果
            desires_after: 执行后欲望
            context_factors: 影响因素
        
        Returns:
            经验记录
        """
        exp_id = f"exp_{self.experience_counter}"
        self.experience_counter += 1
        
        # 计算欲望变化
        desire_changes = {
            key: desires_after.get(key, 0) - desires_before.get(key, 0)
            for key in desires_before.keys()
        }
        
        experience = Experience(
            id=exp_id,
            timestamp=time.time(),
            means_id=means_id,
            means_description=means_description,
            target_purposes=target_purposes,
            context=context,
            desires_before=desires_before,
            action_taken=action_taken,
            outcome=outcome,
            desires_after=desires_after,
            desire_changes=desire_changes,
            is_beneficial=False,
            total_satisfaction_delta=0.0,
            context_factors=context_factors or []
        )
        
        # 计算满足度变化
        experience.calculate_satisfaction_delta()
        
        self.experiences[exp_id] = experience
        
        return experience
    
    def review_and_adjust_experiences(
        self,
        llm_client,
        current_context: str,
        recent_n: int = 10
    ) -> List[Experience]:
        """
        审视并调整最近的经验
        当情境发生变化时，AI可以审视经验并调整对结果的评估
        
        Args:
            llm_client: LLM客户端
            current_context: 当前情境
            recent_n: 审视最近N条经验
        
        Returns:
            被调整的经验列表
        """
        # 获取最近的经验
        recent_exps = self.get_recent_experiences(recent_n)
        
        if not recent_exps:
            return []
        
        adjusted = []
        
        for exp in recent_exps:
            # 构建审视prompt
            prompt = f"""
请审视以下经验记录，判断是否需要调整评估：

经验ID: {exp.id}
手段: {exp.means_description}
执行情境: {exp.context}
结果: {exp.outcome}
欲望变化: {exp.desire_changes}
当前评估: {'有利' if exp.is_beneficial else '不利'} (总变化: {exp.total_satisfaction_delta:.3f})

情境因素: {exp.context_factors}
历史调整: {len(exp.adjustments)}次

当前情境:
{current_context}

问题：
1. 考虑当前情境，这个经验的结果评估是否准确？
2. 是否有某些情境因素被低估或高估了？
3. 如果需要调整，应该如何调整？

请按以下格式回答：
需要调整: 是/否
如果需要调整：
- 因素: [影响因素]
- 影响: [+0.X或-0.X]
- 原因: [简要说明]
"""
            
            response = llm_client.generate(prompt, max_tokens=300)
            
            # 解析响应
            if "需要调整: 是" in response or "需要调整：是" in response:
                # 尝试提取调整信息
                try:
                    lines = response.split('\n')
                    factor = ""
                    impact = 0.0
                    reason = ""
                    
                    for line in lines:
                        if "因素:" in line or "因素：" in line:
                            factor = line.split(':', 1)[-1].strip()
                        elif "影响:" in line or "影响：" in line:
                            impact_str = line.split(':', 1)[-1].strip()
                            # 提取数字
                            import re
                            numbers = re.findall(r'[-+]?\d*\.\d+|\d+', impact_str)
                            if numbers:
                                impact = float(numbers[0])
                        elif "原因:" in line or "原因：" in line:
                            reason = line.split(':', 1)[-1].strip()
                    
                    if factor and reason:
                        exp.add_adjustment(
                            reason=reason,
                            factor=factor,
                            impact=impact,
                            adjusted_by="AI"
                        )
                        adjusted.append(exp)
                
                except Exception as e:
                    # 解析失败，跳过
                    continue
        
        return adjusted
    
    def get_experiences_for_means(self, means_id: str) -> List[Experience]:
        """获取特定手段的所有经验"""
        return [
            exp for exp in self.experiences.values()
            if exp.means_id == means_id
        ]
    
    def get_experiences_for_purpose(self, purpose_id: str) -> List[Experience]:
        """获取与特定目的相关的经验"""
        return [
            exp for exp in self.experiences.values()
            if purpose_id in exp.target_purposes
        ]
    
    def get_recent_experiences(self, n: int = 10) -> List[Experience]:
        """获取最近的N条经验"""
        sorted_exps = sorted(
            self.experiences.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_exps[:n]
    
    def get_beneficial_experiences(self) -> List[Experience]:
        """获取所有有利的经验"""
        return [
            exp for exp in self.experiences.values()
            if exp.is_beneficial
        ]
    
    def get_detrimental_experiences(self) -> List[Experience]:
        """获取所有不利的经验"""
        return [
            exp for exp in self.experiences.values()
            if not exp.is_beneficial
        ]
    
    def search_similar_experiences(
        self,
        context: str,
        means_description: str = None,
        min_similarity: float = 0.6
    ) -> List[Experience]:
        """
        搜索相似的经验
        简化实现：基于关键词匹配
        """
        results = []
        
        context_words = set(context.lower().split())
        
        for exp in self.experiences.values():
            # 计算情境相似度
            exp_words = set(exp.context.lower().split())
            similarity = len(context_words & exp_words) / max(len(context_words), len(exp_words))
            
            # 如果指定了手段描述，也要匹配
            if means_description:
                if means_description.lower() not in exp.means_description.lower():
                    continue
            
            if similarity >= min_similarity:
                results.append((exp, similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in results]
    
    def get_context_for_llm(self, n_recent: int = 5) -> str:
        """
        获取用于LLM输入的经验上下文
        """
        recent = self.get_recent_experiences(n_recent)
        
        if not recent:
            return "无历史经验记录"
        
        context_parts = []
        for i, exp in enumerate(reversed(recent), 1):
            adjustment_info = ""
            if exp.adjustment_count > 0:
                adjustment_info = f" (已调整{exp.adjustment_count}次)"
            
            context_parts.append(f"""
经验 {i}: {exp.means_description}{adjustment_info}
情境: {exp.context[:150]}
结果: {'有利' if exp.is_beneficial else '不利'} (变化: {exp.total_satisfaction_delta:+.3f})
可靠性: {exp.get_reliability():.1%}
""")
        
        return '\n'.join(context_parts)
    
    def save(self):
        """保存到文件"""
        data = {
            'experience_counter': self.experience_counter,
            'experiences': {
                exp_id: exp.to_dict()
                for exp_id, exp in self.experiences.items()
            }
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.experience_counter = data.get('experience_counter', 0)
            
            experiences_data = data.get('experiences', {})
            for exp_id, exp_dict in experiences_data.items():
                self.experiences[exp_id] = Experience.from_dict(exp_dict)
        
        except Exception as e:
            print(f"加载经验失败: {e}")
    
    def cleanup_old_experiences(self, max_age: float = 604800.0):
        """清理过期的经验（默认保留7天）"""
        now = time.time()
        for exp_id, exp in list(self.experiences.items()):
            if (now - exp.timestamp) > max_age:
                del self.experiences[exp_id]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.experiences)
        beneficial = len(self.get_beneficial_experiences())
        detrimental = len(self.get_detrimental_experiences())
        
        total_adjustments = sum(exp.adjustment_count for exp in self.experiences.values())
        
        avg_satisfaction = (
            sum(exp.total_satisfaction_delta for exp in self.experiences.values()) / total
            if total > 0 else 0
        )
        
        return {
            'total_experiences': total,
            'beneficial': beneficial,
            'detrimental': detrimental,
            'beneficial_rate': beneficial / total if total > 0 else 0,
            'total_adjustments': total_adjustments,
            'avg_satisfaction_delta': avg_satisfaction
        }

