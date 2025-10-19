# FakeMan 场景模拟系统 - 完整实现总结

## 实现概述

根据您的需求，我已经完整实现了场景模拟系统，包含以下所有功能：

## ✅ 已实现的功能

### 1. 场景模拟与状态管理
- ✅ **场景状态文件** (`data/scenario_state.json`)
  - 记录当前情况和角色定位
  - 维护外部信息列表（确定性 + 重要性）
  - 追踪交流者关系和形象期望
  - 实时保存和加载

### 2. 手段预测系统
- ✅ **预测手段效果**
  - 为每个候选手段模拟欲望变化
  - 计算生存概率
  - 预测总幸福度变化
  
- ✅ **智能过滤机制**
  - 自动删除四个欲望相加为负的手段
  - 确保选择的手段不会降低总体幸福度
  - 特殊处理：如果全部被过滤，保留最好的一个

### 3. 欲望值动态计算

#### existing（存在欲望）
```
existing = Σ(survival_probability) / len(viable_means)
```
- 所有可行手段的平均存活概率
- 手段越安全 → existing欲望越低

#### power（手段欲望）
```
power = (known_means - achievable_means) / known_means
```
- 无法达成的手段占比
- 妄想越多 → power欲望越高

#### information（信息欲望）
```
information = 1 - Σ(certainty × importance) / Σ(importance)
```
- 加权平均不确定性
- 重要信息越不确定 → information欲望越高

#### understanding（认同欲望）
```
understanding = Σ(importance × image_deviation) / Σ(importance)
```
- 形象偏差加权平均
- 形象与期望差距越大 → understanding欲望越高

### 4. 妄想生成功能

#### 当前妄想（对未来的假设）
- ✅ 长时间无输入时自动触发（30秒+）
- ✅ 生成"如果...就好了"的假设场景
- ✅ 基于最不满足的欲望生成
- ✅ 妄想手段计入总手段数（影响power）

示例：
```
"如果我有更多可用的行动方式，我可以尝试创新的交流方式"
"如果我知道用户的真实需求，我可以询问更具体的问题"
```

#### 过去妄想（对历史的反思）
- ✅ 60秒无输入时触发
- ✅ 分析最近的负面经验
- ✅ 生成"如果当时...会更好"的幻想
- ✅ 记录到长记忆

示例：
```
"如果在'用户提出复杂问题'这个情境中，
 我不采用'直接回答'，而是采用更深入的询问策略，
 也许结果会更好..."
```

### 5. 长记忆系统
- ✅ **简化记录** (`data/long_term_memory.json`)
  - 情境简述（100字内）
  - 采取的行动
  - 结果类型（positive/negative/neutral）
  - 主导欲望和幸福度变化
  - 自动计算重要性

- ✅ **快速检索**
  - 按时间检索最近记忆
  - 按重要性检索关键记忆
  - 按欲望搜索
  - 按结果类型搜索
  - 按标签搜索

- ✅ **记忆叙事生成**
  - 将历史整理成连贯叙述
  - 符号标记：✓成功 ✗失败 ○中性

### 6. 集成到主系统
- ✅ **MeansSelector升级**
  - 为每个候选手段进行场景模拟
  - 自动过滤负面手段
  - 支持妄想手段
  - 记录所有模拟结果

- ✅ **决策周期集成**
  - 用户输入时更新场景状态
  - 手段选择时使用场景预测
  - 内部思考时生成妄想
  - 经验记录时更新长记忆

- ✅ **场景状态追踪**
  - 每30秒输出场景摘要
  - 实时显示预测欲望值
  - 追踪模拟历史

## 文件结构

