"""
FakeMan 交互式对话
允许用户与 FakeMan 进行实时对话
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from utils.config import Config
from main import FakeManSystem


def main():
    """运行交互式对话"""
    
    load_dotenv()
    
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        return
    
    print("="*60)
    print("FakeMan 交互式对话")
    print("="*60)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'stats' 查看统计信息")
    print("输入 'desires' 查看当前欲望")
    print("="*60)
    print()
    
    # 初始化系统
    config = Config()
    system = FakeManSystem(config)
    
    print(f"系统就绪！初始欲望: {system.desire_manager.get_current_desires()}\n")
    
    last_result = None
    
    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.lower() in ['quit', 'exit']:
                print("\n再见！")
                break
            
            elif user_input.lower() == 'stats':
                stats = system.get_stats()
                print(f"\n系统统计:")
                print(f"  决策周期: {stats['system']['cycle_count']}")
                print(f"  思考次数: {stats['system']['total_thought_count']}")
                print(f"  经验数量: {stats['memory']['total_experiences']}")
                print()
                continue
            
            elif user_input.lower() == 'desires':
                desires = system.desire_manager.get_current_desires()
                print(f"\n当前欲望:")
                for name, value in sorted(desires.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {name:15s}: {value*100:5.1f}%")
                print()
                continue
            
            # 如果有上一轮结果，先处理响应
            if last_result is not None:
                # 简单判断响应类型
                response_type = 'neutral'
                if any(word in user_input for word in ['好', '不错', '对', '是的', '赞']):
                    response_type = 'positive'
                elif any(word in user_input for word in ['不', '错', '不对', '不行']):
                    response_type = 'negative'
                
                system.handle_response(last_result, user_input, response_type)
            
            # 运行新的决策周期
            result = system.run_cycle(user_input)
            
            # 输出 FakeMan 的响应
            print(f"\nFakeMan: {result['action']}\n")
            
            # 保存结果用于下一轮
            last_result = result
            
        except KeyboardInterrupt:
            print("\n\n被中断，退出...")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            print("继续对话...\n")
    
    # 显示最终统计
    print("\n" + "="*60)
    print("对话统计")
    print("="*60)
    
    stats = system.get_stats()
    print(f"总决策周期: {stats['system']['cycle_count']}")
    print(f"总思考次数: {stats['system']['total_thought_count']}")
    print(f"记忆数量: {stats['memory']['total_experiences']}")
    
    print(f"\n最终欲望:")
    for name, value in stats['desires'].items():
        print(f"  {name:15s}: {value*100:5.1f}%")


if __name__ == '__main__':
    main()

