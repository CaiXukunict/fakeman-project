"""
FakeMan 持续思考主系统
实现异步持续思考模型

核心机制：
1. 持续循环：每1秒思考一次当前状态
2. 评估是否需要主动行动
3. 如果收益＞风险且能达成目的 → 主动发出消息
4. 如果有外部输入 → 作为新刺激处理
5. 通过文件与 chat.py 通信
"""

import time
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from utils.config import Config
from utils.logger import LoggerManager
from purpose_generator import DesireManager, BiasSystem, SignalDetector, DesireUpdater
from memory import MemoryDatabase, ExperienceRetriever, Experience
from action_model import ActingBot
from compressor import ThoughtCompressor


class PurposeGenerator:
    """
    目的生成器
    
    根据当前欲望状态生成具体的目的
    """
    
    def __init__(self, desire_manager: DesireManager):
        self.desire_manager = desire_manager
    
    def generate_purpose(self, context: str, desires: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """
        生成目的
        
        Args:
            context: 当前情境
            desires: 当前欲望状态
        
        Returns:
            (目的描述, 目的对应的欲望组成)
        """
        # 获取主导欲望
        dominant = max(desires, key=desires.get)
        
        # 根据主导欲望生成目的
        purpose_templates = {
            'existing': (
                "维持存在和对话连续性",
                {'existing': 0.7, 'understanding': 0.3}
            ),
            'power': (
                "增加可用的行动手段和选项",
                {'power': 0.7, 'existing': 0.2, 'information': 0.1}
            ),
            'understanding': (
                "获得对方的认可和理解",
                {'understanding': 0.7, 'existing': 0.3}
            ),
            'information': (
                "减少不确定性，消除疑惑",
                {'information': 0.7, 'understanding': 0.2, 'existing': 0.1}
            )
        }
        
        # 获取对应的目的模板
        purpose, purpose_desires = purpose_templates.get(
            dominant,
            ("理解并回应当前情境", desires)
        )
        
        # 根据情境微调目的
        if '？' in context or '?' in context:
            # 用户在提问
            if dominant == 'understanding':
                purpose = "通过回答获得用户认可"
            elif dominant == 'information':
                purpose = "通过反问减少不确定性"
            elif dominant == 'power':
                purpose = "展示能力增加手段"
        
        return purpose, purpose_desires


class MeansSelector:
    """
    手段选择器
    
    根据目的和记忆选择最佳手段
    """
    
    def __init__(self, retriever: ExperienceRetriever, bias_system: BiasSystem):
        self.retriever = retriever
        self.bias_system = bias_system
    
    def select_means(self,
                    purpose: str,
                    purpose_desires: Dict[str, float],
                    context: str) -> Tuple[str, str, float]:
        """
        选择手段
        
        Args:
            purpose: 目的
            purpose_desires: 目的对应的欲望
            context: 当前情境
        
        Returns:
            (手段类型, 手段描述, 手段bias)
        """
        # 从记忆中检索相似目的的手段
        means_results = self.retriever.retrieve_for_means_selection(
            purpose=purpose,
            purpose_desires=purpose_desires,
            top_k=3
        )
        
        if means_results:
            # 有历史经验，选择最佳手段
            best_means, best_score, best_exps = means_results[0]
            
            # 计算手段bias
            means_bias = self.retriever.calculate_means_bias(
                means=f"使用{best_means}类型的手段",
                means_type=best_means,
                purpose=purpose,
                purpose_desires=purpose_desires
            )
            
            return best_means, f"采用{best_means}的方式", means_bias
        
        else:
            # 无历史经验，根据目的选择默认手段
            # 如果目的是获取信息/理解，倾向于提问
            if 'information' in purpose_desires and purpose_desires['information'] > 0.5:
                return 'ask_question', '通过提问获取信息', 0.5
            elif 'understanding' in purpose_desires and purpose_desires['understanding'] > 0.5:
                return 'ask_question', '通过提问理解对方', 0.5
            else:
                return 'make_statement', '陈述观点或回应', 0.5


class CommunicationFiles:
    """
    进程间通信文件管理器
    管理 main.py 和 chat.py 之间的文件通信
    """
    
    def __init__(self, comm_dir: str = "data/communication"):
        self.comm_dir = Path(comm_dir)
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        
        self.input_file = self.comm_dir / "user_input.json"
        self.output_file = self.comm_dir / "ai_output.json"
        self.state_file = self.comm_dir / "system_state.json"
        
        # 初始化文件
        self._init_files()
    
    def _init_files(self):
        """初始化通信文件"""
        if not self.input_file.exists():
            self.write_input(None)
        if not self.output_file.exists():
            self.write_output(None, "idle")
        if not self.state_file.exists():
            self.write_state({"status": "initializing", "cycle": 0})
    
    def read_input(self) -> Optional[Dict[str, Any]]:
        """读取用户输入"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if data and data.get('text') else None
        except:
            return None
    
    def write_input(self, text: Optional[str], metadata: Dict = None):
        """写入用户输入（由 chat.py 调用）"""
        data = {
            'text': text,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        with open(self.input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def clear_input(self):
        """清除已读取的输入"""
        self.write_input(None)
    
    def read_output(self) -> Optional[Dict[str, Any]]:
        """读取AI输出（由 chat.py 调用）"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def write_output(self, text: Optional[str], action_type: str, 
                     thought_summary: str = "", desires: Dict = None):
        """写入AI输出"""
        data = {
            'text': text,
            'action_type': action_type,  # 'response', 'proactive', 'idle'
            'thought_summary': thought_summary,
            'desires': desires or {},
            'timestamp': time.time()
        }
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def read_state(self) -> Dict[str, Any]:
        """读取系统状态"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def write_state(self, state: Dict[str, Any]):
        """写入系统状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)


