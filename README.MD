FakeMan - 基于欲望的自主智能体
### 概述
FakeMan 是基于米塞斯人类行动学理论构建的智能体架构。系统核心思想是：智能体通过记忆"行动导致欲望如何变化"来理解因果关系，复杂的智能行为从简单的基础规则中自然涌现。
### 系统包含三个核心组件：
```
Purpose Generator（目的生成器）：基于当前欲望状态和历史经验生成行动目的
Acting Bot（行动执行器）：执行具体行动并观察结果
Muscle Memory Database（经验记忆数据库）：记录所有行动及其导致的欲望变化
```
### 核心机制
```
欲望系统：四种基础欲望（生存、权力、来自他人的理解、信息），总和恒为1，通过边际效用递减实现动态再分配。
偏见系统：四种调节器影响决策，分别是：时间偏好，损失偏好，边际效用递减，可能性偏见

具体的偏见含意：
时间偏好：近期满足价值更高
损失厌恶：负面结果权重2.5倍
边际效用递减：重复满足导致欲望权重降低
可能性偏见：基于历史成功率自动计算行动可靠性
```
### 学习循环：
行动 → 观察欲望变化 → 记录到数据库 → 未来根据记忆预测 → 决策
### 
不依赖符号推理或抽象因果图，而是通过记忆"行动→欲望变化"的时序模式实现因果学习，支持关联、干预、反事实三个层次的推理。
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