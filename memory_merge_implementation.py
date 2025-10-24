# -*- coding: utf-8 -*-
"""
记忆合并系统 - 最终实现

根据你的需求：
- 循环 1: [1]
- 循环 2: [1, 1]
- 循环 3: [1, 2]
- 循环 4: [2, 2]

规则：
1. 每次循环添加一个值为1的新记忆
2. 不合并本次刚加入的内容
3. 每次只能合并一次
4. 合并：相邻且相同的值合并成value+1

我将实现多个版本供你选择
"""


def 方法1_从左到右合并(memory_list):
    """
    添加1到末尾，然后从左到右查找第一对相邻相同的元素（不包括刚添加的）
    """
    result = memory_list + [1]
    
    # 查找范围：不包括最后一个元素
    for i in range(len(memory_list) - 1):
        if memory_list[i] == memory_list[i + 1]:
            # 合并：删除两个，在该位置添加升级的值，保留新添加的1
            result = memory_list[:i] + [memory_list[i] + 1] + memory_list[i+2:] + [1]
            break
    
    return result


def 方法2_从右到左合并(memory_list):
    """
    添加1到末尾，然后从右到左查找第一对相邻相同的元素（不包括刚添加的）
    """
    result = memory_list + [1]
    
    # 查找范围：不包括最后一个元素，从右到左
    for i in range(len(memory_list) - 1, 0, -1):
        if memory_list[i] == memory_list[i - 1]:
            # 合并
            result = memory_list[:i-1] + [memory_list[i] + 1] + memory_list[i+1:] + [1]
            break
    
    return result


def 方法3_合并到右侧(memory_list):
    """
    添加1，然后合并时将结果放在右侧位置
    [1,1,新1] → [1,2]而不是[2,1]
    """
    result = memory_list + [1]
    
    # 从右到左查找
    for i in range(len(memory_list) - 1, 0, -1):
        if memory_list[i] == memory_list[i - 1]:
            # 删除i-1，保留i并升级，加上新的1
            # [1,1] i=1: [:0] + [2] + [2:] + [1] = [] + [2] + [] + [1] = [2,1]
            # 还是不对...
            
            # 尝试：保留到i-1，跳过i和i+1，添加升级值，添加剩余，添加1
            # 不对，让我想想如何让2出现在右边...
            # [1,1] → 合并 → [2] → 但2应该在原来第二个1的位置
            # 如果添加新1后: [2,1]
            # 期望 [1,2]，说明合并后的2在原索引1，新1被"插入"到了...索引0?
            
            # 也许是：保留i之前的，插入新1，然后是升级后的值？
            result = memory_list[:i-1] + [1] + [memory_list[i] + 1] + memory_list[i+1:]
            break
    
    return result


def 方法4_新元素插左边(memory_list):
    """
    先合并旧元素，然后将新的1插入到合并位置的左边
    """
    # 先查找可合并的对
    merge_pos = -1
    for i in range(len(memory_list) - 1):
        if memory_list[i] == memory_list[i + 1]:
            merge_pos = i
            break  # 找到第一对
    
    if merge_pos >= 0:
        # 合并并插入新1
        # [1,1] 合并位置0: [:0] + [1] + [2] + [2:]
        result = memory_list[:merge_pos] + [1] + [memory_list[merge_pos] + 1] + memory_list[merge_pos+2:]
    else:
        # 无法合并，直接添加
        result = memory_list + [1]
    
    return result


# 测试所有方法
print("=" * 70)
print("测试不同的合并方法")
print("=" * 70)
print()

methods = [
    ("方法1_从左到右合并", 方法1_从左到右合并),
    ("方法2_从右到左合并", 方法2_从右到左合并),
    ("方法3_合并到右侧", 方法3_合并到右侧),
    ("方法4_新元素插左边", 方法4_新元素插左边),
]

expected = {
    1: [1],
    2: [1, 1],
    3: [1, 2],
    4: [2, 2]
}

for method_name, method_func in methods:
    print(f"{method_name}:")
    print("-" * 70)
    
    memory = []
    all_correct = True
    
    for cycle in range(1, 5):
        memory = method_func(memory)
        is_correct = (memory == expected[cycle])
        status = "✓" if is_correct else "✗"
        
        print(f"  循环 {cycle}: {str(memory):15s} | 预期: {str(expected[cycle]):15s} | {status}")
        
        if not is_correct:
            all_correct = False
    
    if all_correct:
        print(f"  >>> 此方法完全正确！ <<<")
    
    print()

