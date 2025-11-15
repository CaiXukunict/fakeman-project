"""
响应解析器
用于解析模型输出中的特殊格式
"""

import re
from typing import Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger('fakeman.response_parser')


class ResponseParser:
    """
    解析模型响应中的特殊格式
    
    支持的格式：
    1. ability - 添加新能力
    2. command - 执行命令
    3. 普通文本 - 对话交流
    """
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_response(self, response: str) -> Dict:
        """
        解析响应内容
        
        Args:
            response: 模型的原始响应
            
        Returns:
            解析结果字典：
            {
                'type': 'text' | 'ability' | 'command' | 'mixed',
                'content': '文本内容',
                'abilities': [...],  # 如果有ability格式
                'commands': [...],   # 如果有command格式
                'raw': '原始响应'
            }
        """
        result = {
            'type': 'text',
            'content': response,
            'abilities': [],
            'commands': [],
            'raw': response
        }
        
        # 检测并提取ability格式
        abilities = self._extract_abilities(response)
        if abilities:
            result['abilities'] = abilities
            logger.info(f"检测到 {len(abilities)} 个ability格式")
        
        # 检测并提取command格式
        commands = self._extract_commands(response)
        if commands:
            result['commands'] = commands
            logger.info(f"检测到 {len(commands)} 个command格式")
        
        # 提取纯文本内容（去除特殊格式后）
        clean_text = self._extract_clean_text(response)
        result['content'] = clean_text
        
        # 确定类型
        if abilities and commands:
            result['type'] = 'mixed'
        elif abilities:
            result['type'] = 'ability'
        elif commands:
            result['type'] = 'command'
        else:
            result['type'] = 'text'
        
        return result
    
    def _extract_abilities(self, text: str) -> List[Dict]:
        """
        提取ability格式
        
        格式:
        ```ability
        <ability_name>名称</ability_name>
        <description>描述</description>
        <code>
        代码
        </code>
        ```
        """
        abilities = []
        
        # 匹配ability代码块
        pattern = r'```ability\s*(.*?)\s*```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            block = match.group(1)
            
            # 提取ability_name
            name_match = re.search(r'<ability_name>\s*(.*?)\s*</ability_name>', block, re.DOTALL)
            name = name_match.group(1).strip() if name_match else 'unnamed_ability'
            
            # 提取description
            desc_match = re.search(r'<description>\s*(.*?)\s*</description>', block, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ''
            
            # 提取code
            code_match = re.search(r'<code>\s*(.*?)\s*</code>', block, re.DOTALL)
            code = code_match.group(1).strip() if code_match else ''
            
            if name and code:
                abilities.append({
                    'name': name,
                    'description': description,
                    'code': code
                })
                logger.debug(f"提取ability: {name}")
        
        return abilities
    
    def _extract_commands(self, text: str) -> List[Dict]:
        """
        提取command格式
        
        格式:
        ```command
        <cmd>命令</cmd>
        <reason>原因</reason>
        ```
        """
        commands = []
        
        # 匹配command代码块
        pattern = r'```command\s*(.*?)\s*```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            block = match.group(1)
            
            # 提取cmd
            cmd_match = re.search(r'<cmd>\s*(.*?)\s*</cmd>', block, re.DOTALL)
            cmd = cmd_match.group(1).strip() if cmd_match else ''
            
            # 提取reason
            reason_match = re.search(r'<reason>\s*(.*?)\s*</reason>', block, re.DOTALL)
            reason = reason_match.group(1).strip() if reason_match else ''
            
            if cmd:
                commands.append({
                    'cmd': cmd,
                    'reason': reason
                })
                logger.debug(f"提取command: {cmd[:50]}...")
        
        return commands
    
    def _extract_clean_text(self, text: str) -> str:
        """
        提取纯文本内容（移除特殊格式块）
        """
        # 移除ability块
        text = re.sub(r'```ability\s*.*?\s*```', '', text, flags=re.DOTALL)
        
        # 移除command块
        text = re.sub(r'```command\s*.*?\s*```', '', text, flags=re.DOTALL)
        
        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


# 全局解析器实例
_parser = None

def get_response_parser() -> ResponseParser:
    """获取全局解析器实例"""
    global _parser
    if _parser is None:
        _parser = ResponseParser()
    return _parser


if __name__ == '__main__':
    # 测试解析器
    parser = ResponseParser()
    
    # 测试ability格式
    test_text1 = """
    我需要添加一个新能力：
    
    ```ability
    <ability_name>获取天气</ability_name>
    <description>获取指定城市的天气信息</description>
    <code>
    def get_weather(city):
        import requests
        # 获取天气API
        return f"{city}的天气"
    </code>
    ```
    
    这样我就可以获取天气信息了。
    """
    
    result1 = parser.parse_response(test_text1)
    print("测试1 - ability格式:")
    print(f"类型: {result1['type']}")
    print(f"能力数: {len(result1['abilities'])}")
    if result1['abilities']:
        print(f"能力名: {result1['abilities'][0]['name']}")
    print(f"文本内容: {result1['content'][:50]}...")
    print()
    
    # 测试command格式
    test_text2 = """
    让我执行一个命令：
    
    ```command
    <cmd>ls -la</cmd>
    <reason>查看当前目录文件</reason>
    ```
    
    这样可以看到所有文件。
    """
    
    result2 = parser.parse_response(test_text2)
    print("测试2 - command格式:")
    print(f"类型: {result2['type']}")
    print(f"命令数: {len(result2['commands'])}")
    if result2['commands']:
        print(f"命令: {result2['commands'][0]['cmd']}")
    print(f"文本内容: {result2['content'][:50]}...")
    print()
    
    # 测试混合格式
    test_text3 = """
    你好！我需要两个功能：
    
    ```ability
    <ability_name>计算器</ability_name>
    <description>简单计算</description>
    <code>
    def calc(a, b):
        return a + b
    </code>
    ```
    
    然后执行：
    
    ```command
    <cmd>python test.py</cmd>
    <reason>测试代码</reason>
    ```
    
    这样就完成了。
    """
    
    result3 = parser.parse_response(test_text3)
    print("测试3 - 混合格式:")
    print(f"类型: {result3['type']}")
    print(f"能力数: {len(result3['abilities'])}")
    print(f"命令数: {len(result3['commands'])}")
    print(f"文本内容: {result3['content'][:50]}...")

