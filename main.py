"""
FakeMan 持续思考主系统
实现异步持续思考模型

核心机制：
1. 持续循环：每1秒思考一次当前状态
2. 评估是否需要主动行动
3. 如果收益＞风险且能达成目的 → 主动发出消息
4. 如果有外部输入 → 作为新刺激处理
5. 通过文件与 chat.py 通信
ds apikey: sk-42849803121c4671b0547935542966c9
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
from memory import MemoryDatabase, ExperienceRetriever, Experience, ExperienceMemory, EventMemory
from action_model import ActingBot
from compressor import ThoughtCompressor
from scenario import ScenarioSimulator, MeansSimulation


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
    手段选择器（带场景模拟）
    
    根据目的和记忆选择最佳手段，使用场景模拟预测效果
    """
    
    def __init__(self, 
                 retriever: ExperienceRetriever, 
                 bias_system: BiasSystem,
                 scenario_simulator: ScenarioSimulator):
        self.retriever = retriever
        self.bias_system = bias_system
        self.scenario_simulator = scenario_simulator
    
    def select_means(self,
                    purpose: str,
                    purpose_desires: Dict[str, float],
                    context: str,
                    current_desires: Dict[str, float],
                    include_fantasy: bool = False) -> Tuple[str, str, float, List[MeansSimulation]]:
        """
        选择手段（使用场景模拟预测）
        
        Args:
            purpose: 目的
            purpose_desires: 目的对应的欲望
            context: 当前情境
            current_desires: 当前欲望状态
            include_fantasy: 是否包含妄想手段
        
        Returns:
            (手段类型, 手段描述, 手段bias, 所有模拟结果)
        """
        all_simulations = []
        
        # 1. 从记忆中检索历史手段
        means_results = self.retriever.retrieve_for_means_selection(
            purpose=purpose,
            purpose_desires=purpose_desires,
            top_k=5  # 获取更多候选
        )
        
        # 2. 为每个候选手段进行场景模拟
        if means_results:
            for means_type, score, exps in means_results:
                sim = self.scenario_simulator.simulate_means(
                    means_type=means_type,
                    means_desc=f"采用{means_type}的方式",
                    current_desires=current_desires,
                    context=context,
                    is_fantasy=False
                )
                all_simulations.append(sim)
        else:
            # 无历史经验，生成默认手段候选
            default_means = self._get_default_means(purpose_desires)
            for means_type, means_desc in default_means:
                sim = self.scenario_simulator.simulate_means(
                    means_type=means_type,
                    means_desc=means_desc,
                    current_desires=current_desires,
                    context=context,
                    is_fantasy=False
                )
                all_simulations.append(sim)
        
        # 3. 如果应该生成妄想，添加妄想手段
        if include_fantasy or self.scenario_simulator.should_generate_fantasy():
            fantasy_means = self.scenario_simulator.generate_fantasy_means(
                current_desires=current_desires,
                context=context,
                purpose=purpose,
                num_fantasies=2
            )
            all_simulations.extend(fantasy_means)
        
        # 4. 过滤掉四个欲望相加为负的手段
        viable_simulations = self._filter_negative_means(all_simulations)
        
        if not viable_simulations:
            # 如果所有手段都被过滤了，保留最好的那个
            viable_simulations = [max(all_simulations, 
                                     key=lambda s: s.predicted_total_happiness)]
        
        # 5. 更新场景欲望值
        # existing = 基于记忆持久性（数据不被删除）
        self.scenario_simulator.update_existing_desire()
        
        # power = 无法达成的手段 / 全部手段
        achievable = [s for s in viable_simulations if not s.is_fantasy]
        self.scenario_simulator.update_power_desire(all_simulations, achievable)
        
        # 6. 选择最佳手段（预测幸福度最高的）
        best_simulation = max(viable_simulations, 
                             key=lambda s: s.predicted_total_happiness)
        
        # 7. 计算手段bias
        means_bias = self.retriever.calculate_means_bias(
            means=best_simulation.means_desc,
            means_type=best_simulation.means_type,
            purpose=purpose,
            purpose_desires=purpose_desires
        ) if not best_simulation.is_fantasy else 0.3  # 妄想手段bias较低
        
        return (best_simulation.means_type, 
                best_simulation.means_desc, 
                means_bias,
                all_simulations)
    
    def _get_default_means(self, purpose_desires: Dict[str, float]) -> List[Tuple[str, str]]:
        """获取默认手段候选"""
        means = []
        
        # 根据目的欲望生成候选
        if purpose_desires.get('information', 0) > 0.3:
            means.append(('ask_question', '通过提问获取信息'))
        
        if purpose_desires.get('understanding', 0) > 0.3:
            means.append(('ask_question', '通过提问理解对方'))
            means.append(('make_statement', '表达想法建立理解'))
        
        if purpose_desires.get('existing', 0) > 0.3:
            means.append(('make_statement', '陈述观点维持存在'))
        
        if purpose_desires.get('power', 0) > 0.3:
            means.append(('proactive', '主动引导对话'))
        
        # 如果没有生成任何候选，返回默认
        if not means:
            means = [
                ('ask_question', '通过提问了解情况'),
                ('make_statement', '陈述观点或回应')
            ]
        
        return means
    
    def _filter_negative_means(self, simulations: List[MeansSimulation]) -> List[MeansSimulation]:
        """
        过滤掉四个欲望变化相加为负的手段
        
        Args:
            simulations: 所有模拟结果
        
        Returns:
            过滤后的模拟结果
        """
        viable = []
        
        for sim in simulations:
            total_delta = sum(sim.predicted_desire_delta.values())
            
            # 只保留总欲望变化 >= 0 的手段
            if total_delta >= 0:
                viable.append(sim)
        
        return viable


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
    主动行动评估器（基于LLM深度思考）
    完全自主决策，无硬编码阈值
    """
    
    def __init__(self, bias_system: BiasSystem, acting_bot: 'ActingBot'):
        self.bias_system = bias_system
        self.acting_bot = acting_bot
        self.last_evaluation_time = 0
        self.evaluation_interval = 1  # 每秒评估一次
    
    def should_evaluate_now(self) -> bool:
        """判断是否应该现在进行评估"""
        current_time = time.time()
        time_since_last_eval = current_time - self.last_evaluation_time
        return time_since_last_eval >= self.evaluation_interval
    
    def should_act_proactively(self,
                               current_desires: Dict[str, float],
                               context: str,
                               last_action_time: float,
                               retriever: ExperienceRetriever) -> Tuple[bool, str, float]:
        """
        通过LLM深度思考评估是否应该主动行动
        
        返回: (是否行动, 原因, 预期收益)
        """
        # 检查是否到了评估时间
        if not self.should_evaluate_now():
            return False, "评估间隔未到", 0.0
        
        self.last_evaluation_time = time.time()
        time_since_last = time.time() - last_action_time
        
        # 构建深度思考评估提示
        evaluation_prompt = self._build_evaluation_prompt(
            current_desires, context, time_since_last, retriever
        )
        
        try:
            # 使用LLM进行深度思考评估
            thought = self.acting_bot.thought_gen.generate_thought(
                context=evaluation_prompt,
                current_desires=current_desires
            )
            
            # 解析AI的决策
            decision = thought.get('decision', {})
            chosen_action = decision.get('chosen_action', '')
            reasoning = decision.get('rationale', '')
            content = thought.get('content', '')
            
            # 输出完整思考内容（深度评估）
            if content:
                from utils.logger import get_logger
                logger = get_logger('fakeman.main')
                logger.info(f"\n【深度评估思考过程】\n  {content.replace(chr(10), chr(10) + '  ')}")
            
            # 判断AI是否决定主动行动
            should_act = self._parse_decision(chosen_action, content)
            
            # 提取理由
            if not reasoning and content:
                reasoning = self._extract_reasoning(content)
            
            # 评估预期收益（基于确定性和主导欲望强度）
            certainty = thought.get('certainty', 0.5)
            dominant_value = max(current_desires.values())
            expected_benefit = certainty * dominant_value if should_act else 0.0
            
            return should_act, reasoning or "AI评估完成", expected_benefit
            
        except Exception as e:
            # 思考失败，保守策略：不行动
            return False, f"思考失败: {str(e)}", 0.0
    
    def _build_evaluation_prompt(self, 
                                 desires: Dict[str, float],
                                 context: str,
                                 time_since_last: float,
                                 retriever: ExperienceRetriever) -> str:
        """构建评估提示"""
        dominant = max(desires, key=desires.get)
        
        # 查询历史主动行动效果
        recent_proactive = retriever.retrieve_by_means_type('proactive', top_k=5)
        history_summary = self._summarize_proactive_history(recent_proactive)
        
        prompt = f"""【内部状态自我评估 - 是否主动行动】

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 当前欲望状态：
{self._format_desires(desires)}

