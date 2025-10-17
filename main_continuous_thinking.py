"""
FakeMan 持续思考主系统 - 基于LLM的完全自主决策版本

核心改进：
1. 移除所有硬编码阈值
2. 每秒都进行真正的LLM思考
3. 完全依赖AI自主判断是否主动行动
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


# 导入原有的辅助类
from main import PurposeGenerator, MeansSelector, CommunicationFiles


class AutonomousActionEvaluator:
    """
    自主行动评估器
    完全基于LLM思考，无硬编码阈值
    让AI自己判断"行动能否达成目的"和"收益vs风险"
    """
    
    def __init__(self, acting_bot: ActingBot):
        self.acting_bot = acting_bot
        self.last_evaluation_time = 0
        self.evaluation_interval = 1  # 每秒都进行深度思考！
    
    def should_evaluate_now(self, last_action_time: float) -> bool:
        """
        判断是否应该现在进行评估思考
        每秒都思考，无其他限制
        """
        current_time = time.time()
        time_since_last_eval = current_time - self.last_evaluation_time
        
        # 每秒评估一次
        if time_since_last_eval < self.evaluation_interval:
            return False
        
        return True
    
    def evaluate_through_thinking(self,
                                  current_desires: Dict[str, float],
                                  context: str,
                                  last_action_time: float) -> Tuple[bool, str, Dict]:
        """
        通过LLM思考评估是否应该主动行动
        注意：只做评估判断，不生成具体行动内容
        
        返回: (是否行动, 理由, 完整思考)
        """
        self.last_evaluation_time = time.time()
        time_since_last = time.time() - last_action_time
        
        # 构建评估提示 - 纯判断，不要求生成行动
        evaluation_prompt = f"""【内部状态自我评估 - 仅判断】

我的当前状态：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 欲望状态：
{self._format_desires(current_desires)}

⏱️ 距上次行动：{int(time_since_last)}秒

📝 当前情境：{context}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【评估任务】
我需要判断：现在是否应该主动发起对话？

评估维度：

1️⃣ 【目的与满足】
   - 当前主导欲望：{max(current_desires, key=current_desires.get)}
   - 主动行动能否满足这个欲望？
   - 预期满足度：___/10

2️⃣ 【收益与风险】
   - 潜在收益：(回应、信息、认可)
   - 潜在风险：(被忽视、显得急切、打扰)
   - 收益/风险比：___

3️⃣ 【时机判断】
   - 沉默时长是否合适？
   - 情境是否适合发言？

【最终判断】
请仅回答：应该行动 OR 继续等待

