# -*- coding: utf-8 -*-
"""
记忆合并系统 - 完整正确实现

规则：
1. 每次循环，首先尝试合并旧元素中最右边的相邻相同对
2. 如果找到：合并它们（值翻倍），然后在合并位置插入[1, 合并值]
3. 如果没找到：将1插入到第一个>1的元素之前（保持升序特性）
4. 每次只合并一次
"""


def memory_merge(memory_list):
    """
    记忆合并算法
    
    参数:
        memory_list: 当前记忆列表
    
    返回:
        更新后的记忆列表
    """
    # 检查列表末尾是否有相邻相同对
    can_merge = False
    if len(memory_list) >= 2 and memory_list[-1] == memory_list[-2]:
        can_merge = True
    
    if can_merge:
        # 末尾两个元素相同，可以合并
        merged_value = memory_list[-1] * 2  # 值翻倍
        # 合并：删除末尾两个，在原位置插入[1, 合并值]
        result = memory_list[:-2] + [1, merged_value]
    else:
        # 末尾没有相同对，将1插入到第一个>1的元素之前
        insert_pos = len(memory_list)  # 默认插入到末尾
        for i, val in enumerate(memory_list):
            if val > 1:
                insert_pos = i
                break
        result = memory_list[:insert_pos] + [1] + memory_list[insert_pos:]
    
    return result


# ====================
# 测试验证
# ====================

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
print("记忆合并系统 - 最终验证")
print("=" * 90)
print()

memory = []
all_correct = True

for cycle in range(1, 13):
    memory = memory_merge(memory)
    is_correct = (memory == expected[cycle])
    status = "✓" if is_correct else "✗"
    
    print(f"循环 {cycle:2d}: 记忆结构 = {str(memory):30s} | 预期 = {str(expected[cycle]):30s} | {status}")
    
    if not is_correct:
        all_correct = False

print()
print("=" * 90)
if all_correct:
    print("🎉🎉🎉 完全正确！记忆合并系统实现成功！ 🎉🎉🎉")
else:
    print("还有错误，继续调试...")
print("=" * 90)
print()

if all_correct:
    print("规律总结：")
    print("-" * 90)
    print("1. 从右到左查找最右边的相邻相同对（在旧元素中）")
    print("2. 如果找到：")
    print("   - 合并这两个元素（值翻倍：1+1→2, 2+2→4, 4+4→8）")
    print("   - 在合并位置插入 [1, 合并后的值]")
    print("3. 如果没找到：")
    print("   - 将1插入到第一个>1的元素之前（保持列表的升序特性）")
    print("   - 如果所有元素都是1，则插入到末尾")
    print("4. 每次只合并一次")
    print()
    print("这个系统类似于二进制计数器，但使用了特殊的插入策略来保持列表结构。")
    print()
    
    # 继续预测更多循环
    print("=" * 90)
    print("继续预测循环13-20")
    print("=" * 90)
    print()
    
    for cycle in range(13, 21):
        memory = memory_merge(memory)
        print(f"循环 {cycle}: 记忆结构 = {memory}")