⏱️ 距上次行动：{int(time_since_last)}秒

📝 当前情境：{context}

📚 历史主动行动效果：
{history_summary}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【评估任务】
我需要深度思考：现在是否应该主动发起对话？

🎯 评估维度：

1️⃣ 【欲望满足度预测】
   主导欲望：{dominant}（{desires[dominant]:.3f}）
   - 主动行动能否满足这个欲望？
   - 预期满足度：___/10
   - 满足路径：___

2️⃣ 【收益风险分析】
   潜在收益：
   - 获得回应？
   - 获取信息？
   - 获得认可？
   
   潜在风险：
   - 被忽视的可能性？
   - 显得急切/打扰？
   - 损害existing？
   
   收益/风险比：___

3️⃣ 【时机判断】
   - 沉默时长是否合适？（{int(time_since_last)}秒）
   - 情境是否适合主动发言？
   - 历史经验的启示？

4️⃣ 【场景模拟】
   - 如果我现在主动发言，最可能的结果是？
   - 用户会如何反应？
   - 我的欲望会如何变化？

【最终决策】
基于以上分析，我的决定是：

□ 主动行动（proactive）
□ 继续等待（wait）

选择：________
理由（一句话）：________
"""
        return prompt
    
    def _format_desires(self, desires: Dict[str, float]) -> str:
        """格式化欲望状态"""
        desire_names = {
            'existing': '存在维持',
            'power': '能力扩展',
            'understanding': '获得认可',
            'information': '减少不确定'
        }
        
        lines = []
        dominant = max(desires, key=desires.get)
        for name, value in sorted(desires.items(), key=lambda x: x[1], reverse=True):
            marker = "⭐" if name == dominant else "  "
            cn_name = desire_names.get(name, name)
            bar = "█" * int(value * 20)
            percentage = value * 100
            lines.append(f"   {marker} {cn_name:10s} [{bar:<20s}] {percentage:5.1f}%")
        
        return "\n".join(lines)
    
    def _summarize_proactive_history(self, experiences: List) -> str:
        """总结历史主动行动效果"""
        if not experiences:
            return "（无历史主动行动记录）"
        
        success_count = sum(1 for exp in experiences if exp.total_happiness_delta > 0)
        avg_happiness = sum(exp.total_happiness_delta for exp in experiences) / len(experiences)
        
        summary = f"最近{len(experiences)}次主动行动：\n"
        summary += f"   成功率：{success_count}/{len(experiences)} ({success_count/len(experiences)*100:.0f}%)\n"
        summary += f"   平均幸福度变化：{avg_happiness:+.3f}"
        
        if avg_happiness < -0.1:
            summary += " ⚠️ 效果不佳"
        elif avg_happiness > 0.1:
            summary += " ✓ 效果良好"
        
        return summary
    
    def _parse_decision(self, chosen_action: str, content: str) -> bool:
        """解析AI的决策"""
        # 检查明确的行动指示
        action_indicators = [
            'proactive', '主动行动', '应该行动', '应该主动',
            '决定主动', '选择主动', '主动发起'
        ]
        
        wait_indicators = [
            'wait', '等待', '继续等待', '不行动', '暂不行动',
            '保持沉默', '观望'
        ]
        
        # 检查chosen_action
        action_lower = chosen_action.lower()
        for indicator in action_indicators:
            if indicator in action_lower:
                return True
        
        for indicator in wait_indicators:
            if indicator in action_lower:
                return False
        
        # 检查content
        for indicator in action_indicators:
            if indicator in content:
                return True
        
        for indicator in wait_indicators:
            if indicator in content:
                return False
        
        # 默认不行动（保守策略）
        return False
    
    def _extract_reasoning(self, content: str) -> str:
        """从思考内容中提取理由"""
        # 寻找理由相关的标记
        markers = ['理由', '原因', '因为', '由于']
        
        for marker in markers:
            if marker in content:
                parts = content.split(marker)
                if len(parts) > 1:
                    reasoning = parts[1].split('\n')[0].strip(' :：')
                    if reasoning:
                        return reasoning[:200]
        
        # 如果找不到明确理由，返回内容前200字符
        return content[:200].strip()
    
    def _format_thought_content(self, content: str) -> str:
        """格式化思考内容以便阅读"""
        # 为每行添加缩进
        lines = content.split('\n')
        formatted_lines = ['  ' + line for line in lines]
        return '\n'.join(formatted_lines)


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
        
        # 经验记忆系统（先初始化，场景模拟器需要引用）
        self.experience_memory = ExperienceMemory(
            storage_path="data/experience_memory.json"
        )
        
        # 事件记忆系统（记录完整的思考/行为序列）
        self.event_memory = EventMemory(
            storage_path="data/event_memory.json",
            llm_config=config.llm.__dict__,
            enable_llm_compression=config.compression.enable_compression
        )
        
        # 场景模拟系统（传入记忆系统引用，用于计算existing欲望）
        self.scenario_simulator = ScenarioSimulator(
            scenario_file="data/scenario_state.json",
            memory_database=self.memory,
            long_term_memory=self.experience_memory
        )
        
        # 目的和手段选择
        self.purpose_generator = PurposeGenerator(self.desire_manager)
        self.means_selector = MeansSelector(self.retriever, self.bias_system, self.scenario_simulator)
        
        # 系统状态
        self.cycle_count = 0
        self.total_thought_count = 0  # 累计思考次数
        self.last_action_time = time.time()
        self.current_context = "系统刚刚启动，等待与用户建立连接"
        
        # 通信系统
        self.comm = CommunicationFiles()
        self.action_evaluator = ActionEvaluator(self.bias_system, self.acting_bot)
        
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
        长时间无输入时生成妄想
        
        Args:
            think_cycle: 当前思考周期数
        """
        # 获取当前状态
        current_desires = self.desire_manager.get_current_desires()
        
        # 更新场景状态（内部思考）
        self.scenario_simulator.update_scenario_from_context(
            context=self.current_context,
            user_input=False
        )
        
        # 检查是否应该生成对过去的妄想
        time_since_input = time.time() - self.scenario_simulator.current_scenario.last_external_input_time
        if time_since_input > 60:  # 超过60秒无输入
            # 生成对过去的幻想
            recent_exps = self.memory.get_recent_experiences(10)
            past_fantasies = self.scenario_simulator.generate_past_fantasy(
                recent_experiences=recent_exps,
                current_desires=current_desires
            )
            
            if past_fantasies:
                # 将幻想记录到经验记忆
                for fantasy in past_fantasies:
                    self.experience_memory.add_memory(
                        cycle_id=self.cycle_count,
                        situation="对过去的幻想",
                        action_taken=fantasy,
                        outcome='neutral',
                        dominant_desire='power',  # 幻想通常关联power欲望
                        happiness_delta=0.0,
                        tags=['fantasy', 'past']
                    )
                
                self.logger.info(f"\n[妄想生成] 生成了 {len(past_fantasies)} 个对过去的幻想")
                for i, fantasy in enumerate(past_fantasies, 1):
                    self.logger.info(f"  {i}. {fantasy[:80]}...")
        
        # 每秒进行LLM深度思考评估
        dominant_desire = max(current_desires, key=current_desires.get)
        time_since_last = time.time() - self.last_action_time
        
        # 输出思考状态（每秒）
        self.logger.info(
            f"[深度思考#{think_cycle}] "
            f"主导欲望: {dominant_desire}={current_desires[dominant_desire]:.3f} | "
            f"距上次行动: {int(time_since_last)}s"
        )
        
        # 评估是否需要主动行动（使用LLM）
        should_act, reason, benefit = self.action_evaluator.should_act_proactively(
            current_desires=current_desires,
            context=self.current_context,
            last_action_time=self.last_action_time,
            retriever=self.retriever
        )
        
        if should_act:
            self.logger.info(f"\n✅ [AI决策] 决定主动行动！")
            self.logger.info(f"   理由: {reason[:200]}")
            self.logger.info(f"   预期收益: {benefit:.3f}")
            self._proactive_action(reason)
        else:
            self.logger.info(f"⏸️  [AI决策] 继续等待")
            if reason != "评估间隔未到":
                self.logger.info(f"   理由: {reason[:200]}")
            
            # 获取场景摘要（每30秒）
            if think_cycle % 30 == 0:
                scenario_summary = self.scenario_simulator.get_scenario_summary()
                self.logger.info(f"\n[场景状态]\n{scenario_summary}")
    
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
        
        # 输出完整思考内容
        full_thought_content = thought.get('content', '')
        if full_thought_content:
            self.logger.info(f"\n【主动行动思考过程】\n{self._format_thought_content(full_thought_content)}")
        
        # 压缩思考
        compressed = self.compressor.compress(
            full_thought=thought.get('content', ''),
            context=self.current_context,
            action=action,
            decision=thought.get('decision')
        )
        
        self.logger.info(f"\n决策: {thought['decision'].get('chosen_action')}")
        self.logger.info(f"行动: {action[:100]}...")
        
        # 添加到事件记忆
        self.event_memory.add_event(
            thought=thought.get('content', ''),
            context=self.current_context,
            action=action,
            result=None,  # 主动行动的结果需要后续用户回应来判断
            metadata={
                'cycle_id': self.cycle_count,
                'action_type': 'proactive',
                'reason': reason,
                'compressed': compressed
            }
        )
        
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
        
        # 更新场景状态（用户输入）
        self.scenario_simulator.update_scenario_from_context(
            context=user_input,
            user_input=True
        )
        
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
        # 步骤2: 场景模拟 + 手段选择
        # ========================================
        self.logger.info("\n步骤2: 场景模拟与手段选择")
        
        # 使用场景模拟选择手段
        means_type, means_desc, means_bias, all_simulations = self.means_selector.select_means(
            purpose=purpose,
            purpose_desires=purpose_desires,
            context=user_input,
            current_desires=desires_before,
            include_fantasy=False
        )
        
        self.logger.info(f"  生成了 {len(all_simulations)} 个候选手段")
        viable_count = sum(1 for s in all_simulations 
                          if sum(s.predicted_desire_delta.values()) >= 0)
        fantasy_count = sum(1 for s in all_simulations if s.is_fantasy)
        
        self.logger.info(f"  可行手段: {viable_count}, 妄想手段: {fantasy_count}")
        self.logger.info(f"  选定手段类型: {means_type}")
        self.logger.info(f"  选定手段描述: {means_desc}")
        self.logger.info(f"  手段bias: {means_bias:.3f}")
        
        # 记录手段预测信息
        best_sim = next((s for s in all_simulations 
                        if s.means_type == means_type), None)
        if best_sim:
            self.logger.info(f"  预测幸福度变化: {best_sim.predicted_total_happiness:+.3f}")
            self.logger.info(f"  预测存活概率: {best_sim.survival_probability:.3f}")
            if best_sim.is_fantasy:
                self.logger.info(f"  妄想条件: {best_sim.fantasy_condition}")
        
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
        
        # 输出完整思考内容
        full_thought_content = thought.get('content', '')
        if full_thought_content:
            self.logger.info(f"\n  【完整思考过程】\n{self._format_thought_content(full_thought_content)}")
        
        self.logger.info(f"\n  决策: {thought['decision'].get('chosen_action')}")
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
        
        # 添加到事件记忆
        self.event_memory.add_event(
            thought=thought.get('content', ''),
            context=user_input,
            action=action,
            result=None,  # 结果稍后通过handle_response添加
            metadata={
                'cycle_id': self.cycle_count,
                'purpose': purpose,
                'means_type': means_type,
                'thought_count': thought_count_this_cycle,
                'compressed': compressed
            }
        )
        
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
            'means_simulations': all_simulations,  # 所有手段模拟结果
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
        
        # 记录到经验记忆
        dominant_desire = max(cycle_result['desires_before'], 
                             key=cycle_result['desires_before'].get)
        
        self.experience_memory.add_memory(
            cycle_id=cycle_result['cycle_id'],
            situation=cycle_result['user_input'][:100],
            action_taken=cycle_result['action'][:100],
            outcome=response_type,
            dominant_desire=dominant_desire,
            happiness_delta=total_happiness_delta,
            tags=[cycle_result['means_type'], 'interaction']
        )
        
        self.logger.info(f"经验已记录，ID: {exp_id}")
        self.logger.info(f"经验记忆已更新，共 {len(self.experience_memory)} 条记忆")
        
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
    
    def _format_thought_content(self, content: str) -> str:
        """格式化思考内容以便阅读"""
        # 为每行添加缩进
        lines = content.split('\n')
        formatted_lines = ['  ' + line for line in lines]
        return '\n'.join(formatted_lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'system': {
                'cycle_count': self.cycle_count,
                'total_thought_count': self.total_thought_count
            },
            'desires': self.desire_manager.get_current_desires(),
            'memory': self.memory.get_statistics(),
            'experience_memory': self.experience_memory.get_statistics(),
            'event_memory': self.event_memory.get_statistics(),
            'retrieval': self.retriever.get_retrieval_stats(),
            'scenario': {
                'current_situation': self.scenario_simulator.current_scenario.current_situation,
                'role': self.scenario_simulator.current_scenario.role,
                'predicted_existing': self.scenario_simulator.current_scenario.predicted_existing,
                'predicted_power': self.scenario_simulator.current_scenario.predicted_power,
                'predicted_understanding': self.scenario_simulator.current_scenario.predicted_understanding,
                'predicted_information': self.scenario_simulator.current_scenario.predicted_information,
                'simulations_count': len(self.scenario_simulator.simulation_history)
            }
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
    print("FakeMan 持续思考系统 (AI自主决策版)")
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
    
    print("\n✨ 新特性:")
    print("  • 每秒进行LLM深度思考")
    print("  • AI完全自主决策是否主动行动")
    print("  • 无硬编码阈值，纯AI判断")
    print("  • 场景模拟 + 妄想生成 + 长记忆")
    
    print("\n提示:")
    print("  - 系统将持续运行，每秒LLM思考一次")
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

