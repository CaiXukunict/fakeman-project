
from typing import Dict, List, Optional
from .thought_generator import ThoughtGenerator
from .action_executor import ActionExecutor


class ActingBot:
    """
    Acting Bot 主类
    负责思考和行动的完整流程
    """
    
    def __init__(self, llm_config: Dict, memory_db=None):
        """
        初始化 Acting Bot
        
        Args:
            llm_config: LLM 配置
            memory_db: 记忆数据库实例（可选）
        """
        self.thought_gen = ThoughtGenerator(llm_config)
        self.action_exec = ActionExecutor(llm_config)
        self.memory = memory_db
    
    def think(self,
             context: str,
             current_desires: Dict[str, float],
             retrieve_memories: bool = True) -> Dict:
        """
        执行思考
        
        Args:
            context: 当前情境（用户输入）
            current_desires: 当前欲望状态
            retrieve_memories: 是否检索相关记忆
        
        Returns:
            思考内容字典
        """
        # 检索相关记忆
        relevant_memories = None
        if retrieve_memories and self.memory:
            try:
                relevant_memories = self._retrieve_relevant_memories(
                    context, 
                    current_desires
                )
            except Exception as e:
                print(f"记忆检索失败: {e}")
        
        # 生成思考
        thought = self.thought_gen.generate_thought(
            context=context,
            current_desires=current_desires,
            relevant_memories=relevant_memories
        )
        
        return thought
    
    def act(self,
           thought: Dict,
           current_desires: Dict[str, float]) -> str:
        """
        执行行动
        
        Args:
            thought: 思考内容
            current_desires: 当前欲望状态
        
        Returns:
            行动文本
        """
        action = self.action_exec.execute(thought, current_desires)
        return action
    
    def think_and_act(self,
                     context: str,
                     current_desires: Dict[str, float]) -> tuple[Dict, str]:
        """
        完整的思考-行动流程
        
        Args:
            context: 当前情境
            current_desires: 当前欲望状态
        
        Returns:
            (thought, action) 元组
        """
        thought = self.think(context, current_desires)
        action = self.act(thought, current_desires)
        
        return thought, action
    
    def _retrieve_relevant_memories(self,
                                    context: str,
                                    desires: Dict[str, float]) -> List[Dict]:
        """检索相关记忆"""
        if not self.memory:
            return []
        
        # 获取主导欲望
        dominant = max(desires, key=desires.get)
        
        # 从数据库查询（简化版本）
        # 实际实现需要更复杂的检索逻辑
        try:
            results = self.memory.query_by_action(context)  # 简化
            return results[:5]  # 返回最多5条
        except:
            return []
