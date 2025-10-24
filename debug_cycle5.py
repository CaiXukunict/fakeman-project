# -*- coding: utf-8 -*-
"""
调试循环4→5
"""

input_mem = [1, 1, 2]
expected = [1, 2, 2]

print("=" * 80)
print("调试循环4→5")
print("=" * 80)
print()
print(f"输入: {input_mem}")
print(f"期望: {expected}")
print()

print("观察：")
print("  输入有[1,1]在前面")
print("  期望变成[1,2,2]")
print("  这意味着前面的[1,1]被合并成了2！")
print()

print("新理解：")
print("  也许规则是：")
print("  1. 先检查是否有任何相邻相同对（不只是末尾）")
print("  2. 如果有，合并最右边的那对")
print("  3. 然后添加1")
print()

print("但这和之前的推理矛盾...")
print("让我重新看所有数据...")
print()

# 重新分析所有转换
all_data = {
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
print("重新分析所有长度变化")
print("=" * 80)
print()

for i in range(1, 12):
    curr = all_data[i]
    next_val = all_data[i + 1]
    len_change = len(next_val) - len(curr)
    
    print(f"循环 {i:2d} → {i+1:2d}: 长度 {len(curr)} → {len(next_val)} (变化: {len_change:+d})")
    
    if len_change == 0:
        print(f"  {curr} → {next_val}")
        print("  长度不变！说明添加1的同时合并了一对")
    elif len_change == 1:
        print(f"  {curr} → {next_val}")
        print("  长度+1，说明只添加了1，没有合并")
    elif len_change == -1:
        print(f"  {curr} → {next_val}")
        print("  长度-1，说明合并了两对或有特殊操作")
    
    print()

