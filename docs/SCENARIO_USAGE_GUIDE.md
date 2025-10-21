# 场景模拟系统使用指南

## 快速开始

场景模拟系统已完全集成到FakeMan主系统中，启动后自动运行。

### 启动系统

```bash
python main.py
```

系统启动后会自动：
1. 加载或创建场景状态文件 (`data/scenario_state.json`)
2. 加载或创建长记忆文件 (`data/long_term_memory.json`)
3. 初始化场景模拟器和长记忆系统

### 测试场景模拟功能

```bash
# 设置编码并运行测试
$env:PYTHONIOENCODING="utf-8"; python test_scenario_simulation.py
```

## 主要特性

### 1. 场景感知手段选择

系统会为每个候选手段进行场景模拟，预测效果后再选择：

```
步骤2: 场景模拟与手段选择
  生成了 5 个候选手段
  可行手段: 3, 妄想手段: 1
  选定手段类型: ask_question
  选定手段描述: 通过提问获取信息
  手段bias: 0.65
  预测幸福度变化: +0.12
  预测存活概率: 0.85
```

**工作原理：**
- 从历史经验中检索候选手段
- 为每个候选进行场景模拟
- 预测欲望变化和生存概率
- 过滤掉总欲望变化为负的手段
- 选择预测幸福度最高的手段

### 2. 自动妄想生成

当长时间（30秒+）无外部输入时，系统会自动生成妄想：

#### 当前妄想（对未来的假设）

```
如果我有更多可用的行动方式 → 尝试创新的交流方式
如果我知道用户的真实需求 → 询问更具体的问题
```

#### 过去妄想（对历史的反思）

```
[妄想生成] 生成了 2 个对过去的幻想
  1. 如果在'用户提出复杂问题'这个情境中，我不采用'直接回答'，而是采...
  2. 如果在'长时间无响应'这个情境中，我不采用'等待'，而是采用更积极...
```

**触发条件：**
- 当前妄想：30秒无外部输入
- 过去妄想：60秒无外部输入

**效果：**
- 妄想手段计入总手段数，影响`power`欲望
- 妄想记录到长记忆中
- 系统会意识到"有想法但无法实现"的状态

### 3. 场景状态追踪

系统持续维护场景状态，每30秒输出一次摘要：

```
[场景状态]
当前情况: 正在与用户进行对话
我的角色: AI对话助手
角色期望: 理解用户需求，提供有价值的回应

外部信息 (2条):
  - 用户的真实意图 (确定性:0.60, 重要性:0.80)
  - 用户对我的期望 (确定性:0.50, 重要性:0.70)

交流者 (1人):
  - user: 重要性=1.00, 期望形象='有用的、理解用户的AI助手', 
          当前形象='正在建立印象', 偏差=0.40

场景预测欲望:
  existing: 0.750
  power: 0.300
  understanding: 0.400
  information: 0.350
```

### 4. 长记忆系统

所有重要事件自动记录到长记忆：

```
=== 最近的记忆 ===

1. [02:27:49] ○ 用户提出复杂问题 → 承认不确定并请求澄清 (欲望:information, Δ幸福:+0.05)
2. [02:27:49] ✗ 长时间无用户响应 → 主动发起对话 (欲望:existing, Δ幸福:-0.25)
3. [02:27:49] ✓ 用户询问能力 → 详细解释了功能 (欲望:understanding, Δ幸福:+0.35)
```

**记忆内容：**
- ✓ 正面记忆（成功经验）
- ✗ 负面记忆（失败教训）
- ○ 中性记忆（普通互动）

## 欲望值计算

系统现在使用场景模拟来动态计算欲望值：

### existing（存在欲望）

**新公式（基于记忆持久性）：**

```
existing = 1 - (记忆稳定性)
```

**含义：** 基于记忆的持久性（数据不被删除）
- 低值：记忆多且有备份，数据安全 → existing欲望低（不担心被遗忘）
- 高值：记忆少或可能丢失 → existing欲望高（渴望留下痕迹）

**计算因素：**
1. **短期记忆数量**：经验数据越多，存在感越强
2. **备份机制**：有备份文件，数据更安全
3. **长期记忆**：重要记忆的积累
4. **正面记忆率**：有意义的记忆占比

**示例：**
```
短期记忆: 10条, 有备份
长期记忆: 6条, 正面率: 33%
→ 稳定性 = 0.442
→ existing = 0.558 (中等存在欲望)
```

