# 基于权重的幻想生成系统

## 概述

基于权重的幻想生成系统是FakeMan项目的新功能，它根据历史经验中的欲望满足度变化，按权重优先级生成幻想。这个系统取代了原有的简单模板式幻想生成，提供了更加动态和个性化的幻想内容。

## 核心特性

### 1. 权重计算机制

系统为每个历史经验计算两种权重：

#### 变化幅度权重 (Magnitude Weight)
- **计算公式**: 所有欲望变化的绝对值之和
- **含义**: 变化越大的经验，权重越高
- **示例**: 如果某次经验导致 `understanding` 提升 0.2，`information` 提升 0.1，则幅度权重为 0.3

#### 时间权重 (Time Weight)
- **计算公式**: `exp(-decay_factor * time_diff)`
- **含义**: 距离现在越近的经验，权重越高；越远的经验，权重越低
- **衰减因子**: 默认为 0.0001，可调整

#### 总权重 (Total Weight)
- **计算公式**: `0.7 * magnitude_weight + 0.3 * time_weight`
- **权重分配**: 
  - 70% 基于变化幅度（更重视经验的影响力）
  - 30% 基于时间（保持时效性）

### 2. 幻想类型

系统根据欲望变化的正负性生成两种幻想：

#### 回忆重现 (Positive Experience)
- **触发条件**: 欲望变化为正值
- **幻想内容**: "如果我能再次遇到类似的情况，采用同样的手段..."
- **目的**: 希望重现美好的经验

#### 改变过去 (Negative Experience)
- **触发条件**: 欲望变化为负值
- **幻想内容**: "如果回到那个情况，我不应该采用那个手段，而是应该..."
- **目的**: 反思失败，希望改变过去的决策

### 3. 状态判断机制

系统使用 `long_term_memory.json` 而非 `scenario_state.json` 来判断当前状态：

#### 从长期记忆推断状态
- **记忆数量**: 反映系统的经验积累
- **最近模式**: 分析最近的记忆，识别主导主题
- **情感基调**: 基于正面/负面记忆比例判断
- **交流者信息**: 从记忆中提取互动对象和关系

#### 状态对幻想的影响
- **负面基调 + 正面记忆**: 幻想强度"强烈"（更容易怀念过去）
- **正面基调 + 负面记忆**: 幻想强度"轻微"（不太在意过去失败）
- **其他情况**: 幻想强度"中等"

## 使用方法

### 基本使用

```python
from memory.database import MemoryDatabase
from memory.long_term_memory import LongTermMemory
from scenario.weighted_fantasy_generator import WeightedFantasyGenerator

# 初始化记忆系统
memory_db = MemoryDatabase('data/experiences.json')
long_memory = LongTermMemory('data/long_term_memory.json')

# 创建幻想生成器
fantasy_gen = WeightedFantasyGenerator(
    memory_database=memory_db,
    long_term_memory=long_memory,
    time_decay_factor=0.0001  # 可选：调整时间衰减速度
)

# 生成幻想
fantasies = fantasy_gen.generate_fantasies(
    num_fantasies=3,        # 生成3个幻想
    min_magnitude=0.05      # 最小变化幅度阈值
)

# 获取幻想摘要
summary = fantasy_gen.get_fantasy_summary(fantasies)
print(summary)
```

### 集成到场景模拟器

```python
from scenario import ScenarioSimulator

# 初始化场景模拟器（自动使用long_term_memory判断状态）
simulator = ScenarioSimulator(
    memory_database=memory_db,
    long_term_memory=long_memory,
    use_long_memory_for_state=True  # 使用long_term_memory而非scenario_state.json
)

# 生成幻想手段（自动使用权重系统）
current_desires = {
    'existing': 0.3,
    'power': 0.2,
    'understanding': 0.3,
    'information': 0.2
}

fantasy_means = simulator.generate_fantasy_means(
    current_desires=current_desires,
    context="当前情境",
    num_fantasies=3,
    use_weighted=True  # 使用基于权重的幻想生成
)
```

### 获取高权重经验

```python
# 获取权重最高的经验
weighted_exps = fantasy_gen.get_weighted_experiences(
    limit=5,              # 返回前5个
    min_magnitude=0.05    # 最小变化幅度
)

for exp in weighted_exps:
    print(f"总权重: {exp.total_weight:.4f}")
    print(f"幅度权重: {exp.magnitude_weight:.3f}")
    print(f"时间权重: {exp.time_weight:.3f}")
    print(f"情境: {exp.context}")
    print(f"手段: {exp.means}")
    print()
```

## 配置参数

