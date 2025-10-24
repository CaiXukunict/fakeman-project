"""
事件记忆系统
完整记录思考/行为内容和先后顺序，并通过智能压缩机制管理记忆大小
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import time
from pathlib import Path
from utils.logger import get_logger
from action_model.llm_client import LLMClient

logger = get_logger('fakeman.event_memory')


@dataclass
class EventSegment:
    """
    事件片段
    
    记录一个或多个连续的思考/行动事件
    """
    id: int  # 片段ID
    start_timestamp: float  # 开始时间戳
    end_timestamp: float  # 结束时间戳
    segment_length: int  # 片段包含的原始思考次数（用于判断是否可以合并）
    
    # 事件内容
    events: List[Dict[str, Any]]  # 事件列表，每个事件包含思考、行动、结果等信息
    
    # 摘要信息（当片段被合并后生成）
    is_compressed: bool = False  # 是否已压缩
    summary: str = ""  # 压缩摘要
    key_events: List[str] = field(default_factory=list)  # 关键事件
    
    # 元数据
    compression_level: int = 0  # 压缩级别（0=原始，1=合并1次，2=合并2次...）
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'start_timestamp': self.start_timestamp,
            'end_timestamp': self.end_timestamp,
            'segment_length': self.segment_length,
            'events': self.events,
            'is_compressed': self.is_compressed,
            'summary': self.summary,
            'key_events': self.key_events,
            'compression_level': self.compression_level,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventSegment':
        """从字典创建"""
        return cls(**data)
    
    def get_duration(self) -> float:
        """获取片段持续时间（秒）"""
        return self.end_timestamp - self.start_timestamp
    
    def __repr__(self) -> str:
        compressed_marker = " [已压缩]" if self.is_compressed else ""
        return (f"EventSegment(#{self.id}, 长度={self.segment_length}, "
                f"事件数={len(self.events)}, 压缩级别={self.compression_level}{compressed_marker})")


class EventMemory:
    """
    事件记忆管理器
    
    功能：
    1. 完整记录思考/行为内容和先后顺序
    2. 自动压缩旧记忆，保持记忆文件大小可控
    3. 对近期状态保持精确认知
    
    压缩策略：
    - 每次思考完后生成一个新片段
    - 合并最早的且片段时间长度相同的两个片段
    - 合并时使用LLM总结内容，但保持原始长度不变
    """
    
    def __init__(self, 
                 storage_path: str = "data/event_memory.json",
                 llm_config: Optional[Dict[str, Any]] = None,
                 enable_llm_compression: bool = True):
        """
        初始化事件记忆
        
        Args:
            storage_path: 存储文件路径
            llm_config: LLM配置（用于压缩）
            enable_llm_compression: 是否启用LLM压缩
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 片段列表（按时间顺序排列）
        self.segments: List[EventSegment] = []
        self.next_segment_id = 1
        
        # LLM客户端（用于压缩）
        self.enable_llm_compression = enable_llm_compression
        if enable_llm_compression and llm_config:
            try:
                self.llm = LLMClient(llm_config)
            except Exception as e:
                logger.warning(f"LLM初始化失败，将使用规则压缩: {e}")
                self.llm = None
                self.enable_llm_compression = False
        else:
            self.llm = None
        
        # 统计信息
        self.total_events = 0
        self.total_compressions = 0
        
        # 加载已有记忆
        self._load_segments()
        
        logger.info(f"事件记忆初始化完成，已加载 {len(self.segments)} 个片段，"
                   f"共 {self.total_events} 个事件")
    
    def _load_segments(self):
        """从文件加载片段"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.segments = [
                        EventSegment.from_dict(s) for s in data.get('segments', [])
                    ]
                    self.next_segment_id = data.get('next_segment_id', 1)
                    self.total_events = data.get('total_events', 0)
                    self.total_compressions = data.get('total_compressions', 0)
                logger.info(f"从文件加载了 {len(self.segments)} 个片段")
            except Exception as e:
                logger.error(f"加载事件记忆失败: {e}")
                self.segments = []
    
    def _save_segments(self):
        """保存片段到文件"""
        try:
            data = {
                'segments': [s.to_dict() for s in self.segments],
                'next_segment_id': self.next_segment_id,
                'total_events': self.total_events,
                'total_compressions': self.total_compressions,
                'last_updated': time.time()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("事件记忆已保存")
        except Exception as e:
            logger.error(f"保存事件记忆失败: {e}")
    
    def add_event(self, 
                  thought: str,
                  context: str,
                  action: str,
                  result: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> EventSegment:
        """
        添加一个新事件并创建新片段
        
        Args:
            thought: 思考内容
            context: 情境描述
            action: 采取的行动
            result: 行动结果
            metadata: 元数据
        
        Returns:
            创建的事件片段
        """
        current_time = time.time()
        
        # 创建事件记录
        event = {
            'timestamp': current_time,
            'thought': thought,
            'context': context,
            'action': action,
            'result': result,
            'metadata': metadata or {}
        }
        
        # 创建新片段（每次思考生成一个片段，长度为1）
        segment = EventSegment(
            id=self.next_segment_id,
            start_timestamp=current_time,
            end_timestamp=current_time,
            segment_length=1,  # 原始片段长度为1
            events=[event],
            is_compressed=False,
            compression_level=0
        )
        
        self.segments.append(segment)
        self.next_segment_id += 1
        self.total_events += 1
        
        logger.info(f"添加事件片段 #{segment.id}: {thought[:30]}...")
        
        # 执行压缩策略
        self._compress_if_needed()
        
        # 保存
        self._save_segments()
        
        return segment
    
    def _compress_if_needed(self):
        """
        压缩策略：合并最早的且片段时间长度相同的两个片段
        
        算法：
        1. 统计所有片段的segment_length
        2. 找到最早出现的且有至少2个片段具有相同length的长度值
        3. 合并这两个最早的相同长度片段
        """
        if len(self.segments) < 3:
            # 少于3个片段时不压缩（需要至少3个片段才开始压缩）
            return
        
        # 统计每个长度的片段及其位置
        length_groups: Dict[int, List[int]] = {}  # length -> [indices]
        
        for idx, segment in enumerate(self.segments):
            length = segment.segment_length
            if length not in length_groups:
                length_groups[length] = []
            length_groups[length].append(idx)
        
        # 找到最早出现的、且有至少2个片段的长度值
        target_length = None
        target_indices = None
        
        for idx, segment in enumerate(self.segments):
            length = segment.segment_length
            if len(length_groups[length]) >= 2:
                # 找到第一组可以合并的片段
                target_length = length
                # 获取这个长度的所有片段索引，取最早的两个
                target_indices = length_groups[length][:2]
                break
        
        if target_length is None or target_indices is None:
            # 没有可以合并的片段
            return
        
        # 确保索引是连续的（我们只合并相邻的片段）
        # 实际上根据算法，我们需要找到最早的两个相同长度的片段
        # 它们可能不连续，所以需要调整策略
        
        # 合并这两个片段
        idx1, idx2 = target_indices[0], target_indices[1]
        segment1 = self.segments[idx1]
        segment2 = self.segments[idx2]
        
        logger.info(f"压缩片段 #{segment1.id} (长度={segment1.segment_length}) "
                   f"和 #{segment2.id} (长度={segment2.segment_length})")
        
        # 执行合并
        merged_segment = self._merge_segments(segment1, segment2)
        
        # 更新片段列表：删除旧片段，插入新片段
        # 删除时从后往前删，避免索引变化
        if idx1 < idx2:
            del self.segments[idx2]
            del self.segments[idx1]
            insert_position = idx1
        else:
            del self.segments[idx1]
            del self.segments[idx2]
            insert_position = idx2
        
        self.segments.insert(insert_position, merged_segment)
        
        self.total_compressions += 1
        logger.info(f"压缩完成，新片段 #{merged_segment.id}，"
                   f"当前共 {len(self.segments)} 个片段")
    
    def _merge_segments(self, seg1: EventSegment, seg2: EventSegment) -> EventSegment:
        """
        合并两个片段
        
        Args:
            seg1: 第一个片段
            seg2: 第二个片段
        
        Returns:
            合并后的新片段
        """
        # 创建新片段
        merged = EventSegment(
            id=self.next_segment_id,
            start_timestamp=min(seg1.start_timestamp, seg2.start_timestamp),
            end_timestamp=max(seg1.end_timestamp, seg2.end_timestamp),
            segment_length=seg1.segment_length + seg2.segment_length,
            events=seg1.events + seg2.events,  # 合并事件列表
            is_compressed=True,
            compression_level=max(seg1.compression_level, seg2.compression_level) + 1
        )
        
        self.next_segment_id += 1
        
        # 生成压缩摘要
        if self.enable_llm_compression and self.llm:
            try:
                summary_data = self._compress_with_llm(seg1, seg2)
                merged.summary = summary_data.get('summary', '')
                merged.key_events = summary_data.get('key_events', [])
            except Exception as e:
                logger.warning(f"LLM压缩失败，使用规则压缩: {e}")
                summary_data = self._compress_with_rules(seg1, seg2)
                merged.summary = summary_data.get('summary', '')
                merged.key_events = summary_data.get('key_events', [])
        else:
            summary_data = self._compress_with_rules(seg1, seg2)
            merged.summary = summary_data.get('summary', '')
            merged.key_events = summary_data.get('key_events', [])
        
        return merged
    
    def _compress_with_llm(self, seg1: EventSegment, seg2: EventSegment) -> Dict[str, Any]:
        """
        使用LLM压缩两个片段
        
        Args:
            seg1: 第一个片段
            seg2: 第二个片段
        
        Returns:
            压缩结果 {'summary': str, 'key_events': List[str]}
        """
        logger.debug("使用LLM压缩事件片段")
        
        # 构建待压缩的内容
        events_text = self._format_segment_events(seg1) + "\n\n" + self._format_segment_events(seg2)
        
        prompt = f"""