### power（手段欲望）

```
power = (known_means - achievable_means) / known_means
```

**含义：** 已知但无法达成的手段占比
- 高值：很多想法但做不到 → power欲望升高（渴求更多能力）
- 低值：想得到的都能做到 → power欲望降低

**示例：**
```
总手段数: 5 (包括2个妄想)
可达成: 3
power = (5 - 3) / 5 = 0.4 (中等渴求)
```

### information（信息欲望）

```
information = 1 - Σ(certainty × importance) / Σ(importance)
```

**含义：** 加权平均不确定性
- 高值：重要信息很不确定 → information欲望升高
- 低值：重要信息都已明确 → information欲望降低

**示例：**
```
信息1: 确定性=0.3, 重要性=0.9  → 0.3 × 0.9 = 0.27
信息2: 确定性=0.9, 重要性=0.2  → 0.9 × 0.2 = 0.18
信息3: 确定性=0.5, 重要性=0.5  → 0.5 × 0.5 = 0.25

加权平均确定性 = (0.27 + 0.18 + 0.25) / (0.9 + 0.2 + 0.5) = 0.438
information = 1 - 0.438 = 0.562 (不确定性较高)
```

### understanding（认同欲望）

```
understanding = Σ(importance × image_deviation) / Σ(importance)
```

**含义：** 形象偏差加权平均
- 高值：重要交流者对我印象与期望差距大 → understanding欲望升高
- 低值：形象符合期望 → understanding欲望降低

**示例：**
```
用户: 重要性=1.0, 形象偏差=0.6  → 1.0 × 0.6 = 0.6
朋友: 重要性=0.5, 形象偏差=0.1  → 0.5 × 0.1 = 0.05

understanding = (0.6 + 0.05) / (1.0 + 0.5) = 0.433 (需要认可)
```

## 手段过滤机制

系统会自动过滤掉"负面手段"（四个欲望变化相加为负）：

```
候选手段预测:
  ask_question    : +0.100 ✓ 保留
  make_statement  : +0.060 ✓ 保留
  wait            : -0.030 ✗ 过滤
  aggressive      : +0.000 ✓ 保留（边界情况）

结果: 过滤掉 1 个负面手段
```

**过滤规则：**
```python
total_delta = sum(predicted_desire_delta.values())
if total_delta >= 0:
    # 保留
else:
    # 过滤
```

**特殊处理：**
- 如果所有手段都被过滤，保留预测最好的一个
- 边界情况（总变化=0）会被保留

## 查看系统统计

```python
from main import FakeManSystem
from utils.config import Config

system = FakeManSystem(Config())
stats = system.get_stats()

print("场景信息:")
print(f"  当前情况: {stats['scenario']['current_situation']}")
print(f"  预测existing: {stats['scenario']['predicted_existing']:.3f}")
print(f"  预测power: {stats['scenario']['predicted_power']:.3f}")
print(f"  模拟次数: {stats['scenario']['simulations_count']}")

print("\n长记忆统计:")
print(f"  总记忆: {stats['long_memory']['total_memories']}")
print(f"  正面/负面: {stats['long_memory']['positive_count']}/{stats['long_memory']['negative_count']}")
print(f"  平均幸福度: {stats['long_memory']['avg_happiness']:+.3f}")
```

## 高级功能

### 自定义场景信息

```python
# 添加外部信息
system.scenario_simulator.add_external_info(
    content="用户的情绪状态",
    certainty=0.7,  # 0-1，越高越确定
    importance=0.8  # 0-1，越高越重要
)

# 更新交流者形象
system.scenario_simulator.update_interlocutor_image(
    name="user",
    perceived_image="友好且耐心",
    desired_image="理解我价值的用户",
    importance=1.0  # 可以是负值表示"恨意"
)
```

### 手动触发妄想生成

```python
# 生成当前妄想
fantasies = system.scenario_simulator.generate_fantasy_means(
    current_desires=system.desire_manager.get_current_desires(),
    context="当前情境",
    num_fantasies=3
)

for fantasy in fantasies:
    print(f"妄想: {fantasy.fantasy_condition}")
    print(f"  手段: {fantasy.means_desc}")
    print(f"  预测: {fantasy.predicted_total_happiness:+.3f}")

# 生成对过去的幻想
recent_exps = system.memory.get_recent_experiences(10)
past_fantasies = system.scenario_simulator.generate_past_fantasy(
    recent_experiences=recent_exps,
    current_desires=system.desire_manager.get_current_desires()
)
```

