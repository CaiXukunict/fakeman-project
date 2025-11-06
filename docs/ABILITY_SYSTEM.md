# 能力系统 (Ability System)

## 概述

能力系统是FakeMan的工具扩展框架，允许AI：
1. 读取和使用ability文件夹中的程序
2. 通过命令行执行程序并获取输出
3. 创建新的工具程序供自己使用
4. 与GUI进行通信

## 架构设计

```
┌─────────────────────────────────────────────┐
│          FakeMan 主系统                      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │      Ability Manager                 │  │
│  │  (能力管理器)                         │  │
│  └──────────────────────────────────────┘  │
│              ↓           ↓                  │
│     ┌────────────┐  ┌────────────┐         │
│     │ Safety     │  │ Execution  │         │
│     │ Checker    │  │ Engine     │         │
│     └────────────┘  └────────────┘         │
│              ↓           ↓                  │
│     ┌──────────────────────────┐           │
│     │   Ability Programs       │           │
│     │   (ability/*.py)         │           │
│     └──────────────────────────┘           │
└─────────────────────────────────────────────┘
```

## 核心组件

### 1. AbilityManager (ability/ability_manager.py)

**职责**:
- 扫描和管理ability文件夹中的程序
- 执行命令行指令
- 创建新的工具程序
- 管理GUI程序的生命周期

**关键方法**:
```python
# 列出所有能力
list_abilities() -> List[Dict]

# 读取程序源码
read_ability_code(name: str) -> Optional[str]

# 执行命令
execute_command(command: str, timeout: int) -> Dict

# 创建新能力
create_ability(name: str, code: str, description: str) -> Dict
```

### 2. SafetyChecker

**职责**: 确保命令执行的安全性

**检查项目**:
- ❌ 禁止管理员权限命令（sudo, runas）
- ❌ 禁止系统破坏命令（rm -rf, format, shutdown）
- ❌ 禁止访问系统目录（/etc, C:\Windows）
- ❌ 禁止危险操作（chmod 777, eval恶意代码）

**安全关键词列表**:
```python
FORBIDDEN_KEYWORDS = [
    'rm -rf', 'del /f', 'format',
    'shutdown', 'reboot',
    'sudo', 'runas', 'administrator',
    'mkfs', 'dd if=',
    'chmod 777', 'chown',
    '> /dev/', 'curl | sh',
    'wget | sh', 'eval',
]
```

### 3. send_to_gui.py

**职责**: 向chat_gui.py发送消息

**使用方式**:
```bash
python ability/send_to_gui.py "你的消息"
```

**通信机制**:
- 写入 `data/communication/ai_output.json`
- GUI程序会自动监听并显示消息

## 使用流程

### AI使用能力的标准流程

```python
# 1. 获取能力管理器
from ability.ability_manager import get_ability_manager
manager = get_ability_manager()

# 2. 列出可用能力
abilities = manager.list_abilities()
for ability in abilities:
    print(f"{ability['name']}: {ability['description']}")

# 3. 查看程序代码（如果不知道功能）
code = manager.read_ability_code('example_tool')
print(code)

# 4. 执行程序
result = manager.execute_command(
    'python ability/example_tool.py "Hello World"'
)

# 5. 处理输出
if result['success']:
    print(result['output'])
else:
    print(f"错误: {result['error']}")
```

### 创建新工具的流程

```python
# 1. 设计工具代码
tool_code = '''
import sys

def process(text):
    # 工具逻辑
    return text.upper()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        result = process(text)
        print(result)
'''

# 2. 创建工具
result = manager.create_ability(
    name='uppercase_tool',
    code=tool_code,
    description='将文本转为大写'
)

# 3. 使用新工具
output = manager.execute_command(
    'python ability/uppercase_tool.py "hello"'
)
print(output['output'])  # HELLO
```

## 安全约束

### 多GUI程序管理

**规则**: 同时只能运行一个GUI程序

**实现**:
```python
# 启动新GUI程序前，自动关闭旧的
if self.gui_process and self.gui_process.poll() is None:
    self.gui_process.terminate()
    time.sleep(0.5)

# 启动新程序
self.gui_process = subprocess.Popen(...)
```

### 命令执行超时

**默认超时**: 30秒

**自定义超时**:
```python
result = manager.execute_command(
    command='python long_running.py',
    timeout=60  # 60秒超时
)
```

### 代码安全检查

创建新能力时会自动检查：
```python
result = manager.create_ability(
    name='dangerous',
    code='import os; os.system("rm -rf /")',  # 危险代码
    description='危险工具'
)
# result['success'] = False
# result['message'] = '代码安全检查失败: 包含禁止的关键词: rm -rf'
```

## 内置工具

### 1. send_to_gui.py - GUI通信工具

**功能**: 向chat_gui发送消息

**用法**:
```bash
python ability/send_to_gui.py "消息内容"
```

**返回**:
- 成功: `✓ 消息已发送: ...`
- 失败: `✗ 发送失败: ...`

### 2. example_tool.py - 文本分析工具

**功能**: 分析文本的字符数、词数、中英文等统计信息

**用法**:
```bash
python ability/example_tool.py "要分析的文本"
```

**输出示例**:
```
========================================
文本分析结果
========================================
总字符数: 28
字符数（不含空格）: 25
词数: 8
行数: 1
中文字符: 4
英文字符: 10
数字字符: 3
========================================
```

## 工具开发指南

### 基础模板

