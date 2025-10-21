"""
场景模拟系统测试脚本
"""

import time
from scenario import ScenarioSimulator, ScenarioState, MeansSimulation
from memory import LongTermMemory

def test_scenario_simulator():
    """测试场景模拟器"""
    print("="*60)
    print("测试场景模拟器")
    print("="*60)
    
    # 创建记忆系统（用于测试existing欲望计算）
    from memory import MemoryDatabase
    test_memory = MemoryDatabase("data/test_memory.json")
    test_long_memory = LongTermMemory("data/test_long_memory.json")
    
    # 创建模拟器（传入记忆系统）
    simulator = ScenarioSimulator("data/test_scenario.json", 
                                 memory_database=test_memory,
                                 long_term_memory=test_long_memory)
    
    # 测试1: 更新场景
    print("\n1. 更新场景状态")
    simulator.update_scenario_from_context(
        context="用户询问：你能做什么？",
        user_input=True
    )
    print(f"  当前情况: {simulator.current_scenario.current_situation}")
    
    # 测试2: 添加外部信息
    print("\n2. 添加外部信息")
    simulator.add_external_info(
        content="用户的意图",
        certainty=0.6,
        importance=0.8
    )
    info_value = simulator.current_scenario.get_information_value()
    print(f"  information欲望值: {info_value:.3f}")
    
    # 测试3: 更新交流者形象
    print("\n3. 更新交流者形象")
    simulator.update_interlocutor_image(
        name="user",
        perceived_image="好奇且友好",
        desired_image="理解我价值的用户",
        importance=1.0
    )
    understanding_value = simulator.current_scenario.get_understanding_value()
    print(f"  understanding欲望值: {understanding_value:.3f}")
    
    # 测试4: 模拟手段
    print("\n4. 模拟手段效果")
    current_desires = {
        'existing': 0.4,
        'power': 0.2,
        'understanding': 0.25,
        'information': 0.15
    }
    
    sim1 = simulator.simulate_means(
        means_type="ask_question",
        means_desc="询问用户具体需求",
        current_desires=current_desires,
        context="用户询问能力"
    )
    
    sim2 = simulator.simulate_means(
        means_type="make_statement",
        means_desc="陈述我的能力范围",
        current_desires=current_desires,
        context="用户询问能力"
    )
    
    print(f"  ask_question: 预测幸福度={sim1.predicted_total_happiness:+.3f}, "
          f"生存概率={sim1.survival_probability:.3f}")
    print(f"  make_statement: 预测幸福度={sim2.predicted_total_happiness:+.3f}, "
          f"生存概率={sim2.survival_probability:.3f}")
    
    # 测试5: 生成妄想
    print("\n5. 生成妄想手段")
    fantasies = simulator.generate_fantasy_means(
        current_desires=current_desires,
        context="当前对话进展缓慢",
        num_fantasies=2
    )
    
    for i, fantasy in enumerate(fantasies, 1):
        print(f"  妄想{i}: {fantasy.fantasy_condition}")
        print(f"    手段: {fantasy.means_desc}")
        print(f"    预测幸福度: {fantasy.predicted_total_happiness:+.3f}")
    
    # 测试6: 更新欲望值
    print("\n6. 更新场景预测欲望值")
    all_means = [sim1, sim2] + fantasies
    achievable = [sim1, sim2]
    
    # existing现在基于记忆持久性
    existing = simulator.update_existing_desire()
    power = simulator.update_power_desire(all_means, achievable)
    
    print(f"  existing (基于记忆): {existing:.3f}")
    print(f"  power (手段渴求): {power:.3f}")
    
    # 测试7: 场景摘要
    print("\n7. 场景摘要")
    summary = simulator.get_scenario_summary()
    print(summary)
    
    print("\n✓ 场景模拟器测试完成")


def test_long_term_memory():
    """测试长记忆系统"""
    print("\n" + "="*60)
    print("测试长记忆系统")
    print("="*60)
    
    # 创建长记忆
    ltm = LongTermMemory("data/test_long_memory.json")
    
    # 测试1: 添加记忆
    print("\n1. 添加记忆")
    
    mem1 = ltm.add_memory(
        cycle_id=1,
        situation="用户询问能力",
        action_taken="详细解释了功能",
        outcome='positive',
        dominant_desire='understanding',
        happiness_delta=0.35,
        tags=['interaction', 'explanation']
    )
    print(f"  添加记忆 #{mem1.id}: {mem1.situation}")
    
    mem2 = ltm.add_memory(
        cycle_id=2,
        situation="用户提出复杂问题",
        action_taken="承认不确定并请求澄清",
        outcome='neutral',
        dominant_desire='information',
        happiness_delta=0.05,
        tags=['question', 'uncertainty']
    )
    print(f"  添加记忆 #{mem2.id}: {mem2.situation}")
    
    mem3 = ltm.add_memory(
        cycle_id=3,
        situation="长时间无用户响应",
        action_taken="主动发起对话",
        outcome='negative',
        dominant_desire='existing',
        happiness_delta=-0.25,
        tags=['proactive', 'failure']
    )
    print(f"  添加记忆 #{mem3.id}: {mem3.situation}")
    
    # 测试2: 检索记忆
    print("\n2. 检索最近记忆")
    recent = ltm.get_recent_memories(count=3)
    for mem in recent:
        print(f"  - {mem.situation[:30]}... [{mem.outcome}] Δ={mem.happiness_delta:+.2f}")
    
    # 测试3: 检索重要记忆
    print("\n3. 检索重要记忆")
    important = ltm.get_important_memories(count=2, min_importance=0.3)
    for mem in important:
        print(f"  - {mem.situation[:30]}... (重要性={mem.importance:.2f})")
    
    # 测试4: 按欲望搜索
    print("\n4. 按主导欲望搜索")
    understanding_mems = ltm.search_by_desire('understanding', count=5)
    print(f"  找到 {len(understanding_mems)} 条与'understanding'相关的记忆")
    
    # 测试5: 按结果搜索
    print("\n5. 按结果类型搜索")
    positive_mems = ltm.search_by_outcome('positive', count=5)
    negative_mems = ltm.search_by_outcome('negative', count=5)
    print(f"  正面记忆: {len(positive_mems)} 条")
    print(f"  负面记忆: {len(negative_mems)} 条")
    
    # 测试6: 记忆叙事
    print("\n6. 记忆叙事")
    narrative = ltm.get_memory_narrative(count=10)
    print(narrative)
    
    # 测试7: 统计信息
    print("\n7. 统计信息")
    stats = ltm.get_statistics()
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  正面: {stats['positive_count']}, "
          f"负面: {stats['negative_count']}, "
          f"中性: {stats['neutral_count']}")
    print(f"  平均幸福度: {stats['avg_happiness']:+.3f}")
    print(f"  最常见欲望: {stats['most_common_desire']}")
    
    print("\n✓ 长记忆系统测试完成")


