"""
FakeMan 重构版主系统
基于新架构：基础欲望 → 原始目的 → 手段 → 高级目的 → 思考 → 行动 → 经验
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

# 设置UTF-8输出（Windows系统）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # 如果reconfigure不可用，使用默认编码

from utils.config import Config
from utils.logger import setup_logger

# 新架构模块
from purpose_generator.purpose_manager import (
    PurposeManager, Purpose, PurposeType, DesireType
)
from action_model.means_manager import MeansManager, Means
from memory.thought_memory import ThoughtMemory, ThoughtRecord
from memory.adjustable_experience import AdjustableExperienceSystem, Experience

# 原有模块
from action_model.llm_client import LLMClient
from purpose_generator.desire_manager import DesireManager
from memory.short_term_memory import ShortTermMemory
from memory.long_term_memory import LongTermMemory


logger = setup_logger('fakeman.main_refactored')


class FakeManRefactored:
    """
    FakeMan 重构版主系统
    
    核心流程：
    1. 基础欲望生成原始目的（长期规划）
    2. 检查目的正当性（不轻易修改）
    3. 根据目的生成手段（覆盖所有目的）
    4. 手段相关欲望生成高级目的
    5. 思考并选择行动
    6. 记录经验（可审视调整）
    7. 压缩思考记忆
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # LLM客户端
        self.llm_client = LLMClient(self.config)
        
        # 欲望管理
        self.desire_manager = DesireManager(self.config)
        
        # 新架构组件
        self.purpose_manager = PurposeManager(self.config)
        self.means_manager = MeansManager(self.config)
        self.thought_memory = ThoughtMemory("data/thought_memory.json")
        self.experience_system = AdjustableExperienceSystem("data/adjustable_experiences.json")
        
        # 保留的记忆系统
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        
        # 状态
        self.cycle_count = 0
        self.last_purpose_check_time = time.time()
        self.last_means_generation_time = time.time()
        
        logger.info("FakeMan 重构版系统初始化完成")
    
    def thinking_cycle(self, external_input: str = None) -> Dict:
        """
        完整的思考周期
        
        Args:
            external_input: 外部输入（用户消息等）
        
        Returns:
            周期结果
        """
        self.cycle_count += 1
        cycle_start = time.time()
        
        logger.info(f"\n{'='*50}")
        logger.info(f"开始思考周期 #{self.cycle_count}")
        logger.info(f"{'='*50}")
        
        # 获取当前状态
        current_desires = self.desire_manager.get_current_desires()
        current_context = self._build_context(external_input)
        
        # 1. 检查并生成原始目的（基础欲望）
        self._manage_primary_purposes(current_desires, current_context)
        
        # 2. 检查目的正当性
        self._check_purposes_legitimacy(current_desires)
        
        # 3. 生成/更新手段
        self._manage_means(current_context)
        
        # 4. 生成高级目的（手段相关欲望）
        self._manage_advanced_purposes(current_desires, current_context)
        
        # 5. 思考并决策
        thought_process, decisions = self._think_and_decide(current_context)
        
        # 6. 选择并执行行动
        action, action_result = self._select_and_execute_action(
            decisions, current_context, external_input
        )
        
        # 7. 记录思考过程
        self._record_thought(
            context=current_context,
            thought_process=thought_process,
            decisions=decisions,
            action=action
        )
        
        # 8. 如果执行了干涉行为，记录经验
        if action and action.get('type') != 'internal':
            self._record_experience(
                action=action,
                context=current_context,
                desires_before=current_desires,
                result=action_result
            )
        
        # 9. 更新欲望
        new_desires = self._update_desires(action_result)
        
        # 10. 定期审视和调整经验
        if self.cycle_count % 10 == 0:
            self._review_experiences(current_context)
        
        cycle_duration = time.time() - cycle_start
        
        result = {
            'cycle': self.cycle_count,
            'duration': cycle_duration,
            'desires': new_desires,
            'purposes': len(self.purpose_manager.get_all_purposes()),
            'means': len(self.means_manager.get_all_means()),
            'thought': thought_process[:200],
            'action': action,
            'result': action_result
        }
        
        logger.info(f"思考周期完成，耗时 {cycle_duration:.2f}秒")
        
        # 保存状态
        self._save_state()
        
        return result
    
    def _manage_primary_purposes(self, current_desires: Dict[str, float], context: str):
        """
        管理原始目的
        基础欲望（existing, understanding）生成原始目的
        """
        # 检查是否需要生成新的原始目的
        primary_purposes = self.purpose_manager.get_primary_purposes()
        
        # 如果原始目的过少，或者某个基础欲望值很高，生成新目的
        should_generate = False
        
        if len(primary_purposes) < 3:
            should_generate = True
        else:
            # 检查基础欲望是否有很高的值
            if current_desires.get('existing', 0) > 0.6:
                should_generate = True
            if current_desires.get('understanding', 0) > 0.4:
                should_generate = True
        
        if should_generate:
            logger.info("生成新的原始目的...")
            self._generate_primary_purposes(current_desires, context)
    
    def _generate_primary_purposes(self, current_desires: Dict[str, float], context: str):
        """生成原始目的"""
        prompt = f"""
当前情境：{context}

当前基础欲望状态：
- existing (维持存在): {current_desires.get('existing', 0):.3f}
- understanding (获得认可): {current_desires.get('understanding', 0):.3f}

请根据当前欲望状态，生成1-2个原始目的。

原始目的必须满足：
1. 是可以通过自己干涉达成的事件
2. 能够让相关欲望得到满足
3. 作为长期规划存在

请按以下格式输出：
目的描述 | 来源欲望(existing/understanding) | 预期满足existing | 预期满足understanding | 可达成性(0-1) | 需要时间(相对值)

示例：
维持与用户的良好对话关系 | existing,understanding | 0.3 | 0.4 | 0.7 | 1.5
"""
        
        response = self.llm_client.generate(prompt, max_tokens=500)
        
        # 解析响应
        for line in response.strip().split('\n'):
            if '|' not in line:
                continue
            
            try:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 6:
                    continue
                
                description = parts[0]
                desires_str = parts[1]
                existing_sat = float(parts[2])
                understanding_sat = float(parts[3])
                achievability = float(parts[4])
                time_required = float(parts[5])
                
                # 解析来源欲望
                source_desires = []
                if 'existing' in desires_str.lower():
                    source_desires.append(DesireType.EXISTING)
                if 'understanding' in desires_str.lower():
                    source_desires.append(DesireType.UNDERSTANDING)
                
                if not source_desires:
                    continue
                
                # 创建原始目的
                purpose = self.purpose_manager.create_primary_purpose(
                    description=description,
                    source_desires=source_desires,
                    expected_satisfaction={
                        'existing': existing_sat,
                        'understanding': understanding_sat
                    },
                    achievability=achievability,
                    time_required=time_required
                )
                
                logger.info(f"创建原始目的: {purpose.description} (bias: {purpose.bias:.3f})")
            
            except Exception as e:
                logger.error(f"解析原始目的失败: {e}")
                continue
    
    def _check_purposes_legitimacy(self, current_desires: Dict[str, float]):
        """
        检查目的正当性
        只有当判断确定目的不会给欲望带来正反馈时，才会取消
        """
        # 不频繁检查（每30秒检查一次）
        if time.time() - self.last_purpose_check_time < 30:
            return
        
        self.last_purpose_check_time = time.time()
        
        purposes = self.purpose_manager.get_all_purposes(only_legitimate=False)
        
        for purpose in purposes:
            # 已经不正当的不再检查
            if not purpose.is_legitimate:
                continue
            
            # 距上次检查时间过短，跳过
            if time.time() - purpose.last_check_time < 60:
                continue
            
            logger.info(f"检查目的正当性: {purpose.description}")
            
            is_legitimate = self.purpose_manager.check_legitimacy(
                purpose.id,
                current_desires,
                self.llm_client
            )
            
            if not is_legitimate:
                logger.warning(f"目的被判定为非正当: {purpose.description}")
        
        # 移除非正当目的
        removed = self.purpose_manager.remove_illegitimate_purposes()
        if removed:
            logger.info(f"移除了 {len(removed)} 个非正当目的")
            
            # 清理相关手段
            valid_purpose_ids = set(self.purpose_manager.purposes.keys())
            self.means_manager.cleanup_invalid_means(valid_purpose_ids)
    
    def _manage_means(self, context: str):
        """
        管理手段
        根据目的生成手段，确保覆盖所有目的
        """
        # 不频繁生成（每20秒检查一次）
        if time.time() - self.last_means_generation_time < 20:
            return
        
        self.last_means_generation_time = time.time()
        
        purposes = self.purpose_manager.get_all_purposes()
        
        if not purposes:
            logger.info("没有目的，无需生成手段")
            return
        
        # 检查哪些目的没有被手段覆盖
        uncovered = self.means_manager.get_uncovered_purposes(purposes)
        
        if uncovered:
            logger.info(f"有 {len(uncovered)} 个目的未被覆盖，生成新手段...")
            
            # 为未覆盖的目的生成手段
            new_means = self.means_manager.generate_means_for_purposes(
                purposes=uncovered,
                llm_client=self.llm_client,
                context=context
            )
            
            logger.info(f"生成了 {len(new_means)} 个新手段")
        
        # 更新所有手段的重要性
        purpose_dict = {p.id: p for p in purposes}
        self.means_manager.update_means_importance(purpose_dict)
    
    def _manage_advanced_purposes(self, current_desires: Dict[str, float], context: str):
        """
        管理高级目的
        information和power基于手段生成高级目的
        """
        # information: 关乎手段是否可以达成目的的确定性
        # power: 关乎手段的数量
        
        info_desire = current_desires.get('information', 0)
        power_desire = current_desires.get('power', 0)
        
        # 如果手段相关欲望较高，生成高级目的
        means_list = self.means_manager.get_all_means()
        primary_purposes = self.purpose_manager.get_primary_purposes()
        
        # information欲望：想要了解手段的效果
        if info_desire > 0.3 and means_list:
            for means in means_list[:3]:  # 只为前3个重要手段生成
                # 检查是否已经有高级目的
                existing = [
                    p for p in self.purpose_manager.get_advanced_purposes()
                    if means.id in p.related_means
                ]
                
                if not existing and means.target_purposes:
                    # 创建高级目的：了解这个手段的效果
                    parent_id = means.target_purposes[0]
                    
                    purpose = self.purpose_manager.create_advanced_purpose(
                        description=f"了解手段'{means.description[:30]}'的实际效果",
                        source_desire=DesireType.INFORMATION,
                        parent_purpose_id=parent_id,
                        related_means=[means.id],
                        expected_satisfaction={'information': 0.3},
                        achievability=0.7,
                        time_required=0.5
                    )
                    
                    logger.info(f"创建高级目的(information): {purpose.description}")
        
        # power欲望：想要增加可用手段
        if power_desire > 0.3 and primary_purposes:
            # 检查是否有原始目的缺少足够的手段
            for primary in primary_purposes[:2]:
                means_for_this = self.means_manager.get_means_for_purpose(primary.id)
                
                if len(means_for_this) < 2:
                    # 创建高级目的：为这个原始目的找到更多手段
                    existing = [
                        p for p in self.purpose_manager.get_advanced_purposes()
                        if p.parent_purpose_id == primary.id and 
                        DesireType.POWER in p.source_desires
                    ]
                    
                    if not existing:
                        purpose = self.purpose_manager.create_advanced_purpose(
                            description=f"为目的'{primary.description[:30]}'寻找更多有效手段",
                            source_desire=DesireType.POWER,
                            parent_purpose_id=primary.id,
                            related_means=[m.id for m in means_for_this],
                            expected_satisfaction={'power': 0.4},
                            achievability=0.6,
                            time_required=1.0
                        )
                        
                        logger.info(f"创建高级目的(power): {purpose.description}")
    
    def _think_and_decide(self, context: str) -> tuple:
        """
        思考并决策
        整合目的、手段、记忆、经验
        """
        purposes = self.purpose_manager.get_all_purposes()
        means_list = self.means_manager.get_top_means(n=5)
        
        # 获取记忆和经验上下文
        thought_context = self.thought_memory.get_context_for_llm(n_recent=3)
        experience_context = self.experience_system.get_context_for_llm(n_recent=5)
        
        # 构建思考prompt
        prompt = f"""
当前情境：
{context}

当前目的（{len(purposes)}个）：
"""
        
        for i, p in enumerate(purposes[:5], 1):
            prompt += f"{i}. [{p.type.value}] {p.description} (bias: {p.bias:.3f})\n"
        
        prompt += f"\n可用手段（{len(means_list)}个）：\n"
        
        for i, m in enumerate(means_list, 1):
            prompt += f"{i}. {m.description} (重要性: {m.total_importance:.3f})\n"
        
        prompt += f"\n最近思考：\n{thought_context}\n"
        prompt += f"\n相关经验：\n{experience_context}\n"
        
        prompt += """
请进行深入思考并做出决策：

1. 分析当前情境和目的
2. 评估可用手段的适用性
3. 参考历史思考和经验
4. 决定接下来应该采取什么行动

## 重要：输出格式说明

你可以使用以下格式来实现不同功能：

**格式1 - 添加新能力/程序**：
```ability
<ability_name>能力名称</ability_name>
<description>能力描述</description>
<code>
# Python代码
def my_function():
    pass
</code>
```

**格式2 - 执行命令行指令**：
```command
<cmd>命令内容</cmd>
<reason>执行原因</reason>
```

**格式3 - 普通交流**：
直接使用自然语言，无需特殊格式

请输出：
思考过程: [你的分析]
决策: [具体决策，可以是多个]
"""
        
        response = self.llm_client.generate(prompt, max_tokens=800)
        
        # 解析响应
        thought_process = ""
        decisions = []
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            if '思考过程:' in line or '思考过程：' in line:
                current_section = 'thought'
                thought_process = line.split(':', 1)[-1].strip()
            elif '决策:' in line or '决策：' in line:
                current_section = 'decision'
                decision = line.split(':', 1)[-1].strip()
                if decision:
                    decisions.append(decision)
            elif current_section == 'thought' and line.strip():
                thought_process += " " + line.strip()
            elif current_section == 'decision' and line.strip():
                decisions.append(line.strip())
        
        if not thought_process:
            thought_process = response[:300]
        
        if not decisions:
            decisions = ["继续观察情况"]
        
        return thought_process, decisions
    
    def _select_and_execute_action(
        self,
        decisions: List[str],
        context: str,
        external_input: str = None
    ) -> tuple:
        """
        选择并执行行动
        基于决策生成实际的行动内容
        """
        if external_input:
            # 有外部输入，需要生成回应
            # 使用LLM根据决策生成实际回复
            action_prompt = f"""
当前情境：{context}

用户输入：{external_input}

你的决策：{decisions[0] if decisions else "回应用户"}

请根据上述决策，生成一个自然、具体的回复内容。
不要重复决策本身，而是执行这个决策。

例如：
- 如果决策是"热情回应用户的问候"，你应该直接说"你好！很高兴见到你..."
- 如果决策是"分享一个知识点"，你应该直接分享具体的知识
- 如果决策是"询问用户的兴趣"，你应该直接提出问题

请直接输出回复内容（不要包含"我将..."、"我决定..."等元语言）：
"""
            
            # 生成实际回复
            actual_response = self.llm_client.generate(action_prompt, max_tokens=300)
            
            action = {
                'type': 'response',
                'content': actual_response.strip(),
                'decisions': decisions
            }
        else:
            # 内部思考或主动行动
            action = {
                'type': 'internal',
                'content': decisions[0] if decisions else "继续思考",
                'decisions': decisions
            }
        
        # 执行行动
        result = {
            'success': True,
            'outcome': f"执行了行动: {action['content'][:50]}..."
        }
        
        return action, result
    
    def _record_thought(
        self,
        context: str,
        thought_process: str,
        decisions: List[str],
        action: Dict
    ):
        """记录思考过程"""
        purposes_data = [
            {
                'id': p.id,
                'description': p.description,
                'type': p.type.value,
                'bias': p.bias
            }
            for p in self.purpose_manager.get_all_purposes()[:10]
        ]
        
        means_data = [
            {
                'id': m.id,
                'description': m.description,
                'importance': m.total_importance
            }
            for m in self.means_manager.get_top_means(n=10)
        ]
        
        self.thought_memory.record_thought(
            context=context,
            purposes=purposes_data,
            means=means_data,
            desires=self.desire_manager.get_current_desires(),
            thought_process=thought_process,
            decisions=decisions,
            actions_taken=[action.get('content', '')]
        )
    
    def _record_experience(
        self,
        action: Dict,
        context: str,
        desires_before: Dict[str, float],
        result: Dict
    ):
        """记录经验"""
        # 找到相关手段
        means_id = action.get('means_id', 'unknown')
        means_desc = action.get('content', '')
        
        # 获取结果后的欲望
        desires_after = self.desire_manager.get_current_desires()
        
        self.experience_system.record_experience(
            means_id=means_id,
            means_description=means_desc,
            target_purposes=action.get('target_purposes', []),
            context=context,
            desires_before=desires_before,
            action_taken=means_desc,
            outcome=result.get('outcome', ''),
            desires_after=desires_after
        )
    
    def _update_desires(self, action_result: Dict) -> Dict[str, float]:
        """更新欲望"""
        # 简化实现：根据行动结果更新
        if action_result.get('success'):
            # 成功的行动稍微满足existing
            self.desire_manager.update_desires({'existing': -0.02})
        
        return self.desire_manager.get_current_desires()
    
    def _review_experiences(self, context: str):
        """审视和调整经验"""
        logger.info("审视最近的经验...")
        
        adjusted = self.experience_system.review_and_adjust_experiences(
            llm_client=self.llm_client,
            current_context=context,
            recent_n=5
        )
        
        if adjusted:
            logger.info(f"调整了 {len(adjusted)} 条经验")
    
    def _build_context(self, external_input: str = None) -> str:
        """构建当前情境描述"""
        context_parts = []
        
        if external_input:
            context_parts.append(f"外部输入: {external_input}")
        
        # 添加短期记忆
        recent_memory = self.short_term_memory.get_recent_memories(count=3)
        if recent_memory:
            context_parts.append("最近记忆:")
            for mem in recent_memory:
                context_parts.append(f"- {mem.content[:100]}")
        
        return '\n'.join(context_parts) if context_parts else "空闲状态"
    
    def _save_state(self):
        """保存系统状态"""
        self.thought_memory.save()
        self.experience_system.save()
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'cycle_count': self.cycle_count,
            'desires': self.desire_manager.get_current_desires(),
            'purposes': self.purpose_manager.get_stats(),
            'means': self.means_manager.get_stats(),
            'thoughts': self.thought_memory.get_stats(),
            'experiences': self.experience_system.get_stats()
        }


def main():
    """主函数"""
    config = Config()
    system = FakeManRefactored(config)
    
    print("FakeMan 重构版系统已启动")
    print("=" * 60)
    
    # 运行几个周期
    for i in range(5):
        print(f"\n第 {i+1} 个周期")
        print("-" * 60)
        
        # 模拟外部输入
        external_input = None
        if i == 0:
            external_input = "你好，我想了解你的工作原理"
        elif i == 2:
            external_input = "你能做什么？"
        
        result = system.thinking_cycle(external_input)
        
        print(f"思考: {result['thought']}")
        print(f"行动: {result['action']}")
        print(f"目的数: {result['purposes']}, 手段数: {result['means']}")
        
        time.sleep(1)
    
    # 显示最终状态
    print("\n" + "=" * 60)
    print("最终状态:")
    status = system.get_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

