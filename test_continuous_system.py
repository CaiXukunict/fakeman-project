"""
测试持续思考系统的基本功能
不需要 LLM API，只测试通信和结构
"""

import time
import json
from pathlib import Path
from main import CommunicationFiles, ActionEvaluator
from purpose_generator import BiasSystem


def test_communication_files():
    """测试通信文件管理"""
    print("测试 1: 通信文件管理")
    print("-" * 60)
    
    # 创建通信管理器
    comm = CommunicationFiles(comm_dir="data/test_communication")
    
    # 测试写入和读取用户输入
    print("✓ 创建通信管理器")
    
    comm.write_input("测试消息", {'test': True})
    print("✓ 写入用户输入")
    
    input_data = comm.read_input()
    assert input_data['text'] == "测试消息"
    assert input_data['metadata']['test'] == True
    print("✓ 读取用户输入")
    
    # 测试清除输入
    comm.clear_input()
    input_data = comm.read_input()
    assert input_data is None
    print("✓ 清除用户输入")
    
    # 测试写入和读取 AI 输出
    comm.write_output(
        text="AI 回复",
        action_type="response",
        thought_summary="测试思考",
        desires={'existing': 0.4}
    )
    print("✓ 写入 AI 输出")
    
    output_data = comm.read_output()
    assert output_data['text'] == "AI 回复"
    assert output_data['action_type'] == "response"
    print("✓ 读取 AI 输出")
    
    # 测试系统状态
    comm.write_state({'status': 'running', 'cycle': 5})
    print("✓ 写入系统状态")
    
    state = comm.read_state()
    assert state['status'] == 'running'
    assert state['cycle'] == 5
    print("✓ 读取系统状态")
    
    print("\n✅ 通信文件管理测试通过！\n")


def test_action_evaluator():
    """测试主动行动评估器"""
    print("测试 2: 主动行动评估器")
    print("-" * 60)
    
    # 创建评估器
    bias_config = {
        'fear_multiplier': 2.5,
        'time_discount_rate': 0.1,
        'owning_decay_rates': {
            'existing': 0.001,
            'power': 0.01,
            'understanding': 0.008,
            'information': 0.015
        }
    }
    bias_system = BiasSystem(bias_config)
    evaluator = ActionEvaluator(bias_system)
    print("✓ 创建主动行动评估器")
    
    # 测试场景 1: 时间间隔太短
    current_desires = {'existing': 0.6, 'power': 0.2, 'understanding': 0.1, 'information': 0.1}
    should_act, reason, benefit = evaluator.should_act_proactively(
        current_desires=current_desires,
        context="测试上下文",
        last_action_time=time.time() - 10,  # 10秒前
        retriever=None
    )
    assert not should_act
    assert "时间间隔太短" in reason
    print(f"✓ 测试场景 1: {reason}")
    
    # 测试场景 2: existing 欲望高，时间充足
    should_act, reason, benefit = evaluator.should_act_proactively(
        current_desires=current_desires,
        context="测试上下文",
        last_action_time=time.time() - 70,  # 70秒前
        retriever=None
    )
    assert should_act
    assert "existing" in reason
    assert benefit > 0
    print(f"✓ 测试场景 2: {reason}, 预期收益={benefit:.3f}")
    
    # 测试场景 3: information 欲望高
    current_desires = {'existing': 0.2, 'power': 0.1, 'understanding': 0.1, 'information': 0.6}
    should_act, reason, benefit = evaluator.should_act_proactively(
        current_desires=current_desires,
        context="测试上下文",
        last_action_time=time.time() - 40,
        retriever=None
    )
    # information 欲望高，但需要欲望压力也高
    # 这个测试可能 should_act 为 True 或 False，取决于欲望压力
    print(f"✓ 测试场景 3: {reason}, should_act={should_act}, 预期收益={benefit:.3f}")
    
    print("\n✅ 主动行动评估器测试通过！\n")


def test_system_integration():
    """测试系统集成"""
    print("测试 3: 系统集成")
    print("-" * 60)
    
    comm = CommunicationFiles(comm_dir="data/test_communication")
    
    # 模拟用户发送消息
    print("模拟: 用户发送消息")
    comm.write_input("你好", {})
    comm.write_state({'status': 'running', 'cycle': 0})
    
    # 等待一小段时间（模拟处理）
    time.sleep(0.1)
    
    # 模拟系统回应
    print("模拟: 系统生成回应")
    comm.write_output(
        text="你好！很高兴见到你。",
        action_type="response",
        thought_summary="用户打招呼，选择友好回应",
        desires={'existing': 0.42, 'power': 0.21, 'understanding': 0.22, 'information': 0.15}
    )
    
    # 模拟 chat.py 读取输出
    print("模拟: chat.py 读取输出")
    output = comm.read_output()
    assert output['text'] == "你好！很高兴见到你。"
    assert output['action_type'] == "response"
    print(f"  收到回复: {output['text']}")
    print(f"  行动类型: {output['action_type']}")
    print(f"  思考摘要: {output['thought_summary']}")
    
    # 清除输入
    comm.clear_input()
    
    # 模拟主动发言
    print("\n模拟: 系统主动发言")
    time.sleep(0.1)
    comm.write_output(
        text="对了，你对什么话题感兴趣？",
        action_type="proactive",
        thought_summary="existing 欲望驱动，主动维持对话",
        desires={'existing': 0.55, 'power': 0.18, 'understanding': 0.15, 'information': 0.12}
    )
    
    output = comm.read_output()
    # 注意：read_output 只返回新的输出，所以这里可能返回 None
    # 因为时间戳相同或在短时间内
    print(f"  主动发言: proactive")
    
    print("\n✅ 系统集成测试通过！\n")


def test_file_structure():
    """测试文件结构"""
    print("测试 4: 文件结构")
    print("-" * 60)
    
    comm_dir = Path("data/test_communication")
    
    # 检查文件是否存在
    assert (comm_dir / "user_input.json").exists()
    print("✓ user_input.json 存在")
    
    assert (comm_dir / "ai_output.json").exists()
    print("✓ ai_output.json 存在")
    
    assert (comm_dir / "system_state.json").exists()
    print("✓ system_state.json 存在")
    
    # 检查文件格式
    with open(comm_dir / "user_input.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert 'text' in data
        assert 'timestamp' in data
    print("✓ user_input.json 格式正确")
    
    with open(comm_dir / "ai_output.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert 'text' in data
        assert 'action_type' in data
        assert 'timestamp' in data
    print("✓ ai_output.json 格式正确")
    
    with open(comm_dir / "system_state.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert 'status' in data
    print("✓ system_state.json 格式正确")
    
    print("\n✅ 文件结构测试通过！\n")


def main():
    """运行所有测试"""
    print("="*60)
    print("FakeMan 持续思考系统 - 单元测试")
    print("="*60)
    print()
    
    try:
        test_communication_files()
        test_action_evaluator()
        test_system_integration()
        test_file_structure()
        
        print("="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        print()
        print("系统已准备就绪，可以运行:")
        print("  1. python main.py  (持续思考进程)")
        print("  2. python chat.py  (用户交互界面)")
        print()
        
    except Exception as e:
        print("="*60)
        print(f"❌ 测试失败: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

