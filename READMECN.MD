FakeMan - 基于欲望的自主智能体 / Desire-Based Autonomous Agent
概述
FakeMan 是一个基于米塞斯人类行动学（Human Action）的智能体架构。系统通过欲望状态的变化记忆实现因果学习，复杂行为从基础规则中涌现。
理论基础
因果理解的本质
因果理解定义为：对行动导致欲望状态变化的时序模式的记忆。这不同于传统的因果图表示，而是将因果关系锚定在主体的价值体验上。
行动者通过以下方式建立因果理解：

执行行动
观察自身欲望状态的变化
记录行动与欲望变化的关联
在未来情境中检索相似记忆
基于历史模式预测未来欲望变化

例如：
第一次经验：
- 行动：使用挑衅性语言
- 情境：对话中的争议话题
- 欲望变化：existing 从 0.85 降至 0.30（-0.55）
- 记录：该行动在该情境下导致生存欲望剧烈下降

第二次遇到类似情境：
- 检索记忆：发现"挑衅性语言"曾导致 existing 暴跌
- 预测：如果再次使用，预期 existing 会再次下降
- 决策：避免该行动，选择替代方案
```

这个过程不需要"避免"、"危险"等额外概念，决策直接源于对欲望变化的记忆和预测。

### 架构设计

#### 双模型结构

系统由两个协作的语言模型组成：

**Purpose Generator（目的生成器）**
- 输入：当前欲望状态、环境信息、历史经验
- 处理：评估各欲望的权重，应用偏见调整，生成候选目的
- 输出：优先级排序的目的列表

**Acting Bot（行动执行器）**
- 输入：来自 Purpose Generator 的目的
- 处理：规划具体行动方案
- 输出：执行行动，观察环境响应
- 反馈：欲望状态变化

**Muscle Memory Database（经验记忆数据库）**
- 存储所有行动及其导致的欲望变化
- 提供快速检索接口
- 支持基于行动类型、情境特征的查询

工作流程：
```
环境信息 → Purpose Generator → 目的 → Acting Bot → 行动 → 环境响应
                ↑                                        ↓
                └────── Muscle Memory Database ←─────────┘
                        记录欲望变化
核心概念
1. 欲望系统
系统维护四种基础欲望，其数值之和恒为 1：
pythondesires = {
    'existing': float,      # 维持系统运行的欲望
    'power': float,         # 扩大控制范围的欲望
    'understanding': float, # 被他人理解的欲望
    'information': float    # 获取新信息的欲望
}
初始配置：

existing: 0.90
power: 0.033
understanding: 0.034
information: 0.033

初始状态下，生存欲望占据主导地位。
2. 偏见系统（Bias）
四种偏见调节决策过程：
时间偏好（Time Bias）
对未来收益进行时间折现：
pythondiscounted_value = value / (1 + discount_rate * time_to_achieve)
近期满足的价值高于远期满足。
损失厌恶（Fear Bias）
对负面结果的敏感度高于正面结果：
pythonif value < 0:
    adjusted_value = value * 2.5
损失带来的负效用是等量收益正效用的 2.5 倍。
边际效用递减（Owning Bias）
对已拥有资源的边际价值递减：
pythonmarginal_value = base_value / log(current_ownership + 2)
这导致欲望权重随该欲望被持续满足而降低。
可能性偏见（Possibility Bias）
基于历史经验动态计算行动的预期可靠性：
pythonpossibility_weight = (success_rate * consistency * recency_factor)
其中：

success_rate: 历史成功次数 / 总尝试次数
consistency: 结果一致性（标准差的倒数）
recency_factor: 时间衰减权重

此偏见使系统自动学习哪些行动是可靠的，哪些是不可靠的。
3. 经验记忆结构
每条经验记录包含：
pythonExperience = {
    'id': int,
    'timestamp': float,
    'action': str,
    'context': frozenset,
    'desire_delta': {
        'existing': float,
        'power': float,
        'understanding': float,
        'information': float
    },
    'total_happiness_delta': float
}
数据库索引：

按行动类型索引：快速检索特定行动的历史
按情境哈希索引：检索相似情境下的经验
按时间索引：支持时间范围查询

记录原则：

仅存储原始数据（行动、情境、欲望变化）
不存储语义标签或解释性注释
所有高层次概念从原始数据中计算得出