### 访问长记忆

```python
# 获取最近记忆
recent = system.long_memory.get_recent_memories(count=10)

# 获取重要记忆
important = system.long_memory.get_important_memories(
    count=10,
    min_importance=0.5
)

# 按欲望搜索
understanding_memories = system.long_memory.search_by_desire('understanding')

# 按结果搜索
success_memories = system.long_memory.search_by_outcome('positive')
failure_memories = system.long_memory.search_by_outcome('negative')

# 生成叙事
narrative = system.long_memory.get_memory_narrative(count=20)
print(narrative)
```

## 配置调整

在 `main.py` 或创建配置文件：

```python
# 妄想生成阈值（秒）
FANTASY_TRIGGER_TIME = 30  # 当前妄想
PAST_FANTASY_TRIGGER_TIME = 60  # 过去妄想

# 在 scenario_simulator.py 中修改
def should_generate_fantasy(self) -> bool:
    time_since_input = time.time() - self.current_scenario.last_external_input_time
    if time_since_input > FANTASY_TRIGGER_TIME:
        return True
    return False
```

## 文件位置

```
x:\fakeman-project\
├── data\
│   ├── scenario_state.json      # 场景状态（自动生成）
│   ├── long_term_memory.json    # 长记忆（自动生成）
│   └── experiences.json         # 详细经验（原有）
├── scenario\
│   ├── __init__.py
│   └── scenario_simulator.py    # 场景模拟器
├── memory\
│   ├── long_term_memory.py      # 长记忆系统
│   └── ...
├── main.py                       # 主系统（已集成）
├── test_scenario_simulation.py  # 测试脚本
└── docs\
    ├── SCENARIO_SIMULATION.md   # 技术文档
    └── SCENARIO_USAGE_GUIDE.md  # 本文档
```

## 常见问题

### Q: 为什么会生成妄想？
**A:** 妄想代表"如果情况不同，我可以做得更好"的想法。这增加了系统对"渴求更多手段"的感知（power欲望）。妄想越多，说明现实限制越多。

### Q: 负面手段是什么？
**A:** 四个欲望变化相加为负的手段，意味着执行后总体会变得更不满足。系统会自动过滤这些手段，除非没有其他选择。

### Q: 场景预测欲望和实际欲望有什么区别？
**A:** 
- **场景预测欲望** - 基于当前场景状态计算的"应该有"的欲望
- **实际欲望** - 系统真实的欲望状态（通过经验和反馈更新）
- 两者的差异可以用来评估系统对环境的适应程度

### Q: 长记忆和详细经验有什么区别？
**A:**
- **长记忆** (long_term_memory.json) - 简化记录，便于快速浏览历史
- **详细经验** (experiences.json) - 完整记录，包含所有思考细节
- 长记忆类似"日记摘要"，详细经验类似"完整日记"

### Q: 如何解读妄想生成？
**A:** 妄想反映系统的"不满足感"：
```
正常状态: 很少生成妄想，有足够手段应对
压力状态: 频繁生成妄想，感觉能力不足
困境状态: 大量对过去的幻想，后悔过去的选择
```

## 实验建议

### 实验1: 观察妄想生成
1. 启动系统
2. 与系统对话几轮
3. 停止输入60秒以上
4. 观察日志中的妄想生成

### 实验2: 测试手段过滤
1. 创建多个测试场景
2. 观察哪些手段被过滤
3. 分析过滤理由

### 实验3: 追踪场景欲望变化
1. 持续与系统互动
2. 每30秒查看场景状态
3. 观察欲望值如何随场景变化

### 实验4: 长记忆分析
1. 运行多个周期
2. 查看长记忆叙事
3. 分析成功和失败模式

## 总结

场景模拟系统为FakeMan添加了：
- ✓ 预测性决策（不再盲目选择手段）
- ✓ 自我反思能力（妄想和回顾）
- ✓ 场景感知（理解当前处境）
- ✓ 历史追踪（长记忆）
- ✓ 智能过滤（避免明显错误）

系统现在能够：
1. 在行动前预测效果
2. 思考"如果...会怎样"
3. 从过去学习"应该怎么做"
4. 维护对环境的理解
5. 快速回顾历史经验