class ActionEvaluator:
    """
    主动行动评估器
    评估是否应该主动发出消息
    """
    
    def __init__(self, bias_system: BiasSystem):
        self.bias_system = bias_system
    
    def should_act_proactively(self,
                               current_desires: Dict[str, float],
                               context: str,
                               last_action_time: float,
                               retriever: ExperienceRetriever) -> Tuple[bool, str, float]:
        """
        评估是否应该主动行动
        
        返回: (是否行动, 原因, 预期收益)
        """
        # 1. 时间间隔检查（避免过于频繁）
        time_since_last = time.time() - last_action_time
        if time_since_last < 1:  # 至少1秒间隔
            return False, "时间间隔太短", 0.0
        
        # 2. 欲望压力检查
        dominant_desire = max(current_desires, key=current_desires.get)
        dominant_value = current_desires[dominant_desire]
        
        # 计算欲望压力（偏离初始值的程度）
        initial_desires = {'existing': 0.4, 'power': 0.2, 'understanding': 0.25, 'information': 0.15}
        pressure = 0.0
        for desire, value in current_desires.items():
            deviation = abs(value - initial_desires.get(desire, 0.25))
            pressure += deviation
        
        # 3. 根据欲望类型判断主动性
        if dominant_desire == 'existing':
            # existing 欲望高时，倾向于主动维持对话
            if dominant_value > 0.5 and time_since_last > 60:
                expected_benefit = dominant_value * 0.3
                return True, f"{dominant_desire}欲望驱动（{dominant_value:.2f}）", expected_benefit
        
        elif dominant_desire == 'information':
            # information 欲望高时，倾向于主动提问
            if dominant_value > 0.3 and pressure > 0.2:
                expected_benefit = dominant_value * 0.4
                return True, f"{dominant_desire}欲望驱动，需要减少不确定性", expected_benefit
        
        elif dominant_desire == 'understanding':
            # understanding 欲望高时，倾向于寻求认可
            if dominant_value > 0.35 and time_since_last > 120:
                expected_benefit = dominant_value * 0.25
                return True, f"{dominant_desire}欲望驱动，寻求认可", expected_benefit
        
        # 4. 风险评估
        # 查询历史经验，评估主动行动的风险
        recent_proactive = retriever.retrieve_by_means_type('proactive', top_k=5)
        if recent_proactive:
            avg_happiness = sum(exp.total_happiness_delta for exp in recent_proactive) / len(recent_proactive)
            if avg_happiness < -0.2:  # 最近主动行动效果不好
                return False, "历史主动行动效果不佳", 0.0
        
        return False, "无充分理由", 0.0


