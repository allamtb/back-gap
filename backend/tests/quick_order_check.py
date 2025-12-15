"""
快速检查订单获取
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json


def check_gate_support():
    """检查 Gate.io 订单功能支持情况（只检查 has 属性，不需要真实凭证）"""
    print("\n" + "="*80)
    print("检查 CCXT 对 Gate.io 的功能支持（静态检查）")
    print("="*80 + "\n")
    
    try:
        import ccxt
        
        # ⚠️ 注意：这里用 dummy 是可以的，因为我们只是检查 has 属性
        # has 属性是 CCXT 内置的静态信息，不需要 API 凭证
        config = {
            'apiKey': 'dummy',
            'secret': 'dummy',
            'enableRateLimit': True,
        }
        
        # 测试 Spot
        print("📌 Gate.io Spot:")
        gate_spot = ccxt.gate(config)
        print(f"   has['fetchOrders']: {gate_spot.has.get('fetchOrders', False)}")
        print(f"   has['fetchOpenOrders']: {gate_spot.has.get('fetchOpenOrders', False)}")
        print(f"   has['fetchClosedOrders']: {gate_spot.has.get('fetchClosedOrders', False)}")
        
        # 测试 Futures
        print("\n📌 Gate.io Futures:")
        gate_futures = ccxt.gate({**config, 'options': {'defaultType': 'swap'}})
        print(f"   has['fetchOrders']: {gate_futures.has.get('fetchOrders', False)}")
        print(f"   has['fetchOpenOrders']: {gate_futures.has.get('fetchOpenOrders', False)}")
        print(f"   has['fetchClosedOrders']: {gate_futures.has.get('fetchClosedOrders', False)}")
        
        print("\n💡 说明：")
        print("   - 'has' 属性表示 CCXT 理论上支持该功能")
        print("   - 实际能否调用成功，需要真实 API Key 测试")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def check_adapter_capabilities():
    """检查 Adapter 的能力（不需要真实凭证）"""
    print("\n" + "="*80)
    print("检查 Adapter 能力（静态检查）")
    print("="*80 + "\n")
    
    try:
        from exchange_adapters import get_adapter
        from exchange_adapters.adapter_interface import AdapterCapability
        
        # ⚠️ 注意：这里用 dummy 是可以的，因为我们只是检查能力配置
        config = {
            'apiKey': 'dummy',
            'secret': 'dummy',
        }
        
        for exchange_id in ['binance', 'gate', 'okx', 'bybit']:
            for market_type in ['spot', 'futures']:
                print(f"\n📌 {exchange_id} ({market_type}):")
                
                try:
                    adapter = get_adapter(exchange_id, market_type, config)
                    
                    # 检查订单功能
                    cap = (AdapterCapability.FETCH_SPOT_ORDERS 
                          if market_type == 'spot' 
                          else AdapterCapability.FETCH_FUTURES_ORDERS)
                    
                    supports = adapter.supports_capability(cap)
                    print(f"   支持订单查询: {supports}")
                    
                    if supports:
                        # 检查底层方法
                        print(f"   exchange.fetch_orders: {hasattr(adapter.exchange, 'fetch_orders')}")
                        print(f"   exchange.fetch_open_orders: {hasattr(adapter.exchange, 'fetch_open_orders')}")
                        print(f"   exchange.fetch_closed_orders: {hasattr(adapter.exchange, 'fetch_closed_orders')}")
                    
                except Exception as e:
                    print(f"   ❌ 错误: {e}")
        
        print("\n💡 说明：")
        print("   - 这些检查不需要真实 API Key")
        print("   - 只是检查 Adapter 的能力配置和方法存在性")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def print_api_flow():
    """打印 API 调用流程"""
    print("\n" + "="*80)
    print("API 调用流程说明")
    print("="*80 + "\n")
    
    print("前端 OrderMonitor.jsx:")
    print("  ↓")
    print("  调用: POST /api/orders")
    print("  发送: [{ exchange: 'gate', apiKey: '...', apiSecret: '...' }]")
    print("  ↓")
    print("后端 main.py:@app.post(\"/api/orders\"):")
    print("  ↓")
    print("  扩展为: [")
    print("    { exchange: 'gate', marketType: 'spot', apiKey: '...', ... },")
    print("    { exchange: 'gate', marketType: 'futures', apiKey: '...', ... },")
    print("  ]")
    print("  ↓")
    print("  调用: order_service.get_orders(expanded_credentials)")
    print("  ↓")
    print("services/order_service.py:")
    print("  ↓")
    print("  对每个交易所并发调用:")
    print("  adapter = get_adapter(exchange_id, market_type, config)")
    print("  orders = adapter.fetch_orders(None, since, 50)")
    print("  ↓")
    print("exchange_adapters/base.py:")
    print("  ↓")
    print("  1. 检查是否支持（supports_capability）")
    print("  2. 调用 _fetch_orders_default()")
    print("  3. 尝试:")
    print("     - exchange.fetch_orders()  ← 最优先")
    print("     或")
    print("     - exchange.fetch_open_orders()  + exchange.fetch_closed_orders()")
    print("  4. 标准化数据（_normalize_orders）")
    print("  5. 返回标准化的订单列表")
    
    print("\n💡 关键点:")
    print("  - since = 最近24小时（time.time() - 86400）* 1000")
    print("  - limit = 50")
    print("  - symbol = None （获取所有交易对）")


if __name__ == '__main__':
    print("\n🔍 订单获取快速检查工具\n")
    
    check_gate_support()
    check_adapter_capabilities()
    print_api_flow()
    
    print("\n" + "="*80)
    print("✅ 检查完成")
    print("="*80)
    
    print("\n📋 接下来的步骤:")
    print("  1. 重启后端: cd backend && python main.py")
    print("  2. 在前端刷新订单")
    print("  3. 查看后端日志输出")
    print("  4. 如果还是没有订单，检查:")
    print("     - API Key/Secret 是否正确")
    print("     - 是否真的有最近24小时的订单")
    print("     - 后端日志中的错误信息")
    print()

