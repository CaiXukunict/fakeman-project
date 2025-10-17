"""
FakeMan 配置系统
集中管理所有系统参数，支持环境变量覆盖
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = 'deepseek'  # 'deepseek', 'anthropic', 'openai'
    model: str = 'deepseek-chat'
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    
    def __post_init__(self):
        """从环境变量读取 API Key"""
        if self.api_key is None:
            if self.provider == 'deepseek':
                self.api_key = os.getenv('DEEPSEEK_API_KEY')
                if self.base_url is None:
                    self.base_url = 'https://api.deepseek.com'
            elif self.provider == 'anthropic':
                self.api_key = os.getenv('ANTHROPIC_API_KEY')
            elif self.provider == 'openai':
                self.api_key = os.getenv('OPENAI_API_KEY')


@dataclass
class DesireConfig:
    """欲望系统配置"""
    # 初始欲望状态（总和为1）
    initial_desires: Dict[str, float] = field(default_factory=lambda: {
        'existing': 0.4,        # 维持存在
        'power': 0.2,           # 增加手段
        'understanding': 0.25,  # 获得认可
        'information': 0.15     # 减少不确定性，减少疑惑
    })
    
    # 欲望更新的学习率
    learning_rate: float = 0.1
    
    # 欲望值的边界
    min_desire_value: float = 0.0
    max_desire_value: float = 1.0
    
    # 归一化阈值（如果总和偏差超过此值则重新归一化）
    normalization_threshold: float = 0.01


@dataclass
class BiasConfig:
    """偏见系统配置"""
    # 损失厌恶系数
    fear_multiplier: float = 2.5
    
    # 时间折现率
    time_discount_rate: float = 0.1
    
    # 边际效用递减率（修改后的逻辑：影响目的的可达成性bias）
    owning_decay_rates: Dict[str, float] = field(default_factory=lambda: {
        'existing': 0.001,
        'power': 0.01,
        'understanding': 0.008,
        'information': 0.015
    })
    
    # 可能性偏见参数
    min_experiences_for_reliability: int = 3
    time_decay_rate: float = 0.001  # 经验的时间衰减率
    
    # 可达成性bias调整参数
    achievability_transfer_rate: float = 0.05  # 从高可达性向低可达性转移的比例


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    # 存储路径
    storage_path: str = 'data/experiences.json'
    backup_path: str = 'data/experiences_backup.json'
    
    # 检索参数
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.3
    
    # 时间窗口（用于延迟认可）
    recognition_time_window: int = 300  # 秒
    
    # 成就感参数
    achievement_base_multiplier: float = 1.5  # 基础成就感加成
    achievement_thought_weight: float = 0.2   # 每次思考增加的权重
    max_achievement_multiplier: float = 5.0   # 最大成就感加成
    
    # 无聊机制参数
    boredom_threshold: int = 5  # 连续无效果的次数
    boredom_decay_rate: float = 0.1  # 每次无效果时的possibility bias衰减
    min_possibility_bias: float = 0.1  # 最低possibility bias


@dataclass
class CompressionConfig:
    """思考压缩配置"""
    enable_compression: bool = True
    summary_max_length: int = 100  # 字符
    max_key_elements: int = 5
    compression_llm_provider: str = 'deepseek'  # 使用轻量级模型


@dataclass
class Config:
    """
    FakeMan 主配置类
    整合所有子配置
    """
    llm: LLMConfig = field(default_factory=LLMConfig)
    desire: DesireConfig = field(default_factory=DesireConfig)
    bias: BiasConfig = field(default_factory=BiasConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    
    # 系统级别配置
    enable_logging: bool = True
    log_level: str = 'INFO'
    log_dir: str = 'data/logs'
    
    # 调试模式
    debug_mode: bool = False
    verbose: bool = False
    
    def __post_init__(self):
        """验证配置"""
        self._validate_desires()
        self._ensure_directories()
    
    def _validate_desires(self):
        """验证欲望配置"""
        total = sum(self.desire.initial_desires.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"初始欲望总和必须为1，当前为: {total}")
        
        for name, value in self.desire.initial_desires.items():
            if not (0 <= value <= 1):
                raise ValueError(f"欲望 '{name}' 的值必须在 0-1 之间，当前为: {value}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs = [
            os.path.dirname(self.memory.storage_path),
            os.path.dirname(self.memory.backup_path),
            self.log_dir
        ]
        for dir_path in dirs:
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, file_path: str):
        """导出为 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, file_path: str) -> 'Config':
        """从 JSON 文件加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 递归创建子配置对象
        config = cls(
            llm=LLMConfig(**data.get('llm', {})),
            desire=DesireConfig(**data.get('desire', {})),
            bias=BiasConfig(**data.get('bias', {})),
            memory=MemoryConfig(**data.get('memory', {})),
            compression=CompressionConfig(**data.get('compression', {}))
        )
        
        # 更新系统级别配置
        for key in ['enable_logging', 'log_level', 'log_dir', 'debug_mode', 'verbose']:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量创建配置（覆盖默认值）"""
        config = cls()
        
        # LLM 配置
        if os.getenv('LLM_PROVIDER'):
            config.llm.provider = os.getenv('LLM_PROVIDER')
        if os.getenv('LLM_MODEL'):
            config.llm.model = os.getenv('LLM_MODEL')
        if os.getenv('LLM_TEMPERATURE'):
            config.llm.temperature = float(os.getenv('LLM_TEMPERATURE'))
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            config.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('DEBUG_MODE'):
            config.debug_mode = os.getenv('DEBUG_MODE').lower() == 'true'
        
        return config
    
    def __repr__(self) -> str:
        return f"Config(llm={self.llm.provider}, desires={list(self.desire.initial_desires.keys())})"


# 创建默认配置实例
DEFAULT_CONFIG = Config()


if __name__ == '__main__':
    # 测试配置系统
    config = Config()
    print(config)
    print(f"\n初始欲望: {config.desire.initial_desires}")
    print(f"LLM配置: {config.llm}")
    
    # 测试导出
    config.to_json('config_example.json')
    print("\n配置已导出到 config_example.json")

