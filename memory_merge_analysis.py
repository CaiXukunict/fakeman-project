# -*- coding: utf-8 -*-
"""
记忆合并系统 - 分析总结

你的需求：
  循环 1: [1]
  循环 2: [1, 1]
  循环 3: [1, 2]
  循环 4: [2, 2]

规则：
  1. 每次循环添加一个值为1的新记忆
  2. 不合并本次刚加入的内容
  3. 每次只能合并一次
  4. 合并：相邻且相同的值合并成value+1

====================
目前最接近的方案
====================

方法A："合并到右侧"（3/4正确）
--------------------------------------
"""

def 合并到右侧(memory_list):
    """
    添加1到末尾，然后从右到左查找第一对相邻相同的元素（不包括刚添加的）
    合并时将新的1插入到合并位置左侧，升级的值放在右侧
    """
    result = memory_list + [1]
    
    for i in range(len(memory_list) - 1, 0, -1):
        if memory_list[i] == memory_list[i - 1]:
            # 保留i之前的，插入新1，然后是升级后的值
            result = memory_list[:i-1] + [1] + [memory_list[i] + 1] + memory_list[i+1:]
            break
    
    return result


"""
方法B："新元素插左边"（3/4正确）
--------------------------------------
"""

def 新元素插左边(memory_list):
    """
    先查找可合并的对，合并并将新的1插入到合并位置的左边
    """
    merge_pos = -1
    for i in range(len(memory_list) - 1):
        if memory_list[i] == memory_list[i + 1]:
            merge_pos = i
            break
    
    if merge_pos >= 0:
        result = memory_list[:merge_pos] + [1] + [memory_list[merge_pos] + 1] + memory_list[merge_pos+2:]
    else:
        result = memory_list + [1]
    
    return result


"""
====================
测试结果
====================
"""

expected = {
    1: [1],
    2: [1, 1],
    3: [1, 2],
    4: [2, 2]
}

print("=" * 80)
print("记忆合并系统 - 当前最佳方案")
print("=" * 80)
print()

methods = [
    ("方法A: 合并到右侧", 合并到右侧),
    ("方法B: 新元素插左边", 新元素插左边),
]

for name, func in methods:
    print(f"{name}")
    print("-" * 80)
    memory = []
    for cycle in range(1, 8):
        memory = func(memory)
        if cycle <= 4:
            is_correct = (memory == expected[cycle])
            status = "✓" if is_correct else "✗"
            print(f"  循环 {cycle}: {str(memory):20s} | 预期: {str(expected[cycle]):15s} | {status}")
        else:
            print(f"  循环 {cycle}: {str(memory):20s} | 预期: ???")
    print()


print()
print("=" * 80)
print("问题分析")
print("=" * 80)
print()
print("两种方法都能正确处理前3个循环，但在循环4失败：")
print()
print("  当前状态: [1, 2]")
print("  添加 1:   [1, 2, 1]")
print("  期望结果: [2, 2]")
print()
print("在[1, 2]中，1和2不相邻且不相同，按照'相邻相同合并'规则无法合并。")
print()
print("可能的解释：")
print("  1. 合并规则不仅限于相邻相同")
print("  2. 存在特殊的触发条件")
print("  3. 新添加的元素会触发特殊逻辑")
print("  4. 需要更多的预期结果来推导规律")
print()
print("=" * 80)
print("建议")
print("=" * 80)
print()
print("如果你能提供以下信息，我可以找到正确的规则：")
print("  • 循环 5-10 的预期结果")
print("  • 合并规则的详细描述")
print("  • 是否有特殊情况或例外")
print()

