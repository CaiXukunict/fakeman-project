"""
短期记忆系统 - 自动压缩的时间窗口记忆

特性：
1. 记录每次思考和行动的详细内容
2. 随时间自动合并压缩，保持固定长度
3. 时间量化：每次新内容为1个时间单位
4. 合并规则：只合并相同时间量的相邻内容
5. 结果：固定数量的记忆条目，覆盖的时间跨度逐渐增加

合并示例：
循环1: [1]
循环2: [1, 1]
循环3: [1, 2]         # 前两个1合并成2
循环4: [1, 1, 2]
循环5: [1, 2, 2]      # 中间两个1合并成2
循环6: [1, 1, 4]      # 两个2合并成4
循环7: [1, 2, 4]
循环8: [1, 1, 2, 4]
循环9: [1, 2, 2, 4]
循环10: [1, 1, 4, 4]
循环11: [1, 2, 8]     # 两个4合并成8
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger('fakeman.memory.short_term')


@dataclass
class ShortMemoryEntry:
    """短期记忆条目"""
    content: str  # 记忆内容（可能是合并后的摘要）
    time_units: int  # 时间单位（1=单次，2=两次合并，4=四次合并...）
    start_timestamp: float  # 开始时间戳
    end_timestamp: float  # 结束时间戳
    cycle_count: int  # 包含的循环数
    desires_snapshot: Dict[str, float]  # 欲望快照
    entry_type: str  # 类型：thinking, action, response
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'ShortMemoryEntry':
        """从字典创建"""
        return ShortMemoryEntry(**data)
    
    def get_duration(self) -> float:
        """获取持续时间（秒）"""
        return self.end_timestamp - self.start_timestamp
    
    def get_summary(self) -> str:
        """获取摘要"""
        duration = self.get_duration()
        if duration < 60:
            time_str = f"{duration:.1f}秒"
        elif duration < 3600:
            time_str = f"{duration/60:.1f}分钟"
        else:
            time_str = f"{duration/3600:.1f}小时"
        
        return f"[时间量:{self.time_units}, 时长:{time_str}, 循环数:{self.cycle_count}] {self.content[:100]}..."


class ShortTermMemory:
    """短期记忆系统 - 自动压缩的滑动窗口"""
    
    def __init__(self, storage_path: str = "data/short_term_memory.json"):
        """
        初始化短期记忆系统
        
        Args:
            storage_path: 存储文件路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 短期记忆条目列表（固定长度，会自动合并）
        self.memories: List[ShortMemoryEntry] = []
        
        # 统计信息
        self.total_cycles = 0  # 总循环数
        self.total_merges = 0  # 总合并次数
        
        # 加载已有记忆
        self._load_memory()
        
        logger.info(f"短期记忆系统初始化完成，当前记忆条目数: {len(self.memories)}")
    
    def _load_memory(self):
        """从文件加载记忆"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.memories = [ShortMemoryEntry.from_dict(m) for m in data.get('memories', [])]
                self.total_cycles = data.get('total_cycles', 0)
                self.total_merges = data.get('total_merges', 0)
                
                logger.info(f"加载了 {len(self.memories)} 条短期记忆")
            except Exception as e:
                logger.error(f"加载短期记忆失败: {e}")
                self.memories = []
    
    def _save_memory(self):
        """保存记忆到文件"""
        try:
            data = {
                'memories': [m.to_dict() for m in self.memories],
                'total_cycles': self.total_cycles,
                'total_merges': self.total_merges,
                'last_update': time.time()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存短期记忆失败: {e}")
    
    def add_memory(self, content: str, desires: Dict[str, float], 
                   entry_type: str = "thinking") -> None:
        """
        添加新的记忆条目
        
        Args:
            content: 记忆内容
            desires: 当前欲望状态
            entry_type: 条目类型 (thinking, action, response)
        """
        # 创建新条目（时间单位为1）
        current_time = time.time()
        new_entry = ShortMemoryEntry(
            content=content,
            time_units=1,
            start_timestamp=current_time,
            end_timestamp=current_time,
            cycle_count=1,
            desires_snapshot=desires.copy(),
            entry_type=entry_type
        )
        
        # 添加到记忆列表开头（最新的在左边）
        self.memories.insert(0, new_entry)
        self.total_cycles += 1
        
        logger.debug(f"添加短期记忆: {entry_type} - {content[:50]}...")
        
        # 执行合并
        self._merge_memories()
        
        # 保存
        self._save_memory()
    
    def _merge_memories(self):
        """
        合并记忆：只合并相同时间单位的相邻条目
        
        合并规则（按你的要求）：
        - 新条目添加在列表开头（索引0）
        - 从右往左扫描，找到最右边的两个相同时间单位的条目
        - 合并它们，新条目始终保持为1
        
        示例（最新的在左边）：
        循环1: [1]
        循环2: [1, 1]           # 新1加在左边
        循环3: [1, 2]           # 新1加在左边，右边两个1合并成2
        循环4: [1, 1, 2]        # 新1加在左边
        循环5: [1, 2, 2]        # 新1加在左边，中间两个1合并成2
        循环6: [1, 1, 4]        # 新1加在左边，右边两个2合并成4
        """
        # 只在有3个或更多条目时才考虑合并
        if len(self.memories) < 3:
            return
        
        # 从右往左扫描，找到最右边的两个相同时间单位的相邻条目
        # 保护索引0（最新的条目）
        while len(self.memories) >= 3:
            merged = False
            
            # 从右往左扫描（跳过索引0）
            for i in range(len(self.memories) - 1, 0, -1):
                current = self.memories[i]
                previous = self.memories[i - 1]
                
                # 只有时间单位相同才能合并
                if current.time_units == previous.time_units:
                    # 合并这两个条目
                    merged_entry = self._merge_two_entries(previous, current)
                    
                    # 替换previous位置，删除current
                    self.memories[i - 1] = merged_entry
                    self.memories.pop(i)
                    
                    self.total_merges += 1
                    merged = True
                    
                    logger.debug(f"合并了两个时间单位为 {current.time_units} 的条目，"
                               f"新时间单位: {merged_entry.time_units}")
                    
                    # 只合并一次就停止，让新的结构稳定后再判断
                    break
            
            # 如果这轮没有合并，说明无法再合并了
            if not merged:
                break
    
    def _merge_two_entries(self, entry1: ShortMemoryEntry, 
                          entry2: ShortMemoryEntry) -> ShortMemoryEntry:
        """
        合并两个记忆条目
        
        Args:
            entry1: 较早的条目
            entry2: 较晚的条目
        
        Returns:
            合并后的条目
        """
        # 合并内容（简化摘要）
        merged_content = self._summarize_content(entry1.content, entry2.content)
        
        # 时间单位翻倍
        merged_time_units = entry1.time_units + entry2.time_units
        
        # 时间范围扩展
        start_time = entry1.start_timestamp
        end_time = entry2.end_timestamp
        
        # 循环数相加
        merged_cycle_count = entry1.cycle_count + entry2.cycle_count
        
        # 欲望取平均（或使用最新的）
        merged_desires = entry2.desires_snapshot.copy()
        
        # 类型取最新的
        merged_type = entry2.entry_type
        
        return ShortMemoryEntry(
            content=merged_content,
            time_units=merged_time_units,
            start_timestamp=start_time,
            end_timestamp=end_time,
            cycle_count=merged_cycle_count,
            desires_snapshot=merged_desires,
            entry_type=merged_type
        )
    
    def _summarize_content(self, content1: str, content2: str) -> str:
        """
        合并两段内容的摘要
        
        策略：提取关键信息，保持固定长度
        """
        # 简单策略：提取关键词和主要动作
        # 实际应用中可以使用LLM进行更智能的摘要
        
        # 限制每段的长度
        max_len = 100
        summary1 = content1[:max_len] if len(content1) > max_len else content1
        summary2 = content2[:max_len] if len(content2) > max_len else content2
        
        # 合并摘要
        merged = f"[早期] {summary1} | [近期] {summary2}"
        
        # 如果合并后太长，进一步压缩
        if len(merged) > 250:
            merged = f"{summary1[:80]}... → ...{summary2[-80:]}"
        
        return merged
    
    def get_recent_memories(self, count: int = 10) -> List[ShortMemoryEntry]:
        """
        获取最近的记忆（从新到旧）
        
        Args:
            count: 返回的记忆数量
        
        Returns:
            记忆条目列表（最新的在前）
        """
        return self.memories[:count]
    
    def get_all_memories(self) -> List[ShortMemoryEntry]:
        """获取所有记忆（从新到旧）"""
        return self.memories.copy()
    
    def get_memory_timeline(self) -> str:
        """
        获取记忆时间线的可视化表示
        
        Returns:
            时间线字符串
        """
        if not self.memories:
            return "短期记忆为空"
        
        lines = [
            "=" * 60,
            "短期记忆时间线",
            "=" * 60,
            f"总循环数: {self.total_cycles}, 总合并次数: {self.total_merges}",
            f"当前记忆条目数: {len(self.memories)}",
            "-" * 60
        ]
        
        for i, memory in enumerate(self.memories, 1):
            duration = memory.get_duration()
            time_str = datetime.fromtimestamp(memory.start_timestamp).strftime('%H:%M:%S')
            
            lines.append(f"\n{i}. [{time_str}] 时间量:{memory.time_units}, "
                        f"循环数:{memory.cycle_count}")
            lines.append(f"   类型: {memory.entry_type}")
            lines.append(f"   内容: {memory.content[:150]}...")
            
            if duration > 1:
                if duration < 60:
                    lines.append(f"   持续: {duration:.1f}秒")
                elif duration < 3600:
                    lines.append(f"   持续: {duration/60:.1f}分钟")
                else:
                    lines.append(f"   持续: {duration/3600:.1f}小时")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def get_memory_structure(self) -> str:
        """
        获取记忆结构（时间单位序列）
        
        Returns:
            结构字符串，如 "[1, 2, 4]"
        """
        structure = [m.time_units for m in self.memories]
        return str(structure)
    
    def get_context_for_thinking(self, max_entries: int = 5) -> str:
        """
        获取用于思考的上下文（最近的几条记忆）
        
        Args:
            max_entries: 最多返回的条目数
        
        Returns:
            格式化的上下文字符串
        """
        recent = self.get_recent_memories(max_entries)
        
        if not recent:
            return "暂无短期记忆"
        
        lines = ["【短期记忆上下文】"]
        
        for memory in recent:
            time_str = datetime.fromtimestamp(memory.end_timestamp).strftime('%H:%M:%S')
            lines.append(f"- [{time_str}] ({memory.entry_type}, "
                        f"时间量:{memory.time_units}) {memory.content[:100]}...")
        
        return "\n".join(lines)
    
    def search_memories(self, keyword: str) -> List[ShortMemoryEntry]:
        """
        搜索包含关键词的记忆
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的记忆列表
        """
        results = []
        for memory in self.memories:
            if keyword.lower() in memory.content.lower():
                results.append(memory)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据字典
        """
        if not self.memories:
            return {
                'total_entries': 0,
                'total_cycles': self.total_cycles,
                'total_merges': self.total_merges,
                'memory_structure': '[]',
                'average_compression_ratio': 0
            }
        
        total_time_units = sum(m.time_units for m in self.memories)
        total_cycles = sum(m.cycle_count for m in self.memories)
        
        return {
            'total_entries': len(self.memories),
            'total_cycles': self.total_cycles,
            'total_merges': self.total_merges,
            'memory_structure': self.get_memory_structure(),
            'total_time_units': total_time_units,
            'average_time_units': total_time_units / len(self.memories),
            'compression_ratio': self.total_cycles / len(self.memories) if self.memories else 0,
            'oldest_memory': datetime.fromtimestamp(self.memories[0].start_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'newest_memory': datetime.fromtimestamp(self.memories[-1].end_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'time_span_seconds': self.memories[-1].end_timestamp - self.memories[0].start_timestamp
        }
    
    def clear(self):
        """清空短期记忆"""
        self.memories.clear()
        self.total_cycles = 0
        self.total_merges = 0
        self._save_memory()
        logger.info("短期记忆已清空")