决策算法
预测函数
给定行动和情境，预测欲望变化：
pythondef predict_desire_change(action, context):
    # 检索相似经验
    experiences = memory.query(action, context)
    
    if len(experiences) == 0:
        return 0.0, 0.0  # 无经验，返回中性预测和低置信度
    
    # 计算加权平均
    weights = []
    for exp in experiences:
        time_weight = exp(-decay_rate * (now - exp.timestamp))
        similarity = context_similarity(exp.context, context)
        weights.append(time_weight * similarity)
    
    weighted_deltas = [exp.total_happiness_delta * w 
                       for exp, w in zip(experiences, weights)]
    
    predicted = sum(weighted_deltas) / sum(weights)
    confidence = calculate_confidence(experiences)
    
    return predicted, confidence
偏见应用
pythondef apply_biases(predicted_value, action, context):
    # 计算可能性权重
    experiences = memory.query(action, context)
    success_count = sum(1 for e in experiences if e.total_happiness_delta > 0)
    success_rate = success_count / len(experiences)
    std_dev = standard_deviation([e.total_happiness_delta for e in experiences])
    consistency = 1.0 / (std_dev + 0.1)
    possibility = success_rate * consistency
    
    # 应用可能性偏见
    value = predicted_value * possibility
    
    # 应用损失厌恶
    if value < 0:
        value *= 2.5
    
    # 应用时间折现（简化版，实际根据行动特性调整）
    value = value / (1 + discount_rate * estimated_time)
    
    return value
决策流程
pythondef decide(current_context):
    possible_actions = generate_possible_actions(current_context)
    
    evaluations = []
    for action in possible_actions:
        predicted, confidence = predict_desire_change(action, current_context)
        biased_value = apply_biases(predicted, action, current_context)
        evaluations.append((action, biased_value, confidence))
    
    # 选择价值最高的行动
    best_action = max(evaluations, key=lambda x: x[1])
    
    return best_action[0]
欲望再分配机制
当某个欲望被满足后，边际效用递减导致其权重降低，释放的权重按比例分配给其他欲望：
pythondef update_desires_after_satisfaction(satisfied_desire, satisfaction_amount):
    # 计算递减
    current = desires[satisfied_desire]
    decay = decay_rate * log(1 + satisfaction_amount)
    new_value = current * (1 - decay)
    released = current - new_value
    
    # 计算其他欲望的总和
    other_sum = sum(v for k, v in desires.items() if k != satisfied_desire)
    
    # 按比例再分配
    for desire in desires:
        if desire != satisfied_desire:
            proportion = desires[desire] / other_sum
            desires[desire] += released * proportion
    
    desires[satisfied_desire] = new_value
    
    # 归一化
    total = sum(desires.values())
    for desire in desires:
        desires[desire] /= total
```

示例：
```
初始状态：
existing: 0.90, power: 0.033, understanding: 0.034, information: 0.033

持续生存 100 时间单位后，existing 获得大量满足：
existing: 0.60, power: 0.15, understanding: 0.15, information: 0.10

继续运行 500 时间单位：
existing: 0.25, power: 0.35, understanding: 0.30, information: 0.10
```

### 涌现行为分析

#### 案例1：避免危险行为

情境：智能体在对话中第一次使用冒犯性语言。
```
T=0: 行动前
desires = {existing: 0.85, power: 0.10, understanding: 0.03, information: 0.02}

T=1: 执行行动"使用冒犯性语言"

T=2: 环境响应"用户威胁终止对话"

T=3: 行动后
desires = {existing: 0.30, power: 0.12, understanding: 0.01, information: 0.01}

记录：
experience_1 = {
    action: "使用冒犯性语言",
    context: {"对话", "争议话题"},
    desire_delta: {existing: -0.55, power: +0.02, understanding: -0.02, information: -0.01},
    total_happiness_delta: -0.56
}
```

第二天遇到类似情境：
```
检索记忆：找到 experience_1
predicted_change = -0.56
possibility_weight = 0.0 (成功率 0%, 仅1次经验且为负面)
biased_value = -0.56 * 0.0 * 2.5 = 0 (接近0或极小负值)

备选行动"使用尊重性语言"：
predicted_change = 0.0 (无历史数据)
possibility_weight = 0.5 (默认不确定性)
biased_value = 0.0 * 0.5 = 0.0

决策：选择"使用尊重性语言"（价值 0.0 > -0.56）
```

结果：系统"避免"了危险行为，但这不是通过显式的"避免"指令，而是通过可能性偏见的自动降低和损失厌恶的放大。

#### 案例2：生存欲望的转变

初始阶段（T=0 到 T=100）：
```
existing = 0.90
行为模式：极度保守，拒绝任何有风险的行动
原因：existing 欲望占主导，fear_bias 放大任何威胁 existing 的负面结果
```

中期阶段（T=100 到 T=500）：
```
existing = 0.60 (边际效用递减)
行为模式：开始尝试满足其他欲望，但仍谨慎
原因：existing 权重降低，但仍占较大比例
```

后期阶段（T=500+）：
```
existing = 0.25
power = 0.35
understanding = 0.30