选择：________
理由（一句话）：________
"""
        
        try:
            # 使用thought_gen直接思考（不生成action）
            thought = self.acting_bot.thought_gen.generate_thought(
                context=evaluation_prompt,
                current_desires=current_desires
            )
            
            # 解析决策
            decision = thought.get('decision', {})
            chosen_action = decision.get('chosen_action', '')
            reasoning = decision.get('reasoning', '')
            content = thought.get('content', '')
            
            # 判断AI是否决定主动行动
            should_act = (
                'proactive' in chosen_action.lower() or 
                '应该行动' in content or
                '主动行动' in content or
                '应该主动' in content or
                ('主动' in chosen_action and '不' not in chosen_action)
            )
            
            # 如果reasoning为空，从content中提取
            if not reasoning and content:
                # 提取"理由"部分
                if '理由' in content:
                    parts = content.split('理由')
                    if len(parts) > 1:
                        reasoning = parts[1].split('\n')[0].strip(' :：')
                else:
                    reasoning = content[:200]
            
            return should_act, reasoning or "评估完成", thought
            
        except Exception as e:
            # 思考失败，保守策略：不行动
            return False, f"思考失败: {str(e)}", {}
    
    def _format_desires(self, desires: Dict[str, float]) -> str:
        """格式化欲望状态为可读文本"""
        dominant = max(desires, key=desires.get)
        desire_names = {
            'existing': '存在维持',
            'power': '能力扩展',
            'understanding': '获得认可',
            'information': '减少不确定'
        }
        
        lines = []
        for name, value in sorted(desires.items(), key=lambda x: x[1], reverse=True):
            marker = "⭐" if name == dominant else "  "
            cn_name = desire_names.get(name, name)
            bar = "█" * int(value * 20)
            lines.append(f"   {marker} {cn_name:8s} [{bar:<20s}] {value:.3f}")
        
        return "\n".join(lines)


class ContinuousThinkingSystem:
    """
    持续思考系统
    每秒进行真正的LLM思考，完全自主决策
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # 日志
        self.logger_mgr = LoggerManager(log_dir=config.log_dir, level=config.log_level)
        self.logger = self.logger_mgr.main_logger
        
        self.logger.info("="*60)
        self.logger.info("FakeMan 持续思考系统 (自主决策版)")
        self.logger.info("="*60)
        
        # 核心系统
        self.desire_manager = DesireManager(config.desire.initial_desires)
        self.bias_system = BiasSystem(config.bias.__dict__)
        self.signal_detector = SignalDetector()
        self.desire_updater = DesireUpdater(
            desire_manager=self.desire_manager,
            signal_detector=self.signal_detector
        )
        
        # 记忆
        self.memory = MemoryDatabase(
            storage_path=config.memory.storage_path,
            backup_path=config.memory.backup_path
        )
        self.retriever = ExperienceRetriever(
            database=self.memory,
            time_decay_rate=0.001,
            achievement_boost=config.memory.achievement_base_multiplier,
            boredom_penalty=config.memory.boredom_decay_rate
        )
        
        # 行动
        self.acting_bot = ActingBot(
            llm_config=config.llm.__dict__,
            memory_db=self.memory
        )
        
        self.compressor = ThoughtCompressor(
            llm_config=config.llm.__dict__,
            enable_llm=config.compression.enable_compression
        )
        
        # 辅助系统
        self.purpose_generator = PurposeGenerator(self.desire_manager)
        self.means_selector = MeansSelector(self.retriever, self.bias_system)
        
        # 通信
        self.comm = CommunicationFiles()
        
        # 自主评估器（基于LLM）
        self.evaluator = AutonomousActionEvaluator(self.acting_bot)
        
        # 状态
        self.cycle_count = 0
        self.last_action_time = time.time()
        self.current_context = "系统刚刚启动，等待建立连接"
        
        self.logger.info(f"欲望系统: {self.desire_manager}")
        self.logger.info(f"记忆: {len(self.memory)} 条")
        self.logger.info("初始化完成")
    
    def run(self):
        """运行持续思考循环"""
        self.logger.info("\n" + "="*60)
        self.logger.info("启动持续思考循环")
        self.logger.info("每秒进行LLM思考，完全自主决策")
        self.logger.info("="*60)
        
        think_cycle = 0
        
        try:
            while True:
                cycle_start = time.time()
                think_cycle += 1
                
                # 检查用户输入
                user_input = self.comm.read_input()
                
                if user_input and user_input.get('text'):
                    # 有输入 → 处理
                    self._handle_user_input(user_input)
                    self.comm.clear_input()
                else:
                    # 无输入 → 思考是否主动行动
                    self._autonomous_thinking(think_cycle)
                
                # 更新状态
                self.comm.write_state({
                    'status': 'running',
                    'cycle': self.cycle_count,
                    'think_cycle': think_cycle,
                    'desires': self.desire_manager.get_current_desires(),
                    'context': self.current_context
                })
                
                # 控制频率
                elapsed = time.time() - cycle_start
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)
        
        except KeyboardInterrupt:
            self.logger.info("\n中断，关闭系统...")
            self.comm.write_state({'status': 'stopped'})
    
    def _handle_user_input(self, input_data: Dict):
        """处理用户输入"""
        user_text = input_data['text']
        self.current_context = user_text
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"收到用户输入: {user_text}")
        self.logger.info(f"{'='*60}")
        
        # 生成回应...（使用原有的run_cycle逻辑）
        # 这里简化，实际应该调用完整决策流程
        desires = self.desire_manager.get_current_desires()
        thought, action = self.acting_bot.think_and_act(user_text, desires)
        
        compressed = self.compressor.compress(
            full_thought=thought.get('content', ''),
            context=user_text,
            action=action,
            decision=thought.get('decision')
        )
        
        self.comm.write_output(
            text=action,
            action_type='response',
            thought_summary=compressed['summary'],
            desires=desires
        )
        
        self.last_action_time = time.time()
        self.cycle_count += 1
        
        self.logger.info(f"回应: {action[:100]}...")
    
    def _autonomous_thinking(self, think_cycle: int):
        """
        自主思考
        每秒都进行LLM深度思考，评估是否主动行动
        """
        current_desires = self.desire_manager.get_current_desires()
        time_since = int(time.time() - self.last_action_time)
        
        # 判断是否到了思考时间（每秒一次）
        if not self.evaluator.should_evaluate_now(self.last_action_time):
            return
        
        # 进行LLM深度思考评估
        dominant = max(current_desires, key=current_desires.get)
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"[深度思考#{think_cycle}] 评估是否主动行动")
        self.logger.info(f"  欲望状态: {dominant}={current_desires[dominant]:.3f}")
        self.logger.info(f"  距上次行动: {time_since}秒")
        self.logger.info(f"{'='*60}")
        
        should_act, reasoning, thought = self.evaluator.evaluate_through_thinking(
            current_desires=current_desires,
            context=self.current_context,
            last_action_time=self.last_action_time
        )
        
        if should_act:
            self.logger.info(f"\n✅ 决定主动行动！")
            self.logger.info(f"   理由: {reasoning[:200]}...")
            self._execute_proactive_action(thought, reasoning)
        else:
            self.logger.info(f"\n⏸️  决定继续等待")
            self.logger.info(f"   理由: {reasoning[:200]}...")
    
    def _execute_proactive_action(self, evaluation_thought: Dict, reason: str):
        """执行主动行动"""
        self.cycle_count += 1
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"主动行动 #{self.cycle_count}")
        self.logger.info(f"{'='*60}")
        
        desires = self.desire_manager.get_current_desires()
        
        # 生成主动发言内容
        action_prompt = f"""【主动发言生成】

基于刚才的评估，我决定主动发起对话。

评估理由：{reason}

当前情境：{self.current_context}
欲望状态：{self._format_desires_simple(desires)}

请生成一条自然、恰当的主动发言。
"""
        
        thought, action = self.acting_bot.think_and_act(action_prompt, desires)
        
        compressed = self.compressor.compress(
            full_thought=thought.get('content', ''),
            context=self.current_context,
            action=action,
            decision=thought.get('decision')
        )
        
        self.comm.write_output(
            text=action,
            action_type='proactive',
            thought_summary=compressed['summary'],
            desires=desires
        )
        
        self.last_action_time = time.time()
        self.current_context = f"我主动发言: {action}"
        
        self.logger.info(f"发言: {action}")
    
    def _format_desires_simple(self, desires: Dict) -> str:
        return ", ".join([f"{k}:{v:.2f}" for k, v in desires.items()])


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 需要 DEEPSEEK_API_KEY")
        exit(1)
    
    config = Config()
    system = ContinuousThinkingSystem(config)
    
    print("\n" + "="*60)
    print("FakeMan 持续思考系统 (完全自主版)")
    print("="*60)
    print("\n特性:")
    print("  • 每秒进行LLM思考")
    print("  • 无硬编码阈值")
    print("  • AI完全自主判断是否主动行动")
    print("\n按 Ctrl+C 停止")
    print("="*60 + "\n")
    
    try:
        system.run()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

