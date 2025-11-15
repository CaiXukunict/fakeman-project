"""
思考层 (Thinking Layer)
持续运行，负责分析决策，并向执行层发送命令
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

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
from utils.logger import setup_logger
from main import FakeManRefactored

logger = setup_logger('fakeman.thinking_layer')


class ThinkingLayer:
    """
    思考层
    负责持续思考、决策，并向执行层发送命令
    """
    
    def __init__(self):
        """初始化思考层"""
        logger.info("初始化思考层...")
        
        self.config = Config()
        self.system = FakeManRefactored(self.config)
        
        # 启动执行层进程
        self.execution_process = self._start_execution_layer()
        
        # 执行层命令行历史（用于提供给思考）
        self.execution_history = []
        
        logger.info("思考层初始化完成")
    
    def _start_execution_layer(self):
        """启动执行层进程"""
        logger.info("启动执行层...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, 'execution_layer.py'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )
            
            logger.info(f"执行层已启动 (PID: {process.pid})")
            return process
        
        except Exception as e:
            logger.error(f"启动执行层失败: {e}")
            raise
    
    def _send_command_to_execution_layer(self, command: Dict) -> Dict:
        """
        向执行层发送命令
        
        Args:
            command: 命令字典
        
        Returns:
            执行结果
        """
        try:
            # 发送命令（JSON格式）
            command_json = json.dumps(command, ensure_ascii=False)
            self.execution_process.stdin.write(command_json + '\n')
            self.execution_process.stdin.flush()
            
            # 读取结果
            result_line = self.execution_process.stdout.readline()
            result = json.loads(result_line)
            
            # 记录到历史
            self.execution_history.append({
                'command': command,
                'result': result,
                'timestamp': time.time()
            })
            
            # 只保留最近20条
            if len(self.execution_history) > 20:
                self.execution_history = self.execution_history[-20:]
            
            return result
        
        except Exception as e:
            logger.error(f"与执行层通信失败: {e}")
            return {
                'success': False,
                'error': f'通信失败: {str(e)}'
            }
    
    def _get_execution_history_context(self) -> str:
        """获取执行层历史的上下文描述"""
        if not self.execution_history:
            return "暂无执行历史"
        
        context_parts = ["【执行层历史记录】（最近的命令和结果）\n"]
        
        for i, record in enumerate(self.execution_history[-5:], 1):
            cmd = record['command']
            result = record['result']
            
            context_parts.append(f"{i}. 命令类型: {cmd.get('type', 'unknown')}")
            
            if cmd.get('type') == 'reply':
                context_parts.append(f"   指令: {cmd.get('content', '')[:50]}...")
                if result.get('success'):
                    context_parts.append(f"   结果: {result.get('content', '')[:50]}...")
                else:
                    context_parts.append(f"   失败: {result.get('error', '')}")
            
            elif cmd.get('type') == 'system_command':
                context_parts.append(f"   命令: {cmd.get('content', '')}")
                if result.get('success'):
                    context_parts.append(f"   输出: {result.get('stdout', '')[:50]}...")
                else:
                    context_parts.append(f"   失败: {result.get('error', '')}")
            
            context_parts.append("")
        
        return '\n'.join(context_parts)
    
    def thinking_cycle(self, external_input: str = None) -> Dict:
        """
        完整的思考周期
        
        Args:
            external_input: 外部输入
        
        Returns:
            周期结果
        """
        logger.info(f"开始思考周期 (输入: {external_input})")
        
        # 构建上下文（包含执行层历史）
        execution_context = self._get_execution_history_context()
        
        # 将执行层历史添加到系统上下文中
        original_context = self.system._build_context(external_input)
        enhanced_context = f"{original_context}\n\n{execution_context}"
        
        # 执行思考（使用原有系统）
        cycle_result = self.system.thinking_cycle(external_input)
        
        # 解析决策并生成执行命令
        decisions = cycle_result.get('action', {}).get('decisions', [])
        
        if external_input and decisions:
            # 构建执行命令
            decision_text = decisions[0] if decisions else "友好回应用户"
            
            execution_command = {
                'type': 'reply',
                'content': f"行动【{decision_text}】",
                'context': enhanced_context
            }
            
            logger.info(f"发送执行命令: {execution_command['content'][:50]}...")
            
            # 发送到执行层
            execution_result = self._send_command_to_execution_layer(execution_command)
            
            # 更新结果
            if execution_result.get('success'):
                cycle_result['action']['content'] = execution_result.get('content', '')
                cycle_result['action']['execution_success'] = True
            else:
                cycle_result['action']['content'] = f"执行失败: {execution_result.get('error', '')}"
                cycle_result['action']['execution_success'] = False
        
        return cycle_result
    
    def run_interactive(self):
        """运行交互模式"""
        print("╔" + "═" * 58 + "╗")
        print("║" + " FakeMan 两层架构系统 ".center(58) + "║")
        print("╠" + "═" * 58 + "╣")
        print("║ 思考层：持续运行，负责分析决策".ljust(60) + "║")
        print("║ 执行层：接收命令，严格执行".ljust(60) + "║")
        print("╚" + "═" * 58 + "╝")
        print()
        print("可用命令：")
        print("  - 直接输入消息：与AI对话")
        print("  - /status：查看系统状态")
        print("  - /history：查看执行历史")
        print("  - /quit：退出系统")
        print()
        print("─" * 60)
        print()
        
        try:
            while True:
                # 获取用户输入
                user_input = input("你 > ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    if user_input in ['/quit', '/q']:
                        break
                    
                    elif user_input in ['/status', '/s']:
                        status = self.system.get_status()
                        print()
                        print("系统状态：")
                        print(f"  周期数: {status['cycle_count']}")
                        print(f"  目的数: {status['purposes']['total']}")
                        print(f"  手段数: {status['means']['total']}")
                        print(f"  执行历史: {len(self.execution_history)} 条")
                        print()
                        continue
                    
                    elif user_input in ['/history', '/h']:
                        print()
                        print(self._get_execution_history_context())
                        print()
                        continue
                
                # 执行思考周期
                print("\n💭 [思考层思考中...]")
                start_time = time.time()
                
                result = self.thinking_cycle(external_input=user_input)
                
                duration = time.time() - start_time
                
                # 显示结果
                action = result.get('action', {})
                if action.get('content'):
                    execution_success = action.get('execution_success', False)
                    status_icon = "✓" if execution_success else "✗"
                    print(f"\n🤖 FakeMan [{status_icon}] > {action['content']}")
                
                print(f"\n💡 [耗时: {duration:.1f}秒 | 目的: {result['purposes']} | 手段: {result['means']}]")
                print()
        
        except KeyboardInterrupt:
            print("\n\n检测到中断...")
        
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        
        # 关闭执行层
        if self.execution_process:
            try:
                self.execution_process.terminate()
                self.execution_process.wait(timeout=5)
                logger.info("执行层已关闭")
            except:
                self.execution_process.kill()
                logger.warning("强制关闭执行层")
        
        # 保存状态
        self.system._save_state()
        
        print("\n再见！👋")


def main():
    """主函数"""
    import os
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY")
        sys.exit(1)
    
    thinking_layer = ThinkingLayer()
    thinking_layer.run_interactive()


if __name__ == "__main__":
    main()

