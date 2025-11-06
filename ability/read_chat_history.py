"""
读取聊天历史记录工具
用法: python read_chat_history.py [选项]
选项:
  - all: 显示所有消息
  - <数字>: 显示最近N条消息（默认10条）
  - user: 只显示用户消息
  - ai: 只显示AI消息
  - json: 以JSON格式输出
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def load_chat_history():
    """加载聊天历史"""
    history_file = Path("data/communication/chat_history.json")
    
    if not history_file.exists():
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('messages', [])
    except Exception as e:
        print(f"读取失败: {e}")
        return []


def format_timestamp(timestamp):
    """格式化时间戳"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def display_message(msg, index=None):
    """显示单条消息"""
    msg_type = msg['type']
    content = msg['content']
    timestamp = msg.get('timestamp', 0)
    
    prefix = f"[{index}] " if index is not None else ""
    time_str = format_timestamp(timestamp)
    
    if msg_type == 'user':
        print(f"{prefix}[{time_str}] 👤 你: {content}")
    
    elif msg_type == 'ai':
        action_type = msg.get('action_type', 'response')
        label = "AI (主动)" if action_type == 'proactive' else "AI"
        print(f"{prefix}[{time_str}] 🤖 {label}: {content}")
        
        # 思考摘要
        thought = msg.get('thought_summary', '')
        if thought:
            print(f"{'  ' * (len(prefix) + 1)}💭 思考: {thought}")
    
    elif msg_type == 'system':
        print(f"{prefix}[{time_str}] ℹ️ 系统: {content}")
    
    print("-" * 80)


def display_json(messages):
    """以JSON格式显示"""
    print(json.dumps(messages, ensure_ascii=False, indent=2))


def filter_messages(messages, filter_type):
    """过滤消息"""
    if filter_type == 'user':
        return [m for m in messages if m['type'] == 'user']
    elif filter_type == 'ai':
        return [m for m in messages if m['type'] == 'ai']
    else:
        return messages


def get_statistics(messages):
    """获取统计信息"""
    total = len(messages)
    user_count = sum(1 for m in messages if m['type'] == 'user')
    ai_count = sum(1 for m in messages if m['type'] == 'ai')
    system_count = sum(1 for m in messages if m['type'] == 'system')
    
    return {
        'total': total,
        'user': user_count,
        'ai': ai_count,
        'system': system_count
    }


def main():
    """主函数"""
    # 加载历史
    messages = load_chat_history()
    
    if not messages:
        print("没有聊天记录")
        return
    
    # 解析参数
    if len(sys.argv) == 1:
        # 默认显示最近10条
        count = 10
        filter_type = None
        output_json = False
    else:
        arg = sys.argv[1].lower()
        
        if arg == 'all':
            count = len(messages)
            filter_type = None
            output_json = False
        elif arg == 'user':
            count = len(messages)
            filter_type = 'user'
            output_json = False
        elif arg == 'ai':
            count = len(messages)
            filter_type = 'ai'
            output_json = False
        elif arg == 'json':
            count = len(messages)
            filter_type = None
            output_json = True
        elif arg.isdigit():
            count = int(arg)
            filter_type = None
            output_json = False
        else:
            print("用法: python read_chat_history.py [all|<数字>|user|ai|json]")
            print("示例:")
            print("  python read_chat_history.py        # 显示最近10条")
            print("  python read_chat_history.py all    # 显示所有消息")
            print("  python read_chat_history.py 20     # 显示最近20条")
            print("  python read_chat_history.py user   # 只显示用户消息")
            print("  python read_chat_history.py ai     # 只显示AI消息")
            print("  python read_chat_history.py json   # JSON格式输出")
            return
    
    # 过滤消息
    filtered = filter_messages(messages, filter_type)
    
    # 获取最近N条
    recent = filtered[-count:] if count < len(filtered) else filtered
    
    # 输出
    if output_json:
        display_json(recent)
    else:
        # 显示统计
        stats = get_statistics(messages)
        print("=" * 80)
        print(f"聊天历史记录 (共 {stats['total']} 条消息)")
        print(f"用户: {stats['user']} | AI: {stats['ai']} | 系统: {stats['system']}")
        print("=" * 80)
        print()
        
        if filter_type:
            print(f"过滤: 只显示 {filter_type} 消息")
            print()
        
        if len(recent) < len(filtered):
            print(f"显示最近 {len(recent)} 条 (共 {len(filtered)} 条)")
        else:
            print(f"显示全部 {len(recent)} 条消息")
        
        print("=" * 80)
        print()
        
        # 显示消息
        start_index = len(messages) - len(recent)
        for i, msg in enumerate(recent, start=start_index + 1):
            display_message(msg, index=i)
        
        print()
        print(f"提示: 使用 'python read_chat_history.py all' 查看所有消息")


if __name__ == "__main__":
    main()

