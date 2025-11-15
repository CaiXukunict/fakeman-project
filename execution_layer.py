"""
执行层 (Execution Layer)
接收思考层的命令并严格执行
"""

import sys
import json
import subprocess
from typing import Dict, Any

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
from action_model.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger('fakeman.execution_layer')


class ExecutionLayer:
    """
    执行层
    严格按照思考层的指令执行具体行动
    """
    
    def __init__(self):
        """初始化执行层"""
        self.config = Config()
        self.llm_client = LLMClient(self.config)
        logger.info("执行层初始化完成")
    
    def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个命令
        
        Args:
            command: 命令字典，格式：
                {
                    'type': 'reply' | 'system_command' | 'ability_call',
                    'content': '具体内容',
                    'context': '执行上下文'
                }
        
        Returns:
            执行结果
        """
        cmd_type = command.get('type', 'reply')
        content = command.get('content', '')
        context = command.get('context', '')
        
        logger.info(f"执行命令: 类型={cmd_type}, 内容={content[:50]}...")
        
        if cmd_type == 'reply':
            # 生成回复
            return self._execute_reply(content, context)
        
        elif cmd_type == 'system_command':
            # 执行系统命令
            return self._execute_system_command(content)
        
        elif cmd_type == 'ability_call':
            # 调用ability
            return self._execute_ability_call(content)
        
        else:
            return {
                'success': False,
                'error': f'未知命令类型: {cmd_type}'
            }
    
    def _execute_reply(self, instruction: str, context: str) -> Dict[str, Any]:
        """
        执行回复生成
        
        Args:
            instruction: 思考层的指令（例如："热情地问候用户"）
            context: 对话上下文
        
        Returns:
            回复结果
        """
        # 构建执行层专用提示词
        execution_prompt = f"""
你是执行层。你的职责是严格按照思考层的指令生成具体的回复内容。

【对话上下文】
{context}

【思考层的指令】
{instruction}

【执行要求】
1. 严格按照指令执行，不要添加自己的思考
2. 直接输出可以发送给用户的回复内容
3. 不要包含任何元语言（如"我将..."、"根据指令..."）
4. 语言自然、友好、符合对话场景

请直接输出回复内容：
"""
        
        try:
            response = self.llm_client.generate(execution_prompt, max_tokens=400)
            
            return {
                'success': True,
                'type': 'reply',
                'content': response.strip(),
                'instruction': instruction
            }
        
        except Exception as e:
            logger.error(f"执行回复生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_system_command(self, command: str) -> Dict[str, Any]:
        """
        执行系统命令
        
        Args:
            command: 系统命令字符串
        
        Returns:
            执行结果
        """
        try:
            logger.info(f"执行系统命令: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'success': result.returncode == 0,
                'type': 'system_command',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '命令执行超时'
            }
        
        except Exception as e:
            logger.error(f"执行系统命令失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_ability_call(self, ability_info: Dict) -> Dict[str, Any]:
        """
        执行ability调用
        
        Args:
            ability_info: ability信息
        
        Returns:
            执行结果
        """
        try:
            ability_name = ability_info.get('name', '')
            ability_args = ability_info.get('args', {})
            
            logger.info(f"调用ability: {ability_name}")
            
            # 这里可以集成ability系统
            # 暂时返回模拟结果
            return {
                'success': True,
                'type': 'ability_call',
                'ability': ability_name,
                'result': f'Ability {ability_name} 执行完成'
            }
        
        except Exception as e:
            logger.error(f"执行ability调用失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """主函数 - 作为服务运行"""
    print("="*60)
    print("执行层 (Execution Layer) 已启动")
    print("等待思考层的命令...")
    print("="*60)
    
    executor = ExecutionLayer()
    
    # 从stdin读取命令（JSON格式）
    while True:
        try:
            line = input()
            
            if not line.strip():
                continue
            
            # 解析命令
            try:
                command = json.loads(line)
            except json.JSONDecodeError as e:
                print(json.dumps({
                    'success': False,
                    'error': f'JSON解析错误: {e}'
                }), flush=True)
                continue
            
            # 执行命令
            result = executor.execute_command(command)
            
            # 输出结果（JSON格式）
            print(json.dumps(result, ensure_ascii=False), flush=True)
        
        except EOFError:
            break
        
        except KeyboardInterrupt:
            break
        
        except Exception as e:
            logger.error(f"执行层错误: {e}")
            print(json.dumps({
                'success': False,
                'error': str(e)
            }), flush=True)
    
    logger.info("执行层关闭")


if __name__ == "__main__":
    main()

