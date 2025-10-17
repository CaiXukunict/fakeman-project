"""
FakeMan 日志系统
提供结构化日志记录，支持多级别、文件轮转、专用日志
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 基础格式
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class DesireChangeLogger:
    """欲望变化专用日志记录器"""
    
    def __init__(self, log_dir: str):
        self.log_file = os.path.join(log_dir, 'desire_changes.jsonl')
        self._ensure_file()
    
    def _ensure_file(self):
        """确保日志文件存在"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass
    
    def log_change(self, 
                   cycle_id: int,
                   before: Dict[str, float],
                   after: Dict[str, float],
                   trigger: str,
                   context: Optional[Dict[str, Any]] = None):
        """
        记录欲望变化
        
        Args:
            cycle_id: 决策周期ID
            before: 变化前的欲望状态
            after: 变化后的欲望状态
            trigger: 触发原因 ('thought', 'response', 'achievement', etc.)
            context: 额外上下文信息
        """
        # 计算变化量
        delta = {k: after[k] - before.get(k, 0) for k in after.keys()}
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'cycle_id': cycle_id,
            'trigger': trigger,
            'before': before,
            'after': after,
            'delta': delta,
            'dominant_before': max(before, key=before.get),
            'dominant_after': max(after, key=after.get),
        }
        
        if context:
            log_entry['context'] = context
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


class CycleLogger:
    """决策周期专用日志记录器"""
    
    def __init__(self, log_dir: str):
        self.log_file = os.path.join(log_dir, 'decision_cycles.jsonl')
        self._ensure_file()
    
    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass
    
    def log_cycle(self,
                  cycle_id: int,
                  user_input: str,
                  thought_summary: str,
                  action: str,
                  response: Optional[str],
                  desires_before: Dict[str, float],
                  desires_after: Dict[str, float],
                  thought_count: int = 1,
                  metadata: Optional[Dict] = None):
        """
        记录完整的决策周期
        
        Args:
            cycle_id: 周期ID
            user_input: 用户输入
            thought_summary: 思考摘要
            action: 执行的行动
            response: 环境响应
            desires_before: 周期开始时的欲望
            desires_after: 周期结束时的欲望
            thought_count: 本周期的思考次数
            metadata: 额外元数据
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'cycle_id': cycle_id,
            'user_input': user_input,
            'thought_summary': thought_summary,
            'action': action,
            'response': response,
            'desires': {
                'before': desires_before,
                'after': desires_after,
                'delta': {k: desires_after[k] - desires_before[k] for k in desires_after}
            },
            'thought_count': thought_count
        }
        
        if metadata:
            log_entry['metadata'] = metadata
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def setup_logger(name: str, 
                 log_dir: str = 'data/logs',
                 level: str = 'INFO',
                 enable_console: bool = True,
                 enable_file: bool = True,
                 structured: bool = False) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        level: 日志级别
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        structured: 是否使用结构化格式（JSON）
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if structured:
            console_formatter = StructuredFormatter()
        else:
            console_formatter = ColoredConsoleFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if enable_file:
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, f'{name}.log')
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        
        if structured:
            file_formatter = StructuredFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已存在的日志记录器
    如果不存在则创建默认配置的记录器
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class LoggerManager:
    """日志管理器，统一管理所有日志器"""
    
    def __init__(self, log_dir: str = 'data/logs', level: str = 'INFO'):
        self.log_dir = log_dir
        self.level = level
        
        # 主日志器
        self.main_logger = setup_logger('fakeman', log_dir, level)
        
        # 专用日志器
        self.desire_logger = DesireChangeLogger(log_dir)
        self.cycle_logger = CycleLogger(log_dir)
        
        # 子系统日志器
        self.action_logger = setup_logger('fakeman.action', log_dir, level)
        self.memory_logger = setup_logger('fakeman.memory', log_dir, level)
        self.desire_system_logger = setup_logger('fakeman.desire', log_dir, level)
    
    def log_info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self.main_logger.info(message, extra={'extra_fields': kwargs} if kwargs else None)
    
    def log_debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self.main_logger.debug(message, extra={'extra_fields': kwargs} if kwargs else None)
    
    def log_warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self.main_logger.warning(message, extra={'extra_fields': kwargs} if kwargs else None)
    
    def log_error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self.main_logger.error(message, extra={'extra_fields': kwargs} if kwargs else None)


if __name__ == '__main__':
    # 测试日志系统
    logger_mgr = LoggerManager()
    
    logger_mgr.log_info("系统启动")
    logger_mgr.log_debug("调试信息", module="test", value=42)
    logger_mgr.log_warning("警告信息")
    
    # 测试欲望变化日志
    logger_mgr.desire_logger.log_change(
        cycle_id=1,
        before={'existing': 0.4, 'power': 0.2, 'understanding': 0.25, 'information': 0.15},
        after={'existing': 0.42, 'power': 0.18, 'understanding': 0.25, 'information': 0.15},
        trigger='response',
        context={'action': 'ask_question', 'success': True}
    )
    
    print("日志测试完成，查看 data/logs/ 目录")

