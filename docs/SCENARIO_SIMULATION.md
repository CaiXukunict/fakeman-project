# 场景模拟系统文档

## 概述

场景模拟系统是FakeMan项目的重要扩展，实现了以下核心功能：

1. **场景状态管理** - 维护当前情况、角色定位和环境信息
2. **手段预测** - 模拟不同手段的效果，预测欲望变化
3. **妄想生成** - 在长时间无输入时生成假设场景
4. **长记忆** - 简要记录历史事件便于快速回顾

## 核心组件

### 1. ScenarioSimulator（场景模拟器）

位置: `scenario/scenario_simulator.py`

#### 主要功能：

- **维护场景状态** (`ScenarioState`)
  - 当前情况和角色定位
  - 外部信息列表（带确定性和重要性）
  - 交流者关系（重要性、期望形象、当前形象）
  - 场景预测欲望值

- **手段模拟** (`simulate_means`)
  - 预测每个候选手段的欲望变化
  - 计算生存概率
  - 支持妄想手段模拟

- **欲望计算**
  - `existing` = 平均存活概率
  - `power` = 无法达成的手段数 / 全部手段数
  - `information` = 1 - Σ(确定性 × 重要性) / 信息数量
  - `understanding` = 基于形象偏差的加权平均

- **妄想生成**
  - 当前妄想：如果场景变化，我可以更好地满足欲望
  - 过去妄想：如果过去做了不同选择，现在会更好

### 2. LongTermMemory（长记忆系统）

位置: `memory/long_term_memory.py`

#### 特点：

- **简化记录** - 只保留关键信息
  - 情境简述
  - 采取的行动
  - 结果（positive/negative/neutral）
  - 主导欲望和幸福度变化

- **重要性计算** - 自动评估记忆重要性
  - 幸福度变化大的事件更重要
  - 重大成功/失败更容易被记住

- **快速检索**
  - 按时间检索最近记忆
  - 按重要性检索关键记忆
  - 按欲望、结果、标签搜索

### 3. MeansSelector（手段选择器升级）

位置: `main.py`

#### 新增功能：

1. **场景模拟集成**
   - 为每个候选手段进行场景模拟
   - 预测欲望变化和生存概率
   - 记录所有模拟结果

2. **负面手段过滤**
   - 删除四个欲望变化相加为负的手段
   - 确保选择的手段至少不会降低总体幸福度

3. **妄想手段支持**
   - 长时间无输入时自动生成妄想手段
   - 妄想手段标记为`is_fantasy=True`
   - 记录妄想条件（"如果...就好了"）

## 使用场景

### 场景1: 正常对话

```python
# 用户输入触发
user_input = "你今天感觉怎么样？"

# 系统流程：
# 1. 更新场景状态（用户输入）
# 2. 生成目的
# 3. 场景模拟 - 生成多个候选手段
#    - 提问了解情况 (预测 +0.1 幸福度)
#    - 陈述表达感受 (预测 +0.08 幸福度)
# 4. 过滤负面手段
# 5. 选择最佳手段
# 6. 执行思考和行动
```

### 场景2: 长时间无输入（妄想生成）

```python
# 60秒无用户输入
# 系统自动：
# 1. 检测长时间无输入
# 2. 生成对过去的妄想
#    "如果在'用户询问需求'这个情境中，
#     我不采用'直接回答'，而是采用更深入的询问策略，
#     也许结果会更好..."
# 3. 记录妄想到长记忆
# 4. 妄想手段计入总手段数，影响power欲望
```

### 场景3: 手段预测和过滤

```python
# 候选手段：
means_candidates = [
    {"type": "aggressive", "predicted_delta": {"existing": -0.3, "power": +0.5, ...}},  # 总计 +0.1
    {"type": "safe", "predicted_delta": {"existing": +0.1, "power": -0.05, ...}},      # 总计 +0.05
    {"type": "risky", "predicted_delta": {"existing": -0.5, "power": +0.2, ...}},      # 总计 -0.15 ❌
]

# 过滤后：保留 aggressive 和 safe
# 选择：aggressive（预测幸福度最高）
```

## 场景状态文件

保存在 `data/scenario_state.json`

```json
{
  "current_situation": "正在与用户进行对话",
  "role": "AI对话助手",
  "role_expectations": "理解用户需求，提供有价值的回应",
  "external_info": [
    {
      "content": "用户的真实意图",
      "certainty": 0.6,
      "importance": 0.8
    }
  ],
  "interlocutors": {
    "user": {
      "importance": 1.0,
      "desired_image": "有用的、理解用户的AI助手",
      "perceived_image": "正在建立印象",
      "image_deviation": 0.4
    }
  },
  "predicted_existing": 0.7,
  "predicted_power": 0.3,
  "predicted_understanding": 0.4,
  "predicted_information": 0.5
}
```

## 长记忆文件

保存在 `data/long_term_memory.json`

