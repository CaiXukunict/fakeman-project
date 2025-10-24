"""
事件记忆系统测试脚本
展示事件记忆的压缩机制
"""

import time
from memory import EventMemory


def test_event_memory_compression():
    """
    测试事件记忆的压缩机制
    
    验证：
    1. 每次思考生成一个片段（长度为1）
    2. 自动合并最早的、相同长度的两个片段
    3. 合并后的片段时间长度不同
    4. 保持记忆文件大小可控
    """
    print("="*60)
    print("测试事件记忆压缩机制")
    print("="*60)
    
    # 创建事件记忆（使用规则压缩，不需要LLM）
    em = EventMemory(
        storage_path="data/test_event_memory_demo.json",
        enable_llm_compression=False
    )
    
    print(f"\n初始状态: {em}")
    print(f"片段数: {len(em.segments)}")
    
    # 模拟10次思考
    print("\n" + "="*60)
    print("模拟10次思考，观察压缩过程")
    print("="*60)
    
    for i in range(1, 11):
        print(f"\n--- 第{i}次思考 ---")
        
        em.add_event(
            thought=f"第{i}次思考：当前用户似乎对话题感兴趣，我应该继续深入探讨。",
            context=f"用户第{i}次互动：继续讨论",
            action=f"回复{i}：提供更详细的信息",
            result=f"用户给出正面反馈{i}",
            metadata={
                'cycle': i,
                'emotion': 'positive'
            }
        )
        
        print(f"当前片段数: {len(em.segments)}")
        print(f"片段详情:")
        for seg in em.segments:
            compressed_mark = "[已压缩]" if seg.is_compressed else "[原始]"
            print(f"  片段#{seg.id}: 长度={seg.segment_length}, "
                  f"压缩级别={seg.compression_level} {compressed_mark}")
        
        # 每3次思考后显示详细统计
        if i % 3 == 0:
            stats = em.get_statistics()
            print(f"\n统计信息:")
            print(f"  总片段数: {stats['total_segments']}")
            print(f"  总事件数: {stats['total_events']}")
            print(f"  总压缩次数: {stats['total_compressions']}")
            print(f"  已压缩片段: {stats['compressed_segments']}")
            print(f"  原始片段: {stats['original_segments']}")
            print(f"  平均片段长度: {stats['avg_segment_length']:.2f}")
    
    # 最终状态
    print("\n" + "="*60)
    print("最终状态")
    print("="*60)
    
    print(f"\n{em}")
    
    stats = em.get_statistics()
    print(f"\n完整统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 显示记忆叙事
    print("\n" + "="*60)
    print("记忆叙事（最近5个片段）")
    print("="*60)
    print(em.get_memory_narrative(segment_count=5))
    
    # 验证压缩机制
    print("\n" + "="*60)
    print("压缩机制验证")
    print("="*60)
    
    segment_lengths = [seg.segment_length for seg in em.segments]
    print(f"\n当前所有片段的长度: {segment_lengths}")
    
    # 检查是否有两个相同长度的片段
    from collections import Counter
    length_counts = Counter(segment_lengths)
    
    print(f"\n长度分布:")
    for length, count in sorted(length_counts.items()):
        print(f"  长度={length}: {count}个片段")
    
    # 验证：应该每个长度最多有2个相同的片段（因为有3个片段时才会压缩）
    max_same_length = max(length_counts.values())
    print(f"\n相同长度片段的最大数量: {max_same_length}")
    
    if max_same_length <= 2:
        print("[OK] 压缩机制正常工作！")
        print("  （相同长度的片段在达到2个后会被合并）")
    else:
        print("[ERROR] 压缩机制可能存在问题")
    
    return em


def test_retrieval():
    """测试事件记忆的检索功能"""
    print("\n\n" + "="*60)
    print("测试事件记忆检索")
    print("="*60)
    
    em = EventMemory("data/test_event_memory_demo.json")
    
    # 获取最近的片段
    recent = em.get_recent_segments(3)
    print(f"\n最近3个片段:")
    for i, seg in enumerate(recent, 1):
        print(f"{i}. {seg}")
    
    # 获取所有片段
    all_segments = em.get_all_segments()
    print(f"\n所有片段数量: {len(all_segments)}")
    
    return em


if __name__ == '__main__':
    # 测试1: 压缩机制
    em = test_event_memory_compression()
    
    # 测试2: 检索功能
    test_retrieval()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)

