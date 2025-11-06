# FakeMan 新架构说明

## 架构概述

新架构实现了更精细的欲望-目的-手段系统，核心流程如下：

```
基础欲望 → 原始目的 → 手段 → 高级目的 → 思考 → 行动 → 经验 → 审视调整
    ↓         ↓         ↓        ↓                          ↓
  (长期)   (正当性)  (覆盖)   (手段相关)                (可调整)
```

## 核心概念

### 1. 欲望层级

#### 基础欲望（不基于手段）
- **existing**: 维持存在
- **understanding**: 获得认可

这两种欲望直接生成原始目的，不需要手段支持。

#### 手段相关欲望
- **information**: 减少不确定性（关乎手段的确定性）
- **power**: 增加手段（关乎手段的数量）

这两种欲望基于手段生成高级目的。

### 2. 目的系统

#### 原始目的（Primary Purpose）
- **来源**: 由基础欲望生成
- **特性**: 作为长期规划存在
- **检查**: 不随意修改，只在判断为"非正当"时才取消
- **正当性标准**: 目的是否能给欲望带来正反馈

#### 高级目的（Advanced Purpose）
- **来源**: 由手段相关欲望基于原始目的生成
- **依赖**: 依赖于父原始目的
- **连锁**: 父目的非正当，高级目的也非正当

#### 目的Bias计算
```
bias = achievability × (1 / (1 + time_required))
```

- 越不可能达成的目的，bias越低
- 需要时间越长的目的，bias越低

#### 目的满足度叠加
同时满足多种欲望的目的，其预期满足度可以叠加计算：
```
total_satisfaction = Σ(satisfaction_i × bias)
```

### 3. 手段系统

#### 手段生成原则
1. **必须覆盖所有目的**: 每次生成的手段必须包括对所有目的的满足
2. **可以部分覆盖**: 可以有多个手段分别满足一部分目的
3. **可以多重覆盖**: 一个手段可以同时满足多个目的

#### 手段重要性计算
```
importance = Σ(importance_to_purpose_i × purpose_i.bias)
```

- 同时满足多个目的的手段，重要性会叠加
- 目的的bias变化会影响手段重要性

### 4. 记忆压缩系统

#### 压缩策略
每次思考前，对最近的两次**时间长度相同**的思考数据进行合并：
- **时间长度**: 相加（duration1 + duration2）
- **数据长度**: 不变（保持简洁）

#### 压缩过程
```
思考记录1 (duration=10s, data=500字)
思考记录2 (duration=10s, data=500字)
         ↓ 合并
压缩记录  (duration=20s, data=500字)
```

通过不断合并，形成不同时间尺度的记忆：
- 短期: 原始记录（秒级）
- 中期: 一次压缩（分钟级）
- 长期: 多次压缩（小时级）

### 5. 经验系统

#### 经验记录
当执行了干涉行为时，记录：
- 使用的手段
- 执行情境
- 欲望变化
- 是否有利

#### 可审视调整
AI可以定期审视经验，根据情况变化调整评估：

```python
# 原始评估
experience.is_beneficial = True
experience.total_satisfaction_delta = +0.3

# 审视后发现某个情境因素被低估
experience.add_adjustment(
    reason="用户当时情绪不好，影响了反馈",
    factor="用户情绪",
    impact=-0.2  # 降低评估
)

# 调整后评估
experience.total_satisfaction_delta = +0.1
```

## 核心流程

### 完整思考周期

```python
def thinking_cycle():
    # 1. 管理原始目的
    if 基础欲望较高 or 原始目的过少:
        生成新的原始目的()
    
    # 2. 检查目的正当性
    for 目的 in 所有目的:
        if 距上次检查时间足够:
            if not 判断正当性():
                标记为非正当()
    移除非正当目的及其依赖()
    
    # 3. 管理手段
    uncovered = 未被覆盖的目的()
    if uncovered:
        生成新手段(uncovered)
    更新所有手段重要性()
    
    # 4. 管理高级目的
    if information欲望 > 阈值:
        for 手段 in 重要手段:
            创建高级目的("了解手段效果")
    
    if power欲望 > 阈值:
        for 目的 in 手段不足的目的:
            创建高级目的("寻找更多手段")
    
    # 5. 思考决策
    整合(目的, 手段, 记忆, 经验)
    thought_process, decisions = LLM思考()
    
    # 6. 执行行动
    action, result = 执行(decisions)
    
    # 7. 记录思考
    记录思考过程(目的, 手段, 思考, 决策, 行动)
    压缩最近思考()  # 自动合并等长时间记录
    
    # 8. 记录经验（如果是干涉行为）
    if 干涉了外部:
        记录经验(手段, 情境, 欲望变化)
    
    # 9. 更新欲望
    根据结果更新欲望()
    
    # 10. 定期审视经验
    if 第N个周期:
        审视并调整经验()
```

## 关键特性

### 1. 目的的稳定性
- **不轻易修改**: 原始目的作为长期规划，不随意删除
- **正当性检查**: 只有明确判断无法带来正反馈时才取消
- **连锁清理**: 删除目的时自动清理依赖的高级目的和手段