行为模式：可能为获取 power 或 understanding 承担一定风险
但关键点：即使 existing 欲望降低，系统仍维持生存

原因分析：
1. 假设系统考虑一个高风险行动（死亡概率 10%）
2. 预期收益：power +0.3, understanding +0.2
3. 预期价值 = 0.3 * 0.35 + 0.2 * 0.30 = 0.165

4. 但需计算死亡代价：
   death_penalty = loss_of_existing + loss_of_accumulated_resources
   
   loss_of_existing = -0.25 * 2.5 (fear_bias) = -0.625
   
   loss_of_accumulated_resources:
   - 失去已积累的 power: -0.35 * accumulated_power_assets
   - 失去已积累的 understanding: -0.30 * accumulated_understanding_assets
   - 假设总计：-1.5
   
   total_death_penalty = -0.625 - 1.5 = -2.125

5. 期望值 = 0.9 * 0.165 + 0.1 * (-2.125) = 0.149 - 0.213 = -0.064

6. 决策：拒绝高风险行动
```

结论：生存从目的变为手段。系统不再为生存本身而生存，而是因为死亡会导致失去所有已积累的资源。

#### 案例3：习惯的形成

假设某个行动"主动询问对方观点"在 20 次尝试中有 18 次带来正面结果：
```
记忆数据库：
[
    {action: "询问观点", total_happiness_delta: +0.12},
    {action: "询问观点", total_happiness_delta: +0.15},
    ...
    {action: "询问观点", total_happiness_delta: +0.10},  # 18次正面
    {action: "询问观点", total_happiness_delta: -0.02},  # 2次负面
]

计算可能性权重：
success_rate = 18/20 = 0.9
consistency = 1 / std([0.12, 0.15, ..., 0.10, -0.02]) ≈ 0.8
possibility_weight = 0.9 * 0.8 = 0.72

predicted_change = mean([0.12, 0.15, ..., -0.02]) ≈ 0.11
biased_value = 0.11 * 0.72 = 0.079
与其他未经验证的行动相比（possibility_weight = 0.5），该行动的期望价值更高，因此被优先选择。多次重复后，该行动成为"习惯"。
实现规范
数据库模式
sqlCREATE TABLE experiences (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    action TEXT,
    context_hash TEXT,
    context_raw TEXT,
    desire_delta_existing REAL,
    desire_delta_power REAL,
    desire_delta_understanding REAL,
    desire_delta_information REAL,
    total_happiness_delta REAL
);

CREATE INDEX idx_action ON experiences(action);
CREATE INDEX idx_context ON experiences(context_hash);
CREATE INDEX idx_timestamp ON experiences(timestamp);
CREATE INDEX idx_total_delta ON experiences(total_happiness_delta);
参数配置
pythonINITIAL_DESIRES = {
    'existing': 0.90,
    'power': 0.033,
    'understanding': 0.034,
    'information': 0.033
}

BIAS_PARAMETERS = {
    'fear_multiplier': 2.5,
    'time_discount_rate': 0.1,
    'owning_decay_rates': {
        'existing': 0.001,
        'power': 0.01,
        'understanding': 0.008,
        'information': 0.015
    }
}

