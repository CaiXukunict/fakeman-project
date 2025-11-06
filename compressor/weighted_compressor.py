# -*- coding: utf-8 -*-
"""
基于权重的记忆压缩器
在原有压缩规则基础上，添加权重分配机制
"""

from typing import List, Dict, Any
import time
from utils.logger import get_logger

logger = get_logger('fakeman.weighted_compressor')


class WeightedMemoryCompressor:
    """
    基于权重的记忆压缩器
    
    核心规则：
    1. 保留原有的压缩规则（时间、重要性等）
    2. 新增：根据思考内容的权重分配合并后的篇幅
    3. 权重越高的内容，在合并时获得更多篇幅
    """
    
    def __init__(self, 
                 base_summary_length: int = 200,
                 min_weight_threshold: float = 0.1):
        """
        初始化压缩器
        
        Args:
            base_summary_length: 基础摘要长度
            min_weight_threshold: 最小权重阈值（低于此值的思考被过滤）
        """
        self.base_summary_length = base_summary_length
        self.min_weight_threshold = min_weight_threshold
        
        logger.info("基于权重的记忆压缩器初始化完成")
    
    def compress_memories(self,
                         memories: List[Dict[str, Any]],
                         target_count: int = None,
                         merge_similar: bool = True) -> List[Dict[str, Any]]:
        """
        压缩记忆列表
        
        Args:
            memories: 记忆列表
            target_count: 目标数量（如果为None，则按规则自动压缩）
            merge_similar: 是否合并相似记忆
        
        Returns:
            压缩后的记忆列表
        """
        if not memories:
            return []
        
        logger.info(f"开始压缩 {len(memories)} 条记忆")
        
        # 1. 首先过滤低权重的思考内容
        filtered_memories = self._filter_low_weight_thoughts(memories)
        
        # 2. 如果需要合并相似记忆
        if merge_similar:
            filtered_memories = self._merge_similar_memories(filtered_memories)
        
        # 3. 如果指定了目标数量，进行进一步压缩
        if target_count and len(filtered_memories) > target_count:
            filtered_memories = self._reduce_to_target_count(
                filtered_memories, 
                target_count
            )
        
        logger.info(f"压缩完成，剩余 {len(filtered_memories)} 条记忆")
        
        return filtered_memories
    
    def _filter_low_weight_thoughts(self,
                                   memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤每条记忆中的低权重思考内容
        
        Args:
            memories: 记忆列表
        
        Returns:
            过滤后的记忆列表
        """
        filtered = []
        
        for memory in memories:
            # 复制记忆以避免修改原数据
            mem_copy = memory.copy()
            
            # 获取思考内容
            thought_contents = mem_copy.get('thought_contents', [])
            
            if thought_contents:
                # 过滤低权重思考
                filtered_thoughts = [
                    t for t in thought_contents
                    if t.get('weight', 0) >= self.min_weight_threshold
                ]
                
                mem_copy['thought_contents'] = filtered_thoughts
                
                logger.debug(
                    f"记忆 #{mem_copy.get('id')}: "
                    f"{len(thought_contents)} → {len(filtered_thoughts)} 条思考"
                )
            
            filtered.append(mem_copy)
        
        return filtered
    
    def _merge_similar_memories(self,
                               memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并相似的记忆（基于权重分配篇幅）
        
        Args:
            memories: 记忆列表
        
        Returns:
            合并后的记忆列表
        """
        if len(memories) < 2:
            return memories
        
        merged = []
        used_indices = set()
        
        for i, mem1 in enumerate(memories):
            if i in used_indices:
                continue
            
            # 寻找相似的记忆
            similar_group = [mem1]
            similar_indices = [i]
            
            for j, mem2 in enumerate(memories[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # 判断是否相似（基于情境和行动）
                if self._is_similar(mem1, mem2):
                    similar_group.append(mem2)
                    similar_indices.append(j)
            
            # 如果找到相似记忆，进行合并
            if len(similar_group) > 1:
                merged_memory = self._merge_memory_group(similar_group)
                merged.append(merged_memory)
                used_indices.update(similar_indices)
                
                logger.debug(
                    f"合并了 {len(similar_group)} 条相似记忆 → "
                    f"记忆 #{merged_memory['id']}"
                )
            else:
                merged.append(mem1)
                used_indices.add(i)
        
        return merged
    
    def _is_similar(self, mem1: Dict[str, Any], mem2: Dict[str, Any],
                   similarity_threshold: float = 0.6) -> bool:
        """
        判断两条记忆是否相似
        
        简化实现：基于情境和行动的文本相似度
        
        Args:
            mem1, mem2: 两条记忆
            similarity_threshold: 相似度阈值
        
        Returns:
            是否相似
        """
        # 简单的相似度判断：检查关键词重叠
        situation1 = mem1.get('situation', '').lower()
        situation2 = mem2.get('situation', '').lower()
        
        action1 = mem1.get('action_taken', '').lower()
        action2 = mem2.get('action_taken', '').lower()
        
        # 检查是否有相同的主导欲望
        same_desire = (mem1.get('dominant_desire') == mem2.get('dominant_desire'))
        
        # 检查时间接近度（1小时内）
        time_diff = abs(mem1.get('timestamp', 0) - mem2.get('timestamp', 0))
        time_close = time_diff < 3600
        
        # 简化判断：相同欲望且时间接近
        return same_desire and time_close
    
    def _merge_memory_group(self,
                           memory_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并一组相似记忆（基于权重分配篇幅）
        
        核心：权重越高的记忆，在合并摘要中获得越多篇幅
        
        Args:
            memory_group: 要合并的记忆组
        
        Returns:
            合并后的记忆
        """
        # 使用第一条记忆作为基础
        merged = memory_group[0].copy()
        
        # 计算总权重
        total_weight = sum(
            mem.get('compression_weight', 1.0) 
            for mem in memory_group
        )
        
        # 合并思考内容（基于权重）
        all_thoughts = []
        for mem in memory_group:
            mem_weight = mem.get('compression_weight', 1.0)
            thoughts = mem.get('thought_contents', [])
            
            # 为每个思考添加来源记忆的权重
            for thought in thoughts:
                thought_copy = thought.copy()
                # 综合权重 = 思考权重 * 记忆权重
                thought_copy['combined_weight'] = (
                    thought.get('weight', 0.5) * mem_weight / total_weight
                )
                all_thoughts.append(thought_copy)
        
        # 按综合权重排序
        all_thoughts.sort(key=lambda x: x['combined_weight'], reverse=True)
        
        # 分配篇幅并生成摘要
        merged['thought_contents'] = self._allocate_space_by_weight(
            all_thoughts,
            self.base_summary_length
        )
        
        # 合并其他信息
        merged['situation'] = self._merge_text_field(
            memory_group, 'situation', total_weight
        )
        
        merged['action_taken'] = self._merge_text_field(
            memory_group, 'action_taken', total_weight
        )
        
        merged['output_text'] = self._merge_text_field(
            memory_group, 'output_text', total_weight
        )
        
        # 更新统计信息
        merged['happiness_delta'] = sum(
            mem.get('happiness_delta', 0) for mem in memory_group
        ) / len(memory_group)
        
        merged['importance'] = max(
            mem.get('importance', 0.5) for mem in memory_group
        )
        
        # 标记为合并记忆
        merged['is_merged'] = True
        merged['merged_from_count'] = len(memory_group)
        merged['merged_ids'] = [mem['id'] for mem in memory_group]
        
        return merged
    
    def _allocate_space_by_weight(self,
                                 thoughts: List[Dict[str, Any]],
                                 total_length: int) -> List[Dict[str, Any]]:
        """
        根据权重分配思考内容的篇幅
        
        Args:
            thoughts: 思考列表（已按权重排序）
            total_length: 总可用长度
        
        Returns:
            分配后的思考列表（可能被截断）
        """
        if not thoughts:
            return []
        
        allocated_thoughts = []
        remaining_length = total_length
        total_weight = sum(t['combined_weight'] for t in thoughts)
        
        if total_weight == 0:
            return thoughts[:3]  # 如果没有权重，返回前3个
        
        for thought in thoughts:
            if remaining_length <= 0:
                break
            
            # 计算该思考应得的字符数
            weight_ratio = thought['combined_weight'] / total_weight
            allocated_length = int(weight_ratio * total_length)
            allocated_length = min(allocated_length, remaining_length)
            
            if allocated_length > 10:  # 至少10个字符才有意义
                thought_copy = thought.copy()
                content = thought['content']
                
                if len(content) > allocated_length:
                    thought_copy['content'] = content[:allocated_length-3] + "..."
                
                allocated_thoughts.append(thought_copy)
                remaining_length -= len(thought_copy['content'])
        
        return allocated_thoughts
    
    def _merge_text_field(self,
                         memory_group: List[Dict[str, Any]],
                         field_name: str,
                         total_weight: float) -> str:
        """
        合并文本字段（基于权重）
        
        Args:
            memory_group: 记忆组
            field_name: 字段名
            total_weight: 总权重
        
        Returns:
            合并后的文本
        """
        # 按权重排序
        weighted_texts = []
        for mem in memory_group:
            text = mem.get(field_name, '')
            if text:
                weight = mem.get('compression_weight', 1.0)
                weighted_texts.append((text, weight / total_weight))
        
        if not weighted_texts:
            return ""
        
        # 权重最高的优先
        weighted_texts.sort(key=lambda x: x[1], reverse=True)
        
        # 如果权重差异不大，合并所有文本
        if len(weighted_texts) > 1 and weighted_texts[0][1] - weighted_texts[-1][1] < 0.3:
            return " | ".join(text for text, _ in weighted_texts[:3])
        else:
            # 否则只保留权重最高的
            return weighted_texts[0][0]
    
    def _reduce_to_target_count(self,
                               memories: List[Dict[str, Any]],
                               target_count: int) -> List[Dict[str, Any]]:
        """
        将记忆数量减少到目标数量
        
        保留最重要的记忆
        
        Args:
            memories: 记忆列表
            target_count: 目标数量
        
        Returns:
            筛选后的记忆列表
        """
        if len(memories) <= target_count:
            return memories
        
        # 按重要性和压缩权重排序
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get('importance', 0.5) * m.get('compression_weight', 1.0),
            reverse=True
        )
        
        return sorted_memories[:target_count]
    
    def compress_single_memory(self,
                              memory: Dict[str, Any],
                              max_length: int = None) -> Dict[str, Any]:
        """
        压缩单条记忆
        
        Args:
            memory: 记忆字典
            max_length: 最大长度
        
        Returns:
            压缩后的记忆
        """
        if max_length is None:
            max_length = self.base_summary_length
        
        compressed = memory.copy()
        
        # 压缩思考内容
        thoughts = compressed.get('thought_contents', [])
        if thoughts:
            # 过滤低权重
            thoughts = [
                t for t in thoughts
                if t.get('weight', 0) >= self.min_weight_threshold
            ]
            
            # 按权重排序
            thoughts.sort(key=lambda x: x.get('weight', 0), reverse=True)
            
            # 分配篇幅
            compressed['thought_contents'] = self._allocate_space_by_weight(
                thoughts,
                max_length
            )
        
        return compressed


# 测试代码
if __name__ == '__main__':
    # 创建测试数据
    test_memories = [
        {
            'id': 1,
            'timestamp': time.time(),
            'cycle_id': 1,
            'situation': '用户询问系统功能',
            'action_taken': '详细解释',
            'outcome': 'positive',
            'dominant_desire': 'understanding',
            'happiness_delta': 0.3,
            'importance': 0.8,
            'compression_weight': 1.0,
            'thought_contents': [
                {'content': '用户想了解系统', 'weight': 0.9, 'type': 'analysis'},
                {'content': '需要清晰解释', 'weight': 0.7, 'type': 'planning'},
                {'content': '避免技术术语', 'weight': 0.5, 'type': 'strategy'}
            ],
            'output_text': '这是一个AI系统，具有目的、欲望和记忆能力。'
        },
        {
            'id': 2,
            'timestamp': time.time() + 100,
            'cycle_id': 2,
            'situation': '用户继续询问细节',
            'action_taken': '补充说明',
            'outcome': 'positive',
            'dominant_desire': 'understanding',
            'happiness_delta': 0.2,
            'importance': 0.6,
            'compression_weight': 0.8,
            'thought_contents': [
                {'content': '用户需要更多细节', 'weight': 0.8, 'type': 'analysis'},
                {'content': '提供具体例子', 'weight': 0.6, 'type': 'planning'}
            ],
            'output_text': '系统通过经验学习，不断优化行为。'
        }
    ]
    
    # 创建压缩器
    compressor = WeightedMemoryCompressor(base_summary_length=150)
    
    print("=" * 80)
    print("测试：基于权重的记忆压缩")
    print("=" * 80)
    print()
    
    # 测试1：过滤低权重思考
    print("1. 原始记忆：")
    for mem in test_memories:
        print(f"   记忆 #{mem['id']}: {len(mem['thought_contents'])} 条思考")
    print()
    
    # 测试2：合并相似记忆
    print("2. 合并相似记忆：")
    compressed = compressor.compress_memories(test_memories, merge_similar=True)
    print(f"   压缩后: {len(compressed)} 条记忆")
    print()
    
    # 测试3：查看合并结果
    if compressed:
        merged_mem = compressed[0]
        print("3. 合并后的记忆详情：")
        print(f"   ID: {merged_mem['id']}")
        print(f"   是否合并: {merged_mem.get('is_merged', False)}")
        if merged_mem.get('is_merged'):
            print(f"   合并数量: {merged_mem.get('merged_from_count')}")
            print(f"   来源ID: {merged_mem.get('merged_ids')}")
        print(f"   思考内容数: {len(merged_mem.get('thought_contents', []))}")
        print()
        print("   思考内容（按权重分配篇幅后）：")
        for i, thought in enumerate(merged_mem.get('thought_contents', []), 1):
            print(f"   {i}. [{thought.get('type')}] {thought['content']}")
            print(f"      权重: {thought.get('combined_weight', 0):.3f}")
    
    print()
    print("=" * 80)

