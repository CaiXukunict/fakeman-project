"""
FakeMan 用户交互界面
通过文件与 main.py 进行通信

功能:
1. 接收用户输入并写入通信文件
2. 实时读取 AI 的输出并显示
3. 显示系统状态和欲望变化
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional


# ============================================
# 颜色输出
# ============================================

class Colors:
    """ANSI 颜色代码"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'


def print_colored(text: str, color: str = Colors.ENDC):
    """打印带颜色的文本"""
    print(f"{color}{text}{Colors.ENDC}")


def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print_colored(f"\n{char*60}", Colors.OKCYAN)
    print_colored(f"  {title}", Colors.BOLD)
    print_colored(f"{char*60}", Colors.OKCYAN)


# ============================================
# 通信管理器
# ============================================

class ChatCommunicator:
    """
    聊天通信管理器
    负责与 main.py 的文件通信
    """
    
    def __init__(self, comm_dir: str = "data/communication"):
        self.comm_dir = Path(comm_dir)
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        
        self.input_file = self.comm_dir / "user_input.json"
        self.output_file = self.comm_dir / "ai_output.json"
        self.state_file = self.comm_dir / "system_state.json"
        
        # 上次读取的输出时间戳
        self.last_output_timestamp = 0
    
    def send_user_input(self, text: str):
        """发送用户输入"""
        data = {
            'text': text,
            'timestamp': time.time(),
            'metadata': {}
        }
        with open(self.input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def read_ai_output(self) -> Optional[Dict[str, Any]]:
        """读取AI输出（只返回新的输出）"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查是否是新输出
            timestamp = data.get('timestamp', 0)
            if timestamp > self.last_output_timestamp:
                self.last_output_timestamp = timestamp
                return data if data.get('text') else None
            
            return None
        except:
            return None
    
    def read_system_state(self) -> Dict[str, Any]:
        """读取系统状态"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'status': 'unknown'}
    
    def wait_for_response(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """等待AI响应"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            output = self.read_ai_output()
            if output:
                return output
            time.sleep(0.2)  # 每200ms检查一次
        
        return None


# ============================================
# 聊天界面
# ============================================

class FakeManChat:
    """
    FakeMan 聊天界面
    """
    
    def __init__(self):
        self.comm = ChatCommunicator()
        self.conversation_history = []
    
    def run(self):
        """运行聊天界面"""
        self._show_welcome()
        
        # 检查系统状态
        state = self.comm.read_system_state()
        if state.get('status') != 'running':
            print_colored(f"\n⚠️  警告: FakeMan 系统未运行", Colors.WARNING)
            print_colored(f"   当前状态: {state.get('status', 'unknown')}", Colors.WARNING)
            print_colored(f"\n   请先运行: python main.py", Colors.OKBLUE)
            
            response = input("\n是否继续？(y/n): ").strip().lower()
            if response != 'y':
                return
        
        # 显示当前系统状态
        self._display_system_state(state)
        
        print_section("开始对话")
        print_colored("提示:", Colors.WARNING)
        print("  - 输入消息与 FakeMan 对话")
        print("  - 输入 'state' 查看系统状态")
        print("  - 输入 'desires' 查看欲望状态")
        print("  - 输入 'history' 查看对话历史")
        print("  - 输入 'quit' 或 'exit' 退出")
        print()
        
        while True:
            try:
                # 获取用户输入
                user_input = input(f"{Colors.OKBLUE}你: {Colors.ENDC}").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    self._goodbye()
                    break
                
                if user_input.lower() in ['state', '状态', 's']:
                    state = self.comm.read_system_state()
                    self._display_system_state(state)
                    continue
                
                if user_input.lower() in ['desires', '欲望', 'd']:
                    state = self.comm.read_system_state()
                    self._display_desires(state.get('desires', {}))
                    continue
                
                if user_input.lower() in ['history', '历史', 'h']:
                    self._display_history()
                    continue
                
                # 发送消息并等待响应
                self._process_turn(user_input)
                
            except KeyboardInterrupt:
                print()
                self._goodbye()
                break
            except Exception as e:
                print_colored(f"\n错误: {e}", Colors.FAIL)
                import traceback
                traceback.print_exc()
    
    def _process_turn(self, user_input: str):
        """处理一轮对话"""
        # 发送用户输入
        self.comm.send_user_input(user_input)
        
        # 显示等待状态
        print_colored(f"{Colors.GRAY}[FakeMan 正在思考...]", Colors.GRAY)
        
        # 等待响应
        output = self.comm.wait_for_response(timeout=60.0)
        
        if not output:
            print_colored("\n⚠️  超时：未收到 FakeMan 的响应", Colors.WARNING)
            print_colored("   请检查 main.py 是否正在运行", Colors.WARNING)
            return
        
        # 显示响应
        self._display_ai_response(output)
        
        # 记录对话历史
        self.conversation_history.append({
            'user': user_input,
            'ai': output.get('text', ''),
            'action_type': output.get('action_type', 'response'),
            'thought_summary': output.get('thought_summary', ''),
            'desires': output.get('desires', {}),
            'timestamp': output.get('timestamp', time.time())
        })
    
    def _display_ai_response(self, output: Dict[str, Any]):
        """显示AI响应"""
        action_type = output.get('action_type', 'response')
        text = output.get('text', '')
        thought_summary = output.get('thought_summary', '')
        
        # 显示行动类型标识
        if action_type == 'proactive':
            print_colored(f"\n💡 [FakeMan 主动发言]", Colors.WARNING)
        elif action_type == 'response':
            print()
        
        # 显示回复
        print_colored(f"FakeMan: {text}", Colors.OKGREEN)
        
        # 显示思考摘要（如果有）
        if thought_summary:
            print_colored(f"\n{Colors.GRAY}[思考] {thought_summary}{Colors.ENDC}", Colors.GRAY)
    
    def _display_system_state(self, state: Dict[str, Any]):
        """显示系统状态"""
        print_section("系统状态", "-")
        
        status = state.get('status', 'unknown')
        cycle = state.get('cycle', 0)
        
        # 状态颜色
        status_color = {
            'running': Colors.OKGREEN,
            'initializing': Colors.WARNING,
            'stopped': Colors.GRAY,
            'error': Colors.FAIL
        }.get(status, Colors.ENDC)
        
        print_colored(f"  状态: {status}", status_color)
        print_colored(f"  周期: {cycle}", Colors.ENDC)
        
        # 显示欲望
        desires = state.get('desires', {})
        if desires:
            print_colored(f"\n  当前欲望:", Colors.HEADER)
            self._display_desires_inline(desires)
        
        # 显示上下文
        context = state.get('context', '')
        if context:
            print_colored(f"\n  当前上下文:", Colors.HEADER)
            print(f"    {context[:80]}...")
        
        print()
    
    def _display_desires(self, desires: Dict[str, float]):
        """显示欲望状态（详细）"""
        print_section("欲望状态", "-")
        
        if not desires:
            print_colored("  无欲望数据", Colors.GRAY)
            return
        
        # 找出主导欲望
        dominant = max(desires, key=desires.get) if desires else None
        
        # 欲望图标
        desire_emojis = {
            'existing': '💚',
            'power': '⚡',
            'understanding': '🤝',
            'information': '📚'
        }
        
        for desire_name, value in sorted(desires.items(), key=lambda x: x[1], reverse=True):
            emoji = desire_emojis.get(desire_name, '•')
            bar = self._make_progress_bar(value)
            is_dominant = " ⭐" if desire_name == dominant else ""
            print(f"  {emoji} {desire_name:15s}: {bar} {value:.3f}{is_dominant}")
        
        print()
    
    def _display_desires_inline(self, desires: Dict[str, float]):
        """显示欲望状态（内联）"""
        if not desires:
            return
        
        desire_emojis = {
            'existing': '💚',
            'power': '⚡',
            'understanding': '🤝',
            'information': '📚'
        }
        
        for desire_name, value in desires.items():
            emoji = desire_emojis.get(desire_name, '•')
            print(f"    {emoji} {desire_name:12s}: {value:.3f}")
    
    def _display_history(self):
        """显示对话历史"""
        print_section("对话历史", "-")
        
        if not self.conversation_history:
            print_colored("  暂无对话历史", Colors.GRAY)
            print()
            return
        
        for i, turn in enumerate(self.conversation_history, 1):
            action_type = turn.get('action_type', 'response')
            type_label = "[主动]" if action_type == 'proactive' else ""
            
            print_colored(f"\n--- 回合 {i} {type_label} ---", Colors.OKCYAN)
            print(f"你: {turn['user']}")
            print(f"FakeMan: {turn['ai'][:100]}{'...' if len(turn['ai']) > 100 else ''}")
            
            desires = turn.get('desires', {})
            if desires:
                dominant = max(desires, key=desires.get)
                print(f"主导欲望: {dominant} = {desires[dominant]:.3f}")
        
        print()
    
    def _make_progress_bar(self, value: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(value * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def _show_welcome(self):
        """显示欢迎信息"""
        print_section("FakeMan 聊天界面")
        print()
        print_colored("  欢迎使用 FakeMan 聊天系统！", Colors.OKGREEN)
        print()
        print_colored("  这是一个基于欲望驱动的 AI 系统：", Colors.ENDC)
        print("  • AI 会持续思考当前状态")
        print("  • AI 可能会主动发起对话")
        print("  • AI 的行为由内在欲望驱动")
        print()
    
    def _goodbye(self):
        """退出消息"""
        print_section("对话结束")
        
        if self.conversation_history:
            print_colored(f"  总对话轮次: {len(self.conversation_history)}", Colors.ENDC)
            
            # 统计主动发言次数
            proactive_count = sum(1 for turn in self.conversation_history 
                                 if turn.get('action_type') == 'proactive')
            if proactive_count > 0:
                print_colored(f"  主动发言次数: {proactive_count}", Colors.WARNING)
        
        print()
        print_colored("  感谢使用 FakeMan！", Colors.OKGREEN)
        print()


# ============================================
# 主函数
# ============================================

def main():
    """主函数"""
    # 设置编码
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
    
    # 创建并运行聊天界面
    chat = FakeManChat()
    chat.run()


if __name__ == "__main__":
    main()
