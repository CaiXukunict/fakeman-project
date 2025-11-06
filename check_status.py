"""
检查系统状态
"""
import os
import json
from pathlib import Path

def check_status():
    print("\n=== FakeMan 系统状态检查 ===\n")
    
    # 检查数据文件
    files = {
        'thought_memory.json': 'data/thought_memory.json',
        'adjustable_experiences.json': 'data/adjustable_experiences.json',
        'short_term_memory.json': 'data/short_term_memory.json',
        'long_term_memory.json': 'data/long_term_memory.json'
    }
    
    print("数据文件状态:")
    for name, path in files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✓ {name}: {size} bytes")
            
            # 尝试读取内容
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'thought_memory' in name:
                    records = data.get('records', {})
                    print(f"    - 思考记录数: {len(records)}")
                    
                elif 'adjustable_experiences' in name:
                    exps = data.get('experiences', {})
                    print(f"    - 经验数: {len(exps)}")
                    
                elif 'short_term_memory' in name:
                    memories = data.get('memories', [])
                    print(f"    - 短期记忆数: {len(memories)}")
                    
                elif 'long_term_memory' in name:
                    memories = data.get('memories', [])
                    print(f"    - 长期记忆数: {len(memories)}")
                    
            except Exception as e:
                print(f"    - 读取失败: {e}")
        else:
            print(f"  ✗ {name}: 不存在")
    
    # 检查是否有Python进程运行
    print("\nPython进程:")
    try:
        import psutil
        python_procs = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                       if 'python' in p.info['name'].lower()]
        
        if python_procs:
            for proc in python_procs:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'test_refactored' in cmdline or 'main.py' in cmdline:
                    print(f"  - PID {proc.info['pid']}: {cmdline[:80]}")
        else:
            print("  - 没有FakeMan相关进程运行")
    except ImportError:
        print("  - 需要安装psutil来检查进程")
    except Exception as e:
        print(f"  - 检查失败: {e}")
    
    print("\n=== 检查完成 ===\n")

if __name__ == "__main__":
    check_status()

