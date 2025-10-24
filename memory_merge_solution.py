# -*- coding: utf-8 -*-
"""
记忆合并系统实现

根据你的需求：
  循环 1: 记忆结构 = [1]
  循环 2: 记忆结构 = [1, 1]
  循环 3: 记忆结构 = [1, 2]
  循环 4: 记忆结构 = [2, 2]

规则：
  • 每次循环添加一个值为1的新记忆
  • 不合并本次刚加入的内容
  • 每次只能合并一次
  • 合并：相邻且相同的值合并成value+1
"""


def memory_merge_method_a(memory_list):
    """
    方法A：合并到右侧位置，新元素插入左边
    
    此方法能正确处理循环1-3，但循环4结果为[1,2,1]而非[2,2]
    
    流程：
    1. 从右到左查找第一对相邻相同的旧元素
    2. 如果找到，删除左边的元素，保留右边并升级
    3. 将新的1插入到合并位置的左侧
    4. 如果没找到可合并的，直接在末尾添加1
    """
    result = memory_list + [1]
    
    for i in range(len(memory_list) - 1, 0, -1):
        if memory_list[i] == memory_list[i - 1]:
            result = memory_list[:i-1] + [1] + [memory_list[i] + 1] + memory_list[i+1:]
            break
    
    return result


def memory_merge_method_b(memory_list):
    """
    方法B：新元素插入到合并位置左侧
    
    此方法也能正确处理循环1-3，但循环4结果为[1,2,1]而非[2,2]
    
    流程：
    1. 从左到右查找第一对相邻相同的元素
    2. 如果找到，合并它们并将新的1插入到合并位置左侧
    3. 如果没找到，直接在末尾添加1
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


# ====================
# 测试演示
# ====================

if __name__ == "__main__":
    expected = {
        1: [1],
        2: [1, 1],
        3: [1, 2],
        4: [2, 2]
    }
    
    print("=" * 80)
    print("记忆合并系统 - 实现演示")
    print("=" * 80)
    print()
    print("你的预期结果：")
    for cycle, result in expected.items():
        print(f"  循环 {cycle}: {result}")
    print()
    print("=" * 80)
    print()
    
    methods = [
        ("方法A (合并到右侧)", memory_merge_method_a),
        ("方法B (新元素插左边)", memory_merge_method_b),
    ]
    
    for name, func in methods:
        print(f"{name}")
        print("-" * 80)
        memory = []
        for cycle in range(1, 10):
            memory = func(memory)
            if cycle <= 4:
                is_correct = (memory == expected[cycle])
                status = "✓" if is_correct else "✗"
                print(f"  循环 {cycle}: {str(memory):20s} | 预期: {str(expected[cycle]):15s} | {status}")
            else:
                print(f"  循环 {cycle}: {str(memory):20s}")
        print()
    
    print()
    print("=" * 80)
    print("分析说明")
    print("=" * 80)
    print()
    print("两种方法都成功实现了前3个循环的预期结果。")
    print()
    print("循环4的问题：")
    print("  • 从状态 [1, 2] 开始")
    print("  • 添加1后变成 [1, 2, 1]")
    print("  • 在旧元素 [1, 2] 中没有相邻相同的元素可以合并")
    print("  • 按现有规则无法得到期望的 [2, 2]")
    print()
    print("可能需要的额外信息：")
    print("  1. 循环5-10的预期结果（用于推导更复杂的规律）")
    print("  2. 是否有特殊的合并规则（如非相邻合并）")
    print("  3. '不合并本次加入的内容'的精确定义")
    print("  4. 是否允许多步操作（如先合并，触发连锁反应）")
    print()
    print("如果你能提供更多循环的预期结果，我可以找出完整的规律！")
    print()

