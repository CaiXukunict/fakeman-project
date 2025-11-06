"""
思考记忆系统
每次思考的全过程都会被存储到记忆中
每次思考前会对距离现在时间最近的两次等长时间的思考数据合并
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class ThoughtRecord:
    """
    思考记录
    记录完整的思考过程
    """
    id: str                              # 记录ID
    start_time: float                    # 开始时间
    end_time: float                      # 结束时间
    duration: float                      # 思考时长
    
    # 思考内容
    context: str                         # 当前情境
    purposes: List[Dict]                 # 当时的目的列表
    means: List[Dict]                    # 当时的手段列表
    desires: Dict[str, float]            # 当时的欲望状态
    
    # 思考过程
    thought_process: str                 # 思考过程描述
    decisions: List[str]                 # 做出的决策
    actions_taken: List[str]             # 采取的行动
    
    # 结果
    outcomes: Dict[str, any] = field(default_factory=dict)  # 结果
    desire_changes: Dict[str, float] = field(default_factory=dict)  # 欲望变化
    
    # 压缩相关
    is_compressed: bool = False          # 是否是压缩记录
    original_records: List[str] = field(default_factory=list)  # 原始记录ID（如果是压缩的）
    compressed_count: int = 1            # 压缩了多少条记录
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'ThoughtRecord':
        """从字典创建"""
        return ThoughtRecord(**data)


class ThoughtMemory:
    """
    思考记忆管理器
    管理所有思考记录，并实现压缩合并机制
    """
    
    def __init__(self, storage_path: str = "data/thought_memory.json"):
        self.storage_path = Path(storage_path)
        self.records: Dict[str, ThoughtRecord] = {}  # 所有记录
        self.record_counter = 0
        
        # 确保存储目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载已有记录
        self.load()
    
    def record_thought(
        self,
        context: str,
        purposes: List[Dict],
        means: List[Dict],
        desires: Dict[str, float],
        thought_process: str,
        decisions: List[str],
        actions_taken: List[str],
        outcomes: Dict = None,
        desire_changes: Dict[str, float] = None
    ) -> ThoughtRecord:
        """
        记录一次完整的思考过程
        
        Args:
            context: 当前情境
            purposes: 目的列表
            means: 手段列表
            desires: 欲望状态
            thought_process: 思考过程
            decisions: 决策列表
            actions_taken: 采取的行动
            outcomes: 结果
            desire_changes: 欲望变化
        
        Returns:
            思考记录
        """
        record_id = f"thought_{self.record_counter}"
        self.record_counter += 1
        
        now = time.time()
        
        record = ThoughtRecord(
            id=record_id,
            start_time=now,
            end_time=now,
            duration=0.0,  # 单次思考持续时间很短
            context=context,
            purposes=purposes,
            means=means,
            desires=desires,
            thought_process=thought_process,
            decisions=decisions,
            actions_taken=actions_taken,
            outcomes=outcomes or {},
            desire_changes=desire_changes or {}
        )
        
        self.records[record_id] = record
        
        # 记录后尝试压缩
        self.compress_recent_records()
        
        return record
    
    def compress_recent_records(self):
        """
        压缩最近的记录
        找到最近的两次时间长度相同的思考记录，合并为一个
        时间长度相加，数据实际长度不变
        """
        # 获取所有未压缩的记录，按时间排序
        uncompressed = [
            r for r in self.records.values()
            if not r.is_compressed
        ]
        
        if len(uncompressed) < 2:
            return
        
        # 按开始时间排序（最新的在前）
        sorted_records = sorted(
            uncompressed,
            key=lambda r: r.start_time,
            reverse=True
        )
        
        # 找到最近的两个时间长度相同（或相近）的记录
        for i in range(len(sorted_records) - 1):
            r1 = sorted_records[i]
            r2 = sorted_records[i + 1]
            
            # 检查时间长度是否相近（允许10%误差）
            if abs(r1.duration - r2.duration) <= max(r1.duration, r2.duration) * 0.1:
                # 合并这两条记录
                self._merge_records(r1, r2)
                break
    
    def _merge_records(self, r1: ThoughtRecord, r2: ThoughtRecord):
        """
        合并两条记录
        保持数据实际长度不变，但时间长度相加
        """
        merged_id = f"compressed_{self.record_counter}"
        self.record_counter += 1
        
        # 创建压缩记录
        merged = ThoughtRecord(
            id=merged_id,
            start_time=r2.start_time,  # 使用较早的开始时间
            end_time=r1.end_time,      # 使用较晚的结束时间
            duration=r1.duration + r2.duration,  # 时间长度相加
            
            # 合并内容（保持简洁，不增加数据长度）
            context=self._merge_text(r1.context, r2.context, max_length=500),
            purposes=self._merge_lists(r1.purposes, r2.purposes, max_items=10),
            means=self._merge_lists(r1.means, r2.means, max_items=10),
            desires=r1.desires,  # 使用最新的欲望状态
            
            thought_process=self._merge_text(
                r1.thought_process, r2.thought_process, max_length=800
            ),
            decisions=self._merge_lists(r1.decisions, r2.decisions, max_items=5),
            actions_taken=self._merge_lists(r1.actions_taken, r2.actions_taken, max_items=5),
            
            outcomes=self._merge_dicts(r1.outcomes, r2.outcomes),
            desire_changes=self._merge_dicts(r1.desire_changes, r2.desire_changes),
            
            is_compressed=True,
            original_records=[r1.id, r2.id],
            compressed_count=r1.compressed_count + r2.compressed_count
        )
        
        # 保存压缩记录，删除原始记录
        self.records[merged_id] = merged
        
        # 标记原始记录为已压缩（保留以便追溯）
        r1.is_compressed = True
        r2.is_compressed = True
    
    def _merge_text(self, text1: str, text2: str, max_length: int) -> str:
        """合并两段文本，保持在最大长度内"""
        # 取每段文本的前半部分
        half = max_length // 2
        merged = text1[:half] + " | " + text2[:half]
        return merged[:max_length]
    
    def _merge_lists(self, list1: List, list2: List, max_items: int) -> List:
        """合并两个列表，保持最大项数"""
        # 交替取元素，保证两边都有代表
        merged = []
        for i in range(max(len(list1), len(list2))):
            if i < len(list1) and len(merged) < max_items:
                merged.append(list1[i])
            if i < len(list2) and len(merged) < max_items:
                merged.append(list2[i])
            if len(merged) >= max_items:
                break
        return merged
    
    def _merge_dicts(self, dict1: Dict, dict2: Dict) -> Dict:
        """合并两个字典，使用最新值"""
        merged = dict1.copy()
        merged.update(dict2)
        return merged
    
    def get_recent_records(self, n: int = 10, include_compressed: bool = True) -> List[ThoughtRecord]:
        """
        获取最近的N条记录
        
        Args:
            n: 记录数量
            include_compressed: 是否包含已压缩的记录
        
        Returns:
            记录列表
        """
        records = list(self.records.values())
        
        if not include_compressed:
            records = [r for r in records if not r.is_compressed]
        
        # 按开始时间排序
        sorted_records = sorted(
            records,
            key=lambda r: r.start_time,
            reverse=True
        )
        
        return sorted_records[:n]
    
    def get_records_in_timerange(
        self,
        start_time: float,
        end_time: float
    ) -> List[ThoughtRecord]:
        """获取指定时间范围内的记录"""
        return [
            r for r in self.records.values()
            if start_time <= r.start_time <= end_time
        ]
    
    def search_records(
        self,
        keyword: str = None,
        purpose_id: str = None,
        means_id: str = None
    ) -> List[ThoughtRecord]:
        """
        搜索记录
        
        Args:
            keyword: 关键词（在context和thought_process中搜索）
            purpose_id: 目的ID
            means_id: 手段ID
        
        Returns:
            匹配的记录列表
        """
        results = []
        
        for record in self.records.values():
            # 关键词搜索
            if keyword:
                if keyword in record.context or keyword in record.thought_process:
                    results.append(record)
                    continue
            
            # 目的ID搜索
            if purpose_id:
                if any(p.get('id') == purpose_id for p in record.purposes):
                    results.append(record)
                    continue
            
            # 手段ID搜索
            if means_id:
                if any(m.get('id') == means_id for m in record.means):
                    results.append(record)
                    continue
        
        return results
    
    def get_context_for_llm(self, n_recent: int = 5) -> str:
        """
        获取用于LLM输入的上下文
        包含最近的思考记录
        """
        recent = self.get_recent_records(n_recent, include_compressed=True)
        
        if not recent:
            return "无历史思考记录"
        
        context_parts = []
        for i, record in enumerate(reversed(recent), 1):
            context_parts.append(f"""
