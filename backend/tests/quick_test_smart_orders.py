"""
快速测试：Binance 智能订单获取

使用方法：
    python backend/tests/quick_test_smart_orders.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exchange_adapters import get_adapter

# === 配置 ===
config = {
    'apiKey': "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3",
    'secret': "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a",
    'enableRateLimit': True,
    'proxies': {
        'http': "http://127.0.0.1:1080",
        'https': "http://127.0.0.1:1080",
    }
}

def main():
    print("🚀 Binance 智能订单获取测试")
    print("="*60)
    
    try:
        # 创建 Adapter
        print("\n[1/3] 创建 Binance Spot Adapter...")
        adapter = get_adapter('binance', 'spot', config)
        print("    ✅ 创建成功")
        
        # 智能推断交易对
        print("\n[2/3] 智能推断活跃交易对...")
        active_symbols = adapter._get_active_symbols_from_balance_smart()
        print(f"    ✅ 推断出 {len(active_symbols)} 个交易对")
        
        if active_symbols:
            print(f"    📋 前10个交易对:")
            for i, symbol in enumerate(sorted(active_symbols)[:10], 1):
                print(f"       {i}. {symbol}")
        
        # 获取订单
        print("\n[3/3] 获取订单（无需指定 symbol）...")
        orders = adapter.fetch_orders(symbol=None, limit=50)
        print(f"    ✅ 成功获取 {len(orders)} 个订单")
        
        if orders:
            # 统计
            symbols_in_orders = set(order['symbol'] for order in orders)
            status_counts = {}
            for order in orders:
                status = order.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n    📊 订单统计:")
            print(f"       • 涉及交易对: {len(symbols_in_orders)} 个")
            print(f"       • 状态分布: {status_counts}")
            
            # 显示前5个订单
            print(f"\n    📄 前5个订单:")
            for i, order in enumerate(orders[:5], 1):
                symbol = order['symbol']
                side = order['side']
                order_type = order.get('type', 'unknown')
                status = order['status']
                time = order.get('orderTime', 'N/A')
                
                print(f"       {i}. {symbol:<15} {side:<4} {order_type:<10} {status:<10} {time}")
        else:
            print("    ℹ️  最近无订单记录")
        
        print("\n" + "="*60)
        print("✅ 测试完成！")
        print("\n💡 说明:")
        print("   这个测试展示了改进后的 Adapter 如何智能处理 Binance 的限制")
        print("   即使不传 symbol，也能成功获取所有订单")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

