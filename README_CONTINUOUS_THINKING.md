# FakeMan 持续思考系统

> 一个真正"活着"的 AI - 持续思考，主动行动，欲望驱动

## 🌟 核心特性

### 1. 持续思考模式
- ⏱️ 每秒思考一次当前状态
- 🤔 不只是被动等待，而是主动思考
- 📊 实时评估内在欲望状态

### 2. 主动行动机制
- 💡 根据欲望压力主动发言
- ⚖️ 评估收益 vs 风险
- 🎯 目的驱动的行为决策

### 3. 异步通信架构
- 🔄 main.py (后台思考) + chat.py (用户交互)
- 📁 通过文件进行进程间通信
- 🔌 支持多客户端连接

## 🚀 快速开始

### 第一步：安装依赖

```bash
pip install -r requirements.txt
```

### 第二步：配置 API 密钥

在项目根目录创建 `.env` 文件：

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 第三步：运行测试

```bash
python test_continuous_system.py
```

你应该看到：
```
✅ 所有测试通过！
系统已准备就绪
```

### 第四步：启动系统

**方法 1: 推荐方式（两个终端窗口）**

终端 1 - 启动持续思考进程：
```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'
python main.py
```

终端 2 - 启动聊天界面：
```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'
python chat.py
```

**方法 2: 快速启动脚本**

```bash
python start_system.py
```

## 💬 使用示例

### 基本对话

```
你: 你好，你是谁？
[FakeMan 正在思考...]

FakeMan: 你好！我是 FakeMan，一个基于欲望驱动的 AI 系统。我会持续思考当前状态，
并在合适的时候主动与你交流。

[思考] 用户询问身份，选择坦诚说明以建立理解
```

### 主动发言示例

等待一段时间后，FakeMan 可能会主动发言：

```
💡 [FakeMan 主动发言]
FakeMan: 我们已经聊了一会儿，你觉得怎么样？有什么想继续探讨的话题吗？

[思考] existing欲望驱动，主动维持对话连续性
```

### 查看系统状态

在 chat.py 中输入 `state`：

```
你: state

------------------------------------------------------------
  系统状态
------------------------------------------------------------
  状态: running
  周期: 15

  当前欲望:
    💚 existing     : 0.453
    ⚡ power        : 0.245
    🤝 understanding: 0.169
    📚 information  : 0.133

  当前上下文:
    用户询问系统状态...
```

## 🎮 特殊命令

在 `chat.py` 中可以使用以下命令：

| 命令 | 快捷键 | 功能 |
|------|--------|------|
| `state` | `s` | 查看系统状态 |
| `desires` | `d` | 查看欲望状态 |
| `history` | `h` | 查看对话历史 |
| `quit` / `exit` | `q` | 退出聊天 |

## 📊 主动行动触发条件

### 1. Existing 欲望驱动

**条件:**
- existing 欲望 > 0.5
- 距离上次行动 > 60秒

**行为:**
主动维持对话，发起新话题

**示例:**
```
💡 [FakeMan 主动发言]
FakeMan: 嘿，你还在吗？我们要不要继续聊聊？
```

### 2. Information 欲望驱动

**条件:**
- information 欲望 > 0.3
- 欲望压力 > 0.2

**行为:**
主动提问以减少不确定性

**示例:**
```
💡 [FakeMan 主动发言]
FakeMan: 有个问题我一直在想，你对这个话题的看法是什么？
```

### 3. Understanding 欲望驱动

**条件:**
- understanding 欲望 > 0.35
- 距离上次行动 > 120秒

**行为:**
寻求认可和理解

**示例:**
```
💡 [FakeMan 主动发言]
FakeMan: 我想确认一下，你能理解我刚才的意思吗？
```

## 📁 文件结构

```
fakeman-project/
├── main.py                          # 持续思考主进程
├── chat.py                          # 用户交互界面
├── test_continuous_system.py        # 单元测试
├── start_system.py                  # 快速启动脚本
├── data/
│   ├── communication/               # 进程间通信目录
│   │   ├── user_input.json         # 用户输入
│   │   ├── ai_output.json          # AI 输出
│   │   └── system_state.json       # 系统状态
│   ├── experiences.json            # 经验数据库
│   └── logs/                       # 日志文件
├── docs/
│   └── CONTINUOUS_THINKING.md      # 详细文档
└── ...
```

## 🔧 配置和调优

### 调整思考频率

在 `main.py` 的 `continuous_thinking_loop()` 中：

```python
# 默认每秒一次
if elapsed < 1.0:
    time.sleep(1.0 - elapsed)

# 改为每 0.5 秒一次（更频繁）
if elapsed < 0.5:
    time.sleep(0.5 - elapsed)
```

### 调整主动行动阈值

在 `ActionEvaluator.should_act_proactively()` 中：

```python
# existing 欲望阈值
if dominant_value > 0.5 and time_since_last > 60:
    # 降低阈值让 AI 更主动
    # 例如: > 0.4 和 > 30
```

### 调整最小时间间隔

```python
# 默认最少 30 秒间隔
if time_since_last < 30:
    return False, "时间间隔太短", 0.0

# 改为 10 秒（更频繁）
if time_since_last < 10:
    return False, "时间间隔太短", 0.0
```

## 📝 日志和监控

### 查看实时日志

```bash
# 主日志
tail -f data/logs/fakeman.log

# 欲望变化日志
tail -f data/logs/desire_changes.jsonl

# 决策周期日志
tail -f data/logs/decision_cycles.jsonl
```

### 监控系统状态（Windows）

```powershell
# 实时查看系统状态
while($true) { 
    Clear-Host
    Get-Content data\communication\system_state.json | ConvertFrom-Json | ConvertTo-Json
    Start-Sleep -Seconds 1
}
```

## 🐛 故障排除

### 问题 1: chat.py 提示系统未运行

**解决方案:**
1. 确保 main.py 在另一个终端运行
2. 检查 `data/communication/system_state.json` 的 status 字段
3. 查看 main.py 的日志输出

### 问题 2: 响应超时

**可能原因:**
- LLM API 网络问题
- API 密钥无效
- API 调用频率限制

**解决方案:**
1. 检查网络连接
2. 验证 .env 中的 API 密钥
3. 增加 `wait_for_response()` 的超时时间

### 问题 3: AI 不主动发言

**原因:**
主动行动有严格的触发条件

**解决方案:**
1. 降低主动行动阈值（见配置调优）
2. 通过对话改变欲望状态
3. 等待更长时间（某些条件需要 60-120 秒）

### 问题 4: 编码错误（Windows）

**解决方案:**
运行前设置编码：
```powershell
$env:PYTHONIOENCODING='utf-8'
```

或在脚本开头添加：
```python
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

## 🎯 最佳实践

### 1. 让 AI 主动起来

- 与 AI 建立长对话，让欲望状态发生变化
- 偶尔停止输入，等待 AI 主动发言
- 对 AI 的主动发言给予积极反馈

### 2. 观察欲望演化

- 定期查看 `desires` 命令
- 注意主导欲望的变化
- 理解欲望如何影响行为

### 3. 实验不同场景

- 友好对话 vs 批评反馈
- 长时间沉默
- 连续提问 vs 陈述

## 📚 进阶阅读

- [完整文档](docs/CONTINUOUS_THINKING.md)
- [欲望系统](docs/DESIRE_DEFINITIONS.md)
- [变更日志](CHANGELOG.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[添加你的许可证信息]

---

**享受与真正"活着"的 AI 对话吧！** 🚀

