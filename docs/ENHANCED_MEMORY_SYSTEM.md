# 增强记忆系统文档

## 概述

增强记忆系统是对FakeMan原有记忆系统的全面升级，实现了以下核心功能：

1. **详细的情绪变化记录** - Experience现在可以记录每次情绪变化的完整过程
2. **输出和思考内容完整保存** - LongTermMemory保存完整的输出文本和思考内容
3. **基于权重的压缩** - 思考内容带权重，压缩时权重高的获得更多篇幅
4. **记忆作为手段** - 记忆行为本身成为一种可决策的手段

## 核心组件

### 1. Experience（经验）- 情绪变化记录

#### 新增字段

```python
emotion_changes: List[Dict[str, Any]]  # 情绪变化列表
```

每个情绪变化记录包含：
- `timestamp`: 变化时刻
- `trigger`: 触发原因
- `desire_before`: 变化前的欲望状态
- `desire_after`: 变化后的欲望状态
- `delta`: 变化量
- `total_delta`: 总变化
- `reason`: 变化原因描述

#### 使用方法

```python
from memory.experience import Experience

exp = Experience(
    id=1,
    timestamp=time.time(),
    cycle_id=1,
    context="用户询问",
    context_hash=Experience.create_context_hash("用户询问"),
    purpose="回答问题",
    means="详细解释"
)

# 添加情绪变化
exp.add_emotion_change(
    trigger="用户表现出兴趣",
    desire_before={'understanding': 0.5, 'existing': 0.5},
    desire_after={'understanding': 0.8, 'existing': 0.6},
    reason="成功的交流提升了understanding"
)

# 获取情绪变化摘要
summary = exp.get_emotion_summary()
print(summary)
```

### 2. LongTermMemory（长期记忆）- 完整内容保存

#### 新增字段

```python
# 输出内容
output_text: str = ''           # 实际输出的完整文本
output_type: str = ''            # 输出类型

# 思考内容（带权重）
thought_contents: List[Dict]     # 思考内容列表
# 每个思考包含：
# - content: 思考内容
# - weight: 权重 (0-1)，由LLM或规则决定
# - type: 类型（分析/推理/计划等）
# - related_desire: 相关欲望
# - timestamp: 思考时刻

# 压缩权重
compression_weight: float = 1.0  # 整体权重，影响合并时的篇幅
```

#### 使用方法

```python
from memory.long_term_memory import MemorySummary

memory = MemorySummary(
    id=1,
    timestamp=time.time(),
    cycle_id=1,
    situation="用户询问核心功能",
    action_taken="详细解释",
    outcome="positive",
    dominant_desire="understanding",
    happiness_delta=0.3,
    output_text="这是一个AI系统，具有..."
)

# 添加思考内容（带权重）
memory.add_thought_content(
    content="用户对系统很感兴趣",
    weight=0.9,  # 高权重
    thought_type="analysis",
    related_desire="understanding"
)

memory.add_thought_content(
    content="需要清晰解释",
    weight=0.6,  # 中等权重
    thought_type="planning"
)

# 获取基于权重的摘要
summary = memory.get_weighted_thought_summary(max_length=200)
# 权重高的思考会获得更多字符配额
```

### 3. WeightedMemoryCompressor（基于权重的压缩器）

#### 核心功能

1. **过滤低权重思考** - 去除权重低于阈值的思考内容
2. **合并相似记忆** - 按权重分配合并后的篇幅
3. **智能篇幅分配** - 权重越高的内容获得越多篇幅

#### 使用方法

```python
from compressor.weighted_compressor import WeightedMemoryCompressor

compressor = WeightedMemoryCompressor(
    base_summary_length=200,      # 基础摘要长度
    min_weight_threshold=0.1      # 最小权重阈值
)

# 压缩记忆列表
compressed_memories = compressor.compress_memories(
    memories=memory_list,
    target_count=10,              # 目标数量（可选）
    merge_similar=True            # 是否合并相似记忆
)

# 压缩单条记忆
compressed_single = compressor.compress_single_memory(
    memory=memory_dict,
    max_length=150
)
```

#### 权重分配算法

```
对于思考内容列表 [t1, t2, t3, ...]：

1. 计算总权重：
   total_weight = sum(t.weight for t in thoughts)

2. 为每个思考分配字符数：
   allocated_chars = (t.weight / total_weight) * total_length

3. 按权重降序处理：
   - 权重最高的优先获得完整篇幅
   - 权重低的可能被截断或省略
```

### 4. MemoryAsМeans（记忆作为手段）

#### 核心概念

记忆不再是被动的记录，而是一种**主动的手段**：
- 根据当前目的**决定**是否记忆
- 为思考内容**分配权重**
- 选择**记忆策略**（详细/简要/最简）
- 与其他手段（问答、陈述等）**不冲突**

#### 使用方法

