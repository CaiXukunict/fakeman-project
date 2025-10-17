# FakeMan - 基于欲望驱动的自主智能体

> 滚动查看英文版 / Scroll down for English version

## 概述

FakeMan 是基于**米塞斯人类行动学理论**构建的智能体架构。系统核心思想是：智能体通过记忆"行动导致欲望如何变化"来理解因果关系，复杂的智能行为从简单的基础规则中自然涌现。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API密钥（创建 .env 文件）
echo "DEEPSEEK_API_KEY=your_api_key" > .env

# 3. 运行示例
python examples/simple_demo.py

# 4. 或交互式对话
python examples/interactive_chat.py
```

详见 [QUICKSTART.md](QUICKSTART.md)

## 核心特性

### 1. 欲望驱动系统

四种基础欲望（总和恒为1）：
- **existing** (维持存在): 维持自身的存在和延续
- **power** (增加手段): 增加可用的行动手段和能力
- **understanding** (获得认可): 获得他人的认可和理解
- **information** (减少不确定性): 减少信息的不确定性，减少疑惑

### 2. 决策流程

```
欲望 → 目的 → 手段 → 思考 → 行动
                              ↓
        记录经验 ← 更新欲望 ← 环境响应
```

**新增优化：**
- ✅ **边际效用改进**：最容易达成的欲望bias降低，难以达成的欲望bias增加
- ✅ **成就感机制**：思考越多（API调用越多），成功时奖励越大，失败时惩罚也越大
- ✅ **无聊机制**：持续重复无效的手段，其possibility bias会下降
- ✅ **手段bias计算**：手段对目的可能性的影响 × 完成目的后欲望变化程度
- ✅ **JSON存储**：经验记录使用JSON格式，便于查看和调试

### 3. 偏见系统

四种认知偏见影响决策：

| 偏见类型 | 作用 | 参数 |
|---------|------|------|
| 损失厌恶 | 负面结果权重放大 | `fear_multiplier=2.5` |
| 时间折现 | 远期收益价值打折 | `time_discount_rate=0.1` |
| 边际效用递减 | 易达成欲望权重降低 | 基于可达成性动态转移 |
| 可能性偏见 | 基于历史成功率 | 自动计算 |

### 4. 记忆系统

- **存储格式**：JSON 文件 (`data/experiences.json`)
- **检索策略**：情境相似度 + 目的重合度 + 时间衰减
- **成就感追踪**：记录每次经验的思考次数和成就感倍数
- **无聊检测**：追踪重复手段的有效性历史

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    FakeMan System                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Desire Mgr   │──────│ Bias System  │               │
│  │ (欲望管理)    │      │ (偏见系统)    │               │
│  └──────────────┘      └──────────────┘               │
│         │                      │                        │
│         ↓                      ↓                        │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Purpose Gen  │──────│ Means Select │               │
│  │ (目的生成)    │      │ (手段选择)    │               │
│  └──────────────┘      └──────────────┘               │
│         │                      │                        │
│         ↓                      ↓                        │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Acting Bot   │──────│ Memory DB    │               │
│  │ (行动执行)    │      │ (记忆系统)    │               │
│  └──────────────┘      └──────────────┘               │
│         │                      │                        │
│         ↓                      ↓                        │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Compressor   │──────│ Experience   │               │
│  │ (思考压缩)    │      │ (经验记录)    │               │
│  └──────────────┘      └──────────────┘               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## LLM 支持

支持多个 LLM 提供商：

- ✅ **DeepSeek** (默认推荐) - 性价比高
- ✅ **Anthropic Claude** - 高质量输出
- ✅ **OpenAI GPT** - 通用选择

配置方式：
```python
config.llm.provider = 'deepseek'  # 或 'anthropic', 'openai'
config.llm.model = 'deepseek-chat'
```

## 项目结构

```
fakeman-project/
├── action_model/         # 行动模型（思考生成、行动执行）
├── memory/               # 记忆系统（经验存储、检索）
├── purpose_generator/    # 欲望系统（欲望管理、偏见、信号检测）
├── compressor/           # 思考压缩
├── utils/                # 工具（配置、日志）
├── examples/             # 示例程序
├── main.py               # 主系统集成
├── requirements.txt      # 依赖列表
└── README.md             # 本文件
```

## 使用示例

### 基础对话

```python
from utils.config import Config
from main import FakeManSystem

# 初始化
config = Config()
system = FakeManSystem(config)

# 执行决策周期
result = system.run_cycle("你对人工智能有什么看法？")
print(result['action'])

# 处理响应
system.handle_response(result, "很有见地！", response_type='positive')

