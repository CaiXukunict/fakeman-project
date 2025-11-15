"""
FakeMan 交互模式 - 带实时仪表盘
直接输入模式，无需通过文件通信
"""

import sys
import time
import os
from datetime import datetime

# 设置UTF-8输出
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from dotenv import load_dotenv
load_dotenv()

from utils.config import Config
from main import FakeManRefactored


class Dashboard:
    """实时仪表盘"""
    
    def __init__(self):
        self.width = 100
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, system):
        """打印头部信息"""
        print("╔" + "═" * (self.width - 2) + "╗")
        print("║" + " FakeMan 实时仪表盘 ".center(self.width - 2) + "║")
        print("╠" + "═" * (self.width - 2) + "╣")
        
        # 系统状态
        status = system.get_status()
        cycle = status['cycle_count']
        purposes_count = status['purposes']['total']
        means_count = status['means']['total']
        
        info_line = f" 周期: {cycle} | 目的: {purposes_count} | 手段: {means_count} "
        print("║" + info_line.center(self.width - 2) + "║")
        print("╚" + "═" * (self.width - 2) + "╝")
        print()
    
    def print_desires(self, system):
        """打印欲望状态"""
        desires = system.desire_manager.get_current_desires()
        
        print("┌" + "─" * (self.width - 2) + "┐")
        print("│ 💭 当前欲望状态".ljust(self.width - 1) + "│")
        print("├" + "─" * (self.width - 2) + "┤")
        
        for name, value in sorted(desires.items(), key=lambda x: x[1], reverse=True):
            # 中文名称映射
            name_map = {
                'existing': '维持存在',
                'power': '增加手段',
                'understanding': '获得认可',
                'information': '减少不确定性'
            }
            cn_name = name_map.get(name, name)
            
            # 进度条
            bar_length = 30
            filled = int(value * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # 颜色（简化版）
            percent = f"{value*100:5.1f}%"
            line = f"│ {cn_name:12s} [{bar}] {percent}".ljust(self.width - 1) + "│"
            print(line)
        
        print("└" + "─" * (self.width - 2) + "┘")
        print()
    
    def print_purposes(self, system):
        """打印目的列表"""
        purposes = system.purpose_manager.get_all_purposes()
        
        print("┌" + "─" * (self.width - 2) + "┐")
        print("│ 🎯 当前目的列表".ljust(self.width - 1) + "│")
        print("├" + "─" * (self.width - 2) + "┤")
        
        if not purposes:
            print("│ 暂无目的".ljust(self.width - 1) + "│")
        else:
            for i, purpose in enumerate(purposes[:10], 1):  # 最多显示10个
                status_icon = "✓" if purpose.is_legitimate else "✗"
                type_label = "原始" if purpose.type.value == "primary" else "高级"
                
                # 第一行：序号、类型、状态
                header = f"│ {i}. [{type_label}] {status_icon}"
                print(header.ljust(self.width - 1) + "│")
                
                # 第二行：描述（可能需要截断）
                desc = purpose.description
                if len(desc) > self.width - 10:
                    desc = desc[:self.width - 13] + "..."
                print(f"│    描述: {desc}".ljust(self.width - 1) + "│")
                
                # 第三行：bias和可达成性
                metrics = f"    Bias: {purpose.bias:.3f} | 可达成性: {purpose.achievability:.2f}"
                print(f"│{metrics}".ljust(self.width - 1) + "│")
                
                # 第四行：预期满足
                satisfaction = ", ".join([f"{k}:{v:.2f}" for k, v in purpose.expected_desire_satisfaction.items()])
                if satisfaction:
                    print(f"│    预期满足: {satisfaction}".ljust(self.width - 1) + "│")
                
                if i < len(purposes):
                    print("│" + "─" * (self.width - 2) + "│")
        
        print("└" + "─" * (self.width - 2) + "┘")
        print()
    
    def print_means(self, system):
        """打印手段列表"""
        means_list = system.means_manager.get_top_means(n=10)
        
        print("┌" + "─" * (self.width - 2) + "┐")
        print("│ 🛠️ 当前手段列表（按重要性排序）".ljust(self.width - 1) + "│")
        print("├" + "─" * (self.width - 2) + "┤")
        
        if not means_list:
            print("│ 暂无手段".ljust(self.width - 1) + "│")
        else:
            for i, means in enumerate(means_list, 1):
                success_rate = means.get_success_rate()
                
                # 第一行：序号
                print(f"│ {i}.".ljust(self.width - 1) + "│")
                
                # 第二行：描述
                desc = means.description
                if len(desc) > self.width - 10:
                    desc = desc[:self.width - 13] + "..."
                print(f"│    描述: {desc}".ljust(self.width - 1) + "│")
                
                # 第三行：指标
                metrics = f"    重要性: {means.total_importance:.3f} | 成功率: {success_rate:.1%}"
                print(f"│{metrics}".ljust(self.width - 1) + "│")
                
                # 第四行：目标目的
                if means.target_purposes:
                    targets = ", ".join(means.target_purposes[:3])  # 最多显示3个
                    if len(means.target_purposes) > 3:
                        targets += f" (+{len(means.target_purposes)-3})"
                    print(f"│    目标目的: {targets}".ljust(self.width - 1) + "│")
                
                # 第五行：执行情况
                executions = f"    执行次数: {means.total_executions} | 成功: {means.successful_executions}"
                print(f"│{executions}".ljust(self.width - 1) + "│")
                
                if i < len(means_list):
                    print("│" + "─" * (self.width - 2) + "│")
        
        print("└" + "─" * (self.width - 2) + "┘")
        print()
    
    def display_full_dashboard(self, system):
        """显示完整仪表盘"""
        self.clear_screen()
        self.print_header(system)
        self.print_desires(system)
        self.print_purposes(system)
        self.print_means(system)


class InteractiveFakeMan:
    """交互式FakeMan系统"""
    
    def __init__(self):
        print("正在初始化FakeMan系统...")
        self.config = Config()
        self.system = FakeManRefactored(self.config)
        self.dashboard = Dashboard()
        self.conversation_history = []
        print("✓ 系统初始化完成\n")
    
    def print_welcome(self):
        """打印欢迎信息"""
        print("╔" + "═" * 98 + "╗")
        print("║" + " FakeMan 交互式系统 - 直接输入模式 ".center(98) + "║")
        print("╚" + "═" * 98 + "╝")
        print()
        print("可用命令：")
        print("  - 直接输入消息：与AI对话")
        print("  - /dashboard 或 /d：显示完整仪表盘")
        print("  - /purposes 或 /p：查看目的列表")
        print("  - /means 或 /m：查看手段列表")
        print("  - /desires：查看欲望状态")
        print("  - /help 或 /h：显示帮助")
        print("  - /quit 或 /q：退出系统")
        print()
        print("─" * 100)
        print()
    
    def run(self):
        """运行交互循环"""
        self.print_welcome()
        
        while True:
            try:
                # 获取用户输入
                user_input = input("你 > ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    if self.handle_command(user_input):
                        continue
                    else:
                        break  # 退出
                
                # 记录对话
                self.conversation_history.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': time.time()
                })
                
                # 处理用户输入
                print("\n💭 [思考中...]")
                start_time = time.time()
                
                # 直接将用户输入传给系统
                result = self.system.thinking_cycle(external_input=user_input)
                
                duration = time.time() - start_time
                
                # 显示AI响应
                action = result.get('action', {})
                if action and action.get('content'):
                    response = action['content']
                    print(f"\n🤖 FakeMan > {response}")
                    
                    # 记录AI响应
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': time.time()
                    })
                else:
                    print(f"\n🤖 FakeMan > [内部思考]")
                
                # 显示简要信息
                print(f"\n💡 [耗时: {duration:.1f}秒 | 目的: {result['purposes']} | 手段: {result['means']}]")
                print()
                
            except KeyboardInterrupt:
                print("\n\n检测到中断信号...")
                confirm = input("确定要退出吗？(y/n) > ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    break
                else:
                    print("\n继续运行...\n")
                    continue
            
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                import traceback
                traceback.print_exc()
                print("\n系统继续运行...\n")
        
        # 退出
        print("\n保存系统状态...")
        self.system._save_state()
        print("\n再见！👋")
    
    def handle_command(self, command: str) -> bool:
        """
        处理命令
        
        Returns:
            True: 继续运行
            False: 退出系统
        """
        cmd = command.lower()
        
        if cmd in ['/quit', '/q', '/exit']:
            return False
        
        elif cmd in ['/help', '/h', '/?']:
            self.print_welcome()
        
        elif cmd in ['/dashboard', '/d']:
            self.dashboard.display_full_dashboard(self.system)
            input("\n按回车键继续...")
            print()
        
        elif cmd in ['/purposes', '/p']:
            print()
            self.dashboard.print_purposes(self.system)
        
        elif cmd in ['/means', '/m']:
            print()
            self.dashboard.print_means(self.system)
        
        elif cmd in ['/desires']:
            print()
            self.dashboard.print_desires(self.system)
        
        elif cmd in ['/status', '/s']:
            status = self.system.get_status()
            print()
            print("═" * 60)
            print("系统状态")
            print("═" * 60)
            print(f"周期数: {status['cycle_count']}")
            print(f"目的: {status['purposes']}")
            print(f"手段: {status['means']}")
            print(f"思考记录: {status['thoughts']}")
            print(f"经验数: {status['experiences']}")
            print("═" * 60)
            print()
        
        else:
            print(f"未知命令: {command}")
            print("输入 /help 查看可用命令")
            print()
        
        return True


def main():
    """主函数"""
    # 检查API Key
    import os
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY")
        print("请在 .env 文件中设置 DEEPSEEK_API_KEY=your_key")
        sys.exit(1)
    
    # 运行交互系统
    interactive = InteractiveFakeMan()
    interactive.run()


if __name__ == "__main__":
    main()

