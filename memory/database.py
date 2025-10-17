"""
记忆数据库 - 基于 JSON 文件
提供经验的存储、查询和管理功能
"""

import json
import os
import time
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from .experience import Experience, PurposeRecord
from utils.logger import get_logger

logger = get_logger('fakeman.memory.database')


class MemoryDatabase:
    """
    记忆数据库（JSON文件存储）
    
    使用JSON文件而非SQLite，便于查看和调试
    """
    
    def __init__(self, storage_path: str = 'data/experiences.json',
                 backup_path: str = 'data/experiences_backup.json',
                 auto_backup: bool = True,
                 backup_interval: int = 100):
        """
        初始化记忆数据库
        
        Args:
            storage_path: 主存储文件路径
            backup_path: 备份文件路径
            auto_backup: 是否自动备份
            backup_interval: 每N次写入后备份一次
        """
        self.storage_path = Path(storage_path)
        self.backup_path = Path(backup_path)
        self.auto_backup = auto_backup
        self.backup_interval = backup_interval
        
        # 内存中的数据
        self.experiences: List[Experience] = []
        self.purpose_records: Dict[str, PurposeRecord] = {}  # key: purpose_hash
        
        # 统计信息
        self.next_id = 1
        self.write_count = 0
        self.last_backup_time = 0
        
        # 确保目录存在
        self._ensure_directory()
        
        # 加载现有数据
        self._load_from_file()
        
        logger.info(f"记忆数据库初始化完成，已加载 {len(self.experiences)} 条经验")
    
    def _ensure_directory(self):
        """确保存储目录存在"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if self.backup_path:
            self.backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_from_file(self):
        """从文件加载数据"""
        if not self.storage_path.exists():
            logger.info(f"存储文件不存在，创建新文件: {self.storage_path}")
            self._save_to_file()
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载经验
            experiences_data = data.get('experiences', [])
            self.experiences = [Experience.from_dict(exp) for exp in experiences_data]
            
            # 加载目的记录
            purpose_records_data = data.get('purpose_records', {})
            self.purpose_records = {
                key: PurposeRecord.from_dict(rec)
                for key, rec in purpose_records_data.items()
            }
            
            # 更新ID计数器
            if self.experiences:
                self.next_id = max(exp.id for exp in self.experiences) + 1
            
            logger.info(f"成功加载 {len(self.experiences)} 条经验和 {len(self.purpose_records)} 条目的记录")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON文件解析失败: {e}")
            # 尝试加载备份
            if self.backup_path.exists():
                logger.info("尝试从备份恢复...")
                try:
                    shutil.copy(self.backup_path, self.storage_path)
                    self._load_from_file()
                except Exception as e2:
                    logger.error(f"从备份恢复失败: {e2}")
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
    
    def _save_to_file(self):
        """保存数据到文件"""
        try:
            # 准备数据
            data = {
                'metadata': {
                    'last_updated': time.time(),
                    'total_experiences': len(self.experiences),
                    'total_purposes': len(self.purpose_records)
                },
                'experiences': [exp.to_dict() for exp in self.experiences],
                'purpose_records': {
                    key: rec.to_dict()
                    for key, rec in self.purpose_records.items()
                }
            }
            
            # 写入临时文件
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            shutil.move(temp_path, self.storage_path)
            
            self.write_count += 1
            
            # 自动备份
            if self.auto_backup and self.write_count % self.backup_interval == 0:
                self._create_backup()
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise
    
    def _create_backup(self):
        """创建备份"""
        try:
            if self.storage_path.exists():
                shutil.copy(self.storage_path, self.backup_path)
                self.last_backup_time = time.time()
                logger.info(f"已创建备份: {self.backup_path}")
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")
    
    # ==========================================
    # 经验操作
    # ==========================================
    
    def insert_experience(self, exp: Experience) -> int:
        """
        插入新经验
        
        Args:
            exp: 经验对象（可以不设置id）
        
        Returns:
            分配的经验ID
        """
        if exp.id == 0 or exp.id is None:
            exp.id = self.next_id
            self.next_id += 1
        
        self.experiences.append(exp)
        self._save_to_file()
        
        logger.debug(f"插入新经验: ID={exp.id}, 目的={exp.purpose[:30]}...")
        
        return exp.id
    
    def get_experience_by_id(self, exp_id: int) -> Optional[Experience]:
        """根据ID获取经验"""
        for exp in self.experiences:
            if exp.id == exp_id:
                return exp
        return None
    
    def get_all_experiences(self) -> List[Experience]:
        """获取所有经验"""
        return self.experiences.copy()
    
    def get_recent_experiences(self, n: int = 10) -> List[Experience]:
        """获取最近的N条经验"""
        return sorted(self.experiences, key=lambda x: x.timestamp, reverse=True)[:n]
    
    def query_by_purpose(self, purpose: str, fuzzy: bool = True) -> List[Experience]:
        """
        按目的查询经验
        
        Args:
            purpose: 目的描述
            fuzzy: 是否模糊匹配
        
        Returns:
            匹配的经验列表
        """
        if fuzzy:
            return [exp for exp in self.experiences if purpose.lower() in exp.purpose.lower()]
        else:
            return [exp for exp in self.experiences if exp.purpose == purpose]
    
    def query_by_means(self, means: str) -> List[Experience]:
        """按手段查询经验"""
        return [exp for exp in self.experiences if means.lower() in exp.means.lower()]
    
    def query_by_context_hash(self, context_hash: str) -> List[Experience]:
        """按情境哈希查询"""
        return [exp for exp in self.experiences if exp.context_hash == context_hash]
    
    def query_by_time_range(self, start_time: float, end_time: float) -> List[Experience]:
        """按时间范围查询"""
        return [
            exp for exp in self.experiences
            if start_time <= exp.timestamp <= end_time
        ]
    
    def query_by_desire(self, desire_name: str, threshold: float = 0.1) -> List[Experience]:
        """
        查询对特定欲望影响较大的经验
        
        Args:
            desire_name: 欲望名称
            threshold: 影响阈值
        
        Returns:
            影响该欲望的经验列表
        """
        return [
            exp for exp in self.experiences
            if abs(exp.desire_delta.get(desire_name, 0)) > threshold
        ]
    
    def query_positive_experiences(self) -> List[Experience]:
        """查询所有正面经验"""
        return [exp for exp in self.experiences if exp.is_positive]
    
    def query_negative_experiences(self) -> List[Experience]:
        """查询所有负面经验"""
        return [exp for exp in self.experiences if exp.is_negative]
    
    def query_achievements(self) -> List[Experience]:
        """查询所有成就事件"""
        return [exp for exp in self.experiences if exp.is_achievement]
    
    # ==========================================
    # 目的记录操作
    # ==========================================
    
    def get_or_create_purpose_record(self, purpose: str, 
                                     desire_composition: Dict[str, float]) -> PurposeRecord:
        """获取或创建目的记录"""
        purpose_hash = PurposeRecord.create_purpose_hash(purpose)
        
        if purpose_hash not in self.purpose_records:
            self.purpose_records[purpose_hash] = PurposeRecord(
                purpose=purpose,
                purpose_hash=purpose_hash,
                desire_composition=desire_composition
            )
            self._save_to_file()
        
        return self.purpose_records[purpose_hash]
    
    def update_purpose_record(self, purpose: str, means: str, 
                             effectiveness: float, success: bool):
        """更新目的记录"""
        purpose_hash = PurposeRecord.create_purpose_hash(purpose)
        
        if purpose_hash in self.purpose_records:
            record = self.purpose_records[purpose_hash]
            record.add_attempt(means, effectiveness, success)
            self._save_to_file()
    
    def get_purpose_record(self, purpose: str) -> Optional[PurposeRecord]:
        """获取目的记录"""
        purpose_hash = PurposeRecord.create_purpose_hash(purpose)
        return self.purpose_records.get(purpose_hash)
    
    # ==========================================
    # 统计功能
    # ==========================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        if not self.experiences:
            return {
                'total_experiences': 0,
                'total_purposes': 0
            }
        
        positive_count = len([exp for exp in self.experiences if exp.is_positive])
        negative_count = len([exp for exp in self.experiences if exp.is_negative])
        
        return {
            'total_experiences': len(self.experiences),
            'total_purposes': len(self.purpose_records),
            'positive_experiences': positive_count,
            'negative_experiences': negative_count,
            'positive_rate': positive_count / len(self.experiences) if self.experiences else 0,
            'achievement_count': len([exp for exp in self.experiences if exp.is_achievement]),
            'avg_happiness_delta': sum(exp.total_happiness_delta for exp in self.experiences) / len(self.experiences),
            'oldest_experience': min(exp.timestamp for exp in self.experiences),
            'newest_experience': max(exp.timestamp for exp in self.experiences),
            'write_count': self.write_count,
            'last_backup': self.last_backup_time
        }
    
    def clear_all(self):
        """清空所有数据（谨慎使用）"""
        logger.warning("清空所有记忆数据")
        self._create_backup()  # 先备份
        self.experiences = []
        self.purpose_records = {}
        self.next_id = 1
        self._save_to_file()
    
    def __len__(self) -> int:
        """返回经验总数"""
        return len(self.experiences)
    
    def __repr__(self) -> str:
        return f"MemoryDatabase(experiences={len(self.experiences)}, purposes={len(self.purpose_records)})"


if __name__ == '__main__':
    # 测试记忆数据库
    db = MemoryDatabase('data/test_experiences.json')
    
    # 创建测试经验
    exp = Experience(
        id=0,
        timestamp=time.time(),
        cycle_id=1,
        context="测试情境",
        context_hash=Experience.create_context_hash("测试情境"),
        purpose="测试目的",
        purpose_desires={'understanding': 0.6, 'information': 0.4},
        means="测试手段",
        thought_count=2,
        total_happiness_delta=0.5,
        purpose_achieved=True
    )
    
    # 插入经验
    exp_id = db.insert_experience(exp)
    print(f"插入经验，ID: {exp_id}")
    
    # 查询
    results = db.query_by_purpose("测试")
    print(f"\n找到 {len(results)} 条相关经验")
    
    # 统计
    stats = db.get_statistics()
    print(f"\n数据库统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n{db}")