### WeightedFantasyGenerator 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `memory_database` | MemoryDatabase | None | 经验数据库实例 |
| `long_term_memory` | LongTermMemory | None | 长期记忆实例 |
| `time_decay_factor` | float | 0.001 | 时间衰减因子（越大衰减越快） |
| `min_weight_threshold` | float | 0.01 | 最小权重阈值 |

### generate_fantasies 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `num_fantasies` | int | 3 | 生成幻想数量 |
| `min_magnitude` | float | 0.1 | 最小变化幅度 |

## 输出格式

### 幻想对象结构

```python
{
    'type': str,              # 幻想类型：'回忆重现' 或 '改变过去'
    'intensity': str,         # 强度：'强烈'、'中等'、'轻微'
    'weight': float,          # 总权重
    'condition': str,         # 幻想条件
    'action': str,            # 建议行动
    'expectation': str,       # 期望结果
    'affected_desire': str,   # 受影响的欲望
    'original_change': float, # 原始变化值
    'timestamp': float,       # 原始经验时间戳
    'time_ago_seconds': float # 距今秒数
}
```

## 示例输出

```
当前有 3 个幻想：

1. [回忆重现] (中等强度，权重=0.475)
   时间: 1.0小时前
   如果我能再次遇到类似'用户问：什么是FakeMan？...'的情况
   我应该采用同样的手段：'详细解释系统'
   这样可以再次提升understanding欲望（上次提升了0.200）

2. [回忆重现] (中等强度，权重=0.466)
   时间: 5分钟前
   如果我能再次遇到类似'用户问：你好吗？...'的情况
   我应该采用同样的手段：'友好回应'
   这样可以再次提升understanding欲望（上次提升了0.150）

3. [改变过去] (中等强度，权重=0.422)
   时间: 2分钟前
   如果回到'长时间无用户输入...'的情况
   我不应该采用'主动发起对话'，而是应该...
   这样可以避免existing欲望下降（上次下降了0.080）
```

## 架构设计

### 类图

```
WeightedFantasyGenerator
├── memory_database (MemoryDatabase)
├── long_term_memory (LongTermMemory)
├── calculate_magnitude_weight()
├── calculate_time_weight()
├── calculate_total_weight()
├── get_weighted_experiences()
├── get_current_state_from_long_memory()
├── generate_fantasy_for_experience()
└── generate_fantasies()

ScenarioSimulator
├── fantasy_generator (WeightedFantasyGenerator)
├── _create_scenario_from_long_memory()
├── generate_weighted_fantasies()
└── generate_fantasy_means()
```

### 数据流

```
experiences.json → MemoryDatabase → WeightedFantasyGenerator
                                            ↓
long_term_memory.json → LongTermMemory → 当前状态判断
                                            ↓
                                      权重计算 + 幻想生成
                                            ↓
                                      幻想列表输出
```

## 与原系统的区别

| 特性 | 原系统 | 新系统 |
|------|--------|--------|
| 幻想来源 | 预定义模板 | 历史经验 |
| 优先级 | 基于当前欲望 | 基于经验权重 |
| 个性化 | 低 | 高 |
| 动态性 | 静态模板 | 动态生成 |
| 状态判断 | scenario_state.json | long_term_memory.json |
| 时间因素 | 不考虑 | 指数衰减 |

## 测试

运行测试脚本：

```bash
python test_weighted_fantasy.py
```

测试将：
1. 创建测试经验数据
2. 计算经验权重
3. 生成幻想
4. 输出详细结果

## 文件位置

- **核心模块**: `scenario/weighted_fantasy_generator.py`
- **集成模块**: `scenario/scenario_simulator.py`
- **测试脚本**: `test_weighted_fantasy.py`
- **文档**: `docs/WEIGHTED_FANTASY_SYSTEM.md`

## 未来改进

1. **机器学习优化**: 使用ML模型自动调整权重系数
2. **复杂模式识别**: 识别更复杂的经验模式
3. **幻想实现度追踪**: 追踪幻想是否在后续经验中实现
4. **群体幻想**: 基于多个相关经验生成组合幻想
5. **情感强度调节**: 更细粒度的幻想强度控制

## 贡献

如需改进或扩展此系统，请：
1. 在 `scenario/weighted_fantasy_generator.py` 中修改核心逻辑
2. 在 `test_weighted_fantasy.py` 中添加测试用例
3. 更新本文档

## 版本历史

- **v1.0.0** (2025-10-24): 初始版本
  - 实现基于权重的幻想生成
  - 集成到场景模拟器
  - 使用long_term_memory判断状态