```json
{
  "memories": [
    {
      "id": 1,
      "timestamp": 1697654321.5,
      "cycle_id": 5,
      "situation": "用户询问我的能力",
      "action_taken": "详细解释了我的功能",
      "outcome": "positive",
      "dominant_desire": "understanding",
      "happiness_delta": 0.3,
      "importance": 0.45,
      "tags": ["interaction", "explanation"]
    }
  ],
  "next_id": 2
}
```

## 欲望值计算详解

### existing（存在欲望）

```
existing = Σ(survival_probability) / len(viable_means)
```

- 所有可行手段的平均存活概率
- 如果可选手段的存活率都很高，existing欲望降低
- 如果大部分手段都危险，existing欲望升高

### power（手段欲望）

```
power = (known_means - achievable_means) / known_means
```

- 已知但无法达成的手段占比
- 妄想越多，总手段数越多，power欲望越高
- 体现对"渴求更多行动能力"的程度

### information（信息欲望）

```
information = 1 - Σ(certainty_i × importance_i) / Σ(importance_i)
```

- 加权平均不确定性
- 重要信息越不确定，information欲望越高
- 当获得明确信息时，该欲望降低

### understanding（认同欲望）

```
understanding = Σ(importance_i × image_deviation_i) / Σ(importance_i)
```

- 基于所有交流者的形象偏差
- 如果重要交流者对我的印象与期望差距大，understanding欲望升高
- 负重要性（恨意）也算入计算

## 日志示例

```
[场景模拟与手段选择]
  生成了 5 个候选手段
  可行手段: 3, 妄想手段: 1
  选定手段类型: ask_question
  选定手段描述: 通过提问获取信息
  手段bias: 0.65
  预测幸福度变化: +0.12
  预测存活概率: 0.85

[妄想生成] 生成了 2 个对过去的幻想
  1. 如果在'用户提出复杂问题'这个情境中，我不采用'直接回答'，而是采...
  2. 如果在'长时间无响应'这个情境中，我不采用'等待'，而是采用更积极...

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

## API接口

### ScenarioSimulator

```python
# 初始化
simulator = ScenarioSimulator(scenario_file="data/scenario_state.json")

# 更新场景
simulator.update_scenario_from_context(context="用户提问", user_input=True)

# 模拟手段
simulation = simulator.simulate_means(
    means_type="ask_question",
    means_desc="询问更多细节",
    current_desires=desires,
    context=context
)

# 生成妄想
fantasies = simulator.generate_fantasy_means(
    current_desires=desires,
    context=context,
    num_fantasies=2
)

# 生成对过去的幻想
past_fantasies = simulator.generate_past_fantasy(
    recent_experiences=experiences,
    current_desires=desires
)

# 更新欲望值
simulator.update_existing_desire(viable_means)
simulator.update_power_desire(all_means, achievable_means)

# 添加外部信息
simulator.add_external_info(
    content="用户的情绪状态",
    certainty=0.7,
    importance=0.8
)

# 更新交流者形象
simulator.update_interlocutor_image(
    name="user",
    perceived_image="友好且耐心",
    desired_image="理解我、认可我的价值"
)
```

### LongTermMemory

```python
# 初始化
ltm = LongTermMemory(storage_path="data/long_term_memory.json")

# 添加记忆
memory = ltm.add_memory(
    cycle_id=1,
    situation="用户询问能力",
    action_taken="详细解释功能",
    outcome='positive',
    dominant_desire='understanding',
    happiness_delta=0.3,
    tags=['interaction', 'explanation']
)

# 检索记忆
recent = ltm.get_recent_memories(count=10)
important = ltm.get_important_memories(count=10, min_importance=0.5)
by_desire = ltm.search_by_desire('understanding', count=5)

# 生成记忆叙事
narrative = ltm.get_memory_narrative(count=20)
print(narrative)

# 获取统计
stats = ltm.get_statistics()
```

## 配置建议

```python
# 妄想生成阈值
FANTASY_TRIGGER_TIME = 30  # 秒，无输入后开始生成当前妄想
PAST_FANTASY_TRIGGER_TIME = 60  # 秒，无输入后开始回顾过去

# 手段过滤
MIN_TOTAL_DESIRE_DELTA = 0.0  # 最小总欲望变化（负值手段被过滤）

# 场景更新频率
SCENARIO_SUMMARY_INTERVAL = 30  # 秒，输出场景摘要的间隔
```

## 注意事项

1. **场景状态持久化** - 场景状态保存在JSON文件中，系统重启后会加载
2. **妄想计入总手段** - 妄想手段会影响power欲望计算
3. **负面手段过滤** - 确保系统不会选择明显有害的手段
4. **长记忆轻量级** - 只保存关键信息，不存储完整思考过程
5. **欲望值动态计算** - 场景欲望值实时根据环境信息计算

## 未来扩展

- [ ] 使用LLM增强场景分析
- [ ] 更复杂的手段效果预测模型
- [ ] 多交流者场景支持
- [ ] 场景变化历史追踪
- [ ] 妄想实现检测（妄想条件是否成真）

