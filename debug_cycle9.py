# -*- coding: utf-8 -*-
"""
调试循环9
"""

# 循环8→9的转换
input_mem = [1, 1, 2, 4]
expected = [1, 1, 1, 2, 4]

print("=" * 80)
print("调试循环8→9")
print("=" * 80)
print()
print(f"输入: {input_mem}")
print(f"期望: {expected}")
print()

# 按我的逻辑：
print("我的逻辑:")
print("  1. 查找最右边的相邻相同对: [1,1] 在位置0-1")
print("  2. 合并: 1*2 = 2")
print("  3. 结果: [] + [1, 2] + [2, 4] = [1, 2, 2, 4]")
print()

# 但期望是[1,1,1,2,4]，长度增加了！
print("期望结果分析:")
print(f"  输入长度: {len(input_mem)}")
print(f"  期望长度: {len(expected)}")
print("  长度增加了1！说明没有合并，而是单纯添加了1")
print()

# 重新理解：也许只有在"末尾"有相邻相同对时才合并？
print("新猜想：只合并列表末尾的相邻相同对？")
print("  [1,1,2,4] 末尾是4，倒数第二是2，不相同")
print("  所以不合并，直接插入1")
print("  插入位置：第一个>1的元素之前 = 位置1")
print("  结果：[1] + [1] + [1,2,4] = [1,1,1,2,4] ✓")
print()

# 再看其他case
print("=" * 80)
print("验证其他case")
print("=" * 80)
print()

test_cases = [
    ([1, 1], [1, 2], "循环2→3: 末尾有[1,1]相同对"),
    ([1, 2, 2], [1, 1, 4], "循环5→6: 末尾有[2,2]相同对"),
    ([1, 2, 4], [1, 1, 2, 4], "循环7→8: 末尾没有相同对"),
]

for inp, exp, desc in test_cases:
    print(f"{desc}")
    print(f"  输入: {inp}")
    print(f"  末尾两个: {inp[-2:] if len(inp) >= 2 else inp}")
    has_tail_pair = len(inp) >= 2 and inp[-1] == inp[-2]
    print(f"  末尾是相同对: {has_tail_pair}")
    print(f"  期望: {exp}")
    print()

print("结论：只合并列表末尾的相邻相同对！")