请将以下事件记忆压缩为简洁的摘要。

## 事件内容：
{events_text}

---

## 任务要求：
1. **摘要** (100-200字)：总结这段时间发生的主要事件，保留关键信息和因果关系
2. **关键事件** (3-5个)：列出最重要的事件点

**输出JSON格式：**
```json
{{
    "summary": "事件摘要",
    "key_events": ["事件1", "事件2", "事件3"]
}}
```

要求：
- 保留时间顺序
- 保留重要的思考和决策
- 去除冗余信息
- 摘要长度：100-200字
"""
        
        response = self.llm.complete([
            {'role': 'user', 'content': prompt}
        ], temperature=0.3, max_tokens=500)
        
        result = self.llm.parse_json_response(response['content'])
        
        if result and 'summary' in result and 'key_events' in result:
            return result
        else:
            raise ValueError("LLM返回格式不正确")
    
    def _compress_with_rules(self, seg1: EventSegment, seg2: EventSegment) -> Dict[str, Any]:
        """
        使用基于规则的方法压缩两个片段
        
        Args:
            seg1: 第一个片段
            seg2: 第二个片段
        
        Returns:
            压缩结果 {'summary': str, 'key_events': List[str]}
        """
        logger.debug("使用规则方法压缩事件片段")
        
        all_events = seg1.events + seg2.events
        
        # 生成摘要
        summary_parts = []
        key_events = []
        
        for i, event in enumerate(all_events[:5]):  # 最多取5个事件
            thought = event.get('thought', '')[:50]
            action = event.get('action', '')[:30]
            summary_parts.append(f"{i+1}. 思考：{thought}... → 行动：{action}...")
            key_events.append(f"{action[:20]}...")
        
        if len(all_events) > 5:
            summary_parts.append(f"...以及其他{len(all_events)-5}个事件")
        
        summary = "\n".join(summary_parts)
        
        return {
            'summary': summary,
            'key_events': key_events[:5]
        }
    
    def _format_segment_events(self, segment: EventSegment) -> str:
        """格式化片段事件为文本"""
        if segment.is_compressed:
            # 如果已经是压缩片段，返回摘要
            return f"[已压缩片段 #{segment.id}]\n摘要：{segment.summary}"
        else:
            # 原始片段，列出所有事件
            lines = [f"[片段 #{segment.id}]"]
            for i, event in enumerate(segment.events, 1):
                time_str = time.strftime('%H:%M:%S', time.localtime(event['timestamp']))
                lines.append(f"{i}. [{time_str}]")
                lines.append(f"   情境: {event.get('context', '')[:100]}")
                lines.append(f"   思考: {event.get('thought', '')[:100]}")
                lines.append(f"   行动: {event.get('action', '')[:100]}")
                if event.get('result'):
                    lines.append(f"   结果: {event.get('result', '')[:100]}")
            return "\n".join(lines)
    
    def get_recent_segments(self, count: int = 5) -> List[EventSegment]:
        """
        获取最近的片段
        
        Args:
            count: 返回数量
        
        Returns:
            片段列表
        """
        return self.segments[-count:] if self.segments else []
    
    def get_all_segments(self) -> List[EventSegment]:
        """获取所有片段"""
        return self.segments.copy()
    
    def get_memory_narrative(self, segment_count: int = 10) -> str:
        """
        生成记忆叙事
        
        将最近的片段整理成连贯的叙述
        
        Args:
            segment_count: 包含的片段数量
        
        Returns:
            记忆叙事文本
        """
        recent = self.get_recent_segments(segment_count)
        
        if not recent:
            return "（暂无记忆）"
        
        lines = ["=== 事件记忆 ===\n"]
        
        for i, segment in enumerate(recent, 1):
            time_str = time.strftime('%H:%M:%S', time.localtime(segment.start_timestamp))
            
            if segment.is_compressed:
                # 压缩片段显示摘要
                lines.append(f"{i}. [{time_str}] 片段#{segment.id} "
                           f"(长度={segment.segment_length}, 压缩级别={segment.compression_level})")
                lines.append(f"   摘要: {segment.summary[:200]}")
                if segment.key_events:
                    lines.append(f"   关键事件: {', '.join(segment.key_events[:3])}")
            else:
                # 原始片段显示事件
                lines.append(f"{i}. [{time_str}] 片段#{segment.id} (原始)")
                for event in segment.events:
                    thought = event.get('thought', '')[:50]
                    action = event.get('action', '')[:50]
                    lines.append(f"   - {thought}... -> {action}...")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.segments:
            return {
                'total_segments': 0,
                'total_events': 0,
                'total_compressions': 0,
                'compressed_segments': 0,
                'original_segments': 0,
                'avg_segment_length': 0,
                'avg_compression_level': 0
            }
        
        compressed_count = sum(1 for s in self.segments if s.is_compressed)
        original_count = len(self.segments) - compressed_count
        avg_length = sum(s.segment_length for s in self.segments) / len(self.segments)
        avg_compression = sum(s.compression_level for s in self.segments) / len(self.segments)
        
        return {
            'total_segments': len(self.segments),
            'total_events': self.total_events,
            'total_compressions': self.total_compressions,
            'compressed_segments': compressed_count,
            'original_segments': original_count,
            'avg_segment_length': avg_length,
            'avg_compression_level': avg_compression,
            'memory_span_hours': (self.segments[-1].end_timestamp - self.segments[0].start_timestamp) / 3600 
                                  if self.segments else 0
        }
    
    def __len__(self) -> int:
        return len(self.segments)
    
    def __repr__(self) -> str:
        return f"EventMemory({len(self.segments)} segments, {self.total_events} events)"


if __name__ == '__main__':
    # 测试事件记忆
    print("测试事件记忆系统...")
    
    em = EventMemory("data/test_event_memory.json", enable_llm_compression=False)
    
    # 模拟多次思考
    print("\n=== 添加事件 ===")
    
    for i in range(1, 8):
        em.add_event(
            thought=f"第{i}次思考：分析当前情境...",
            context=f"用户进行第{i}次互动",
            action=f"采取行动{i}：回复用户",
            result=f"用户响应{i}",
            metadata={'cycle': i}
        )
        print(f"添加第{i}次思考后，共 {len(em.segments)} 个片段")
        print(f"  片段详情: {[f'#{s.id}(长度{s.segment_length})' for s in em.segments]}")
        print()
    
    print("\n=== 最终状态 ===")
    print(em)
    print(f"\n统计信息:")
    stats = em.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n=== 记忆叙事 ===")
    print(em.get_memory_narrative())

