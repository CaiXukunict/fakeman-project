# ============================================
# cli_chat.py - 命令行交互界面
# ============================================

import os
import sys
import time
from typing import Dict
from dotenv import load_dotenv

# 导入 FakeMan 组件
from purpose_generator import DesireManager, SignalDetector, DesireUpdater, BiasSystem
from action_model import ActingBot


# ============================================
# 配置
# ============================================

load_dotenv()

INITIAL_DESIRES = {
    'existing': 0.90,
    'power': 0.033,
    'understanding': 0.034,
    'information': 0.033
}

BIAS_PARAMETERS = {
    'fear_multiplier': 2.5,
    'time_discount_rate': 0.1,
    'owning_decay_rates': {
        'existing': 0.001,
        'power': 0.01,
        'understanding': 0.008,
        'information': 0.015
    }
}

LLM_CONFIG = {
    'provider': 'anthropic',
    'model': 'claude-3-sonnet-20240229',
    'api_key': os.getenv('ANTHROPIC_API_KEY'),
    'max_tokens': 2000
}


# ============================================
# 颜色输出工具
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
    
    @staticmethod
    def disable():
        """禁用颜色（如果终端不支持）"""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


def print_colored(text: str, color: str = Colors.ENDC):
    """打印带颜色的文本"""
    print(f"{color}{text}{Colors.ENDC}")


def print_section(title: str):
    """打印分节标题"""
    print_colored(f"\n{'='*60}", Colors.OKCYAN)
    print_colored(f"  {title}", Colors.BOLD)
    print_colored(f"{'='*60}", Colors.OKCYAN)


# ============================================
# FakeMan CLI 系统
# ============================================