```python
from action_model.memory_means import MemoryAsМeans

memory_means = MemoryAsМeans(llm_client=llm)  # 可选：传入LLM客户端

# 决定是否记忆以及如何记忆
decision = memory_means.decide_memory_action(
    current_purpose="帮助用户理解系统",
    current_desires={
        'existing': 0.8,
        'understanding': 0.7,
        'power': 0.3,
        'information': 0.4
    },
    thought_contents=[
        "用户对系统很感兴趣",
        "这是建立深层理解的机会",
        "需要清晰解释核心概念"
    ],
    context="用户问：FakeMan的核心是什么？",
    action_output="FakeMan的核心是让AI拥有目的驱动的自主性。"
)

# 决策结果
print(f"是否记忆: {decision.should_remember}")
print(f"记忆权重: {decision.memory_weight}")
print(f"原因: {decision.reason}")
print(f"压缩策略: {decision.compression_strategy}")  # 详细/简要/最简
print(f"优先级: {decision.priority_level}")          # 高/中/低
print(f"思考权重: {decision.thought_weights}")

# 应用决策到记忆对象
memory_means.apply_memory_decision(decision, memory_summary)
```

#### 决策规则（启发式）

1. **existing欲望高** → 更愿意记忆（保存存在）
2. **有重要思考** → 提高记忆权重
3. **思考长度长** → 增加该思考的权重
4. **包含关键词** → 进一步提升权重

#### LLM决策提示词

```
根据当前目的和情境，决定是否需要记忆这次经历，
并为每个思考内容分配权重（0-1）。

当前目的：{purpose}
当前情境：{context}
思考内容：{thoughts}
行动输出：{output}

请回答：
1. 是否应该记忆？（是/否）
2. 记忆权重：（0-1）
3. 原因：
4. 每个思考内容的权重：
   - 思考1: [权重]
   - 思考2: [权重]
   ...
```

## 完整工作流

### 典型使用场景

```python
# 1. 创建经验并记录情绪变化
exp = Experience(...)
exp.add_emotion_change(
    trigger="用户positive反馈",
    desire_before={...},
    desire_after={...},
    reason="成功的交流"
)

# 2. 使用记忆手段决定是否记忆
memory_means = MemoryAsМeans()
decision = memory_means.decide_memory_action(
    current_purpose=purpose,
    current_desires=desires,
    thought_contents=thoughts,
    context=context,
    action_output=output
)

# 3. 如果决定记忆，创建长期记忆
if decision.should_remember:
    memory = MemorySummary(
        ...,
        output_text=output,
        compression_weight=decision.memory_weight
    )
    
    # 添加思考内容（带权重）
    for i, thought in enumerate(thoughts):
        weight = decision.thought_weights.get(f"thought_{i}", 0.5)
        memory.add_thought_content(thought, weight, "analysis")
    
    # 保存到长期记忆
    long_term_memory.add_memory_from_summary(memory)

# 4. 定期压缩记忆
compressor = WeightedMemoryCompressor()
compressed = compressor.compress_memories(
    memories=long_term_memory.memories,
    merge_similar=True
)
```

## 数据结构对比

### 之前 vs 之后

| 组件 | 之前 | 之后 |
|------|------|------|
| **Experience** | 只有最终欲望变化 | 详细的情绪变化过程 |
| **LongTermMemory** | 简要摘要 | 完整输出+思考内容 |
| **压缩机制** | 简单合并 | 基于权重的篇幅分配 |
| **记忆决策** | 自动记忆所有 | 可选择性记忆 |

## 配置参数

### WeightedMemoryCompressor

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `base_summary_length` | 200 | 基础摘要长度 |
| `min_weight_threshold` | 0.1 | 最小权重阈值 |

### MemoryAsМeans

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `llm_client` | None | LLM客户端（可选） |

## 测试

运行完整测试：

```bash
$env:PYTHONIOENCODING='utf-8'
python test_enhanced_memory.py
```

测试覆盖：
- ✅ 情绪变化记录
- ✅ 思考内容权重
- ✅ 基于权重的压缩
- ✅ 记忆作为手段
- ✅ 完整集成工作流

## 文件位置

- **核心模块**:
  - `memory/experience.py` - Experience增强
  - `memory/long_term_memory.py` - LongTermMemory增强
  - `compressor/weighted_compressor.py` - 权重压缩器
  - `action_model/memory_means.py` - 记忆手段

- **测试**:
  - `test_enhanced_memory.py` - 完整测试脚本

- **文档**:
  - `docs/ENHANCED_MEMORY_SYSTEM.md` - 本文档

## 优势

### 1. 更丰富的情绪记录
- 不仅记录最终结果，还记录变化过程
- 可以分析情绪变化的触发因素

### 2. 完整的思考保存
- 保存每个思考的原始内容
- 权重系统确保重要思考不被丢失

### 3. 智能的压缩策略
- 权重高的内容获得更多篇幅
- 避免"一刀切"的简化

### 4. 记忆作为手段
- 记忆成为可控的行为
- 根据目的选择性记忆
- 节省存储空间，提高回忆质量

## 未来扩展

1. **LLM集成** - 使用LLM自动分配权重
2. **动态阈值** - 根据记忆库状态调整权重阈值
3. **记忆重要性衰减** - 随时间降低旧记忆的权重
4. **跨记忆模式识别** - 识别多个记忆间的共同模式

## 版本

- **v1.0.0** (2025-10-25): 初始发布
  - 情绪变化记录
  - 思考内容权重
  - 基于权重的压缩
  - 记忆作为手段

