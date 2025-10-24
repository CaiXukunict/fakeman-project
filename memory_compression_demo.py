# -*- coding: utf-8 -*-
"""
记忆压缩系统演示

规则：
1. 每次循环添加一个新记忆（值为1）
2. 不合并本次刚加入的内容
3. 每次只能合并一次
4. 合并规则：找到相邻且相同的两个值，合并成一个value+1的值
"""


def compress_once(memory_list, exclude_last=False):
    """
    对记忆列表执行一次压缩（合并）
    
    参数:
        memory_list: 记忆列表
        exclude_last: 是否排除最后一个元素
    
    返回:
        (成功标志, 新列表)
    """
    if not memory_list:
        return False, memory_list
    
    # 确定搜索范围
    search_len = len(memory_list) - 1 if exclude_last else len(memory_list)
    
    if search_len < 2:
        return False, memory_list
    
    # 从左到右查找第一对相邻且相同的元素
    for i in range(search_len - 1):
        if memory_list[i] == memory_list[i + 1]:
            # 找到可合并的对，执行合并
            # 删除这两个元素，在同一位置添加一个升级的元素
            new_list = memory_list[:i] + [memory_list[i] + 1] + memory_list[i+2:]
            return True, new_list
    
    return False, memory_list


# 让我手动测试一下逻辑
print("手动测试压缩逻辑:")
print("=" * 60)

# 测试1: [1,1] 合并
test = [1, 1]
success, result = compress_once(test, exclude_last=False)
print(f"[1,1] 合并 (exclude_last=False) → {result} (期望: [2])")

# 测试2: [1,1,1] 不包括最后一个
test = [1, 1, 1]
success, result = compress_once(test, exclude_last=True)
print(f"[1,1,1] 合并前两个 (exclude_last=True) → {result} (期望: [2,1])")

print()
print("现在模拟你的预期流程:")
print("=" * 60)

# 循环1
mem = []
mem.append(1)
print(f"循环 1: {mem} (期望: [1])")

# 循环2
mem.append(1)
print(f"循环 2: {mem} (期望: [1,1])")

# 循环3
mem.append(1)  # 先添加
print(f"  添加后: {mem}")
success, mem = compress_once(mem, exclude_last=True)  # 再合并（不包括刚加的）
print(f"  合并后: {mem} (期望: [1,2])")

# 循环4
mem.append(1)
print(f"  添加后: {mem}")
success, mem = compress_once(mem, exclude_last=True)
print(f"  合并后: {mem} (期望: [2,2])")

print()
print("分析问题：")
print("=" * 60)
print("循环3得到[2,1]但期望[1,2]")
print("这意味着合并[1,1]应该得到[2]放在右边位置而不是左边")
print("也就是说，合并时应该保留右边的位置！")

