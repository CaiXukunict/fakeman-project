# 场景模拟系统 - 快速入门

## 🎯 这是什么？

为FakeMan添加的场景模拟系统，让AI能够：
- 在行动前**预测效果**
- 思考"**如果...就好了**"
- **记住重要历史**
- **避免明显错误**

## 🚀 快速开始

### 1. 直接使用（已集成）

```bash
# 正常启动FakeMan即可
python main.py
```

场景模拟会自动运行，你会看到：
```
步骤2: 场景模拟与手段选择
  生成了 5 个候选手段
  可行手段: 3, 妄想手段: 1
  选定手段类型: ask_question
  预测幸福度变化: +0.12
```

### 2. 运行测试

```bash
# Windows PowerShell
$env:PYTHONIOENCODING="utf-8"; python test_scenario_simulation.py
```

## 📁 新增文件

```
scenario/
  └── scenario_simulator.py      # 场景模拟器

memory/
  └── long_term_memory.py        # 长记忆系统

data/
  ├── scenario_state.json        # 场景状态（自动生成）
  └── long_term_memory.json      # 长记忆（自动生成）

test_scenario_simulation.py      # 测试脚本

docs/
  ├── SCENARIO_SIMULATION.md     # 技术文档
  └── SCENARIO_USAGE_GUIDE.md    # 详细指南
```

## ✨ 核心功能

### 1️⃣ 手段预测
系统会模拟每个手段的效果再做选择：
```
候选1: ask_question    → 预测 +0.12 幸福度 ✓
候选2: make_statement  → 预测 +0.06 幸福度 ✓
候选3: wait            → 预测 -0.03 幸福度 ✗ 过滤
```

### 2️⃣ 妄想生成
长时间无输入时，系统会开始"做梦"：
```
30秒无输入 → 生成当前妄想
  "如果我有更多行动方式就好了..."

60秒无输入 → 回顾过去
  "如果当时我那样做，现在会更好..."
```

### 3️⃣ 场景感知
系统知道当前的情况：
```
当前情况: 正在与用户对话
我的角色: AI助手
交流者: user (重要性=1.0, 形象偏差=0.4)
```

### 4️⃣ 长记忆
快速回顾历史：
```
✓ 用户询问能力 → 详细解释 (+0.35幸福度)
✗ 长时间无响应 → 主动对话 (-0.25幸福度)
○ 用户提问题 → 请求澄清 (+0.05幸福度)
```

## 🔢 欲望计算

### existing（存在）= 平均存活概率
- 手段越安全 → existing越低
- 环境越危险 → existing越高

### power（手段）= 无法达成的手段比例  
- 妄想越多 → power越高
- 能力越强 → power越低

### information（信息）= 1 - 确定性
- 越不确定 → information越高
- 越明确 → information越低

### understanding（认同）= 形象偏差
- 形象差距大 → understanding越高
- 被理解 → understanding越低

## 📊 查看状态

### 场景状态
```bash
cat data/scenario_state.json
```

### 长记忆
```bash
cat data/long_term_memory.json
```

### 系统统计
```python
from main import FakeManSystem
from utils.config import Config

system = FakeManSystem(Config())
stats = system.get_stats()

print(stats['scenario'])       # 场景信息
print(stats['long_memory'])    # 记忆统计
```

## 🎮 互动示例

```
你: 你好

系统内部:
  [场景模拟] 生成3个候选手段
  [预测] ask_question: +0.1
  [预测] make_statement: +0.08  
  [预测] wait: -0.02 ✗ 过滤
  [选择] ask_question (最优)

AI: 你好！有什么我可以帮助你的吗？

---30秒后无输入---

系统内部:
  [妄想生成] "如果我知道用户想要什么就好了..."
  [power欲望] 上升（有想法但做不到）

---60秒后无输入---

系统内部:
  [回顾过去] "如果刚才我主动提供信息，用户可能会回应..."
  [记录幻想] 存入长记忆
```

## 📚 文档

- **SCENARIO_SYSTEM_SUMMARY.md** - 完整实现总结
- **docs/SCENARIO_SIMULATION.md** - 技术文档  
- **docs/SCENARIO_USAGE_GUIDE.md** - 详细使用指南

## ⚙️ 配置

```python
# 妄想触发时间（秒）
FANTASY_TRIGGER_TIME = 30      # 当前妄想
PAST_FANTASY_TRIGGER_TIME = 60 # 过去反思

# 手段过滤
MIN_DESIRE_DELTA = 0.0  # 负值手段被过滤

# 场景摘要频率
SUMMARY_INTERVAL = 30   # 每30秒输出
```

## ✅ 测试结果

```
✓ 场景模拟器测试完成
✓ 长记忆系统测试完成  
✓ 手段过滤测试完成
✓ 场景欲望计算测试完成

所有测试通过！
```

## 🎯 实现的需求

✅ 场景模拟和状态文件  
✅ 手段预测和效果评估  
✅ 动态欲望计算（existing/power/information/understanding）  
✅ 负面手段过滤（四个欲望相加为负）  
✅ 妄想生成（当前假设 + 过去反思）  
✅ 长记忆系统（简要历史记录）  
✅ 完整集成到main.py  

## 🌟 特色

- 🔮 **预测性决策** - 先模拟后行动
- 💭 **反思能力** - 能够幻想和后悔
- 🎭 **角色感知** - 知道自己在扮演什么
- 🛡️ **智能过滤** - 避免有害选择
- 📝 **历史意识** - 记住重要事件
- ⚡ **轻量高效** - 最小性能影响

## 💡 提示

1. **观察妄想** - 停止输入30-60秒，查看系统"做梦"
2. **查看预测** - 注意日志中的"预测幸福度变化"
3. **分析过滤** - 看哪些手段被标记为"负面"
4. **追踪场景** - 每30秒会输出场景摘要

## 🐛 常见问题

**Q: 为什么会生成妄想？**  
A: 长时间无输入时，系统开始思考"如果...会怎样"，这增加了power欲望（渴求更多能力）。

**Q: 负面手段是什么？**  
A: 四个欲望变化相加为负的手段，执行后会更不满足。

**Q: 场景预测欲望和实际欲望有什么区别？**  
A: 场景预测是"应该有"的欲望，实际欲望是"真实"的欲望。

**Q: 如何关闭妄想生成？**  
A: 在 `scenario_simulator.py` 中将触发时间设为很大（如9999秒）。

---

**开始使用：**
```bash
python main.py
```

**运行测试：**
```bash
$env:PYTHONIOENCODING="utf-8"; python test_scenario_simulation.py
```

**查看文档：**
- SCENARIO_SYSTEM_SUMMARY.md
- docs/SCENARIO_USAGE_GUIDE.md

