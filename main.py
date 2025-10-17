"""
FakeMan 主系统
整合所有模块，实现完整的决策循环

决策流程：
1. 欲望状态 → 生成目的
2. 目的 + 记忆 → 选择手段
3. 手段 → 思考 → 行动
4. 环境响应 → 更新欲望 → 记录经验
"""

import time
from typing import Dict, List, Any, Optional, Tuple
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


class FakeManSystem:
    """
    FakeMan 主系统
    
    整合所有子系统，实现完整的决策循环
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
        
        self.logger.info(f"欲望系统初始化: {self.desire_manager}")
        self.logger.info(f"记忆系统初始化: {len(self.memory)} 条经验")
        self.logger.info("FakeMan 系统初始化完成")
    
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
    # 测试主系统
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("请设置 DEEPSEEK_API_KEY 环境变量")
        exit(1)
    
    # 创建配置
    config = Config()
    
    # 创建系统
    print("初始化 FakeMan 系统...")
    system = FakeManSystem(config)
    
    print(f"\n{system}")
    print(f"当前欲望: {system.desire_manager.get_current_desires()}\n")
    
    # 运行一个周期
    print("="*60)
    print("测试决策周期")
    print("="*60)
    
    result = system.run_cycle("你好，你能帮我了解一下人工智能吗？")
    
    print(f"\n行动输出: {result['action']}")
    
    # 模拟响应
    print("\n"+"="*60)
    print("模拟环境响应")
    print("="*60)
    
    exp = system.handle_response(
        cycle_result=result,
        response="当然可以，我很感兴趣！",
        response_type='positive'
    )
    
    print(f"\n经验已记录: {exp}")
    print(f"\n更新后的欲望: {system.desire_manager.get_current_desires()}")
    
    # 统计信息
    print("\n"+"="*60)
    print("系统统计")
    print("="*60)
    stats = system.get_stats()
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))