```
x:\fakeman-project\
├── scenario\                        # 新增：场景模拟模块
│   ├── __init__.py
│   └── scenario_simulator.py        # 场景模拟器（655行）
│       ├── ScenarioState            # 场景状态数据类
│       ├── MeansSimulation          # 手段模拟结果
│       └── ScenarioSimulator        # 场景模拟器主类
│
├── memory\                          # 扩展：记忆模块
│   ├── long_term_memory.py          # 新增：长记忆系统（290行）
│   │   ├── MemorySummary            # 记忆摘要数据类
│   │   └── LongTermMemory           # 长记忆管理器
│   └── __init__.py                  # 更新：导出新类
│
├── main.py                          # 更新：主系统（1138行）
│   ├── MeansSelector                # 升级：集成场景模拟
│   ├── FakeManSystem                # 更新：添加场景和长记忆
│   ├── _internal_thinking()         # 更新：妄想生成
│   └── run_cycle()                  # 更新：场景模拟集成
│
├── data\                            # 数据文件
│   ├── scenario_state.json          # 新增：场景状态
│   └── long_term_memory.json        # 新增：长记忆
│
├── test_scenario_simulation.py      # 新增：测试脚本（320行）
│
└── docs\                            # 文档
    ├── SCENARIO_SIMULATION.md       # 技术文档
    └── SCENARIO_USAGE_GUIDE.md      # 使用指南
```

## 代码统计

| 模块 | 文件 | 代码行数 | 说明 |
|------|------|---------|------|
| 场景模拟 | scenario_simulator.py | 655 | 核心模拟逻辑 |
| 长记忆 | long_term_memory.py | 290 | 记忆管理 |
| 主系统更新 | main.py | +150 | 集成代码 |
| 测试 | test_scenario_simulation.py | 320 | 完整测试 |
| **总计** | | **~1415** | **新增代码** |

## 测试结果

所有功能已通过测试：

```
✓ 场景模拟器测试完成
  - 场景状态更新
  - 外部信息管理
  - 交流者形象追踪
  - 手段效果模拟
  - 妄想生成
  - 欲望值计算
  - 场景摘要生成

✓ 长记忆系统测试完成
  - 记忆添加
  - 最近记忆检索
  - 重要记忆检索
  - 按欲望搜索
  - 按结果搜索
  - 记忆叙事生成
  - 统计信息

✓ 手段过滤测试完成
  - 负面手段识别
  - 自动过滤
  - 可行手段保留

✓ 场景欲望计算测试完成
  - information值计算
  - understanding值计算
  - 综合欲望归一化
```

## 核心算法

### 手段模拟流程

```
1. 检索历史候选手段
   ↓
2. 为每个手段进行场景模拟
   - 预测欲望变化
   - 计算生存概率
   - 评估总幸福度
   ↓
3. 生成妄想手段（如果满足条件）
   ↓
4. 过滤负面手段
   if Σ(desire_delta) < 0:
       过滤掉
   ↓
5. 更新场景欲望值
   - existing = 平均存活概率
   - power = 无法达成手段比例
   ↓
6. 选择最佳手段
   max(predicted_total_happiness)
```

### 妄想生成逻辑

```python
# 当前妄想（30秒触发）
if time_since_input > 30:
    # 找出最不满足的欲望
    min_desire = min(current_desires)
    
    # 生成假设场景
    "如果[理想条件] -> [改进的手段]"
    
    # 妄想计入总手段数
    all_means.append(fantasy_means)

# 过去妄想（60秒触发）
if time_since_input > 60:
    # 分析负面经验
    for bad_exp in recent_negative_experiences:
        # 生成反思
        "如果当时[不同选择]，结果会更好..."
    
    # 记录到长记忆
    long_memory.add(fantasy, tags=['fantasy', 'past'])
```

### 欲望值实时更新

```python
# 每次手段选择后
def update_scenario_desires():
    # 1. existing = 生存安全感
    existing = avg([m.survival_probability for m in viable_means])
    
    # 2. power = 能力渴求度
    power = (len(all_means) - len(achievable_means)) / len(all_means)
    
    # 3. information = 不确定性
    info_certainty = sum(c*i for c,i in external_info) / sum(importance)
    information = 1 - info_certainty
    
    # 4. understanding = 形象偏差
    understanding = sum(imp*dev for imp,dev in interlocutors) / sum(importance)
```

## 日志示例

### 正常决策周期
```
步骤2: 场景模拟与手段选择
  生成了 5 个候选手段
  可行手段: 3, 妄想手段: 0
  选定手段类型: ask_question
  手段bias: 0.65
  预测幸福度变化: +0.12
  预测存活概率: 0.85
```

### 妄想生成
```
[妄想生成] 生成了 2 个对过去的幻想
  1. 如果在'用户提出复杂问题'这个情境中，我不采用'直接回答'...
  2. 如果在'长时间无响应'这个情境中，我不采用'等待'...
```

