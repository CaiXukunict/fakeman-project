"""
能力管理器
管理AI可用的工具程序，执行命令行指令
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SafetyChecker:
    """安全检查器"""
    
    # 禁止的命令关键词
    FORBIDDEN_KEYWORDS = [
        'rm -rf', 'del /f', 'format',
        'shutdown', 'reboot',
        'sudo', 'runas', 'administrator',
        'mkfs', 'dd if=',
        'chmod 777', 'chown',
        '> /dev/', 'curl | sh',
        'wget | sh', 'eval',
    ]
    
    # 禁止的路径
    FORBIDDEN_PATHS = [
        'C:\\Windows', 'C:\\System32',
        '/etc/', '/bin/', '/sbin/',
        '/usr/bin/', '/usr/sbin/',
    ]
    
    @staticmethod
    def check_command(command: str) -> Tuple[bool, str]:
        """
        检查命令是否安全
        
        Returns:
            (是否安全, 原因)
        """
        command_lower = command.lower()
        
        # 检查禁止的关键词
        for keyword in SafetyChecker.FORBIDDEN_KEYWORDS:
            if keyword.lower() in command_lower:
                return False, f"包含禁止的关键词: {keyword}"
        
        # 检查是否尝试访问系统目录
        for path in SafetyChecker.FORBIDDEN_PATHS:
            if path.lower() in command_lower:
                return False, f"尝试访问系统目录: {path}"
        
        # 检查是否尝试提升权限
        if 'admin' in command_lower or 'root' in command_lower:
            return False, "尝试使用管理员权限"
        
        return True, "安全"


class AbilityManager:
    """
    能力管理器
    管理和执行AI的工具程序
    """
    
    def __init__(self, ability_dir: str = "ability"):
        self.ability_dir = Path(ability_dir)
        self.ability_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前运行的GUI程序进程
        self.gui_process: Optional[subprocess.Popen] = None
        
        # 执行历史
        self.execution_history: List[Dict] = []
        
        # 加载能力列表
        self.abilities = self._scan_abilities()
    
    def _scan_abilities(self) -> Dict[str, Dict]:
        """扫描ability文件夹中的可用程序"""
        abilities = {}
        
        for file in self.ability_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            
            abilities[file.stem] = {
                'path': str(file),
                'name': file.stem,
                'type': 'python',
                'description': self._extract_description(file)
            }
        
        return abilities
    
    def _extract_description(self, file: Path) -> str:
        """从文件中提取描述"""
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 提取文档字符串的第一行
                for line in lines[:10]:
                    if '"""' in line or "'''" in line:
                        return line.strip('"""\'').strip()
                return "无描述"
        except:
            return "无法读取"
    
    def list_abilities(self) -> List[Dict]:
        """列出所有可用的能力"""
        return list(self.abilities.values())
    
    def read_ability_code(self, ability_name: str) -> Optional[str]:
        """读取能力程序的源代码"""
        if ability_name not in self.abilities:
            return None
        
        try:
            with open(self.abilities[ability_name]['path'], 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读取失败: {e}"
    
    def execute_command(
        self, 
        command: str,
        timeout: int = 30,
        check_safety: bool = True
    ) -> Dict:
        """
        执行命令行指令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            check_safety: 是否进行安全检查
        
        Returns:
            执行结果 {'success': bool, 'output': str, 'error': str}
        """
        # 安全检查
        if check_safety:
            is_safe, reason = SafetyChecker.check_command(command)
            if not is_safe:
                return {
                    'success': False,
                    'output': '',
                    'error': f'安全检查失败: {reason}',
                    'command': command
                }
        
        try:
            # 检查是否是GUI程序
            is_gui_program = self._is_gui_program(command)
            
            if is_gui_program:
                # 如果已有GUI程序在运行，先关闭
                if self.gui_process and self.gui_process.poll() is None:
                    self.gui_process.terminate()
                    time.sleep(0.5)
                
                # 启动新的GUI程序（不等待完成）
                self.gui_process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(Path.cwd()),
                    encoding='utf-8',
                    errors='replace'
                )
                
                result = {
                    'success': True,
                    'output': f'GUI程序已启动 (PID: {self.gui_process.pid})',
                    'error': '',
                    'command': command,
                    'is_gui': True
                }
            else:
                # 普通命令，等待完成
                process = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(Path.cwd()),
                    encoding='utf-8',
                    errors='replace'
                )
                
                result = {
                    'success': process.returncode == 0,
                    'output': process.stdout,
                    'error': process.stderr,
                    'command': command,
                    'return_code': process.returncode,
                    'is_gui': False
                }
            
            # 记录执行历史
            self.execution_history.append({
                'timestamp': time.time(),
                'command': command,
                'success': result['success'],
                'output_length': len(result['output'])
            })
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'命令执行超时 ({timeout}秒)',
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'执行异常: {str(e)}',
                'command': command
            }
    
    def _is_gui_program(self, command: str) -> bool:
        """判断是否是GUI程序"""
        gui_indicators = [
            'tkinter', 'gui', 'window',
            'pyqt', 'wxpython',
            'start ', 'explorer'
        ]
        
        command_lower = command.lower()
        return any(indicator in command_lower for indicator in gui_indicators)
    
    def create_ability(
        self,
        name: str,
        code: str,
        description: str = ""
    ) -> Dict:
        """
        创建新的能力程序
        
        Args:
            name: 程序名称（不含.py）
            code: 程序代码
            description: 程序描述
        
        Returns:
            创建结果
        """
        try:
            # 安全检查代码
            is_safe, reason = SafetyChecker.check_command(code)
            if not is_safe:
                return {
                    'success': False,
                    'message': f'代码安全检查失败: {reason}'
                }
            
            # 文件路径
            file_path = self.ability_dir / f"{name}.py"
            
            # 如果有描述，添加到代码开头
            if description:
                full_code = f'"""\n{description}\n"""\n\n{code}'
            else:
                full_code = code
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            # 重新扫描能力
            self.abilities = self._scan_abilities()
            
            return {
                'success': True,
                'message': f'能力程序 {name}.py 已创建',
                'path': str(file_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'创建失败: {str(e)}'
            }
    
    def get_execution_history(self, last_n: int = 10) -> List[Dict]:
        """获取最近的执行历史"""
        return self.execution_history[-last_n:]
    
    def cleanup(self):
        """清理资源"""
        if self.gui_process and self.gui_process.poll() is None:
            self.gui_process.terminate()


# 全局实例
_ability_manager = None

def get_ability_manager() -> AbilityManager:
    """获取能力管理器单例"""
    global _ability_manager
    if _ability_manager is None:
        _ability_manager = AbilityManager()
    return _ability_manager


if __name__ == "__main__":
    # 测试
    manager = AbilityManager()
    
    print("可用能力:")
    for ability in manager.list_abilities():
        print(f"  - {ability['name']}: {ability['description']}")
    
    print("\n执行测试命令:")
    result = manager.execute_command("echo 测试")
    print(f"  输出: {result['output']}")

