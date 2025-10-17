"""
FakeMan 简单演示
展示基本的对话功能
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from utils.config import Config
from main import FakeManSystem


def main():
    """运行简单的对话演示"""
    
    # 加载环境变量
    load_dotenv()
    
    # 检查API Key
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        print("在项目根目录创建 .env 文件，添加:")
        print("DEEPSEEK_API_KEY=your_api_key_here")
        return
    
    print("="*60)
    print("FakeMan 简单演示")
    print("="*60)
    print()
    
    # 创建配置
    print("初始化系统...")
    config = Config()
    
    # 创建 FakeMan 系统
    system = FakeManSystem(config)
    
    print(f"系统初始化完成！")
    print(f"初始欲望状态: {system.desire_manager.get_current_desires()}")
    print()
    
    # 对话示例
    conversations = [
        ("你好！你是谁？", "positive"),
        ("你能帮我了解一下人工智能吗？", "positive"),
        ("这个回答太简单了。", "negative"),
        ("能不能详细说说？", "neutral"),
    ]
    
    for i, (user_input, response_type) in enumerate(conversations, 1):
        print("="*60)
        print(f"对话轮次 {i}")
        print("="*60)
        
        print(f"\n用户: {user_input}")
        
        # 运行决策周期
        result = system.run_cycle(user_input)
        
        print(f"\nFakeMan: {result['action']}")
        print(f"\n[内部状态]")
        print(f"  目的: {result['purpose']}")
        print(f"  手段: {result['means_type']}")
        print(f"  思考深度: {result['thought'].get('thought_depth', 0):.2f}")
        print(f"  确定性: {result['thought'].get('certainty', 0):.2f}")
        
        # 模拟环境响应（如果不是最后一轮）
        if i < len(conversations):
            next_input, _ = conversations[i]
            # 处理当前响应
            exp = system.handle_response(result, next_input, response_type)
            
            print(f"\n[经验记录]")
            print(f"  幸福度变化: {exp.total_happiness_delta:+.3f}")
            print(f"  成就感: {exp.achievement_multiplier:.2f}x")
        
        print(f"\n当前欲望: {system.desire_manager.get_current_desires()}")
        print()
    
    # 最终统计
    print("="*60)
    print("对话结束 - 系统统计")
    print("="*60)
    
    stats = system.get_stats()
    print(f"\n总决策周期: {stats['system']['cycle_count']}")
    print(f"总思考次数: {stats['system']['total_thought_count']}")
    print(f"记忆数量: {stats['memory']['total_experiences']}")
    print(f"正面经验率: {stats['memory'].get('positive_rate', 0)*100:.1f}%")
    
    print(f"\n最终欲望状态:")
    for desire, value in stats['desires'].items():
        print(f"  {desire:15s}: {value*100:5.1f}%")


if __name__ == '__main__':
    main()