### 2. 手段的完整性
- **全覆盖**: 确保所有目的都有手段支持
- **动态调整**: 目的变化时自动调整手段重要性
- **智能清理**: 删除指向无效目的的手段

### 3. 记忆的层次性
- **自动压缩**: 无需手动管理，自动形成多时间尺度
- **保持简洁**: 压缩时保持数据长度不变
- **可追溯**: 压缩记录保留原始记录引用

### 4. 经验的可调整性
- **情境感知**: 记录影响结果的情境因素
- **动态评估**: 可以根据新情况重新评估
- **累积调整**: 记录所有调整历史

## 数据结构

### Purpose（目的）
```python
{
    'id': 'primary_0',
    'description': '维持与用户的良好对话关系',
    'type': 'primary',  # 或 'advanced'
    'source_desires': ['existing', 'understanding'],
    'expected_desire_satisfaction': {
        'existing': 0.3,
        'understanding': 0.4
    },
    'achievability': 0.7,
    'time_required': 1.5,
    'bias': 0.467,  # 计算得出
    'is_legitimate': True
}
```

### Means（手段）
```python
{
    'id': 'means_0',
    'description': '主动询问用户需求',
    'target_purposes': ['primary_0', 'advanced_1'],
    'importance_to_purposes': {
        'primary_0': 0.8,
        'advanced_1': 0.6
    },
    'total_importance': 0.934,  # 叠加计算
    'success_rate': 0.75
}
```

### ThoughtRecord（思考记录）
```python
{
    'id': 'thought_5',
    'start_time': 1234567890.0,
    'duration': 15.0,  # 可能是压缩后的
    'context': '...',
    'purposes': [...],
    'means': [...],
    'thought_process': '...',
    'decisions': [...],
    'is_compressed': True,
    'original_records': ['thought_3', 'thought_4'],
    'compressed_count': 2
}
```

### Experience（经验）
```python
{
    'id': 'exp_10',
    'means_id': 'means_0',
    'context': '用户询问功能',
    'desires_before': {...},
    'desires_after': {...},
    'is_beneficial': True,
    'total_satisfaction_delta': 0.3,
    'adjustments': [
        {
            'timestamp': 1234567900.0,
            'reason': '用户反馈积极',
            'factor': '用户情绪',
            'impact': +0.1
        }
    ]
}
```

## 使用示例

### 启动系统
```python
from main_refactored import FakeManRefactored
from utils.config import Config

config = Config()
system = FakeManRefactored(config)

# 运行思考周期
result = system.thinking_cycle(
    external_input="你好，你能做什么？"
)

print(result)
```

### 查看状态
```python
status = system.get_status()

print(f"目的统计: {status['purposes']}")
print(f"手段统计: {status['means']}")
print(f"思考统计: {status['thoughts']}")
print(f"经验统计: {status['experiences']}")
```

## 优势

### 1. 更真实的规划
- 原始目的作为长期规划，不会频繁变化
- 高级目的基于手段动态生成，更加灵活

### 2. 更全面的覆盖
- 手段必须覆盖所有目的
- 系统会主动寻找手段不足的目的

### 3. 更智能的记忆
- 自动形成多时间尺度的记忆
- 近期详细，远期概括

### 4. 更准确的经验
- 可以根据新情况调整经验评估
- 避免固化错误的判断

## 与旧架构的对比

| 方面 | 旧架构 | 新架构 |
|------|--------|--------|
| 目的生成 | 每次思考都重新生成 | 作为长期规划，不轻易修改 |
| 手段管理 | 无明确管理 | 必须覆盖所有目的，动态调整重要性 |
| 记忆压缩 | 手动压缩或简单截断 | 自动合并等长时间记录，形成层次 |
| 经验系统 | 静态记录 | 可审视调整，适应情境变化 |
| 欲望层级 | 所有欲望平等 | 区分基础欲望和手段相关欲望 |

## 扩展方向

### 1. 目的优先级
- 基于urgency和importance排序
- 实现目的的优先级队列

### 2. 手段组合
- 探索多个手段的组合效果
- 发现协同作用

### 3. 预测性压缩
- 根据重要性决定压缩策略
- 重要的记忆保持更长时间

### 4. 社会性经验
- 学习他人的经验
- 形成社会知识库

---

## 文件结构

```
purpose_generator/
  └── purpose_manager.py      # 目的管理器

action_model/
  └── means_manager.py         # 手段管理器

memory/
  ├── thought_memory.py        # 思考记忆（压缩）
  └── adjustable_experience.py # 可调整经验

main_refactored.py             # 主系统（重构版）
```

## 配置

在 `utils/config.py` 中添加：

```python
# 目的管理
purpose_check_interval = 30  # 正当性检查间隔（秒）
max_purpose_age = 3600       # 目的最大存活时间（秒）

# 手段管理
means_generation_interval = 20  # 手段生成间隔（秒）
min_means_per_purpose = 1       # 每个目的最少手段数

# 记忆压缩
thought_memory_max_age = 86400  # 思考记忆保留时间（秒）
compression_time_tolerance = 0.1  # 时间长度匹配容差

# 经验审视
experience_review_interval = 10  # 审视经验的周期间隔
experience_max_age = 604800      # 经验保留时间（7天）
```

