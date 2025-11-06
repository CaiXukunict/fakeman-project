"""
Acting Bot 主类
整合思考生成、行动执行和记忆检索
"""

from typing import Dict, List, Optional, Tuple, Any
from .thought_generator import ThoughtGenerator
from .action_executor import ActionExecutor
from .logical_closure import check_logical_closure, calculate_thought_depth
from utils.logger import get_logger

logger = get_logger('fakeman.acting_bot')


class ActingBot:
    """
    Acting Bot 主类
    
    负责完整的思考-行动流程
    """
    
    def __init__(self, llm_config: Dict[str, Any], memory_db=None):
        """
        初始化 Acting Bot
        
        Args:
            llm_config: LLM 配置
            memory_db: 记忆数据库实例（可选）
        """
        self.thought_gen = ThoughtGenerator(llm_config)
        self.action_exec = ActionExecutor(llm_config)
        self.memory = memory_db
        
        logger.info("Acting Bot 初始化完成")
    
    def think(self,
             context: str,
             current_desires: Dict[str, float],
             retrieve_memories: bool = True,
             long_term_memories: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        执行思考
        
        Args:
            context: 当前情境（用户输入）
            current_desires: 当前欲望状态
            retrieve_memories: 是否检索相关记忆
            long_term_memories: 长期记忆（持续上下文）
        
        Returns:
            思考内容字典，包含：
                - content: 思考文本
                - decision: 决策信息
                - signals: 信号强度
                - certainty: 确定性
                - logical_closure: 逻辑闭环
                - thought_depth: 思考深度
        """
        logger.debug(f"开始思考，情境: {context[:50]}...")
        
        # 检索相关记忆
        relevant_memories = None
        if retrieve_memories and self.memory:
            try:
                relevant_memories = self._retrieve_relevant_memories(
                    context, 
                    current_desires
                )
            except Exception as e:
                logger.warning(f"记忆检索失败: {e}")
        
        # 生成思考
        thought = self.thought_gen.generate_thought(
            context=context,
            current_desires=current_desires,
            relevant_memories=relevant_memories,
            long_term_memories=long_term_memories
        )
        
        # 判定逻辑闭环
        thought['logical_closure'] = check_logical_closure(thought)
        
        # 计算思考深度
        thought['thought_depth'] = calculate_thought_depth(thought)
        
        logger.info(f"思考完成，决策: {thought['decision'].get('chosen_action')}, "
                   f"闭环: {thought['logical_closure']}, 深度: {thought['thought_depth']:.2f}")
        
        return thought
    
    def act(self,
           thought: Dict[str, Any],
           current_desires: Dict[str, float]) -> str:
        """
        执行行动
        
        Args:
            thought: 思考内容
            current_desires: 当前欲望状态
        
        Returns:
            行动文本
        """
        logger.debug("执行行动")
        
        action = self.action_exec.execute(thought, current_desires)
        
        logger.info(f"行动完成: {action[:50]}...")
        
        return action
    
    def think_and_act(self,
                     context: str,
                     current_desires: Dict[str, float],
                     long_term_memories: Optional[List[Dict]] = None) -> Tuple[Dict[str, Any], str]:
        """
        完整的思考-行动流程
        
        Args:
            context: 当前情境
            current_desires: 当前欲望状态
            long_term_memories: 长期记忆（持续上下文）
        
        Returns:
            (thought, action) 元组
        """
        thought = self.think(context, current_desires, long_term_memories=long_term_memories)
        action = self.act(thought, current_desires)
        
        return thought, action
    
    def _retrieve_relevant_memories(self,
                                    context: str,
                                    desires: Dict[str, float]) -> List[Dict]:
        """
        检索相关记忆
        
        Args:
            context: 当前情境
            desires: 当前欲望
        
        Returns:
            相关记忆列表
        """
        if not self.memory:
            return []
        
        try:
            # 使用记忆系统的检索功能
            from memory.retrieval import ExperienceRetriever
            
            # 创建检索器（如果还没有）
            if not hasattr(self, 'retriever'):
                self.retriever = ExperienceRetriever(self.memory)
            
            # 检索相似经验
            # 注意：这里简化了，实际需要提取目的
            # 在main.py中会有更完整的目的生成逻辑
            
            # 获取主导欲望
            dominant_desire = max(desires, key=desires.get)
            
            # 简单地根据主导欲望构建目的
            purpose_desires = {dominant_desire: 1.0}
            
            experiences = self.retriever.retrieve_similar_experiences(
                context=context,
                purpose="当前情境处理",  # 简化的目的
                purpose_desires=purpose_desires,
                top_k=5
            )
            
            # 转换为字典格式
            memories = []
            for exp in experiences:
                memories.append({
                    'thought_summary': exp.thought_summary,
                    'means': exp.means,
                    'total_happiness_delta': exp.total_happiness_delta,
                    'purpose_achieved': exp.purpose_achieved
                })
            
            return memories
            
        except Exception as e:
            logger.error(f"记忆检索出错: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'thought_generator': self.thought_gen.get_stats(),
            'action_executor': self.action_exec.get_stats()
        }
    
    def __repr__(self) -> str:
        return f"ActingBot(memory={'enabled' if self.memory else 'disabled'})"


if __name__ == '__main__':
    # 测试 Acting Bot
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if os.getenv('DEEPSEEK_API_KEY'):
        config = {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
            'temperature': 0.7,
            'max_tokens': 1500
        }
        
        bot = ActingBot(config)
        
        # 测试完整流程
        context = "用户：你觉得人工智能最大的挑战是什么？"
        desires = {
            'existing': 0.35,
            'power': 0.20,
            'understanding': 0.30,
            'information': 0.15
        }
        
        print("开始测试 Acting Bot...")
        print(f"情境: {context}")
        print(f"欲望: {desires}")
        print("\n" + "="*60 + "\n")
        
        thought, action = bot.think_and_act(context, desires)
        
        print("思考结果:")
        print(f"  决策: {thought['decision']}")
        print(f"  信号: {thought['signals']}")
        print(f"  确定性: {thought['certainty']}")
        print(f"  逻辑闭环: {thought['logical_closure']}")
        print(f"  思考深度: {thought['thought_depth']:.2f}")
        
        print("\n行动输出:")
        print(f"  {action}")
        
        print("\n" + "="*60)
        print(f"统计: {bot.get_stats()}")
    else:
        print("未设置 DEEPSEEK_API_KEY，跳过测试")
