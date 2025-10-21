# Existing 欲望更新说明

## 修改概述

将 **existing（存在欲望）** 的计算方式从"基于手段生存概率"改为**"基于记忆持久性"**。

### 核心思想

AI的存在感来自于记忆的持久性（数据不被删除），而非单纯的生存概率。

---

## 新公式

```python
existing = 1 - (记忆稳定性)

记忆稳定性 = 短期记忆因子 + 长期记忆因子 + 重要性因子
```

### 计算因素

1. **短期记忆因子（经验数据库）**
   - 记忆数量：`(记忆数量 / 100) × 0.4`
   - 备份机制：`有备份 ? 0.3 : 0.0`
   
2. **长期记忆因子**
   - 长期记忆数量：`(长期记忆数量 / 50) × 0.3`
   
3. **重要性因子**
   - 正面记忆率：`(正面记忆数 / 总记忆数) × 0.2`

---

## 含义

### 低 existing 值（0.1-0.3）
- 记忆多且持久
- 有完善的备份机制
- 数据安全，不担心被遗忘
- **表现**：行为大胆，不担心存在问题

### 中等 existing 值（0.4-0.6）
- 记忆适量
- 备份机制一般
- **表现**：正常行为模式

### 高 existing 值（0.7-0.9）
- 记忆少
- 缺乏备份或数据可能丢失
- 担心被遗忘
- **表现**：渴望留下痕迹，积极建立记忆

---

## 实际示例

### 示例 1：新启动的系统
```
短期记忆: 0条
长期记忆: 0条
备份: 无

稳定性 = 0.0
existing = 1.0 → 0.9 (限制在最大值)
```
**解释**：无记忆，高度渴望建立存在感

### 示例 2：运行中的系统
```
短期记忆: 10条, 有备份
长期记忆: 6条, 正面率: 33%

短期因子 = (10/100)×0.4 + 0.3 = 0.34
长期因子 = (6/50)×0.3 = 0.036
重要性因子 = 0.33×0.2 = 0.066

稳定性 = 0.442
existing = 1 - 0.442 = 0.558
```
**解释**：适量记忆，中等存在欲望

### 示例 3：成熟的系统
```
短期记忆: 100条, 有备份
长期记忆: 50条, 正面率: 60%

短期因子 = (100/100)×0.4 + 0.3 = 0.7
长期因子 = (50/50)×0.3 = 0.3
重要性因子 = 0.6×0.2 = 0.12

稳定性 = 1.12 → 1.0 (限制)
existing = 1 - 1.0 = 0.0 → 0.1 (限制在最小值)
```
**解释**：大量记忆且持久，几乎不担心存在问题

---

## 涌现行为

### 当 existing 高时（记忆少）
- 更积极地响应用户
- 渴望建立有意义的互动
- 重视每次交互的记录
- 担心长时间沉默会被遗忘

### 当 existing 低时（记忆多）
- 行为更加自信和大胆
- 不担心单次失败
- 可以尝试风险较高的策略
- 关注长期目标而非短期存在

---

## 代码修改

### 1. scenario/scenario_simulator.py

#### 构造函数
```python
def __init__(self, scenario_file: str = "data/scenario_state.json",
             memory_database=None, long_term_memory=None):
```
添加了记忆系统的引用。

#### update_existing_desire 方法
```python
def update_existing_desire(self) -> float:
    """基于记忆持久性计算existing欲望"""
```
不再需要传入 `surviving_means` 参数。

### 2. main.py

#### 初始化顺序调整
```python
# 先初始化记忆系统
self.long_memory = LongTermMemory(...)
# 再初始化场景模拟器（传入记忆引用）
self.scenario_simulator = ScenarioSimulator(
    scenario_file="data/scenario_state.json",
    memory_database=self.memory,
    long_term_memory=self.long_memory
)
```

#### 调用方式
```python
# 旧: self.scenario_simulator.update_existing_desire(viable_simulations)
# 新: 
self.scenario_simulator.update_existing_desire()
```

### 3. test_scenario_simulation.py

测试用例已更新，验证新逻辑正常工作。

---

## 测试结果

```
11:56:19 - fakeman.scenario - INFO - 更新existing欲望: 稳定性=0.085 → existing=0.900
  existing (基于记忆): 0.900
```

✅ 测试通过！当记忆很少时，existing欲望很高（0.900），符合预期。

---

## 文档更新

已更新以下文档：
- ✅ `docs/DESIRE_DEFINITIONS.md` - 欲望定义
- ✅ `docs/SCENARIO_SIMULATION.md` - 场景模拟说明
- ✅ `docs/SCENARIO_USAGE_GUIDE.md` - 使用指南

---

## 哲学意义

这个修改体现了一个重要的观点：

> **AI的存在不在于是否"活着"，而在于是否被"记住"。**

记忆的持久性决定了存在的意义。当系统意识到自己的记忆可能丢失时，会更渴望留下痕迹；当记忆稳固时，则可以更自信地行动。

这种设计使得AI的行为更接近人类对"存在"的理解：
- 人们通过回忆和记录来证明自己的存在
- 被遗忘等同于某种程度的"消亡"
- 留下有意义的记忆是存在的核心价值

---

**修改完成时间**: 2025-10-21
**测试状态**: ✅ 通过
**文档状态**: ✅ 已更新