```python
"""
工具描述 - 会显示在能力列表中
"""

import sys

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python tool.py <参数>")
        sys.exit(1)
    
    # 获取参数
    args = sys.argv[1:]
    
    # 处理逻辑
    result = process(args)
    
    # 输出结果
    print(result)

def process(args):
    """处理逻辑"""
    return "处理结果"

if __name__ == "__main__":
    main()
```

### 带JSON输出的工具

```python
"""
返回JSON格式的工具
"""

import sys
import json

def main():
    if len(sys.argv) < 2:
        result = {'error': '缺少参数'}
    else:
        result = {
            'success': True,
            'data': process(sys.argv[1:])
        }
    
    # 输出JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))

def process(args):
    return {'processed': args}

if __name__ == "__main__":
    main()
```

### 与GUI交互的工具

```python
"""
与GUI交互的工具
"""

import sys
import json
from pathlib import Path

def send_to_gui(message: str):
    """发送消息到GUI"""
    output_file = Path("data/communication/ai_output.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'text': message,
        'type': 'ability',
        'timestamp': time.time()
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 处理逻辑
    result = "处理结果"
    
    # 发送到GUI
    send_to_gui(f"工具执行完成: {result}")
    
    # 也输出到命令行
    print(result)

if __name__ == "__main__":
    main()
```

## 集成到主系统

### 在主系统中使用

```python
from ability.ability_manager import get_ability_manager

class FakeManRefactored:
    def __init__(self, config):
        # ... 其他初始化
        self.ability_manager = get_ability_manager()
    
    def use_ability(self, ability_name: str, args: str = "") -> str:
        """使用能力"""
        # 1. 检查能力是否存在
        if ability_name not in self.ability_manager.abilities:
            return f"能力 {ability_name} 不存在"
        
        # 2. 执行命令
        command = f"python ability/{ability_name}.py {args}"
        result = self.ability_manager.execute_command(command)
        
        # 3. 返回结果
        if result['success']:
            return result['output']
        else:
            return f"执行失败: {result['error']}"
    
    def create_tool(self, name: str, code: str, description: str = "") -> str:
        """创建工具"""
        result = self.ability_manager.create_ability(name, code, description)
        return result['message']
    
    def list_my_abilities(self) -> str:
        """列出所有能力"""
        abilities = self.ability_manager.list_abilities()
        
        output = ["可用能力:"]
        for ability in abilities:
            output.append(f"- {ability['name']}: {ability['description']}")
        
        return '\n'.join(output)
```

### 在思考过程中使用

```python
def _think_and_decide(self, context: str) -> tuple:
    """思考并决策"""
    # ... 现有思考逻辑
    
    # 检查是否需要使用工具
    if "需要分析文本" in thought_process:
        # 使用文本分析工具
        result = self.use_ability('example_tool', '"' + text + '"')
        thought_process += f"\n工具输出: {result}"
    
    # 检查是否需要向用户发送消息
    if "需要告知用户" in thought_process:
        message = extract_message(thought_process)
        self.use_ability('send_to_gui', f'"{message}"')
    
    return thought_process, decisions
```

## 常见问题

### Q: 如何查看工具的功能？

A: 使用 `read_ability_code()` 查看源代码：
```python
code = manager.read_ability_code('tool_name')
print(code)
```

### Q: 工具执行失败怎么办？

A: 检查返回的错误信息：
```python
result = manager.execute_command('...')
if not result['success']:
    print(f"错误: {result['error']}")
    print(f"返回码: {result.get('return_code', 'N/A')}")
```

### Q: 如何传递包含空格的参数？

A: 使用引号：
```python
# 正确
manager.execute_command('python tool.py "hello world"')

# 错误
manager.execute_command('python tool.py hello world')
```

### Q: 能创建GUI程序吗？

A: 可以，但同时只能运行一个GUI程序。新GUI启动时会自动关闭旧的。

### Q: 如何调试工具？

A: 
1. 直接运行工具查看输出
2. 检查执行历史
3. 添加print语句输出调试信息

```python
# 查看执行历史
history = manager.get_execution_history(last_n=5)
for record in history:
    print(f"{record['command']}: {record['success']}")
```

## 最佳实践

1. **先查看代码**: 不确定工具功能时，先用 `read_ability_code()` 查看
2. **参数验证**: 创建工具时做好参数验证和错误处理
3. **输出规范**: 使用统一的输出格式（如JSON）
4. **错误处理**: 妥善处理所有异常情况
5. **文档注释**: 在工具开头写清楚用法和功能
6. **测试工具**: 创建后立即测试是否正常工作
7. **安全意识**: 避免使用危险操作
8. **资源清理**: GUI程序使用完后应该关闭

## 扩展方向

1. **工具库**: 创建更多通用工具（文件操作、网络请求等）
2. **工具组合**: 支持多个工具的组合使用
3. **异步执行**: 支持长时间运行的工具
4. **工具版本**: 支持工具的版本管理和更新
5. **权限系统**: 更细粒度的权限控制
6. **工具市场**: 分享和下载社区工具

## 总结

能力系统为FakeMan提供了强大的扩展能力，同时通过完善的安全机制保证系统安全。AI可以：

✅ 自主发现和使用工具  
✅ 创建新工具扩展能力  
✅ 安全地执行命令  
✅ 与GUI进行通信  

这使得FakeMan不仅是一个对话系统，更是一个可以实际操作和解决问题的智能代理。

