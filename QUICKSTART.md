# FakeMan 快速开始指南

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd fakeman-project
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并添加API密钥：

```bash
# DeepSeek API (推荐)
DEEPSEEK_API_KEY=your_deepseek_api_key

# 或使用其他提供商
# ANTHROPIC_API_KEY=your_anthropic_api_key
# OPENAI_API_KEY=your_openai_api_key
```

## 基础使用

### 示例1: 简单演示

运行预设的对话示例：

```bash
python examples/simple_demo.py
```

### 示例2: 交互式对话

与 FakeMan 实时对话：

```bash
python examples/interactive_chat.py
```

交互命令：
- 直接输入文本进行对话
- `stats` - 查看系统统计
- `desires` - 查看当前欲望状态
- `quit` / `exit` - 退出

### 示例3: 编程使用

```python
from utils.config import Config
from main import FakeManSystem

# 创建系统
config = Config()
system = FakeManSystem(config)

# 运行决策周期
result = system.run_cycle("你好，今天怎么样？")
print(f"FakeMan: {result['action']}")

# 处理响应
exp = system.handle_response(
    cycle_result=result,
    response="还不错！",
    response_type='positive'
)

# 查看欲望变化
print(f"欲望状态: {system.desire_manager.get_current_desires()}")
```

## 核心概念

### 1. 欲望系统

FakeMan 有四种基础欲望（总和恒为1）：

- **existing** (维持存在): 0.4
- **power** (增加手段): 0.2  
- **understanding** (获得认可): 0.25
- **information** (减少不确定性): 0.15

### 2. 决策流程

```
欲望状态 → 生成目的 → 选择手段 → 思考 → 行动
                                          ↓
环境响应 ← 更新欲望 ← 记录经验 ← 压缩思考 ←
```

### 3. 记忆系统

- 使用 JSON 文件存储（`data/experiences.json`）
- 支持相似度检索
- 包含成就感机制（思考越多，完成时奖励越高）
- 包含无聊机制（重复无效行为会降低bias）

### 4. 手段bias

手段的选择基于：
- 历史成功率
- 对目的的影响程度
- 完成后的欲望变化
- 无聊程度（重复无效会降低）

## 配置

### 修改LLM提供商

编辑 `utils/config.py` 或使用环境变量：

```python
# 使用 DeepSeek (默认)
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# 使用 Claude
LLM_PROVIDER=anthropic  
LLM_MODEL=claude-3-sonnet-20240229

# 使用 GPT
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

### 修改初始欲望

编辑 `utils/config.py` 中的 `DesireConfig.initial_desires`：

```python
initial_desires: Dict[str, float] = {
    'existing': 0.5,      # 增加维持存在欲望
    'power': 0.1,         # 降低增加手段欲望
    'understanding': 0.2,
    'information': 0.2
}
```

### 调整偏见参数

编辑 `utils/config.py` 中的 `BiasConfig`：

```python
fear_multiplier: float = 3.0  # 提高损失厌恶
time_discount_rate: float = 0.2  # 更看重即时满足
```

## 数据目录

运行后会创建以下文件：

```
data/
├── experiences.json          # 经验记忆
├── experiences_backup.json   # 备份
└── logs/                     # 日志文件
    ├── fakeman.log          # 主日志
    ├── desire_changes.jsonl # 欲望变化日志
    └── decision_cycles.jsonl # 决策周期日志
```

## 查看记忆

经验记录在 `data/experiences.json` 中，可以直接打开查看：

```json
{
  "metadata": {
    "last_updated": 1234567890,
    "total_experiences": 10
  },
  "experiences": [
    {
      "id": 1,
      "purpose": "理解用户意图",
      "means": "询问",
      "total_happiness_delta": 0.5,
      "achievement_multiplier": 1.8
    }
  ]
}
```

## 故障排除

### API调用失败

1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看日志：`data/logs/fakeman.log`

### 记忆文件损坏

如果 `experiences.json` 损坏：

1. 使用备份：`cp data/experiences_backup.json data/experiences.json`
2. 或删除文件重新开始：`rm data/experiences.json`

### 导入错误

确保从项目根目录运行：

```bash
# 正确
python examples/simple_demo.py

# 错误
cd examples
python simple_demo.py
```

## 下一步

- 阅读完整文档：`README.md`
- 查看架构设计：`docs/architecture.md`（如果有）
- 探索源代码：从 `main.py` 开始
- 尝试修改配置观察行为变化

## 常见问题

**Q: 为什么 FakeMan 的回答每次都不同？**  
A: 因为欲望状态会随着对话演化，影响决策。这是设计的核心特性。

**Q: 如何让 FakeMan 更"激进"或更"保守"？**  
A: 调整初始欲望和 `BiasConfig` 参数。例如：
   - 提高 `power` 欲望 → 更主动尝试新手段
   - 提高 `existing` 欲望 → 更注重维持稳定
   - 增加 `fear_multiplier` → 更保守避险

**Q: 记忆会无限增长吗？**  
A: 目前没有自动清理机制，但可以手动删除旧记忆或实现自定义清理策略。

**Q: 可以在生产环境使用吗？**  
A: 这是一个实验性项目，建议仅用于研究和学习。

## 联系与反馈

如有问题或建议，请提交 Issue。

