# -*- coding: utf-8 -*-
"""
分析完整数据找出规律
"""

# 完整数据
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
print("逐步分析每次转换")
print("=" * 80)
print()

for i in range(1, 12):
    current = data[i]
    next_val = data[i + 1]
    
    print(f"循环 {i} → {i+1}:")
    print(f"  当前: {current}")
    print(f"  添加1后: {current + [1]}")
    print(f"  结果: {next_val}")
    
    # 分析变化
    added = current + [1]
    if added == next_val:
        print(f"  ✓ 无合并，直接添加")
    else:
        print(f"  需要合并")
        # 找出哪里不同
        
    print()

print()
print("=" * 80)
print("观察总长度变化")
print("=" * 80)
print()

for i in range(1, 13):
    print(f"循环 {i:2d}: 长度={len(data[i]):2d}, 内容={data[i]}")

