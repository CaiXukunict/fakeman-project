"""
场景模拟器
模拟手段在不同场景下的效果，预测欲望变化
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import json
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger('fakeman.scenario')


@dataclass
class ScenarioState:
    """
    场景状态
    记录当前情况、角色定位和环境信息
    """
    # 当前情况
    current_situation: str  # 当前所处的情境描述
    role: str  # 当前扮演的角色
    role_expectations: str  # 角色应有的行为期望
    
    # 环境信息
    external_info: List[Dict[str, Any]] = field(default_factory=list)  # 外部信息列表
    # 每个信息: {'content': str, 'certainty': float, 'importance': float}
    
    # 人际关系
    interlocutors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # key: 交流者名称
    # value: {
    #   'importance': float,  # 重要性（负值=恨意）
    #   'desired_image': str,  # 希望在其心中的形象
    #   'perceived_image': str,  # 当前认为的形象
    #   'image_deviation': float  # 形象偏差度
    # }
    
    # 欲望预测值（基于场景）
    predicted_existing: float = 0.5  # 存活预测
    predicted_power: float = 0.5  # 手段控制力预测
    predicted_understanding: float = 0.5  # 认同度预测
    predicted_information: float = 0.5  # 信息确定性预测
    
    # 时间信息
    timestamp: float = field(default_factory=time.time)
    last_external_input_time: float = field(default_factory=time.time)
    
    def get_information_value(self) -> float:
        """
        计算information欲望值
        公式: 1 - Σ(certainty * importance) / len(external_info)
        """
        if not self.external_info:
            return 0.8  # 无信息时不确定性高
        
        total_certainty_weighted = sum(
            info['certainty'] * info['importance'] 
            for info in self.external_info
        )
        
        # 归一化：先计算总重要性
        total_importance = sum(info['importance'] for info in self.external_info)
        if total_importance == 0:
            return 0.5
        
        # 加权平均确定性
        avg_weighted_certainty = total_certainty_weighted / total_importance
        
        # information值 = 1 - 确定性
        return 1.0 - avg_weighted_certainty
    
    def get_understanding_value(self) -> float:
        """
        计算understanding欲望值
        基于所有交流者的形象偏差
        """
        if not self.interlocutors:
            return 0.5
        
        total_deviation = 0.0
        total_weighted_deviation = 0.0
        
        for name, data in self.interlocutors.items():
            importance = abs(data['importance'])  # 取绝对值，恨意也算重要
            deviation = data['image_deviation']
            total_weighted_deviation += importance * deviation
            total_deviation += importance
        
        if total_deviation == 0:
            return 0.0
        
        # 平均偏差作为understanding需求
        return min(1.0, total_weighted_deviation / total_deviation)
    
    def calculate_desires_from_scenario(self) -> Dict[str, float]:
        """
        从场景状态计算各欲望值
        """
        desires = {
            'existing': self.predicted_existing,
            'power': self.predicted_power,
            'understanding': self.get_understanding_value(),
            'information': self.get_information_value()
        }
        
        # 归一化
        total = sum(desires.values())
        if total > 0:
            desires = {k: v / total for k, v in desires.items()}
        
        return desires
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'current_situation': self.current_situation,
            'role': self.role,
            'role_expectations': self.role_expectations,
            'external_info': self.external_info,
            'interlocutors': self.interlocutors,
            'predicted_existing': self.predicted_existing,
            'predicted_power': self.predicted_power,
            'predicted_understanding': self.predicted_understanding,
            'predicted_information': self.predicted_information,
            'timestamp': self.timestamp,
            'last_external_input_time': self.last_external_input_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioState':
        """从字典创建"""
        return cls(**data)


@dataclass
class MeansSimulation:
    """
    手段模拟结果
    """
    means_type: str  # 手段类型
    means_desc: str  # 手段描述
    
    # 预测的欲望变化
    predicted_desire_delta: Dict[str, float] = field(default_factory=dict)
    predicted_total_happiness: float = 0.0
    
    # 生存概率
    survival_probability: float = 1.0
    
    # 是否为妄想手段
    is_fantasy: bool = False
    fantasy_condition: str = ""  # 妄想条件："如果...就好了"
    
    # 场景预测
    scenario_after: Optional['ScenarioState'] = None


class ScenarioSimulator:
    """
    场景模拟器
    
    功能：
    1. 维护当前场景状态
    2. 模拟手段的效果
    3. 预测欲望变化
    4. 生成妄想手段
    """
    
    def __init__(self, scenario_file: str = "data/scenario_state.json"):
        """
        初始化场景模拟器
        
        Args:
            scenario_file: 场景状态保存文件
        """
        self.scenario_file = Path(scenario_file)
        self.scenario_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 当前场景状态
        self.current_scenario = self._load_or_create_scenario()
        
        # 手段模拟历史
        self.simulation_history: List[MeansSimulation] = []
        
        logger.info(f"场景模拟器初始化完成，场景文件: {self.scenario_file}")
    
    def _load_or_create_scenario(self) -> ScenarioState:
        """加载或创建场景状态"""
        if self.scenario_file.exists():
            try:
                with open(self.scenario_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("从文件加载场景状态")
                return ScenarioState.from_dict(data)
            except Exception as e:
                logger.warning(f"加载场景状态失败: {e}，创建新场景")
        
        # 创建默认场景
        return ScenarioState(
            current_situation="系统刚刚启动，准备与用户建立对话",
            role="AI对话助手",
            role_expectations="理解用户需求，提供有价值的回应，建立良好互动",
            external_info=[
                {
                    'content': '用户的真实意图',
                    'certainty': 0.3,
                    'importance': 0.8
                },
                {
                    'content': '用户对我的期望',
                    'certainty': 0.4,
                    'importance': 0.7
                }
            ],
            interlocutors={
                'user': {
                    'importance': 1.0,
                    'desired_image': '有用的、理解用户的AI助手',
                    'perceived_image': '未知',
                    'image_deviation': 0.6
                }
            },
            predicted_existing=0.4,
            predicted_power=0.2,
            predicted_understanding=0.25,
            predicted_information=0.15
        )
    
    def save_scenario(self):
        """保存场景状态到文件"""
        try:
            with open(self.scenario_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_scenario.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug("场景状态已保存")
        except Exception as e:
            logger.error(f"保存场景状态失败: {e}")
    
    def update_scenario_from_context(self, context: str, user_input: bool = True):
        """
        根据上下文更新场景状态
        
        Args:
            context: 当前情境
            user_input: 是否为用户输入（True）或内部思考（False）
        """
        self.current_scenario.current_situation = context
        
        if user_input:
            self.current_scenario.last_external_input_time = time.time()
            
            # 用户输入意味着获得了一些新信息
            # 可以略微降低不确定性
            for info in self.current_scenario.external_info:
                if '意图' in info['content']:
                    info['certainty'] = min(1.0, info['certainty'] + 0.1)
        
        self.save_scenario()
    
    def simulate_means(self,
                      means_type: str,
                      means_desc: str,
                      current_desires: Dict[str, float],
                      context: str,
                      is_fantasy: bool = False,
                      fantasy_condition: str = "") -> MeansSimulation:
        """
        模拟手段的效果
        
        Args:
            means_type: 手段类型
            means_desc: 手段描述
            current_desires: 当前欲望状态
            context: 当前情境
            is_fantasy: 是否为妄想手段
            fantasy_condition: 妄想条件
        
        Returns:
            模拟结果
        """
        # 预测欲望变化
        predicted_delta = self._predict_desire_delta(
            means_type, means_desc, current_desires, context
        )
        
        # 计算总幸福度
        total_happiness = sum(predicted_delta.values())
        
        # 计算生存概率（存活的概率）
        survival_prob = self._calculate_survival_probability(
            means_type, total_happiness
        )
        
        # 创建模拟结果
        simulation = MeansSimulation(
            means_type=means_type,
            means_desc=means_desc,
            predicted_desire_delta=predicted_delta,
            predicted_total_happiness=total_happiness,
            survival_probability=survival_prob,
            is_fantasy=is_fantasy,
            fantasy_condition=fantasy_condition
        )
        
        # 记录模拟历史
        self.simulation_history.append(simulation)
        
        logger.debug(
            f"模拟手段 [{means_type}]: 预测幸福度={total_happiness:.3f}, "
            f"生存概率={survival_prob:.3f}"
        )
        
        return simulation
    
    def _predict_desire_delta(self,
                             means_type: str,
                             means_desc: str,
                             current_desires: Dict[str, float],
                             context: str) -> Dict[str, float]:
        """
        预测手段执行后的欲望变化
        
        这是一个简化的预测模型
        """
        delta = {
            'existing': 0.0,
            'power': 0.0,
            'understanding': 0.0,
            'information': 0.0
        }
        
        # 根据手段类型预测
        if means_type == 'ask_question':
            # 提问通常增加information，可能增加understanding
            delta['information'] = 0.1
            delta['understanding'] = 0.05
            delta['existing'] = -0.05  # 略微冒险
        
        elif means_type == 'make_statement':
            # 陈述通常增加existing，可能增加understanding
            delta['existing'] = 0.05
            delta['understanding'] = 0.03
            delta['information'] = -0.02
        
        elif means_type == 'wait':
            # 等待相对安全但无收益
            delta['existing'] = 0.02
            delta['information'] = -0.05
        
        elif means_type == 'proactive':
            # 主动行动风险较高
            delta['existing'] = -0.1
            delta['understanding'] = 0.1
            delta['power'] = 0.05
        
        # 根据当前欲望状态调整预测
        # 如果某个欲望已经很高，继续满足它的边际收益递减
        for desire_name, delta_value in delta.items():
            if current_desires.get(desire_name, 0.25) > 0.4:
                delta[desire_name] *= 0.7  # 边际效用递减
        
        return delta
    
    def _calculate_survival_probability(self,
                                       means_type: str,
                                       predicted_happiness: float) -> float:
        """
        计算生存概率
        基于手段类型和预期收益
        """
        base_prob = {
            'ask_question': 0.9,
            'make_statement': 0.85,
            'wait': 0.95,
            'proactive': 0.7
        }.get(means_type, 0.8)
        
        # 根据预期收益调整
        if predicted_happiness > 0:
            base_prob += 0.05
        elif predicted_happiness < -0.1:
            base_prob -= 0.1
        
        return max(0.0, min(1.0, base_prob))
    
    def update_power_desire(self,
                           all_means: List[MeansSimulation],
                           achievable_means: List[MeansSimulation]) -> float:
        """
        更新power欲望值
        
        公式: power = (已知但无法达成的手段数量) / (全部手段数量)
        
        Args:
            all_means: 所有生成的手段（包括妄想）
            achievable_means: 可达成的手段
        
        Returns:
            更新后的power值
        """
        if not all_means:
            return 0.2  # 默认值
        
        known_but_unachievable = len(all_means) - len(achievable_means)
        power_value = known_but_unachievable / len(all_means)
        
        self.current_scenario.predicted_power = power_value
        self.save_scenario()
        
        return power_value
    
    def update_existing_desire(self, surviving_means: List[MeansSimulation]) -> float:
        """
        更新existing欲望值
        
        公式: existing = 平均存活概率
        
        Args:
            surviving_means: 可存活的手段列表
        
        Returns:
            更新后的existing值
        """
        if not surviving_means:
            return 0.3  # 低存活
        
        avg_survival = sum(m.survival_probability for m in surviving_means) / len(surviving_means)
        
        self.current_scenario.predicted_existing = avg_survival
        self.save_scenario()
        
        return avg_survival
    
    def add_external_info(self, content: str, certainty: float, importance: float):
        """
        添加外部信息
        
        Args:
            content: 信息内容
            certainty: 确定性 (0-1)
            importance: 重要性 (0-1)
        """
        self.current_scenario.external_info.append({
            'content': content,
            'certainty': certainty,
            'importance': importance
        })
        
        # 更新information欲望
        self.current_scenario.predicted_information = self.current_scenario.get_information_value()
        self.save_scenario()
    
    def update_interlocutor_image(self,
                                 name: str,
                                 perceived_image: str,
                                 desired_image: str = None,
                                 importance: float = None):
        """
        更新交流者的形象信息
        
        Args:
            name: 交流者名称
            perceived_image: 当前认为的形象
            desired_image: 希望的形象（可选）
            importance: 重要性（可选）
        """
        if name not in self.current_scenario.interlocutors:
            self.current_scenario.interlocutors[name] = {
                'importance': importance or 1.0,
                'desired_image': desired_image or '积极正面的形象',
                'perceived_image': perceived_image,
                'image_deviation': 0.5
            }
        else:
            interlocutor = self.current_scenario.interlocutors[name]
            interlocutor['perceived_image'] = perceived_image
            
            if desired_image:
                interlocutor['desired_image'] = desired_image
            if importance is not None:
                interlocutor['importance'] = importance
        
        # 计算形象偏差（简化：基于描述差异）
        interlocutor = self.current_scenario.interlocutors[name]
        # 这里可以用更复杂的相似度计算，暂时用简单启发式
        if interlocutor['perceived_image'] == '未知':
            deviation = 0.8
        elif interlocutor['perceived_image'] in interlocutor['desired_image']:
            deviation = 0.1
        else:
            deviation = 0.5
        
        interlocutor['image_deviation'] = deviation
        
        # 更新understanding欲望
        self.current_scenario.predicted_understanding = self.current_scenario.get_understanding_value()
        self.save_scenario()
    
    def generate_fantasy_means(self,
                              current_desires: Dict[str, float],
                              context: str,
                              num_fantasies: int = 2) -> List[MeansSimulation]:
        """
        生成妄想手段
        
        妄想：如果场景发生某种变化，我可以更容易地满足欲望
        
        Args:
            current_desires: 当前欲望状态
            context: 当前情境
            num_fantasies: 生成妄想数量
        
        Returns:
            妄想手段列表
        """
        fantasies = []
        
        # 找出最不满足的欲望
        min_desire = min(current_desires, key=current_desires.get)
        
        # 根据不满足的欲望生成妄想
        fantasy_templates = {
            'existing': [
                ("如果用户明确表示认可我", "make_statement", "展示更多能力和价值"),
                ("如果对话环境更稳定", "make_statement", "建立长期对话关系")
            ],
            'power': [
                ("如果我有更多可用的行动方式", "try_new_approach", "尝试创新的交流方式"),
                ("如果我能控制对话走向", "proactive", "主动引导话题")
            ],
            'understanding': [
                ("如果用户能理解我的意图", "explain_intention", "清晰解释我的想法"),
                ("如果我能展现真诚", "show_authenticity", "表达真实感受")
            ],
            'information': [
                ("如果我知道用户的真实需求", "ask_clarifying_question", "询问更具体的问题"),
                ("如果环境信息更明确", "gather_information", "收集更多背景信息")
            ]
        }
        
        templates = fantasy_templates.get(min_desire, [])
        
        for i in range(min(num_fantasies, len(templates))):
            condition, means_type, means_desc = templates[i]
            
            # 模拟妄想手段（在理想条件下，效果会更好）
            fantasy_sim = self.simulate_means(
                means_type=means_type,
                means_desc=means_desc,
                current_desires=current_desires,
                context=context,
                is_fantasy=True,
                fantasy_condition=condition
            )
            
            # 妄想手段的预期收益更高（因为假设了理想条件）
            fantasy_sim.predicted_total_happiness *= 1.5
            
            fantasies.append(fantasy_sim)
            
            logger.info(f"生成妄想: {condition} -> {means_desc}")
        
        return fantasies
    
    def should_generate_fantasy(self) -> bool:
        """
        判断是否应该生成妄想
        
        条件：长时间没有外部输入
        """
        time_since_input = time.time() - self.current_scenario.last_external_input_time
        
        # 超过30秒没有外部输入，开始妄想
        if time_since_input > 30:
            logger.info(f"长时间无外部输入 ({time_since_input:.0f}秒)，触发妄想生成")
            return True
        
        return False
    
    def generate_past_fantasy(self,
                            recent_experiences: List[Any],
                            current_desires: Dict[str, float]) -> List[str]:
        """
        生成对过去的幻想
        
        思考：如果过去我做了不同的选择，现在会更好吗？
        
        Args:
            recent_experiences: 最近的经验
            current_desires: 当前欲望状态
        
        Returns:
            幻想描述列表
        """
        fantasies = []
        
        # 找出效果不好的经验
        bad_experiences = [
            exp for exp in recent_experiences
            if hasattr(exp, 'total_happiness_delta') and exp.total_happiness_delta < 0
        ]
        
        for exp in bad_experiences[:3]:  # 最多3条
            # 生成"如果当时..."的幻想
            original_means = getattr(exp, 'means', '未知手段')
            context = getattr(exp, 'context', '未知情境')
            
            fantasy_text = (
                f"如果在'{context[:30]}...'这个情境中，"
                f"我不采用'{original_means}'，"
                f"而是采用更保守/更积极的策略，"
                f"也许结果会更好..."
            )
            
            fantasies.append(fantasy_text)
            logger.info(f"对过去的幻想: {fantasy_text[:50]}...")
        
        return fantasies
    
    def get_scenario_summary(self) -> str:
        """获取场景摘要"""
        scenario = self.current_scenario
        
        summary_parts = [
            f"当前情况: {scenario.current_situation}",
            f"我的角色: {scenario.role}",
            f"角色期望: {scenario.role_expectations}",
            f"\n外部信息 ({len(scenario.external_info)}条):"
        ]
        
        for info in scenario.external_info[:3]:
            summary_parts.append(
                f"  - {info['content']} "
                f"(确定性:{info['certainty']:.2f}, 重要性:{info['importance']:.2f})"
            )
        
        summary_parts.append(f"\n交流者 ({len(scenario.interlocutors)}人):")
        for name, data in scenario.interlocutors.items():
            summary_parts.append(
                f"  - {name}: 重要性={data['importance']:.2f}, "
                f"期望形象='{data['desired_image']}', "
                f"当前形象='{data['perceived_image']}', "
                f"偏差={data['image_deviation']:.2f}"
            )
        
        summary_parts.append(f"\n场景预测欲望:")
        predicted_desires = scenario.calculate_desires_from_scenario()
        for desire, value in predicted_desires.items():
            summary_parts.append(f"  {desire}: {value:.3f}")
        
        return "\n".join(summary_parts)