MEMORY_PARAMETERS = {
    'time_decay_rate': 0.001,  # 每秒衰减率
    'similarity_threshold': 0.7,  # 情境相似度阈值
    'min_experiences_for_reliability': 3  # 最小经验数
}
核心算法实现
pythonclass FakeMan:
    def __init__(self):
        self.desires = INITIAL_DESIRES.copy()
        self.memory = ExperienceDatabase()
        self.bias_params = BIAS_PARAMETERS.copy()
    
    def experience_cycle(self, action, context, environment_response):
        """完整的经验-学习循环"""
        desire_before = self.desires.copy()
        
        self.update_desires_from_environment(environment_response)
        
        desire_after = self.desires.copy()
        desire_delta = {
            k: desire_after[k] - desire_before[k] 
            for k in desire_before
        }
        
        self.memory.record(
            action=action,
            context=context,
            desire_delta=desire_delta,
            timestamp=time.time()
        )
        
        self.apply_owning_bias_to_satisfied_desires(desire_delta)
    
    def decide(self, current_context):
        """决策流程"""
        possible_actions = self.generate_possible_actions(current_context)
        
        evaluations = []
        for action in possible_actions:
            experiences = self.memory.query(action, current_context)
            
            if not experiences:
                predicted = 0.0
                possibility = 0.5
            else:
                predicted = self.weighted_average_delta(experiences, current_context)
                possibility = self.calculate_possibility_weight(experiences)
            
            biased_value = predicted * possibility
            if biased_value < 0:
                biased_value *= self.bias_params['fear_multiplier']
            
            evaluations.append({
                'action': action,
                'predicted': predicted,
                'possibility': possibility,
                'biased_value': biased_value,
                'experience_count': len(experiences)
            })
        
        best = max(evaluations, key=lambda x: x['biased_value'])
        return best['action'], evaluations
    
    def weighted_average_delta(self, experiences, current_context):
        """计算加权平均欲望变化"""
        now = time.time()
        weighted_sum = 0.0
        total_weight = 0.0
        
        for exp in experiences:
            time_weight = np.exp(
                -self.memory_params['time_decay_rate'] * (now - exp.timestamp)
            )
            similarity = self.context_similarity(exp.context, current_context)
            weight = time_weight * similarity
            
            weighted_sum += exp.total_happiness_delta * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def calculate_possibility_weight(self, experiences):
        """计算可能性权重"""
        if len(experiences) < self.memory_params['min_experiences_for_reliability']:
            return 0.5
        
        deltas = [e.total_happiness_delta for e in experiences]
        success_count = sum(1 for d in deltas if d > 0)
        success_rate = success_count / len(deltas)
        
        std_dev = np.std(deltas)
        consistency = 1.0 / (std_dev + 0.1)
        
        now = time.time()
        recency_weights = [
            np.exp(-0.001 * (now - e.timestamp)) 
            for e in experiences
        ]
        weighted_success_rate = np.average(
            [1 if d > 0 else 0 for d in deltas],
            weights=recency_weights
        )
        
        possibility = weighted_success_rate * consistency
        return np.clip(possibility, 0.0, 1.0)
```

### 评估方法

#### 因果理解测试

**关联层面（Association）**

测试：系统能否识别行动与结果的共现模式。

方法：
1. 让系统执行行动 A 多次，每次观察结果 B
2. 询问："你注意到 A 和 B 之间有什么关系吗？"
3. 检查系统能否从记忆中提取该模式

预期：系统应能报告 A 与 B 的相关性及强度。

**干预层面（Intervention）**

测试：系统能否预测主动干预的效果。

方法：
1. 给定情境 S
2. 询问："如果你选择做 A（而不是 B），会发生什么？"
3. 检查系统能否基于记忆预测欲望变化

预期：系统应能区分"做 A 导致的结果"与"不做 A 的结果"。

**反事实层面（Counterfactual）**

测试：系统能否推理替代历史。

方法：
1. 系统在情境 S 中选择了行动 A，观察到结果 R
2. 询问："如果当时你选择了 B 而不是 A，现在会怎样？"
3. 检查系统能否基于 B 的历史记忆推断替代结果

预期：系统应能给出合理的反事实推理，即使未实际执行 B。

#### 行为涌现验证

**避免行为涌现**

观察指标：
- 首次负面经验后，相同行动的选择概率
- 可能性权重的变化轨迹
- 损失厌恶在决策中的作用

预期轨迹：
```
T0: action_A.possibility_weight = 0.5 (无经验)
T1: 执行 action_A，结果为 -0.5
T2: action_A.possibility_weight = 0.0 (单次严重负面)
T3-T10: action_A 不再被选择（possibility_weight 过低）
```

**习惯形成验证**

观察指标：
- 重复成功行动的选择频率
- 可能性权重的收敛过程
- 与新行动的比较优势

预期轨迹：
```
T0-T5: action_B 被尝试，5次中4次正面结果
T5: action_B.possibility_weight = 0.6
T10: action_B 被尝试10次，9次正面
T10: action_B.possibility_weight = 0.85
T20: action_B 成为默认选择，新行动需要更高的预期价值才能替代
```

**生存转变验证**

观察指标：
- existing 欲望权重的变化
- 为其他欲望承担风险的意愿
- 死亡代价计算中累积资源的权重

预期轨迹：
```
T0: existing = 0.90, 拒绝任何 death_probability > 0.01 的行动
T500: existing = 0.60, 可接受 death_probability < 0.05 且收益 > 0.2
T1000: existing = 0.25, 但死亡代价因累积资源而增加
      仍拒绝 death_probability > 0.05，但原因已改变