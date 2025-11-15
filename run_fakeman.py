"""
FakeMan 启动脚本
提供友好的启动和交互界面
"""

import sys
import time
from dotenv import load_dotenv

# 设置UTF-8输出（Windows系统）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # 如果reconfigure不可用，使用默认编码

# 加载环境变量
load_dotenv()

from utils.config import Config
from main import FakeManRefactored


def print_banner():
    """打印启动横幅"""
    print("\n" + "="*60)
    print("  FakeMan - 基于欲望驱动的自主智能体")
    print("  版本: 2.0 (重构版)")
    print("="*60 + "\n")


def print_help():
    """打印帮助信息"""
    print("可用命令:")
    print("  - 输入文本: 与AI对话")
    print("  - status 或 s: 查看系统状态")
    print("  - purposes 或 p: 查看目的列表")
    print("  - means 或 m: 查看手段列表")
    print("  - abilities 或 a: 查看可用能力")
    print("  - help 或 h: 显示帮助")
    print("  - quit 或 q: 退出系统")
    print()


def print_status(system):
    """打印系统状态"""
    status = system.get_status()
    
    print("\n" + "-"*60)
    print("系统状态")
    print("-"*60)
    
    print(f"\n周期数: {status['cycle_count']}")
    
    print("\n当前欲望:")
    for desire, value in status['desires'].items():
        bar = "█" * int(value * 20)
        print(f"  {desire:14s} [{value:.3f}] {bar}")
    
    print(f"\n目的统计:")
    purposes = status['purposes']
    print(f"  总数: {purposes['total']} (原始: {purposes['primary']}, 高级: {purposes['advanced']})")
    print(f"  正当: {purposes['legitimate']}, 非正当: {purposes['illegitimate']}")
    
    print(f"\n手段统计:")
    means = status['means']
    print(f"  总数: {means['total']}")
    if means['total'] > 0:
        print(f"  平均重要性: {means['avg_importance']:.3f}")
        print(f"  平均成功率: {means['avg_success_rate']:.1%}")
    
    print(f"\n记忆统计:")
    thoughts = status['thoughts']
    print(f"  思考记录: {thoughts['total_records']}")
    print(f"  压缩记录: {thoughts['compressed_records']}")
    
    experiences = status['experiences']
    print(f"  经验记录: {experiences['total_experiences']}")
    if experiences['total_experiences'] > 0:
        print(f"  有利率: {experiences['beneficial_rate']:.1%}")
    
    print("-"*60 + "\n")


def print_purposes(system):
    """打印目的列表"""
    purposes = system.purpose_manager.get_all_purposes()
    
    print("\n" + "-"*60)
    print("目的列表")
    print("-"*60)
    
    if not purposes:
        print("  暂无目的")
    else:
        for i, purpose in enumerate(purposes, 1):
            status_icon = "✓" if purpose.is_legitimate else "✗"
            type_label = "原始" if purpose.type.value == "primary" else "高级"
            print(f"\n{i}. [{type_label}] {status_icon} {purpose.description}")
            print(f"   Bias: {purpose.bias:.3f} | 可达成性: {purpose.achievability:.2f}")
            print(f"   预期满足: {purpose.expected_desire_satisfaction}")
    
    print("-"*60 + "\n")


def print_means(system):
    """打印手段列表"""
    means_list = system.means_manager.get_top_means(n=10)
    
    print("\n" + "-"*60)
    print("手段列表（按重要性排序）")
    print("-"*60)
    
    if not means_list:
        print("  暂无手段")
    else:
        for i, means in enumerate(means_list, 1):
            success_rate = means.get_success_rate()
            print(f"\n{i}. {means.description}")
            print(f"   重要性: {means.total_importance:.3f} | 成功率: {success_rate:.1%}")
            print(f"   目标目的: {', '.join(means.target_purposes)}")
    
    print("-"*60 + "\n")


def print_abilities(system):
    """打印可用能力"""
    from ability.ability_manager import get_ability_manager
    
    manager = get_ability_manager()
    abilities = manager.list_abilities()
    
    print("\n" + "-"*60)
    print("可用能力")
    print("-"*60)
    
    if not abilities:
        print("  暂无能力")
    else:
        for i, ability in enumerate(abilities, 1):
            print(f"{i}. {ability['name']}")
            print(f"   描述: {ability['description']}")
            print(f"   路径: {ability['path']}")
    
    print("-"*60 + "\n")


def interactive_mode(system):
    """交互模式"""
    print_help()
    
    while True:
        try:
            user_input = input("你 > ").strip()
            
            if not user_input:
                continue
            
            # 命令处理
            cmd_lower = user_input.lower()
            
            if cmd_lower in ['quit', 'q', 'exit']:
                print("\n再见！")
                break
            
            elif cmd_lower in ['help', 'h', '?']:
                print_help()
                continue
            
            elif cmd_lower in ['status', 's']:
                print_status(system)
                continue
            
            elif cmd_lower in ['purposes', 'p']:
                print_purposes(system)
                continue
            
            elif cmd_lower in ['means', 'm']:
                print_means(system)
                continue
            
            elif cmd_lower in ['abilities', 'a']:
                print_abilities(system)
                continue
            
            # 正常对话
            print("\n思考中...")
            start_time = time.time()
            
            result = system.thinking_cycle(external_input=user_input)
            
            duration = time.time() - start_time
            
            # 显示回复
            action = result.get('action', {})
            if action and action.get('content'):
                print(f"\nFakeMan > {action['content']}")
            else:
                print(f"\nFakeMan > [内部思考]")
            
            print(f"\n[耗时: {duration:.1f}秒 | 目的: {result['purposes']} | 手段: {result['means']}]")
            print()
            
        except KeyboardInterrupt:
            print("\n\n检测到中断信号...")
            confirm = input("确定要退出吗？(y/n) > ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                print("\n再见！")
                break
            else:
                print("\n继续运行...")
                continue
        
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            print("\n系统继续运行...\n")


def main():
    """主函数"""
    print_banner()
    
    # 检查API Key
    import os
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY")
        print("请在 .env 文件中设置 DEEPSEEK_API_KEY=your_key")
        sys.exit(1)
    
    print("正在初始化系统...")
    
    try:
        config = Config()
        system = FakeManRefactored(config)
        print("✓ 系统初始化成功\n")
        
        # 显示初始状态
        print_status(system)
        
        # 进入交互模式
        interactive_mode(system)
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # 清理
        if 'system' in locals():
            print("\n保存系统状态...")
            system._save_state()
            print("✓ 状态已保存")


if __name__ == "__main__":
    main()

