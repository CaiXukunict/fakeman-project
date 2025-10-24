# -*- coding: utf-8 -*-
"""
记忆合并系统 - 最终实现

关键发现：
1. [1,2] + 1 → [1,1,2]: 新的1插入到了1和2之间！
2. [1,2,2] + 1 → [1,1,4]: 两个2合并成4，新1插入
3. 这像是：先在旧元素中找可合并的，合并后将新1插入到合并位置

规律猜测：
- 找到最右边的相邻相同对（不包括新加的）
- 合并它们
- 将新的1插入到合并位置的左边
"""


def memory_merge_v1(memory_list):
    """
    版本1：合并旧元素，新1插入到合并位置左边
    """
    # 从右到左查找最右边的相邻相同对（不包括新元素）
    merge_pos = -1
    for i in range(len(memory_list) - 1, 0, -1):
        if memory_list[i] == memory_list[i - 1]:
            merge_pos = i - 1  # 记录左边元素的位置
            break
    
    if merge_pos >= 0:
        # 找到可合并的对，在位置merge_pos和merge_pos+1
        merged_value = memory_list[merge_pos] * 2  # 合并：相同值翻倍！
        # 合并：删除这两个，在左边位置插入新1和合并后的值
        result = memory_list[:merge_pos] + [1, merged_value] + memory_list[merge_pos+2:]
    else:
        # 没有可合并的，直接添加
        result = memory_list + [1]
    
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

print("=" * 80)
print("记忆合并系统 - 测试版本1")
print("=" * 80)
print()

memory = []
all_correct = True

for cycle in range(1, 13):
    memory = memory_merge_v1(memory)
    is_correct = (memory == expected[cycle])
    status = "✓" if is_correct else "✗"
    
    print(f"循环 {cycle:2d}: {str(memory):25s} | 预期: {str(expected[cycle]):25s} | {status}")
    
    if not is_correct:
        all_correct = False

print()
if all_correct:
    print("✓✓✓ 完全正确！✓✓✓")
else:
    print("还有问题，继续分析...")

# 详细追踪几个关键循环
print()
print("=" * 80)
print("详细追踪")
print("=" * 80)
print()

test_cases = [
    ([1, 1], [1, 2], "循环2→3"),
    ([1, 2], [1, 1, 2], "循环3→4"),
    ([1, 2, 2], [1, 1, 4], "循环5→6"),
]

for input_mem, expected_output, label in test_cases:
    result = memory_merge_v1(input_mem)
    status = "✓" if result == expected_output else "✗"
    print(f"{label}:")
    print(f"  输入: {input_mem}")
    print(f"  输出: {result}")
    print(f"  期望: {expected_output} {status}")
    print()

