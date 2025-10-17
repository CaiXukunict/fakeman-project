# FakeMan 持续思考系统使用指南

## 系统概述

FakeMan 持续思考系统实现了异步持续思考模型，AI 会持续运行并思考，而不是被动等待用户输入。

### 核心特性

1. **持续思考**: 每秒思考一次当前状态
2. **主动行动**: 根据内在欲望压力评估是否主动发言
3. **异步通信**: main.py 和 chat.py 通过文件进行进程间通信
4. **欲望驱动**: 所有行为由内在欲望状态驱动

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    FakeMan 系统                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           main.py (持续思考进程)                  │  │
│  │                                                   │  │
│  │  [每1秒循环]                                      │  │
│  │    ├─ 检查用户输入                                │  │
│  │    │   └─ 如果有 → 处理并回应                     │  │
│  │    │                                              │  │
│  │    ├─ 内部思考                                    │  │
│  │    │   └─ 评估欲望压力                            │  │
│  │    │   └─ 评估主动行动收益 vs 风险                │  │
│  │    │   └─ 如果条件满足 → 主动发言                 │  │
│  │    │                                              │  │
│  │    └─ 更新系统状态                                │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↕                              │
│                   [文件通信]                             │
│         user_input.json / ai_output.json               │
│              / system_state.json                        │
│                          ↕                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │            chat.py (用户交互界面)                 │  │
│  │                                                   │  │
│  │  ├─ 接收用户输入                                  │  │
│  │  ├─ 写入 user_input.json                         │  │
│  │  ├─ 等待并读取 ai_output.json                    │  │
│  │  └─ 显示 AI 回应                                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 使用方法

### 第一步：启动持续思考进程

在一个终端窗口中启动 main.py：

```bash
# 设置编码（Windows PowerShell）
$env:PYTHONIOENCODING='utf-8'

# 启动系统
python main.py
```

你会看到类似输出：

```
============================================================
FakeMan 持续思考系统
============================================================

正在初始化...
[日志] FakeMan 系统初始化开始
[日志] 欲望系统初始化: DesireManager(...)
[日志] 记忆系统初始化: 0 条经验
[日志] 通信系统初始化完成

FakeManSystem(cycles=0, memories=0)

当前欲望状态:
  existing       : 0.400
  power          : 0.200
  understanding  : 0.250
  information    : 0.150

通信文件目录: data\communication
  - 输入文件: user_input.json
  - 输出文件: ai_output.json
  - 状态文件: system_state.json

提示:
  - 系统将持续运行，每秒思考一次
  - 使用 chat.py 进行交互
  - 按 Ctrl+C 停止系统

启动持续思考循环...
============================================================
[日志] 开始持续思考循环
[日志] [静默思考] 无充分理由
[日志] [静默思考] 无充分理由
...
```

### 第二步：启动用户交互界面

在另一个终端窗口中启动 chat.py：

```bash
# 设置编码（Windows PowerShell）
$env:PYTHONIOENCODING='utf-8'

# 启动聊天界面
python chat.py
```

你会看到：

```
============================================================
  FakeMan 聊天界面
============================================================

  欢迎使用 FakeMan 聊天系统！

  这是一个基于欲望驱动的 AI 系统：
  • AI 会持续思考当前状态
  • AI 可能会主动发起对话
  • AI 的行为由内在欲望驱动

------------------------------------------------------------
  系统状态
------------------------------------------------------------
  状态: running
  周期: 0

  当前欲望:
    💚 existing     : 0.400
    ⚡ power        : 0.200
    🤝 understanding: 0.250
    📚 information  : 0.150

============================================================
  开始对话
============================================================
提示:
  - 输入消息与 FakeMan 对话
  - 输入 'state' 查看系统状态
  - 输入 'desires' 查看欲望状态
  - 输入 'history' 查看对话历史
  - 输入 'quit' 或 'exit' 退出

你: 
```

### 第三步：与 AI 对话

直接输入消息：

```
你: 你好，你是谁？
[FakeMan 正在思考...]

FakeMan: 你好！我是 FakeMan，一个基于欲望驱动的 AI 系统...

[思考] 用户询问身份，选择坦诚回答以建立信任和理解
```

### 特殊命令

- `state` / `s` - 查看系统状态
- `desires` / `d` - 查看欲望状态
- `history` / `h` - 查看对话历史
- `quit` / `exit` / `q` - 退出

## 主动行动机制

AI 会在以下情况下主动发言：

### 1. existing 欲望驱动

当 `existing` 欲望 > 0.5 且距上次行动 > 60秒时：

