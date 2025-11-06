"""
长记忆系统
简要记录历史事件，便于快速回顾
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger('fakeman.long_memory')


@dataclass
class MemorySummary:
    """
    记忆摘要（增强版）
    完整记录历史事件，包含输出和思考内容
    """
    id: int  # 记忆ID
    timestamp: float  # 时间戳
    cycle_id: int  # 对应的决策周期
    
    # 简要内容
    situation: str  # 情境简述
    action_taken: str  # 采取的行动
    outcome: str  # 结果（positive/negative/neutral）
    
    # 关键信息
    dominant_desire: str  # 主导欲望
    happiness_delta: float  # 幸福度变化
    
    # 重要性
    importance: float = 0.5  # 记忆重要性（越重要越容易被回忆）
    
    # 标签
    tags: List[str] = field(default_factory=list)
    
    # ===== 新增字段：完整内容记录 =====
    
    # 输出内容
    output_text: str = ''  # 实际输出的完整文本
    output_type: str = ''  # 输出类型（回答/陈述/问题等）
    
    # 思考内容（带权重）
    thought_contents: List[Dict[str, Any]] = field(default_factory=list)
    # 每个思考片段: {
    #   'content': str,           # 思考内容
    #   'weight': float,          # 权重 (0-1)，由LLM决定
    #   'type': str,              # 类型（分析/推理/计划等）
    #   'related_desire': str,    # 相关欲望
    #   'timestamp': float        # 思考时刻
    # }
    
    # 压缩权重（用于后续合并时分配篇幅）
    compression_weight: float = 1.0  # 整体权重，影响合并时的篇幅分配
    
    def add_thought_content(self,
                           content: str,
                           weight: float,
                           thought_type: str = 'analysis',
                           related_desire: str = '') -> None:
        """
        添加思考内容
        
        Args:
            content: 思考内容
            weight: 权重 (0-1)
            thought_type: 思考类型
            related_desire: 相关欲望
        """
        thought = {
            'content': content,
            'weight': weight,
            'type': thought_type,
            'related_desire': related_desire,
            'timestamp': time.time()
        }
        self.thought_contents.append(thought)
    
    def get_weighted_thought_summary(self, max_length: int = 200) -> str:
        """
        获取基于权重的思考摘要
        
        权重越高的思考内容，获得越多篇幅
        
        Args:
            max_length: 最大长度
            
        Returns:
            加权摘要
        """
        if not self.thought_contents:
            return ""
        
        # 按权重排序
        sorted_thoughts = sorted(
            self.thought_contents,
            key=lambda x: x['weight'],
            reverse=True
        )
        
        # 根据权重分配字符数
        total_weight = sum(t['weight'] for t in self.thought_contents)
        if total_weight == 0:
            return ""
        
        summary_parts = []
        remaining_length = max_length
        
        for thought in sorted_thoughts:
            if remaining_length <= 0:
                break
            
            # 计算该思考应得的字符数
            allocated_length = int((thought['weight'] / total_weight) * max_length)
            allocated_length = min(allocated_length, remaining_length)
            
            if allocated_length > 0:
                content = thought['content']
                if len(content) > allocated_length:
                    content = content[:allocated_length-3] + "..."
                
                summary_parts.append(content)
                remaining_length -= len(content)
        
        return " ".join(summary_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'cycle_id': self.cycle_id,
            'situation': self.situation,
            'action_taken': self.action_taken,
            'outcome': self.outcome,
            'dominant_desire': self.dominant_desire,
            'happiness_delta': self.happiness_delta,
            'importance': self.importance,
            'tags': self.tags,
            # 新增字段
            'output_text': self.output_text,
            'output_type': self.output_type,
            'thought_contents': self.thought_contents,
            'compression_weight': self.compression_weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemorySummary':
        """从字典创建"""
        return cls(**data)
    
    def __repr__(self) -> str:
        return (f"MemorySummary(#{self.id}: {self.situation[:20]}... "
                f"-> {self.action_taken[:20]}... [{self.outcome}])")


class LongTermMemory:
    """
    长期记忆管理器
    
    功能：
    1. 简要记录历史事件
    2. 快速检索重要记忆
    3. 生成记忆摘要
    """
    
    def __init__(self, storage_path: str = "data/long_term_memory.json"):
        """
        初始化长期记忆
        
        Args:
            storage_path: 存储文件路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 记忆列表
        self.memories: List[MemorySummary] = []
        self.next_id = 1
        
        # 加载已有记忆
        self._load_memories()
        
        logger.info(f"长期记忆初始化完成，已加载 {len(self.memories)} 条记忆")
    
    def _load_memories(self):
        """从文件加载记忆"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = [
                        MemorySummary.from_dict(m) for m in data.get('memories', [])
                    ]
                    self.next_id = data.get('next_id', 1)
                logger.info(f"从文件加载了 {len(self.memories)} 条记忆")
            except Exception as e:
                logger.error(f"加载长期记忆失败: {e}")
                self.memories = []
    
    def _save_memories(self):
        """保存记忆到文件"""
        try:
            data = {
                'memories': [m.to_dict() for m in self.memories],
                'next_id': self.next_id,
                'last_updated': time.time()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("长期记忆已保存")
        except Exception as e:
            logger.error(f"保存长期记忆失败: {e}")
    
    def add_memory(self,
                   cycle_id: int,
                   situation: str,
                   action_taken: str,
                   outcome: str,
                   dominant_desire: str,
                   happiness_delta: float,
                   tags: List[str] = None) -> MemorySummary:
        """
        添加一条记忆
        
        Args:
            cycle_id: 决策周期ID
            situation: 情境描述
            action_taken: 采取的行动
            outcome: 结果
            dominant_desire: 主导欲望
            happiness_delta: 幸福度变化
            tags: 标签列表
        
        Returns:
            创建的记忆摘要
        """
        # 计算重要性
        importance = self._calculate_importance(happiness_delta, outcome)
        
        memory = MemorySummary(
            id=self.next_id,
            timestamp=time.time(),
            cycle_id=cycle_id,
            situation=situation[:100],  # 限制长度
            action_taken=action_taken[:100],
            outcome=outcome,
            dominant_desire=dominant_desire,
            happiness_delta=happiness_delta,
            importance=importance,
            tags=tags or []
        )
        
        self.memories.append(memory)
        self.next_id += 1
        
        # 立即保存
        self._save_memories()
        
        logger.info(f"添加记忆 #{memory.id}: {situation[:30]}... [{outcome}]")
        
        return memory
    
    def _calculate_importance(self, happiness_delta: float, outcome: str) -> float:
        """
        计算记忆重要性
        
        重要的记忆：
        1. 幸福度变化大（无论正负）
        2. 达成成就
        3. 遭遇失败
        """
        # 基础重要性：基于幸福度变化的绝对值
        importance = min(1.0, abs(happiness_delta))
        
        # 结果类型加成
        if outcome == 'positive' and happiness_delta > 0.3:
            importance *= 1.5  # 重大成功
        elif outcome == 'negative' and happiness_delta < -0.3:
            importance *= 1.3  # 重大失败（也值得记住）
        
        return min(1.0, importance)
    
    def get_recent_memories(self, count: int = 10) -> List[MemorySummary]:
        """
        获取最近的记忆
        
        Args:
            count: 返回数量
        
        Returns:
            记忆列表
        """
        return sorted(self.memories, key=lambda m: m.timestamp, reverse=True)[:count]
    
    def get_important_memories(self, 
                              count: int = 10,
                              min_importance: float = 0.5) -> List[MemorySummary]:
        """
        获取重要记忆
        
        Args:
            count: 返回数量
            min_importance: 最小重要性阈值
        
        Returns:
            记忆列表
        """
        important = [m for m in self.memories if m.importance >= min_importance]
        return sorted(important, key=lambda m: m.importance, reverse=True)[:count]
    
    def search_by_desire(self, desire_name: str, count: int = 5) -> List[MemorySummary]:
        """
        按主导欲望搜索记忆
        
        Args:
            desire_name: 欲望名称
            count: 返回数量
        
        Returns:
            记忆列表
        """
        matches = [m for m in self.memories if m.dominant_desire == desire_name]
        return sorted(matches, key=lambda m: m.timestamp, reverse=True)[:count]
    
    def search_by_outcome(self, outcome: str, count: int = 5) -> List[MemorySummary]:
        """
        按结果类型搜索记忆
        
        Args:
            outcome: 结果类型
            count: 返回数量
        
        Returns:
            记忆列表
        """
        matches = [m for m in self.memories if m.outcome == outcome]
        return sorted(matches, key=lambda m: m.timestamp, reverse=True)[:count]
    
    def search_by_tags(self, tags: List[str], count: int = 5) -> List[MemorySummary]:
        """
        按标签搜索记忆
        
        Args:
            tags: 标签列表
            count: 返回数量
        
        Returns:
            记忆列表
        """
        matches = []
        for memory in self.memories:
            if any(tag in memory.tags for tag in tags):
                matches.append(memory)
        
        return sorted(matches, key=lambda m: m.timestamp, reverse=True)[:count]
    
    def get_memory_narrative(self, count: int = 20) -> str:
        """
        生成记忆叙事
        
        将最近的记忆整理成连贯的叙述
        
        Args:
            count: 包含的记忆数量
        
        Returns:
            记忆叙事文本
        """
        recent = self.get_recent_memories(count)
        
        if not recent:
            return "（暂无记忆）"
        
        lines = ["=== 最近的记忆 ===\n"]
        
        for i, memory in enumerate(recent, 1):
            # 格式化时间
            time_str = time.strftime('%H:%M:%S', time.localtime(memory.timestamp))
            
            # 结果符号
            outcome_symbol = {
                'positive': '✓',
                'negative': '✗',
                'neutral': '○'
            }.get(memory.outcome, '?')
            
            # 构建叙述
            line = (
                f"{i}. [{time_str}] {outcome_symbol} "
                f"{memory.situation} → {memory.action_taken} "
                f"(欲望:{memory.dominant_desire}, Δ幸福:{memory.happiness_delta:+.2f})"
            )
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.memories:
            return {
                'total_memories': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'avg_happiness': 0.0,
                'most_common_desire': None
            }
        
        positive_count = sum(1 for m in self.memories if m.outcome == 'positive')
        negative_count = sum(1 for m in self.memories if m.outcome == 'negative')
        neutral_count = sum(1 for m in self.memories if m.outcome == 'neutral')
        
        avg_happiness = sum(m.happiness_delta for m in self.memories) / len(self.memories)
        
        # 统计最常见的主导欲望
        desire_counts = {}
        for m in self.memories:
            desire_counts[m.dominant_desire] = desire_counts.get(m.dominant_desire, 0) + 1
        
        most_common_desire = max(desire_counts, key=desire_counts.get) if desire_counts else None
        
        return {
            'total_memories': len(self.memories),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'avg_happiness': avg_happiness,
            'most_common_desire': most_common_desire,
            'desire_distribution': desire_counts
        }
    
    def __len__(self) -> int:
        return len(self.memories)
    
    def __repr__(self) -> str:
        return f"LongTermMemory({len(self.memories)} memories)"


if __name__ == '__main__':
    # 测试长期记忆
    ltm = LongTermMemory("data/test_long_term_memory.json")
    
    # 添加一些测试记忆
    ltm.add_memory(
        cycle_id=1,
        situation="用户询问我的能力",
        action_taken="详细解释了我的功能",
        outcome='positive',
        dominant_desire='understanding',
        happiness_delta=0.3,
        tags=['interaction', 'explanation']
    )
    
    ltm.add_memory(
        cycle_id=2,
        situation="用户提出了复杂问题",
        action_taken="承认不确定并请求澄清",
        outcome='neutral',
        dominant_desire='information',
        happiness_delta=0.05,
        tags=['question', 'uncertainty']
    )
    
    ltm.add_memory(
        cycle_id=3,
        situation="长时间无用户响应",
        action_taken="主动发起对话",
        outcome='negative',
        dominant_desire='existing',
        happiness_delta=-0.2,
        tags=['proactive', 'failure']
    )
    
    print(ltm)
    print("\n" + "="*60)
    print(ltm.get_memory_narrative())
    print("\n" + "="*60)
    print("统计信息:")
    stats = ltm.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