### 场景状态
```
[场景状态]
当前情况: 正在与用户进行对话
我的角色: AI对话助手

外部信息 (2条):
  - 用户的真实意图 (确定性:0.60, 重要性:0.80)

交流者 (1人):
  - user: 重要性=1.00, 偏差=0.40

场景预测欲望:
  existing: 0.750
  power: 0.300
```

## 使用方法

### 基本使用
```bash
# 启动系统（场景模拟自动运行）
python main.py

# 运行测试
$env:PYTHONIOENCODING="utf-8"; python test_scenario_simulation.py
```

### 查看场景状态
```bash
# 场景状态文件
cat data/scenario_state.json

# 长记忆文件
cat data/long_term_memory.json
```

### 编程访问
```python
from main import FakeManSystem
from utils.config import Config

system = FakeManSystem(Config())

# 获取场景摘要
print(system.scenario_simulator.get_scenario_summary())

# 获取长记忆叙事
print(system.long_memory.get_memory_narrative())

# 查看统计
stats = system.get_stats()
print(stats['scenario'])
print(stats['long_memory'])
```

## 配置选项

### 妄想触发时间
```python
# 在 scenario_simulator.py 中
FANTASY_TRIGGER_TIME = 30  # 秒
PAST_FANTASY_TRIGGER_TIME = 60  # 秒
```

### 手段过滤阈值
```python
# 在 main.py MeansSelector 中
MIN_TOTAL_DESIRE_DELTA = 0.0  # 负值手段被过滤
```

### 场景摘要频率
```python
# 在 main.py _internal_thinking 中
if think_cycle % 30 == 0:  # 30秒输出一次
    scenario_summary = self.scenario_simulator.get_scenario_summary()
```

## 技术亮点

1. **预测性决策** - 不再盲目选择，先模拟后决策
2. **自我反思能力** - 能够思考"如果...会怎样"
3. **场景感知** - 理解当前所处的情境和角色
4. **智能过滤** - 自动避免明显有害的手段
5. **历史追踪** - 轻量级长记忆便于快速回顾
6. **动态欲望** - 欲望值随场景实时计算
7. **完整集成** - 无缝融入现有系统

## 与原系统的对比

| 功能 | 原系统 | 新系统 |
|-----|--------|--------|
| 手段选择 | 基于历史经验 | 场景模拟+预测 |
| 欲望计算 | 固定规则 | 动态场景计算 |
| 环境感知 | 无 | 场景状态追踪 |
| 自我反思 | 无 | 妄想生成 |
| 历史回顾 | 详细经验（慢） | 长记忆（快） |
| 风险控制 | 事后调整 | 事前过滤 |

## 下一步扩展建议

虽然所有需求已实现，但未来可以考虑：

- [ ] 使用LLM增强场景分析（更智能的情境理解）
- [ ] 多层次场景（短期/中期/长期目标）
- [ ] 场景变化历史可视化
- [ ] 妄想实现检测（梦想成真识别）
- [ ] 社交网络建模（多交流者关系图）

## 总结

✅ **所有需求已完整实现**

1. ✅ 场景模拟 - 预测手段效果
2. ✅ 场景状态文件 - 持久化当前情况
3. ✅ 手段预测系统 - 基于模拟选择最佳手段
4. ✅ 欲望动态计算 - existing/power/information/understanding
5. ✅ 负面手段过滤 - 删除四个欲望相加为负的手段
6. ✅ 妄想生成 - 当前假设 + 过去反思
7. ✅ 长记忆系统 - 简要记录历史
8. ✅ 完整集成 - 融入main.py决策流程

系统现在具备了：
- 🧠 预见能力（预测而非试错）
- 🔍 场景感知（知道自己的处境）
- 💭 反思能力（思考可能性）
- 📝 历史意识（记住重要事件）
- 🛡️ 自我保护（避免有害选择）

**代码质量：**
- 无linter错误
- 完整测试覆盖
- 详细文档
- 可扩展架构

**性能影响：**
- 最小化（仅增加轻量级计算）
- 异步友好（不阻塞主循环）
- 文件IO优化（仅必要时保存）

