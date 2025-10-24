# -*- coding: utf-8 -*-
"""
记忆合并系统 - 正确实现（带连锁反应）

关键发现：
- 添加1后，新的1可以和旁边元素进行连锁合并
- 类似2048游戏或二进制进位
- 但题目说"每次只能合并一次"...

让我重新理解"每次只能合并一次"：
也许是指"每轮只处理一对"？
"""


def memory_merge_with_cascade(memory_list):
    """
    带连锁反应的合并
    """
    # 先尝试合并现有的相邻相同对（从右到左找第一个）
    result = memory_list[:]
    
    # 从右到左查找最右边的相邻相同对
    merge_happened = False
    for i in range(len(result) - 1, 0, -1):
        if result[i] == result[i - 1]:
            # 合并
            merged = result[i] * 2
            result = result[:i-1] + [merged] + result[i+1:]
            merge_happened = True
            break
    
    # 然后添加1
    # 找插入位置：第一个>1的元素之前
    insert_pos = len(result)
    for i, val in enumerate(result):
        if val > 1:
            insert_pos = i
            break
    result = result[:insert_pos] + [1] + result[insert_pos:]
    
    return result


def memory_merge_add_then_cascade(memory_list):
    """
    先添加1，然后进行一次合并（如果可能）
    """
    # 先添加1到正确位置
    insert_pos = len(memory_list)
    for i, val in enumerate(memory_list):
        if val > 1:
            insert_pos = i
            break
    result = memory_list[:insert_pos] + [1] + memory_list[insert_pos:]
    
    # 然后从右到左查找一对相邻相同的，合并它们
    for i in range(len(result) - 1, 0, -1):
        if result[i] == result[i - 1]:
            merged = result[i] * 2
            result = result[:i-1] + [merged] + result[i+1:]
            break  # 只合并一次
    
    return result


# 测试
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

methods = [
    ("先合并再添加", memory_merge_with_cascade),
    ("先添加再合并", memory_merge_add_then_cascade),
]

for name, func in methods:
    print("=" * 90)
    print(f"测试方法：{name}")
    print("=" * 90)
    print()
    
    memory = []
    all_correct = True
    
    for cycle in range(1, 13):
        memory = func(memory)
        is_correct = (memory == expected[cycle])
        status = "✓" if is_correct else "✗"
        
        print(f"循环 {cycle:2d}: {str(memory):30s} | 预期: {str(expected[cycle]):30s} | {status}")
        
        if not is_correct:
            all_correct = False
    
    print()
    if all_correct:
        print("🎉 完全正确！")
    else:
        print("还有错误...")
    print()

