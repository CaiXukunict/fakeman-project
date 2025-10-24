# -*- coding: utf-8 -*-
"""
测试插入逻辑
"""

# 关键case：没有可合并元素时，新的1插入到哪里？

test_cases = [
    # (输入, 期望输出, 说明)
    ([1, 2], [1, 1, 2], "循环3→4: 1插入到1和2之间"),
    ([1, 2, 4], [1, 1, 2, 4], "循环7→8: 1插入到1和2之间"),
    # 如果没有可合并的，1似乎插入到"第一个大于1的元素"之前
]

print("=" * 80)
print("分析无合并时的插入位置")
print("=" * 80)
print()

for input_mem, expected, desc in test_cases:
    print(f"{desc}")
    print(f"  输入: {input_mem}")
    print(f"  期望: {expected}")
    
    # 找插入位置：第一个>1的元素之前
    insert_pos = len(input_mem)  # 默认末尾
    for i, val in enumerate(input_mem):
        if val > 1:
            insert_pos = i
            break
    
    result = input_mem[:insert_pos] + [1] + input_mem[insert_pos:]
    status = "✓" if result == expected else "✗"
    print(f"  插入位置{insert_pos}: {result} {status}")
    print()

print()
print("=" * 80)
print("观察：1应该插入到第一个>1的元素之前！")
print("这样保持了某种'有序性'")
print("=" * 80)

