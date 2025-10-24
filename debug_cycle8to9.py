# -*- coding: utf-8 -*-
"""
详细调试循环8→9
"""

# 循环8的状态
state8 = [1, 1, 2, 4]
expected9 = [1, 1, 1, 2, 4]

print("=" * 80)
print("详细分析循环8→9")
print("=" * 80)
print()
print(f"循环8状态: {state8}")
print(f"期望循环9: {expected9}")
print()

print("按'先合并再添加'逻辑：")
print("  1. 查找相邻相同对（从右到左）")
print(f"     state8 = {state8}")
print("     找到 [1,1] 在位置0-1")
print("  2. 合并: 1*2 = 2")
print(f"     结果: [] + [2] + [2, 4] = [2, 2, 4]")
print("  3. 添加1到第一个>1的位置之前")
print("     第一个>1是位置0的2")
print(f"     结果: [] + [1] + [2, 2, 4] = [1, 2, 2, 4]")
print()
print(f"我得到: [1, 2, 2, 4]")
print(f"期望是: {expected9}")
print("不匹配！")
print()

print("=" * 80)
print("重新思考：也许不合并任何东西？")
print("=" * 80)
print()
print("如果 [1,1,2,4] 直接添加1:")
print("  插入到第一个>1的位置之前")
print("  第一个>1是位置2的2")
print(f"  结果: [1, 1] + [1] + [2, 4] = [1, 1, 1, 2, 4] ✓")
print()
print("匹配！")
print()

print("所以问题是：什么时候合并，什么时候不合并？")
print()

# 回顾所有case
print("=" * 80)
print("回顾所有有[1,1]的case")
print("=" * 80)
print()

cases = [
    (2, [1, 1], [1, 2], "合并了[1,1]"),
    (4, [1, 1, 2], [1, 2, 2], "合并了[1,1]"),
    (6, [1, 1, 4], [1, 2, 4], "合并了[1,1]"),
    (8, [1, 1, 2, 4], [1, 1, 1, 2, 4], "没有合并[1,1]！"),
    (9, [1, 1, 1, 2, 4], [1, 1, 2, 2, 4], "合并了某个[1,1]"),
]

for cycle, state, next_state, note in cases:
    print(f"循环{cycle}: {state} → {next_state}")
    print(f"  {note}")
    # 检查是否有连续3个1
    has_three_ones = False
    for i in range(len(state) - 2):
        if state[i:i+3] == [1, 1, 1]:
            has_three_ones = True
            break
    print(f"  有连续3个1: {has_three_ones}")
    print()

print("发现：循环8的[1,1,2,4]后面还有更大的数，所以[1,1]不合并？")

