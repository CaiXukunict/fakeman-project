# FakeMan 持续思考系统 - 快速参考

## ⚡ 5 分钟快速开始

### 1️⃣ 安装（1分钟）
```bash
pip install -r requirements.txt
```

### 2️⃣ 配置（30秒）
创建 `.env` 文件：
```
DEEPSEEK_API_KEY=your_key_here
```

### 3️⃣ 测试（1分钟）
```bash
python test_continuous_system.py
```
看到 ✅ 全部通过？继续！

### 4️⃣ 启动（1分钟）

**终端 1:**
```bash
$env:PYTHONIOENCODING='utf-8'
python main.py
```

**终端 2:**
```bash
$env:PYTHONIOENCODING='utf-8'
python chat.py
```

### 5️⃣ 开始对话！（30秒）
```
你: 你好
FakeMan: 你好！...
```

## 🎯 一键速查

### 在 chat.py 中的命令
| 输入 | 功能 |
|------|------|
| `你好` | 普通对话 |
| `state` 或 `s` | 查看系统状态 |
| `desires` 或 `d` | 查看欲望 |
| `history` 或 `h` | 查看历史 |
| `quit` 或 `q` | 退出 |

### 系统行为速查

**响应式回复:**
```
你: [输入消息]
FakeMan: [回复]
```

**主动发言:**
```
💡 [FakeMan 主动发言]
FakeMan: [主动消息]
```

## 🔧 常用配置

### 让 AI 更主动
编辑 `main.py` 第 253 行：
```python
# 改为更短的间隔
if time_since_last < 30:  # 改为 10
```

第 270 行：
```python
# 降低阈值
if dominant_value > 0.5:  # 改为 0.3
```

### 改变思考频率
编辑 `main.py` 第 423 行：
```python
if elapsed < 1.0:  # 改为 0.5 (更快)
    time.sleep(1.0 - elapsed)
```

## 🐛 问题速查

| 问题 | 解决方案 |
|------|----------|
| 系统未运行 | 检查 main.py 是否在运行 |
| 响应超时 | 检查网络和 API key |
| 编码错误 | 设置 `$env:PYTHONIOENCODING='utf-8'` |
| AI 不主动 | 降低阈值或等待更久 |

## 📁 关键文件位置

```
data/communication/
├── user_input.json    ← 你的输入在这里
├── ai_output.json     ← AI 的回复在这里
└── system_state.json  ← 系统状态在这里
```

## 📚 更多信息

- 完整指南: `README_CONTINUOUS_THINKING.md`
- 技术文档: `docs/CONTINUOUS_THINKING.md`
- 实现总结: `SYSTEM_SUMMARY.md`

## 🎉 开始使用！

```bash
# 一条命令运行测试
python test_continuous_system.py

# 看到全部通过？开始玩吧！
python main.py  # 终端1
python chat.py  # 终端2
```

**Enjoy! 🚀**

