"""
测试 OrderService 是否正确使用 Adapter 架构
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from exchange_adapters import get_adapter


def test_adapter_fetch_orders():
    """测试 Adapter 的 fetch_orders 方法"""
    
    # 测试配置（使用空密钥）
    config = {
        'apiKey': 'test',
        'secret': 'test',
        'enableRateLimit': True,
    }
    
    # 测试支持的交易所
    exchanges = ['binance', 'gate', 'okx', 'bybit']
    
    for exchange_id in exchanges:
        for market_type in ['spot', 'futures']:
            print(f"\n{'='*60}")
            print(f"测试: {exchange_id} - {market_type}")
            print(f"{'='*60}")
            
            try:
                # 创建 Adapter
                adapter = get_adapter(exchange_id, market_type, config)
                
                # 检查方法是否存在
                print(f"✅ Adapter 类型: {adapter.__class__.__name__}")
                print(f"✅ 是否有 fetch_orders 方法: {hasattr(adapter, 'fetch_orders')}")
                print(f"✅ 是否有 fetch_open_orders 方法: {hasattr(adapter, 'fetch_open_orders')}")
                
                # 检查底层 exchange 是否有 fetch_orders
                if adapter.exchange:
                    has_ccxt_fetch_orders = hasattr(adapter.exchange, 'fetch_orders')
                    has_ccxt_fetch_closed = hasattr(adapter.exchange, 'fetch_closed_orders')
                    print(f"✅ CCXT 是否有 fetch_orders: {has_ccxt_fetch_orders}")
                    print(f"✅ CCXT 是否有 fetch_closed_orders: {has_ccxt_fetch_closed}")
                
                # 检查支持的功能
                capabilities = adapter.get_supported_capabilities()
                print(f"✅ 支持的功能: {capabilities}")
                
            except Exception as e:
                print(f"❌ 错误: {e}")


def test_adapter_interface():
    """测试 Adapter 接口的完整性"""
    
    print("\n" + "="*60)
    print("测试 Adapter 接口完整性")
    print("="*60)
    
    config = {
        'apiKey': 'test',
        'secret': 'test',
    }
    
    # 测试 OKX（使用默认适配器）
    adapter = get_adapter('okx', 'spot', config)
    
    # 检查所有必要的方法
    methods = [
        'fetch_orders',
        'fetch_open_orders',
        'fetch_positions',
        'fetch_ohlcv',
        '_fetch_orders_default',
        '_fetch_open_orders_default',
        '_normalize_orders',
    ]
    
    for method in methods:
        has_method = hasattr(adapter, method)
        status = "✅" if has_method else "❌"
        print(f"{status} {method}: {has_method}")


if __name__ == '__main__':
    print("\n🎯 测试 Adapter 架构的订单查询功能\n")
    
    test_adapter_fetch_orders()
    test_adapter_interface()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