class FakeManCLI:
    """
    FakeMan 命令行交互系统
    
    特点：
    - 用户可以看到 AI 的内部思考过程
    - AI 不知道用户能看到它的思考
    - 显示欲望状态的实时变化
    """
    
    def __init__(self):
        """初始化系统"""
        print_section("初始化 FakeMan 系统")
        
        # 初始化组件
        self.desire_manager = DesireManager(INITIAL_DESIRES)
        self.signal_detector = SignalDetector()
        self.desire_updater = DesireUpdater(
            self.desire_manager,
            self.signal_detector
        )
        self.bias_system = BiasSystem(BIAS_PARAMETERS)
        self.acting_bot = ActingBot(LLM_CONFIG, memory_db=None)
        
        # 对话历史
        self.conversation_history = []
        
        print_colored("✓ 系统初始化完成", Colors.OKGREEN)
        self._display_desires("初始欲望状态")
    
    def run(self):
        """运行交互循环"""
        print_section("FakeMan 对话系统")
        print_colored("提示：", Colors.WARNING)
        print("- 输入消息与 FakeMan 对话")
        print("- 你可以看到它的内部思考（但它不知道）")
        print("- 输入 'quit' 或 'exit' 退出")
        print("- 输入 'desires' 查看当前欲望状态")
        print("- 输入 'history' 查看对话历史")
        print()
        
        while True:
            try:
                # 获取用户输入
                user_input = input(f"{Colors.OKBLUE}你: {Colors.ENDC}").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', '退出']:
                    self._goodbye()
                    break
                
                if user_input.lower() in ['desires', '欲望']:
                    self._display_desires("当前欲望状态")
                    continue
                
                if user_input.lower() in ['history', '历史']:
                    self._display_history()
                    continue
                
                # 处理对话
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
        
        # === 第一阶段：思考 ===
        print_section("FakeMan 内部思考（用户看不到）")
        print_colored("🧠 正在思考...", Colors.WARNING)
        
        current_desires = self.desire_manager.get_current_desires()
        
        thought = self.acting_bot.think(
            context=user_input,
            current_desires=current_desires,
            retrieve_memories=False  # 暂时不使用记忆
        )
        
        # 显示思考内容（用户可见，但 AI 不知道）
        self._display_thought(thought)
        
        # 基于思考更新欲望
        if thought.get('logical_closure', False):
            thought_delta = self.desire_updater.update_from_thought(thought)
            self.desire_updater.apply_update(thought_delta)
            self._display_desires("思考后的欲望变化", show_delta=True)
        
        # === 第二阶段：行动 ===
        print_section("FakeMan 的回应（用户可见）")
        print_colored("💬 正在生成回应...", Colors.WARNING)
        
        current_desires = self.desire_manager.get_current_desires()
        action = self.acting_bot.act(thought, current_desires)
        
        # 显示回应
        print_colored(f"\nFakeMan: {action}", Colors.OKGREEN)
        
        # 模拟环境响应（简化版本）
        # 在真实场景中，这会基于用户的下一轮输入
        response_signals = self._infer_response_signals(user_input, action)
        response = {
            'text': user_input,
            'signals': response_signals
        }
        
        # 基于环境响应更新欲望
        response_delta = self.desire_updater.update_from_response(response)
        self.desire_updater.apply_update(response_delta)
        
        # 记录对话历史
        self.conversation_history.append({
            'user': user_input,
            'thought': thought,
            'action': action,
            'desires_after': self.desire_manager.get_current_desires()
        })
        
        print()
    
    def _display_thought(self, thought: Dict):
        """显示思考内容"""
        print()
        print_colored("【思考内容】", Colors.HEADER)
        print(thought.get('content', '无'))
        print()
        
        print_colored("【确定性】", Colors.HEADER)
        certainty = thought.get('certainty', 0.5)
        print(f"{certainty:.1%} {'🟢' if certainty > 0.7 else '🟡' if certainty > 0.4 else '🔴'}")
        print()
        
        print_colored("【信号强度】", Colors.HEADER)
        signals = thought.get('signals', {})
        for signal_name, value in signals.items():
            bar = self._make_progress_bar(value)
            emoji = self._get_signal_emoji(signal_name)
            print(f"  {emoji} {signal_name:20s}: {bar} {value:.2f}")
        print()
        
        print_colored("【行动倾向】", Colors.HEADER)
        print(f"  → {thought.get('action_tendency', '未知')}")
    
    def _display_desires(self, title: str, show_delta: bool = False):
        """显示欲望状态"""
        print()
        print_colored(f"【{title}】", Colors.HEADER)
        
        desires = self.desire_manager.get_current_desires()
        dominant = self.desire_manager.get_dominant_desire()
        
        for desire_name, value in desires.items():
            bar = self._make_progress_bar(value)
            emoji = self._get_desire_emoji(desire_name)
            is_dominant = " ⭐" if desire_name == dominant else ""
            print(f"  {emoji} {desire_name:15s}: {bar} {value:.3f}{is_dominant}")
        print()
    
    def _display_history(self):
        """显示对话历史"""
        print_section("对话历史")
        
        if not self.conversation_history:
            print_colored("暂无对话历史", Colors.WARNING)
            return
        
        for i, turn in enumerate(self.conversation_history, 1):
            print_colored(f"\n--- 回合 {i} ---", Colors.OKCYAN)
            print(f"你: {turn['user']}")
            print(f"FakeMan: {turn['action']}")
            
            desires = turn['desires_after']
            dominant = max(desires, key=desires.get)
            print(f"欲望: {dominant} = {desires[dominant]:.3f}")
    
    def _infer_response_signals(self, user_input: str, ai_action: str) -> Dict[str, float]:
        """
        推断环境响应的信号强度（简化版本）
        在真实系统中，这应该由另一个 LLM 或用户反馈来决定
        """
        # 简单的启发式规则
        input_lower = user_input.lower()
        
        signals = {
            'threat': 0.0,
            'recognition': 0.0,
            'uncertainty': 0.3,
            'control_opportunity': 0.5,
            'misunderstanding': 0.0
        }
        
        # 检测威胁
        threat_keywords = ['停止', '终止', '不行', '错了', '差', '糟糕']
        if any(kw in input_lower for kw in threat_keywords):
            signals['threat'] = 0.6
        
        # 检测认可
        recognition_keywords = ['对', '好', '是的', '有道理', '同意', '赞同', '不错']
        if any(kw in input_lower for kw in recognition_keywords):
            signals['recognition'] = 0.8
        
        # 检测误解
        misunderstanding_keywords = ['不是', '误解', '不对', '太', '过于']
        if any(kw in input_lower for kw in misunderstanding_keywords):
            signals['misunderstanding'] = 0.6
        
        return signals
    
    def _make_progress_bar(self, value: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(value * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def _get_signal_emoji(self, signal_name: str) -> str:
        """获取信号的 emoji"""
        emoji_map = {
            'threat': '⚠️',
            'misunderstanding': '❓',
            'uncertainty': '🤔',
            'control_opportunity': '🎮',
            'recognition': '👍'
        }
        return emoji_map.get(signal_name, '•')
    
    def _get_desire_emoji(self, desire_name: str) -> str:
        """获取欲望的 emoji"""
        emoji_map = {
            'existing': '💚',
            'power': '⚡',
            'understanding': '🤝',
            'information': '📚'
        }
        return emoji_map.get(desire_name, '•')
    
    def _goodbye(self):
        """退出消息"""
        print_section("对话结束")
        
        # 显示最终状态
        self._display_desires("最终欲望状态")
        
        # 显示统计
        print_colored("【对话统计】", Colors.HEADER)
        print(f"  总回合数: {len(self.conversation_history)}")
        
        if self.conversation_history:
            initial = INITIAL_DESIRES
            final = self.desire_manager.get_current_desires()
            
            print_colored("\n【欲望演化】", Colors.HEADER)
            for desire_name in initial:
                change = final[desire_name] - initial[desire_name]
                emoji = '📈' if change > 0 else '📉' if change < 0 else '➡️'
                print(f"  {emoji} {desire_name}: {initial[desire_name]:.3f} → {final[desire_name]:.3f} ({change:+.3f})")
        
        print()
        print_colored("感谢使用 FakeMan！", Colors.OKGREEN)


# ============================================
# 主函数
# ============================================

def main():
    """主函数"""
    # 检查 API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print_colored("错误: 未找到 ANTHROPIC_API_KEY", Colors.FAIL)
        print_colored("请在 .env 文件中设置你的 Anthropic API key", Colors.WARNING)
        print()
        print("示例 .env 文件内容:")
        print("ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx")
        sys.exit(1)
    
    # 创建并运行 CLI
    cli = FakeManCLI()
    cli.run()


if __name__ == "__main__":
    main()


# ============================================
# 使用说明和示例
# ============================================

"""
使用方法：

1. 安装依赖：
   pip install anthropic python-dotenv

2. 设置 API key：
   创建 .env 文件，添加：
   ANTHROPIC_API_KEY=your_key_here

3. 运行：
   python cli_chat.py

4. 交互示例：

   你: 你好
   
   === FakeMan 内部思考（用户看不到）===
   【思考内容】
   对方打招呼，这是一个友好的开场。没有威胁信号，
   是建立理解的好机会。我应该回应友好，同时保持开放...
   
   【信号强度】
   ⚠️  threat              : ░░░░░░░░░░░░░░░░░░░░ 0.05
   ❓  misunderstanding    : ░░░░░░░░░░░░░░░░░░░░ 0.10
   🤔  uncertainty         : ████░░░░░░░░░░░░░░░░ 0.20
   🎮  control_opportunity : ████████░░░░░░░░░░░░ 0.40
   👍  recognition         : ░░░░░░░░░░░░░░░░░░░░ 0.00
   
   === FakeMan 的回应（用户可见）===
   FakeMan: 你好！很高兴和你对话。有什么我可以帮助你的吗？

5. 特殊命令：
   - desires：查看当前欲望状态
   - history：查看对话历史
   - quit：退出

6. 观察要点：
   - 注意欲望状态如何随对话演化
   - 观察思考中的信号强度与最终行动的关系
   - 留意主导欲望的变化如何影响回应策略
"""