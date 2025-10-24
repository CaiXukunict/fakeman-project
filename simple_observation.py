# -*- coding: utf-8 -*-
"""
最简单的观察：每次到底做了什么？
"""

data = {
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
print("观察：哪些位置的值发生了变化？")
print("=" * 80)
print()

for i in range(1, 12):
    curr = data[i]
    next_v = data[i + 1]
    
    print(f"循环 {i:2d} → {i+1:2d}:")
    print(f"  前: {curr}")
    print(f"  后: {next_v}")
    
    # 找出差异
    if len(next_v) > len(curr):
        print(f"  操作: 添加了元素，长度 {len(curr)} → {len(next_v)}")
    elif len(next_v) == len(curr):
        print(f"  操作: 长度不变，有合并发生")
        # 找具体哪里不同
        for j in range(min(len(curr), len(next_v))):
            if j < len(curr) and j < len(next_v) and curr[j] != next_v[j]:
                print(f"    位置{j}: {curr[j]} → {next_v[j]}")
    elif len(next_v) < len(curr):
        print(f"  操作: 长度减少，多次合并？")
    
    print()

print()
print("=" * 80)
print("关键观察：")
print("- 循环2,4,6都是[1,1,X...]格式，且都合并成了[1,2,X...]")
print("- 循环8是[1,1,2,4]但没合并，变成[1,1,1,2,4]")
print("- 区别在于：循环8的列表长度已经>=4？")
print("=" * 80)

