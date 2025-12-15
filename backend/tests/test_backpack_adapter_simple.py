"""
简单测试：直接测试 BackpackAdapter 的 fetch_klines 方法
不需要启动服务器
"""

import sys
import os

# 添加后端目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from exchange_adapters import get_adapter, is_exchange_supported


def test_backpack_supported():
    """测试 Backpack 是否被识别为支持的交易所"""
    print("=" * 80)
    print("🧪 测试1: 检查 Backpack 是否被识别")
    print("=" * 80)
    
    supported = is_exchange_supported('backpack')
    print(f"\nis_exchange_supported('backpack'): {supported}")
    
    if supported:
        print("✅ Backpack 已被识别为支持的交易所")
    else:
        print("❌ Backpack 未被识别")
    
    return supported


def test_backpack_adapter_init():
    """测试 BackpackAdapter 无凭证初始化"""
    print("\n" + "=" * 80)
    print("🧪 测试2: BackpackAdapter 无凭证初始化")
    print("=" * 80)
    
    try:
        # 无凭证配置（仅公开API）
        config = {
            'apiKey': '',
            'secret': '',
        }
        
        print(f"\n配置: {config}")
        print("正在初始化 BackpackAdapter...")
        
        adapter = get_adapter('backpack', 'spot', config)
        
        print(f"\n✅ 初始化成功!")
        print(f"   适配器类型: {type(adapter).__name__}")
        print(f"   交易所ID: {adapter.exchange_id}")
        print(f"   市场类型: {adapter.market_type}")
        
        return adapter
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_backpack_fetch_klines(adapter):
    """测试获取 K线数据"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 获取 Backpack K线数据")
    print("=" * 80)
    
    if not adapter:
        print("❌ 跳过测试（适配器初始化失败）")
        return
    
    # 测试参数
    symbol = "SOL/USDC"
    interval = "15m"
    limit = 5
    
    print(f"\n测试参数:")
    print(f"   交易对: {symbol}")
    print(f"   周期: {interval}")
    print(f"   数量: {limit}")
    
    try:
        print(f"\n⏳ 正在获取K线数据...")
        
        klines = adapter.fetch_klines(symbol, interval, limit)
        
        print(f"\n✅ 成功获取 {len(klines)} 条K线数据\n")
        
        if len(klines) > 0:
            print("📈 K线数据:")
            print("-" * 80)
            print(f"{'序号':<6} {'时间戳':<15} {'开盘':<10} {'最高':<10} {'最低':<10} {'收盘':<10} {'成交量':<10}")
            print("-" * 80)
            
            for i, kline in enumerate(klines):
                # kline 格式: [timestamp, open, high, low, close, volume]
                print(f"{i+1:<6} {kline[0]:<15} {kline[1]:<10.2f} {kline[2]:<10.2f} {kline[3]:<10.2f} {kline[4]:<10.2f} {kline[5]:<10.2f}")
            
            print("-" * 80)
            
            # 验证数据格式
            first_kline = klines[0]
            print(f"\n🔍 数据格式验证:")
            print(f"   格式: {type(first_kline)} (应为 list)")
            print(f"   长度: {len(first_kline)} (应为 6)")
            print(f"   时间戳: {first_kline[0]} (应为整数毫秒)")
            print(f"   开盘价: {first_kline[1]} (应为浮点数)")
            
            # 验证是否符合标准 CCXT 格式
            is_valid = (
                isinstance(first_kline, list) and
                len(first_kline) == 6 and
                isinstance(first_kline[0], int) and
                all(isinstance(first_kline[i], (int, float)) for i in range(1, 6))
            )
            
            if is_valid:
                print(f"\n✅ 数据格式验证通过！符合 CCXT 标准格式")
            else:
                print(f"\n⚠️ 数据格式可能不正确")
            
            return True
        else:
            print("⚠️ 返回数据为空")
            return False
        
    except Exception as e:
        print(f"\n❌ 获取K线失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_intervals(adapter):
    """测试多个时间周期"""
    print("\n" + "=" * 80)
    print("🧪 测试4: 多个时间周期")
    print("=" * 80)
    
    if not adapter:
        print("❌ 跳过测试（适配器初始化失败）")
        return
    
    intervals = ["1m", "5m", "15m", "1h", "1d"]
    symbol = "BTC/USDC"
    
    print(f"\n测试交易对: {symbol}")
    print(f"测试周期: {intervals}\n")
    
    results = {}
    for interval in intervals:
        try:
            klines = adapter.fetch_klines(symbol, interval, 3)
            results[interval] = len(klines)
            print(f"   {interval:<6} ✅ 获取 {len(klines)} 条数据")
        except Exception as e:
            results[interval] = 0
            print(f"   {interval:<6} ❌ 失败: {e}")
    
    print(f"\n📊 测试结果: {sum(1 for v in results.values() if v > 0)}/{len(intervals)} 个周期成功")


def main():
    """主测试函数"""
    
    print("\n" + "🎯" * 40)
    print("Backpack Adapter K线功能测试")
    print("🎯" * 40)
    
    # 测试1: 检查支持
    if not test_backpack_supported():
        print("\n❌ Backpack 不被支持，终止测试")
        return
    
    # 测试2: 初始化适配器
    adapter = test_backpack_adapter_init()
    if not adapter:
        print("\n❌ 适配器初始化失败，终止测试")
        return
    
    # 测试3: 获取K线数据
    success = test_backpack_fetch_klines(adapter)
    
    # 测试4: 多个时间周期
    test_multiple_intervals(adapter)
    
    # 总结
    print("\n" + "=" * 80)
    if success:
        print("🎉 所有测试完成！Backpack K线功能正常工作")
    else:
        print("⚠️ 部分测试失败，请检查日志")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