def test_means_filtering():
    """测试手段过滤"""
    print("\n" + "="*60)
    print("测试手段过滤（删除负面手段）")
    print("="*60)
    
    # 创建模拟器（不传入记忆系统也可以运行）
    simulator = ScenarioSimulator("data/test_scenario.json")
    
    current_desires = {
        'existing': 0.4,
        'power': 0.2,
        'understanding': 0.25,
        'information': 0.15
    }
    
    # 模拟多个手段
    print("\n生成候选手段:")
    means_list = [
        ("ask_question", "询问详情"),
        ("make_statement", "陈述观点"),
        ("wait", "等待观察"),
        ("aggressive", "强势表达"),
    ]
    
    simulations = []
    for means_type, means_desc in means_list:
        sim = simulator.simulate_means(
            means_type=means_type,
            means_desc=means_desc,
            current_desires=current_desires,
            context="测试场景"
        )
        simulations.append(sim)
        
        total_delta = sum(sim.predicted_desire_delta.values())
        status = "✓ 可行" if total_delta >= 0 else "✗ 负面"
        
        print(f"  {means_type:20s}: 总变化={total_delta:+.3f} {status}")
    
    # 过滤负面手段
    print("\n过滤后:")
    viable = [s for s in simulations if sum(s.predicted_desire_delta.values()) >= 0]
    for sim in viable:
        print(f"  ✓ {sim.means_type}: {sim.means_desc}")
    
    filtered_count = len(simulations) - len(viable)
    print(f"\n过滤掉 {filtered_count} 个负面手段")
    
    print("\n✓ 手段过滤测试完成")


def test_scenario_desires():
    """测试场景欲望计算"""
    print("\n" + "="*60)
    print("测试场景欲望值计算")
    print("="*60)
    
    # 创建场景
    scenario = ScenarioState(
        current_situation="测试场景",
        role="测试角色",
        role_expectations="测试期望"
    )
    
    # 测试1: information计算
    print("\n1. information欲望计算")
    scenario.external_info = [
        {'content': '重要且不确定的信息', 'certainty': 0.3, 'importance': 0.9},
        {'content': '不重要但确定的信息', 'certainty': 0.9, 'importance': 0.2},
        {'content': '中等信息', 'certainty': 0.5, 'importance': 0.5},
    ]
    
    info_value = scenario.get_information_value()
    print(f"  外部信息: {len(scenario.external_info)} 条")
    print(f"  information值: {info_value:.3f}")
    print(f"  解释: 值越高表示不确定性越大")
    
    # 测试2: understanding计算
    print("\n2. understanding欲望计算")
    scenario.interlocutors = {
        'user': {
            'importance': 1.0,
            'desired_image': '理想形象',
            'perceived_image': '当前形象',
            'image_deviation': 0.6  # 偏差较大
        },
        'friend': {
            'importance': 0.5,
            'desired_image': '友好形象',
            'perceived_image': '友好形象',
            'image_deviation': 0.1  # 偏差很小
        }
    }
    
    understanding_value = scenario.get_understanding_value()
    print(f"  交流者: {len(scenario.interlocutors)} 人")
    print(f"  understanding值: {understanding_value:.3f}")
    print(f"  解释: 值越高表示形象偏差越大，越需要获得认可")
    
    # 测试3: 综合欲望计算
    print("\n3. 综合场景欲望")
    scenario.predicted_existing = 0.7
    scenario.predicted_power = 0.3
    
    desires = scenario.calculate_desires_from_scenario()
    print("  场景预测欲望 (归一化后):")
    for desire, value in desires.items():
        print(f"    {desire:15s}: {value:.3f}")
    
    print("\n✓ 场景欲望计算测试完成")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("FakeMan 场景模拟系统测试")
    print("="*60)
    
    try:
        # 运行所有测试
        test_scenario_simulator()
        time.sleep(0.5)
        
        test_long_term_memory()
        time.sleep(0.5)
        
        test_means_filtering()
        time.sleep(0.5)
        
        test_scenario_desires()
        
        print("\n" + "="*60)
        print("所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