```
[main.py 日志]
[主动思考] 决定主动行动: existing欲望驱动（0.62）, 预期收益: 0.186
主动行动周期 #3
原因: existing欲望驱动（0.62）
```

```
[chat.py 显示]
💡 [FakeMan 主动发言]
FakeMan: 我们聊了这么久，你觉得怎么样？有什么想继续探讨的吗？
```

### 2. information 欲望驱动

当 `information` 欲望 > 0.3 且欲望压力 > 0.2时：

```
💡 [FakeMan 主动发言]
FakeMan: 有个问题我一直在想，你对这个话题有什么看法？
```

### 3. understanding 欲望驱动

当 `understanding` 欲望 > 0.35 且距上次行动 > 120秒时：

```
💡 [FakeMan 主动发言]
FakeMan: 我希望确认一下，我的解释你是否理解了？
```

## 文件通信协议

### user_input.json

```json
{
  "text": "用户输入的消息",
  "timestamp": 1234567890.123,
  "metadata": {}
}
```

### ai_output.json

```json
{
  "text": "AI 的回复",
  "action_type": "response",  // 或 "proactive" 或 "idle"
  "thought_summary": "思考摘要",
  "desires": {
    "existing": 0.45,
    "power": 0.22,
    "understanding": 0.18,
    "information": 0.15
  },
  "timestamp": 1234567890.456
}
```

### system_state.json

```json
{
  "status": "running",  // "initializing", "running", "stopped", "error"
  "cycle": 15,
  "desires": {
    "existing": 0.45,
    "power": 0.22,
    "understanding": 0.18,
    "information": 0.15
  },
  "context": "当前对话上下文",
  "last_action_time": 1234567890.789
}
```

## 系统调优

### 调整思考频率

在 `main.py` 的 `continuous_thinking_loop()` 方法中修改：

```python
if elapsed < 1.0:  # 改为 0.5 表示每0.5秒思考一次
    time.sleep(1.0 - elapsed)
```

### 调整主动行动阈值

在 `ActionEvaluator.should_act_proactively()` 方法中修改：

```python
# 最小时间间隔
if time_since_last < 30:  # 改为更大或更小的值
    return False, "时间间隔太短", 0.0

# existing 欲望阈值
if dominant_value > 0.5 and time_since_last > 60:  # 调整阈值
    ...
```

### 调整欲望更新速度

在配置文件或 `DesireUpdater` 中调整信号强度和更新率。

## 监控和调试

### 查看实时日志

main.py 的所有活动都记录在日志中：

```bash
# 查看主日志
tail -f data/logs/fakeman.log

# 查看欲望变化
tail -f data/logs/desire_changes.jsonl

# 查看决策周期
tail -f data/logs/decision_cycles.jsonl
```

### 查看通信文件

```bash
# 实时查看系统状态（Windows）
Get-Content data/communication/system_state.json -Wait

# Linux/Mac
watch -n 1 cat data/communication/system_state.json
```

## 常见问题

### Q: chat.py 提示系统未运行？

A: 确保 main.py 在另一个终端中正在运行。

### Q: AI 一直不主动发言？

A: 主动行动有严格的条件。可以：
1. 降低主动行动的阈值
2. 增加欲望压力（通过对话改变欲望状态）
3. 等待更长时间

### Q: 响应超时？

A: 检查：
1. main.py 是否正常运行
2. LLM API 是否可用
3. 网络连接是否正常
4. 增加 `wait_for_response()` 的超时时间

### Q: 如何停止系统？

A: 
1. chat.py: 输入 `quit` 或按 Ctrl+C
2. main.py: 按 Ctrl+C

## 进阶使用

### 多用户支持

可以修改通信文件结构，为每个用户创建独立的通信目录：

```python
comm = CommunicationFiles(comm_dir=f"data/communication/{user_id}")
```

### 持久化对话

在 `_handle_user_input()` 中调用 `handle_response()` 记录经验：

```python
# 在下一次用户输入时，根据内容判断上次回应的效果
response_type = self._infer_response_type(user_input)
exp = self.handle_response(last_result, user_input, response_type)
```

### 自定义行动评估

继承 `ActionEvaluator` 并重写 `should_act_proactively()` 方法，实现自定义的主动行动逻辑。

## 总结

持续思考系统让 FakeMan 真正"活"了起来：
- ✅ 持续运行，时刻思考
- ✅ 主动行动，不只是被动回应
- ✅ 欲望驱动，行为有内在动机
- ✅ 异步通信，支持多进程架构

享受与 FakeMan 的对话吧！

