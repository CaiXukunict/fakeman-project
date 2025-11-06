"""
测试重构后的系统
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from utils.config import Config
from main import FakeManRefactored

def test_basic():
    """基础测试"""
    print("="*60)
    print("测试重构后的 FakeMan 系统")
    print("="*60)
    
    # 检查API Key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("\n❌ 错误: 未找到 DEEPSEEK_API_KEY")
        print("请在 .env 文件中设置 DEEPSEEK_API_KEY=your_key")
        return
    
    print(f"\n✓ API Key 已配置: {api_key[:10]}...")
    
    # 初始化系统
    print("\n初始化系统...")
    try:
        config = Config()
        system = FakeManRefactored(config)
        print("✓ 系统初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 查看初始状态
    print("\n初始状态:")
    status = system.get_status()
    print(f"  - 周期数: {status['cycle_count']}")
    print(f"  - 欲望: {status['desires']}")
    print(f"  - 目的数: {status['purposes']}")
    print(f"  - 手段数: {status['means']}")
    
    # 运行一个思考周期
    print("\n" + "-"*60)
    print("运行第1个思考周期...")
    print("-"*60)
    
    try:
        result = system.thinking_cycle(
            external_input="你好，请介绍一下你自己"
        )
        
        print(f"\n✓ 思考周期完成")
        print(f"  - 耗时: {result['duration']:.2f}秒")
        print(f"  - 目的数: {result['purposes']}")
        print(f"  - 手段数: {result['means']}")
        print(f"  - 思考片段: {result['thought'][:100]}...")
        print(f"  - 行动: {result['action']}")
        
    except Exception as e:
        print(f"❌ 思考周期失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 再运行一个周期（内部思考）
    print("\n" + "-"*60)
    print("运行第2个思考周期（内部思考）...")
    print("-"*60)
    
    try:
        result = system.thinking_cycle()
        
        print(f"\n✓ 思考周期完成")
        print(f"  - 目的数: {result['purposes']}")
        print(f"  - 手段数: {result['means']}")
        
    except Exception as e:
        print(f"❌ 思考周期失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 最终状态
    print("\n" + "="*60)
    print("最终状态:")
    print("="*60)
    status = system.get_status()
    
    print(f"\n周期统计:")
    print(f"  - 总周期数: {status['cycle_count']}")
    
    print(f"\n欲望状态:")
    for desire, value in status['desires'].items():
        print(f"  - {desire}: {value:.3f}")
    
    print(f"\n目的统计:")
    for key, value in status['purposes'].items():
        print(f"  - {key}: {value}")
    
    print(f"\n手段统计:")
    for key, value in status['means'].items():
        print(f"  - {key}: {value}")
    
    print(f"\n思考统计:")
    for key, value in status['thoughts'].items():
        print(f"  - {key}: {value}")
    
    print(f"\n经验统计:")
    for key, value in status['experiences'].items():
        print(f"  - {key}: {value}")
    
    print("\n" + "="*60)
    print("✓ 测试完成!")
    print("="*60)


if __name__ == "__main__":
    test_basic()