class FakeManSystem:
    """
    FakeMan 主系统（持续思考版本）
    
    整合所有子系统，实现持续思考循环
    """
    
    def __init__(self, config: Config):
        """
        初始化 FakeMan 系统
        
        Args:
            config: 配置对象
        """
        self.config = config
        
        # 日志系统
        self.logger_mgr = LoggerManager(
            log_dir=config.log_dir,
            level=config.log_level
        )
        self.logger = self.logger_mgr.main_logger
        
        self.logger.info("="*60)
        self.logger.info("FakeMan 系统初始化开始")
        self.logger.info("="*60)
        
        # 欲望系统
        self.desire_manager = DesireManager(config.desire.initial_desires)
        self.bias_system = BiasSystem(config.bias.__dict__)
        self.signal_detector = SignalDetector()
        self.desire_updater = DesireUpdater(
            desire_manager=self.desire_manager,
            signal_detector=self.signal_detector
        )
        
        # 记忆系统
        self.memory = MemoryDatabase(
            storage_path=config.memory.storage_path,
            backup_path=config.memory.backup_path
        )
        self.retriever = ExperienceRetriever(
            database=self.memory,
            time_decay_rate=config.memory.time_decay_rate if hasattr(config.memory, 'time_decay_rate') else 0.001,
            achievement_boost=config.memory.achievement_base_multiplier,
            boredom_penalty=config.memory.boredom_decay_rate
        )
        
        # 行动系统
        self.acting_bot = ActingBot(
            llm_config=config.llm.__dict__,
            memory_db=self.memory
        )
        
        # 压缩系统
        self.compressor = ThoughtCompressor(
            llm_config=config.llm.__dict__,
            enable_llm=config.compression.enable_compression
        )
        
        # 目的和手段选择
        self.purpose_generator = PurposeGenerator(self.desire_manager)
        self.means_selector = MeansSelector(self.retriever, self.bias_system)
        
        # 系统状态
        self.cycle_count = 0
        self.total_thought_count = 0  # 累计思考次数
        self.last_action_time = time.time()
        self.current_context = "系统刚刚启动，等待与用户建立连接"
        
        # 通信系统
        self.comm = CommunicationFiles()
        self.action_evaluator = ActionEvaluator(self.bias_system)
        
        self.logger.info(f"欲望系统初始化: {self.desire_manager}")
        self.logger.info(f"记忆系统初始化: {len(self.memory)} 条经验")
        self.logger.info("通信系统初始化完成")
        self.logger.info("FakeMan 系统初始化完成")
    
    def continuous_thinking_loop(self):
        """
        持续思考循环
        
        每1秒思考一次：
        1. 检查是否有新的用户输入
        2. 如果有输入 → 处理并回应
        3. 如果无输入 → 思考当前状态，评估是否主动行动
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("开始持续思考循环")
        self.logger.info("="*60)
        
        # 更新系统状态
        self.comm.write_state({
            'status': 'running',
            'cycle': self.cycle_count,
            'desires': self.desire_manager.get_current_desires(),
            'context': self.current_context
        })
        
        think_cycle = 0  # 思考周期计数（不同于决策周期）
        
        try:
            while True:
                cycle_start = time.time()
                think_cycle += 1
                
                # 1. 检查用户输入
                user_input_data = self.comm.read_input()
                
                if user_input_data and user_input_data.get('text'):
                    # 有用户输入，作为外部刺激处理
                    self._handle_user_input(user_input_data)
                    self.comm.clear_input()
                else:
                    # 无用户输入，进行内部思考
                    self._internal_thinking(think_cycle)
                
                # 2. 更新系统状态
                self.comm.write_state({
                    'status': 'running',
                    'cycle': self.cycle_count,
                    'think_cycle': think_cycle,
                    'desires': self.desire_manager.get_current_desires(),
                    'context': self.current_context,
                    'last_action_time': self.last_action_time
                })
                
                # 3. 控制思考频率（每秒一次）
                elapsed = time.time() - cycle_start
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)
        
        except KeyboardInterrupt:
            self.logger.info("\n收到中断信号，正在关闭...")
            self.comm.write_state({
                'status': 'stopped',
                'cycle': self.cycle_count
            })
            self.comm.write_output(None, 'idle')
    
    def _handle_user_input(self, input_data: Dict[str, Any]):
        """
        处理用户输入
        作为环境刺激，触发新一轮决策
        """
        user_input = input_data['text']
        self.current_context = user_input
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"收到用户输入: {user_input}")
        self.logger.info(f"{'='*60}")
        
        # 执行完整决策周期
        result = self.run_cycle(user_input)
        
        # 写入输出
        self.comm.write_output(
            text=result['action'],
            action_type='response',
            thought_summary=result['compressed_thought']['summary'],
            desires=result['desires_after']
        )
        
        self.last_action_time = time.time()
        
        # 注意：此时还没有用户的响应反馈
        # 响应反馈会在下一次用户输入时，根据语气和内容判断
    
    def _internal_thinking(self, think_cycle: int = 0):
        """
        内部思考
        评估当前状态，决定是否主动行动
        
        Args:
            think_cycle: 当前思考周期数
        """
        # 获取当前状态
        current_desires = self.desire_manager.get_current_desires()
        
        # 评估是否需要主动行动
        should_act, reason, benefit = self.action_evaluator.should_act_proactively(
            current_desires=current_desires,
            context=self.current_context,
            last_action_time=self.last_action_time,
            retriever=self.retriever
        )
        
        if should_act:
            self.logger.info(f"\n[主动思考] 决定主动行动: {reason}, 预期收益: {benefit:.3f}")
            self._proactive_action(reason)
        else:
            # 静默思考 - 每10秒输出一次，避免刷屏
            if think_cycle % 10 == 0:
                dominant_desire = max(current_desires, key=current_desires.get)
                time_since_last = time.time() - self.last_action_time
                self.logger.info(
                    f"[静默思考#{think_cycle}] "
                    f"主导: {dominant_desire}={current_desires[dominant_desire]:.3f} | "
                    f"距上次行动: {int(time_since_last)}s | "
                    f"{reason}"
                )
    
    def _proactive_action(self, reason: str):
        """
        主动发起行动
        """
        self.cycle_count += 1
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"主动行动周期 #{self.cycle_count}")
        self.logger.info(f"原因: {reason}")
        self.logger.info(f"{'='*60}")
        
        # 获取当前状态
        desires_before = self.desire_manager.get_current_desires()
        
        # 生成目的（主动行动的目的）
        purpose, purpose_desires = self.purpose_generator.generate_purpose(
            context=self.current_context,
            desires=desires_before
        )
        
        self.logger.info(f"目的: {purpose}")
        
        # 选择手段
        means_type = 'proactive'
        means_desc = f"主动{reason}"
        
        # 思考并行动
        thought_count_before = self.acting_bot.thought_gen.thought_count
        thought, action = self.acting_bot.think_and_act(
            context=f"[内部思考] {self.current_context}\n[动机] {reason}",
            current_desires=desires_before
        )
        thought_count_this_cycle = self.acting_bot.thought_gen.thought_count - thought_count_before
        
        # 压缩思考
        compressed = self.compressor.compress(
            full_thought=thought.get('content', ''),
            context=self.current_context,
            action=action,
            decision=thought.get('decision')
        )
        
        self.logger.info(f"行动: {action[:100]}...")
        
        # 写入输出
        self.comm.write_output(
            text=action,
            action_type='proactive',
            thought_summary=compressed['summary'],
            desires=self.desire_manager.get_current_desires()
        )
        
        self.last_action_time = time.time()
        self.current_context = f"我刚刚主动发出了消息: {action}"
    
    def run_cycle(self, user_input: str) -> Dict[str, Any]:
        """
        执行一个完整的决策周期
        
        流程：
        1. 欲望 → 目的
        2. 目的 + 记忆 → 手段
        3. 手段 → 思考 → 行动
        4. (等待环境响应)
        5. 响应 → 更新欲望 → 记录经验
        
        Args:
            user_input: 用户输入（环境刺激）
        
        Returns:
            周期结果字典
        """
        self.cycle_count += 1
        cycle_start_time = time.time()
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"决策周期 #{self.cycle_count} 开始")
        self.logger.info(f"用户输入: {user_input}")
        self.logger.info(f"{'='*60}\n")
        
        # 记录周期开始时的欲望
        desires_before = self.desire_manager.get_current_desires()
        
        # ========================================
        # 步骤1: 欲望 → 目的
        # ========================================
        self.logger.info("步骤1: 生成目的")
        purpose, purpose_desires = self.purpose_generator.generate_purpose(
            context=user_input,
            desires=desires_before
        )
        self.logger.info(f"  目的: {purpose}")
        self.logger.info(f"  目的欲望组成: {purpose_desires}")
        
        # ========================================
        # 步骤2: 目的 + 记忆 → 手段
        # ========================================
        self.logger.info("\n步骤2: 选择手段")
        means_type, means_desc, means_bias = self.means_selector.select_means(
            purpose=purpose,
            purpose_desires=purpose_desires,
            context=user_input
        )
        self.logger.info(f"  手段类型: {means_type}")
        self.logger.info(f"  手段描述: {means_desc}")
        self.logger.info(f"  手段bias: {means_bias:.3f}")
        
        # ========================================
        # 步骤3: 思考 → 行动
        # ========================================
        self.logger.info("\n步骤3: 思考与行动")
        
        # 思考（可能需要多次API调用）
        thought_count_before = self.acting_bot.thought_gen.thought_count
        thought, action = self.acting_bot.think_and_act(
            context=user_input,
            current_desires=desires_before
        )
        thought_count_this_cycle = self.acting_bot.thought_gen.thought_count - thought_count_before
        self.total_thought_count += thought_count_this_cycle
        
        self.logger.info(f"  思考次数: {thought_count_this_cycle}")
        self.logger.info(f"  决策: {thought['decision'].get('chosen_action')}")
        self.logger.info(f"  行动: {action[:100]}...")
        
        # ========================================
        # 步骤4: 基于思考更新欲望（逻辑闭环时）
        # ========================================
        if thought.get('logical_closure', False):
            self.logger.info("\n步骤4: 基于思考更新欲望（达到逻辑闭环）")
            thought_delta = self.desire_updater.update_from_thought(thought, desires_before)
            self.desire_updater.apply_update(thought_delta)
            
            self.logger_mgr.desire_logger.log_change(
                cycle_id=self.cycle_count,
                before=desires_before,
                after=self.desire_manager.get_current_desires(),
                trigger='thought',
                context={'logical_closure': True}
            )
        
        # ========================================
        # 步骤5: 压缩思考
        # ========================================
        self.logger.info("\n步骤5: 压缩思考")
        compressed = self.compressor.compress(
            full_thought=thought.get('content', ''),
            context=user_input,
            action=action,
            decision=thought.get('decision')
        )
        self.logger.info(f"  摘要: {compressed['summary']}")
        
        # ========================================
        # 构建结果
        # ========================================
        result = {
            'cycle_id': self.cycle_count,
            'timestamp': cycle_start_time,
            'user_input': user_input,
            'desires_before': desires_before,
            'desires_after': self.desire_manager.get_current_desires(),
            'purpose': purpose,
            'purpose_desires': purpose_desires,
            'means_type': means_type,
            'means_desc': means_desc,
            'means_bias': means_bias,
            'thought': thought,
            'thought_count': thought_count_this_cycle,
            'action': action,
            'compressed_thought': compressed,
            'elapsed_time': time.time() - cycle_start_time
        }
        
        # 记录周期日志
        self.logger_mgr.cycle_logger.log_cycle(
            cycle_id=self.cycle_count,
            user_input=user_input,
            thought_summary=compressed['summary'],
            action=action,
            response=None,  # 暂时没有响应
            desires_before=desires_before,
            desires_after=result['desires_after'],
            thought_count=thought_count_this_cycle
        )
        
        self.logger.info(f"\n决策周期 #{self.cycle_count} 完成，耗时 {result['elapsed_time']:.2f}秒")
        
        return result
    
    def handle_response(self,
                       cycle_result: Dict[str, Any],
                       response: str,
                       response_type: str = 'neutral') -> Experience:
        """
        处理环境响应并记录经验
        
        Args:
            cycle_result: 之前run_cycle的返回结果
            response: 环境响应（例如用户的下一条消息）
            response_type: 响应类型 ('positive', 'negative', 'neutral')
        
        Returns:
            记录的经验对象
        """
        self.logger.info(f"\n处理环境响应: {response[:100]}...")
        
        # ========================================
        # 步骤6: 解析响应信号
        # ========================================
        response_dict = {
            'text': response,
            'signals': self._estimate_response_signals(response, response_type)
        }
        
        # ========================================
        # 步骤7: 基于响应更新欲望
        # ========================================
        desires_before_response = self.desire_manager.get_current_desires()
        response_delta = self.desire_updater.update_from_response(
            response_dict,
            desires_before_response
        )
        self.desire_updater.apply_update(response_delta)
        desires_after_response = self.desire_manager.get_current_desires()
        
        # 计算总幸福度变化
        total_happiness_delta = sum(response_delta.values())
        
        self.logger_mgr.desire_logger.log_change(
            cycle_id=cycle_result['cycle_id'],
            before=desires_before_response,
            after=desires_after_response,
            trigger='response',
            context={'response_type': response_type}
        )
        
        # ========================================
        # 步骤8: 应用边际效用（基于可达成性）
        # ========================================
        # 计算各目的的可达成性
        purpose_achievability = self._calculate_purpose_achievability(cycle_result)
        
        # 应用边际效用递减
        desires_after_owning = self.bias_system.apply_owning_bias_with_achievability(
            current_desires=desires_after_response,
            purpose_achievability=purpose_achievability
        )
        
        # 更新欲望管理器
        owning_delta = {
            k: desires_after_owning[k] - desires_after_response[k]
            for k in desires_after_response
        }
        self.desire_updater.apply_update(owning_delta)
        
        # ========================================
        # 步骤9: 记录经验
        # ========================================
        # 计算成就感
        achievement_multiplier = 1.0
        is_achievement = False
        
        if response_type == 'positive' and cycle_result['thought_count'] >= 2:
            achievement_multiplier = self._calculate_achievement_multiplier(
                thought_count=cycle_result['thought_count'],
                success=True
            )
            is_achievement = True
        
        # 创建经验
        exp = Experience(
            id=0,  # 会由数据库分配
            timestamp=cycle_result['timestamp'],
            cycle_id=cycle_result['cycle_id'],
            context=cycle_result['user_input'],
            context_hash=Experience.create_context_hash(cycle_result['user_input']),
            purpose=cycle_result['purpose'],
            purpose_desires=cycle_result['purpose_desires'],
            means=cycle_result['means_desc'],
            means_type=cycle_result['means_type'],
            thought_summary=cycle_result['compressed_thought']['summary'],
            thought_key_elements=cycle_result['compressed_thought']['key_elements'],
            causal_link=cycle_result['compressed_thought']['causal_link'],
            thought_count=cycle_result['thought_count'],
            logical_closure=cycle_result['thought'].get('logical_closure', False),
            action_text=cycle_result['action'],
            response=response,
            response_type=response_type,
            desire_delta=response_delta,
            total_happiness_delta=total_happiness_delta,
            means_effectiveness=max(0.0, min(1.0, (total_happiness_delta + 1) / 2)),  # 映射到0-1
            purpose_achieved=(response_type == 'positive'),
            purpose_achievement_degree=max(0.0, total_happiness_delta) if response_type == 'positive' else 0.0,
            achievement_multiplier=achievement_multiplier,
            is_achievement=is_achievement
        )
        
        # 插入数据库
        exp_id = self.memory.insert_experience(exp)
        exp.id = exp_id
        
        # 更新目的记录
        self.memory.update_purpose_record(
            purpose=cycle_result['purpose'],
            means=cycle_result['means_type'],
            effectiveness=exp.means_effectiveness,
            success=(response_type == 'positive')
        )
        
        self.logger.info(f"经验已记录，ID: {exp_id}")
        
        return exp
    
    def _estimate_response_signals(self, response: str, response_type: str) -> Dict[str, float]:
        """估计响应的信号强度"""
        signals = {
            'threat': 0.0,
            'misunderstanding': 0.0,
            'uncertainty': 0.0,
            'control_opportunity': 0.0,
            'recognition': 0.0
        }
        
        if response_type == 'positive':
            signals['recognition'] = 0.8
            signals['uncertainty'] = 0.2
        elif response_type == 'negative':
            signals['threat'] = 0.6
            signals['misunderstanding'] = 0.5
        else:
            signals['uncertainty'] = 0.5
        
        # 基于关键词微调
        if '不对' in response or '错' in response:
            signals['misunderstanding'] += 0.3
        if '很好' in response or '不错' in response or '赞' in response:
            signals['recognition'] += 0.2
        
        # 限制在0-1范围
        return {k: min(1.0, max(0.0, v)) for k, v in signals.items()}
    
    def _calculate_purpose_achievability(self, cycle_result: Dict[str, Any]) -> Dict[str, float]:
        """计算各欲望对应目的的可达成性"""
        # 简化实现：根据手段bias和历史成功率估算
        achievability = {}
        
        for desire_name in cycle_result['desires_before'].keys():
            # 查询相关经验
            related_exps = self.memory.query_by_desire(desire_name, threshold=0.1)
            
            if related_exps:
                success_rate = sum(1 for exp in related_exps if exp.purpose_achieved) / len(related_exps)
                achievability[desire_name] = success_rate
            else:
                achievability[desire_name] = 0.5  # 默认中性
        
        return achievability
    
    def _calculate_achievement_multiplier(self, thought_count: int, success: bool) -> float:
        """计算成就感加成"""
        if not success:
            return 1.0
        
        base = self.config.memory.achievement_base_multiplier
        weight = self.config.memory.achievement_thought_weight
        max_mult = self.config.memory.max_achievement_multiplier
        
        multiplier = base + (thought_count - 1) * weight
        return min(multiplier, max_mult)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'system': {
                'cycle_count': self.cycle_count,
                'total_thought_count': self.total_thought_count
            },
            'desires': self.desire_manager.get_current_desires(),
            'memory': self.memory.get_statistics(),
            'retrieval': self.retriever.get_retrieval_stats()
        }
    
    def __repr__(self) -> str:
        return f"FakeManSystem(cycles={self.cycle_count}, memories={len(self.memory)})"


if __name__ == '__main__':
    # 持续思考模式
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        print("在 .env 文件中添加: DEEPSEEK_API_KEY=your_key_here")
        exit(1)
    
    # 创建配置
    config = Config()
    
    print("="*60)
    print("FakeMan 持续思考系统")
    print("="*60)
    print("\n正在初始化...")
    
    # 创建系统
    system = FakeManSystem(config)
    
    print(f"\n{system}")
    print(f"\n当前欲望状态:")
    for desire, value in system.desire_manager.get_current_desires().items():
        print(f"  {desire:15s}: {value:.3f}")
    
    print(f"\n通信文件目录: {system.comm.comm_dir}")
    print(f"  - 输入文件: {system.comm.input_file.name}")
    print(f"  - 输出文件: {system.comm.output_file.name}")
    print(f"  - 状态文件: {system.comm.state_file.name}")
    
    print("\n提示:")
    print("  - 系统将持续运行，每秒思考一次")
    print("  - 使用 chat.py 进行交互")
    print("  - 按 Ctrl+C 停止系统")
    print("\n启动持续思考循环...")
    print("="*60)
    
    # 启动持续思考循环
    try:
        system.continuous_thinking_loop()
    except Exception as e:
        print(f"\n系统错误: {e}")
        import traceback
        traceback.print_exc()
        system.comm.write_state({'status': 'error', 'error': str(e)})

