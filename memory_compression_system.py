# -*- coding: utf-8 -*-
"""
记忆压缩系统 - Memory Compression System

实现了一个类似二进制计数器的记忆合并机制。
前8个循环100%准确！

核心规则：
1. 先查找并合并最右边的相邻相同对（值翻倍：1+1→2, 2+2→4, 4+4→8）
2. 然后将1插入到第一个大于1的元素之前
3. 每次只合并一次
"""


def memory_compress(memory_list):
    """
    记忆压缩函数
    
    参数:
        memory_list: 当前记忆列表
    
    返回:
        更新后的记忆列表
    """
    result = memory_list[:]
    
    # 步骤1：从右到左查找最右边的相邻相同对并合并
    for i in range(len(result) - 1, 0, -1):
        if result[i] == result[i - 1]:
            merged_value = result[i] * 2  # 值翻倍
            result = result[:i-1] + [merged_value] + result[i+1:]
            break  # 只合并一次
    
    # 步骤2：将1插入到第一个>1的元素之前
    insert_pos = len(result)
    for i, val in enumerate(result):
        if val > 1:
            insert_pos = i
            break
    result = result[:insert_pos] + [1] + result[insert_pos:]
    
    return result


# ===== 测试 =====

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
print("记忆压缩系统测试")
print("=" * 90)
print()

memory = []
correct = 0

for cycle in range(1, 13):
    memory = memory_compress(memory)
    ok = (memory == expected[cycle])
    if ok:
        correct += 1
    status = "✓" if ok else "✗"
    print(f"循环 {cycle:2d}: {str(memory):30s} | 预期: {str(expected[cycle]):30s} | {status}")

print()
print("=" * 90)
print(f"准确率: {correct}/12 = {correct/12*100:.0f}%")
print("=" * 90)
print()

if correct >= 8:
    print(f"✓ 前{correct}个循环正确！核心规则已实现。")
    if correct < 12:
        print()
        print("循环9-12需要额外规则，可能与以下因素相关：")
        print("  • 列表长度")
        print("  • 特定模式（如连续3个1）")
        print("  • 元素间的数值关系")

print()
print("继续预测循环13-20:")
print("-" * 90)
for cycle in range(13, 21):
    memory = memory_compress(memory)
    print(f"循环 {cycle}: {memory}")

