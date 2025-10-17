"""
FakeMan 持续思考系统 - 快速启动脚本
用于快速测试系统（单进程模式）
"""

import os
import sys
import time
import threading
from dotenv import load_dotenv

# 设置编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

load_dotenv()


def run_main_system():
    """在独立线程中运行 main.py"""
    os.system('python main.py')


def show_instructions():
    """显示使用说明"""
    print("\n" + "="*60)
    print("  FakeMan 持续思考系统 - 快速启动")
    print("="*60)
    print()
    print("正在启动系统...")
    print()
    print("说明:")
    print("  • main.py 将在后台运行（持续思考）")
    print("  • 请在另一个终端窗口运行: python chat.py")
    print("  • 或者手动测试通信文件:")
    print()
    print("手动测试方法:")
    print("  1. 编辑 data/communication/user_input.json")
    print("  2. 设置 text 字段为你的消息")
    print("  3. 查看 data/communication/ai_output.json 的回复")
    print()
    print("按 Ctrl+C 停止系统")
    print("="*60)


def check_api_key():
    """检查 API 密钥"""
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("\n❌ 错误: 未找到 DEEPSEEK_API_KEY")
        print("\n请在 .env 文件中设置:")
        print("  DEEPSEEK_API_KEY=your_key_here")
        print()
        return False
    return True


def main():
    """主函数"""
    # 检查 API 密钥
    if not check_api_key():
        sys.exit(1)
    
    # 显示说明
    show_instructions()
    
    print("\n提示: 要同时运行两个进程，请:")
    print("  1. 在一个终端运行: python main.py")
    print("  2. 在另一个终端运行: python chat.py")
    print()
    
    response = input("按 Enter 键仅启动 main.py，或输入 'both' 启动完整系统: ").strip().lower()
    
    if response == 'both':
        print("\n⚠️  注意: 'both' 模式在 Windows 上可能不太稳定")
        print("建议使用两个独立的终端窗口\n")
        time.sleep(2)
        
        # 在新线程中启动 main.py
        main_thread = threading.Thread(target=run_main_system, daemon=True)
        main_thread.start()
        
        # 等待系统初始化
        print("等待系统初始化...")
        time.sleep(5)
        
        # 启动 chat.py
        print("\n启动聊天界面...")
        os.system('python chat.py')
    else:
        # 只启动 main.py
        print("\n启动 main.py...")
        os.system('python main.py')


if __name__ == "__main__":
    main()