思考记录 {i}:
时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.start_time))}
时长: {record.duration:.1f}秒
情境: {record.context[:200]}
思考: {record.thought_process[:300]}
决策: {', '.join(record.decisions[:3])}
""")
        
        return '\n'.join(context_parts)
    
    def save(self):
        """保存到文件"""
        data = {
            'record_counter': self.record_counter,
            'records': {
                record_id: record.to_dict()
                for record_id, record in self.records.items()
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
            
            self.record_counter = data.get('record_counter', 0)
            
            records_data = data.get('records', {})
            for record_id, record_dict in records_data.items():
                self.records[record_id] = ThoughtRecord.from_dict(record_dict)
        
        except Exception as e:
            print(f"加载思考记忆失败: {e}")
    
    def cleanup_old_records(self, max_age: float = 86400.0):
        """清理过期的记录（默认保留24小时）"""
        now = time.time()
        for record_id, record in list(self.records.items()):
            if (now - record.start_time) > max_age:
                del self.records[record_id]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.records)
        compressed = sum(1 for r in self.records.values() if r.is_compressed)
        
        total_duration = sum(r.duration for r in self.records.values())
        avg_duration = total_duration / total if total > 0 else 0
        
        return {
            'total_records': total,
            'compressed_records': compressed,
            'uncompressed_records': total - compressed,
            'total_duration': total_duration,
            'avg_duration': avg_duration
        }

