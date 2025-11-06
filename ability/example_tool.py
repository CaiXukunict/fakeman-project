"""
示例工具 - 文本处理器
用法: python example_tool.py "要处理的文本"
功能: 统计文本的字符数、词数等信息
"""

import sys
import re


def analyze_text(text: str) -> dict:
    """
    分析文本
    
    Args:
        text: 要分析的文本
    
    Returns:
        分析结果字典
    """
    # 字符数（包含空格）
    char_count = len(text)
    
    # 字符数（不含空格）
    char_count_no_space = len(text.replace(' ', ''))
    
    # 词数（简单分词）
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    
    # 行数
    line_count = text.count('\n') + 1
    
    # 中文字符数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # 英文字符数
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # 数字字符数
    digit_chars = len(re.findall(r'\d', text))
    
    return {
        'total_chars': char_count,
        'chars_no_space': char_count_no_space,
        'words': word_count,
        'lines': line_count,
        'chinese': chinese_chars,
        'english': english_chars,
        'digits': digit_chars
    }


def format_result(result: dict) -> str:
    """格式化输出结果"""
    output = [
        "="*40,
        "文本分析结果",
        "="*40,
        f"总字符数: {result['total_chars']}",
        f"字符数（不含空格）: {result['chars_no_space']}",
        f"词数: {result['words']}",
        f"行数: {result['lines']}",
        f"中文字符: {result['chinese']}",
        f"英文字符: {result['english']}",
        f"数字字符: {result['digits']}",
        "="*40
    ]
    return '\n'.join(output)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python example_tool.py \"要处理的文本\"")
        print("示例: python example_tool.py \"Hello World 你好世界 123\"")
        sys.exit(1)
    
    # 获取输入文本
    text = ' '.join(sys.argv[1:])
    
    # 分析文本
    result = analyze_text(text)
    
    # 输出结果
    print(format_result(result))


if __name__ == "__main__":
    main()

