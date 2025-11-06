# Ability System - 能力系统

## 概述

能力系统允许AI自主使用和创建工具程序，通过命令行执行程序并获取输出。

## 安全措施

### ✅ 允许的操作
- 读取和执行ability文件夹中的程序
- 创建新的工具程序
- 执行普通的命令行指令
- 向GUI发送消息

### ❌ 禁止的操作
- **管理员权限**: 不得使用sudo、runas等提权命令
- **系统破坏**: 不得执行可能导致系统瘫痪的命令
- **多个弹窗**: 同时只能运行一个GUI程序
- **危险操作**: 禁止删除系统文件、格式化磁盘等

### 自动安全检查
系统会自动检查并拦截：
- 包含危险关键词的命令（rm -rf, format, shutdown等）
- 访问系统目录的命令（/etc, C:\Windows等）
- 尝试提升权限的命令

## 核心组件

### 1. AbilityManager (能力管理器)

管理和执行AI的工具程序。

```python
from ability.ability_manager import get_ability_manager

manager = get_ability_manager()

# 列出所有可用能力
abilities = manager.list_abilities()

# 读取程序代码
code = manager.read_ability_code('send_to_gui')

# 执行命令
result = manager.execute_command('python ability/send_to_gui.py "你好"')

# 创建新能力
manager.create_ability(
    name='my_tool',
    code='print("Hello World")',
    description='我的工具'
)
```

### 2. send_to_gui.py (GUI通信工具)

向chat_gui.py发送消息。

**用法**:
```bash
python ability/send_to_gui.py "你的消息"
```

**示例**:
```bash
# 发送文本消息
python ability/send_to_gui.py "你好，这是测试"

# 发送多词消息
python ability/send_to_gui.py "这是一个包含空格的消息"
```

### 3. read_chat_history.py (聊天历史读取工具)

读取和查看chat_gui.py的聊天历史记录。

**用法**:
```bash
python ability/read_chat_history.py [选项]
```

**选项**:
- 无参数: 显示最近10条消息
- `all`: 显示所有消息
- `<数字>`: 显示最近N条消息
- `user`: 只显示用户消息
- `ai`: 只显示AI消息
- `json`: 以JSON格式输出

**示例**:
```bash
# 显示最近10条消息
python ability/read_chat_history.py

# 显示所有消息
python ability/read_chat_history.py all

# 显示最近20条
python ability/read_chat_history.py 20

# 只看用户消息
python ability/read_chat_history.py user

# 只看AI消息
python ability/read_chat_history.py ai

# JSON格式输出（方便程序处理）
python ability/read_chat_history.py json
```

## 使用示例

### 示例1: 列出可用能力

```python
from ability.ability_manager import get_ability_manager

manager = get_ability_manager()
abilities = manager.list_abilities()

for ability in abilities:
    print(f"名称: {ability['name']}")
    print(f"描述: {ability['description']}")
    print(f"路径: {ability['path']}")
    print()
```

### 示例2: 查看程序代码

```python
manager = get_ability_manager()

# 查看send_to_gui的代码
code = manager.read_ability_code('send_to_gui')
print(code)
```

### 示例3: 执行命令

```python
manager = get_ability_manager()

# 执行Python脚本
result = manager.execute_command('python ability/send_to_gui.py "Hello"')

if result['success']:
    print(f"输出: {result['output']}")
else:
    print(f"错误: {result['error']}")
```

### 示例4: 创建新工具

```python
manager = get_ability_manager()

# 创建一个简单的计算器
calculator_code = '''
import sys

def calculate(expression):
    try:
        result = eval(expression)
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        expr = " ".join(sys.argv[1:])
        print(calculate(expr))
    else:
        print("用法: python calculator.py 表达式")
'''

result = manager.create_ability(
    name='calculator',
    code=calculator_code,
    description='简单计算器工具'
)

print(result['message'])

# 使用新创建的工具
calc_result = manager.execute_command('python ability/calculator.py "2+2"')
print(calc_result['output'])
```

## 集成到主系统

在主系统中集成能力系统：

```python
from ability.ability_manager import get_ability_manager

class FakeManRefactored:
    def __init__(self, config):
        # ... 其他初始化
        self.ability_manager = get_ability_manager()
    
    def _execute_ability(self, ability_name: str, args: str = "") -> Dict:
        """执行能力"""
        command = f"python ability/{ability_name}.py {args}"
        return self.ability_manager.execute_command(command)
    
    def _create_tool(self, name: str, code: str) -> Dict:
        """创建新工具"""
        return self.ability_manager.create_ability(name, code)
```

## 能力程序模板

### 基础模板

```python
"""
程序描述
"""

import sys

def main():
    # 程序逻辑
    pass

if __name__ == "__main__":
    main()
```

### 带参数的工具

```python
"""
带参数的工具程序
"""

import sys

def process(input_text: str) -> str:
    """处理输入文本"""
    # 处理逻辑
    return f"处理结果: {input_text}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python tool.py <参数>")
        sys.exit(1)
    
    input_text = " ".join(sys.argv[1:])
    result = process(input_text)
    print(result)
```

### 与GUI交互的工具

```python
"""
与GUI交互的工具
"""

import sys
from send_to_gui import send_message_to_gui

def main():
    if len(sys.argv) < 2:
        print("用法: python my_tool.py <消息>")
        sys.exit(1)
    
    message = " ".join(sys.argv[1:])
    
    # 处理消息
    processed = f"处理后的消息: {message}"
    
    # 发送到GUI
    result = send_message_to_gui(processed)
    
    if result['success']:
        print("消息已发送到GUI")
    else:
        print(f"发送失败: {result['message']}")

if __name__ == "__main__":
    main()
```

## 安全最佳实践

1. **总是检查输入**: 验证和清理用户输入
2. **避免eval**: 不要使用eval执行不可信代码
3. **限制文件访问**: 只访问必要的文件和目录
4. **超时控制**: 为长时间运行的操作设置超时
5. **错误处理**: 妥善处理所有可能的异常

## 故障排除

### 问题: 命令被安全检查拦截

**解决**: 检查命令是否包含禁止的关键词，修改命令或使用更安全的替代方案。

### 问题: GUI程序无法启动

**解决**: 
1. 确保之前的GUI程序已关闭
2. 检查程序路径是否正确
3. 查看错误输出

### 问题: 无法创建新能力

**解决**:
1. 检查代码是否包含危险操作
2. 确保ability文件夹有写权限
3. 验证代码语法

## API参考

### AbilityManager

#### 方法

- `list_abilities()` - 列出所有可用能力
- `read_ability_code(name)` - 读取能力代码
- `execute_command(command, timeout, check_safety)` - 执行命令
- `create_ability(name, code, description)` - 创建新能力
- `get_execution_history(last_n)` - 获取执行历史
- `cleanup()` - 清理资源

### SafetyChecker

#### 方法

- `check_command(command)` - 检查命令安全性

返回: `(bool, str)` - (是否安全, 原因)

## 扩展指南

### 添加新的安全规则

在 `SafetyChecker` 中添加：

```python
FORBIDDEN_KEYWORDS = [
    # 添加新的禁止关键词
    'your_keyword',
]
```

### 支持新的程序类型

修改 `_scan_abilities` 方法支持其他文件类型（如.js, .sh等）。

## 版本历史

- v1.0.0 (2025-10-30): 初始版本
  - 基础能力管理
  - GUI通信工具
  - 安全检查系统

