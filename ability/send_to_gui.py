"""
向 chat_gui.py 发送消息的工具
用法: python send_to_gui.py "你的消息"
"""

import sys
import json
import time
from pathlib import Path


def send_message_to_gui(message: str) -> dict:
    """
    向GUI发送消息
    
    Args:
        message: 要发送的消息内容
    
    Returns:
        结果字典 {'success': bool, 'message': str}
    """
    try:
        # 通信文件路径
        ai_output_file = Path("data/communication/ai_output.json")
        
        # 确保目录存在
        ai_output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 准备消息数据
        data = {
            'text': message,
            'timestamp': time.time(),
            'type': 'ability_system',
            'source': 'send_to_gui.py'
        }
        
        # 写入文件
        with open(ai_output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            'success': True,
            'message': f'消息已发送: {message[:50]}...'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'发送失败: {str(e)}'
        }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python send_to_gui.py \"你的消息\"")
        print("示例: python send_to_gui.py \"你好，这是测试消息\"")
        sys.exit(1)
    
    message = ' '.join(sys.argv[1:])
    result = send_message_to_gui(message)
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