# 查看欲望变化
print(system.desire_manager.get_current_desires())
```

### 查看记忆

```python
# 获取统计信息
stats = system.get_stats()
print(f"记忆数量: {stats['memory']['total_experiences']}")
print(f"正面经验率: {stats['memory']['positive_rate']:.1%}")

# 查询特定经验
experiences = system.memory.query_by_purpose("理解用户")
for exp in experiences[:5]:
    print(f"目的: {exp.purpose}, 结果: {exp.total_happiness_delta:+.2f}")
```

## 核心理念

### 学习循环

```
行动 → 观察欲望变化 → 记录经验 → 检索记忆 → 预测结果 → 决策
```

不依赖符号推理或抽象因果图，而是通过记忆"行动→欲望变化"的时序模式实现因果学习，支持：
- **关联**：观察行动和结果的关联
- **干预**：主动选择行动观察效果
- **反事实**：基于记忆推理"如果选择不同会怎样"

### 涌现行为

通过简单规则的组合，系统可能涌现出：
- **避免行为**：对导致负面结果的行动产生规避
- **习惯形成**：对成功的行动产生偏好
- **主动探索**：在 information 欲望驱动下主动提问减少疑惑
- **能力扩展**：在 power 欲望驱动下尝试新的行动手段
- **寻求认可**：在 understanding 欲望驱动下调整回应方式

### 系统包含三个核心组件

```
Purpose Generator（目的生成器）：基于当前欲望状态和历史经验生成行动目的
Acting Bot（行动执行器）：执行具体行动并观察结果
Muscle Memory Database（经验记忆数据库）：记录所有行动及其导致的欲望变化
```

## 配置选项

主要配置在 `utils/config.py`：

```python
# 欲望配置
initial_desires = {
    'existing': 0.4,
    'power': 0.2,
    'understanding': 0.25,
    'information': 0.15
}

# 偏见配置
fear_multiplier = 2.5           # 损失厌恶系数
time_discount_rate = 0.1        # 时间折现率
achievability_transfer_rate = 0.05  # 可达成性转移率

# 成就感配置
achievement_base_multiplier = 1.5
achievement_thought_weight = 0.2
max_achievement_multiplier = 5.0

# 无聊机制配置
boredom_threshold = 5
boredom_decay_rate = 0.1
```

## 依赖项

主要依赖：
- `anthropic>=0.25.0` - Claude API
- `openai>=1.0.0` - OpenAI API  
- `httpx>=0.24.0` - DeepSeek API
- `numpy>=1.24.0` - 数值计算
- `python-dotenv>=1.0.0` - 环境变量

完整列表见 `requirements.txt`

## 开发路线图

- [x] 阶段1: 核心配置与工具
- [x] 阶段2: 欲望系统
- [x] 阶段3: 记忆系统（JSON + 成就感 + 无聊机制）
- [x] 阶段4: 行动模型（DeepSeek支持）
- [x] 阶段5: 思考压缩
- [x] 阶段6: 主系统集成（欲望→目的→手段流程）
- [ ] 阶段7: 测试与验证
- [ ] 阶段8: 性能优化
- [ ] 阶段9: 可视化界面
- [ ] 阶段10: 多智能体交互

## 许可证

MIT License

## 致谢

本项目受以下理论启发：
- Ludwig von Mises 的人类行动学理论
- Judea Pearl 的因果推理框架
- Daniel Kahneman 的认知偏见研究

---
### FakeMan - Desire-Based Autonomous Agent
### Overview
FakeMan is an agent architecture built on Ludwig von Mises' Human Action theory. The core principle is: agents understand causality by remembering "how actions lead to changes in desires," with complex intelligent behaviors emerging naturally from simple foundational rules.
### The system comprises three core components:
```
Purpose Generator: Generates action purposes based on current desire states and historical experience
Acting Bot: Executes specific actions and observes outcomes
Muscle Memory Database: Records all actions and their resulting desire changes
```
### Core Mechanisms
Desire System: 
```
Four fundamental desires (existing, power, understanding from others, information) always summing to 1, with dynamic redistribution through diminishing marginal utility.
```
Bias System: Four regulators influence decision-making
```
Time preference: Near-term satisfaction has higher value
Loss aversion: Negative outcomes weighted 2.5 times more
Diminishing marginal utility: Repeated satisfaction decreases desire weight
Possibility bias: Action reliability automatically calculated from historical success rates
```
### Learning Loop: 
Action → Observe desire changes → Record to database → Future predictions from memory → Decision-making
###
Does not rely on symbolic reasoning or abstract causal graphs, but achieves causal learning through memory of temporal patterns of "action → desire change," supporting three levels of reasoning: association, intervention, and counterfactual.
