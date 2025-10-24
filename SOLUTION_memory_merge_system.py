# -*- coding: utf-8 -*-
"""
记忆合并系统 - 最佳实现方案

基于你提供的12个循环数据，这是目前最接近的实现方案。
前8个循环完全正确，循环9-11需要进一步分析规则。

作者：AI Assistant
日期：2025-10-21
"""


def memory_merge(memory_list):
    """
    记忆合并算法（当前最佳版本）
    
    规则（基于前8个循环的正确实现）：
    1. 从右到左查找最右边的相邻相同对
    2. 如果找到：合并它们（值翻倍），然后在原位置添加[merged_value]
    3. 添加1到第一个大于1的元素之前（保持升序）
    4. 如果没有>1的元素，添加到末尾
    
    参数:
        memory_list (list): 当前记忆列表
    
    返回:
        list: 更新后的记忆列表
        
    示例:
        >>> memory_merge([])
        [1]
        >>> memory_merge([1])
        [1, 1]
        >>> memory_merge([1, 1])
        [1, 2]
        >>> memory_merge([1, 2])
        [1, 1, 2]
    """
    result = memory_list[:]
    
    # 步骤1：从右到左查找最右边的相邻相同对
    merge_pos = -1
    for i in range(len(result) - 1, 0, -1):
        if result[i] == result[i - 1]:
            merge_pos = i - 1
            break
    
    # 步骤2：如果找到相同对，合并它们
    if merge_pos >= 0:
        merged_value = result[merge_pos] * 2
        result = result[:merge_pos] + [merged_value] + result[merge_pos+2:]
    
    # 步骤3：添加1到正确位置
    insert_pos = len(result)
    for i, val in enumerate(result):
        if val > 1:
            insert_pos = i
            break
    result = result[:insert_pos] + [1] + result[insert_pos:]
    
    return result


# ====================
# 验证和演示
# ====================

if __name__ == "__main__":
    # 你提供的完整预期数据
    expected = {
        1: [1],
        2: [1, 1],
        3: [1, 2],
        4: [1, 1, 2],
        5: [1, 2, 2],
        6: [1, 1, 4],
        7: [1, 2, 4],
        8: [1, 1, 2, 4],
        9: [1, 1, 1, 2, 4],
        10: [1, 1, 2, 2, 4],
        11: [1, 1, 1, 4, 4],
        12: [1, 1, 2, 8],
    }
    
    print("=" * 90)
    print("记忆合并系统 - 测试结果")
    print("=" * 90)
    print()
    
    memory = []
    correct_count = 0
    
    for cycle in range(1, 13):
        memory = memory_merge(memory)
        is_correct = (memory == expected[cycle])
        status = "✓" if is_correct else "✗"
        
        if is_correct:
            correct_count += 1
        
        print(f"循环 {cycle:2d}: {str(memory):30s} | 预期: {str(expected[cycle]):30s} | {status}")
    
    print()
    print("=" * 90)
    print(f"正确率: {correct_count}/12 ({correct_count/12*100:.1f}%)")
    print("=" * 90)
    print()
    
    if correct_count == 12:
        print("🎉 完美！所有测试通过！")
    elif correct_count >= 8:
        print(f"✓ 前{correct_count}个循环正确！")
        print()
        print("注意：循环9-12的规则可能需要额外的条件判断。")
        print("可能的因素：")
        print("  - 列表长度")
        print("  - 元素值的大小关系")
        print("  - 是否存在特定模式（如连续3个1）")
    else:
        print("需要进一步分析...")
    
    print()
    print("=" * 90)
    print("使用示例")
    print("=" * 90)
    print()
    print("from SOLUTION_memory_merge_system import memory_merge")
    print()
    print("# 初始化")
    print("memory = []")
    print()
    print("# 运行多个循环")
    print("for cycle in range(1, 10):")
    print("    memory = memory_merge(memory)")
    print("    print(f'循环 {cycle}: {memory}')")
    print()

