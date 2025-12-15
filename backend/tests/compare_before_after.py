"""
对比测试：改进前 vs 改进后
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ccxt
from exchange_adapters import get_adapter

# === 配置 ===
BINANCE_CONFIG = {
    'apiKey': "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3",
    'secret': "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a",
    'enableRateLimit': True,
    'proxies': {
        'http': "http://127.0.0.1:1080",
        'https': "http://127.0.0.1:1080",
    }
}

print("="*80)
print("🧪 对比测试：改进前 vs 改进后")
print("="*80)
print()

# === 改进前：直接使用 CCXT ===
print("📌 改进前：直接使用 CCXT（会失败）")
print("-"*80)
try:
    exchange = ccxt.binance(BINANCE_CONFIG)
    
    print("  [1] 尝试 fetch_orders(symbol=None)")
    try:
        orders = exchange.fetch_orders(symbol=None)
        print(f"      ✅ 成功: {len(orders)} 个订单")
    except Exception as e:
        print(f"      ❌ 失败: {str(e)[:100]}")
    
    print("\n  [2] 尝试 fetch_closed_orders(symbol=None)")
    try:
        orders = exchange.fetch_closed_orders(symbol=None)
        print(f"      ✅ 成功: {len(orders)} 个订单")
    except Exception as e:
        print(f"      ❌ 失败: {str(e)[:100]}")
    
    print("\n  [3] 尝试 fetch_open_orders(symbol=None)")
    try:
        orders = exchange.fetch_open_orders(symbol=None)
        print(f"      ✅ 成功: {len(orders)} 个订单")
    except Exception as e:
        print(f"      ❌ 失败: {str(e)[:100]}")

except Exception as e:
    print(f"  ❌ 初始化失败: {e}")

print()

# === 改进后：使用 Adapter ===
print("📌 改进后：使用 Adapter（智能推断）")
print("-"*80)
try:
    adapter = get_adapter('binance', 'spot', BINANCE_CONFIG)
    
    print("  [1] adapter.fetch_orders(symbol=None)")
    try:
        orders = adapter.fetch_orders(symbol=None)
        print(f"      ✅ 成功: {len(orders)} 个订单")
        
        if orders:
            # 统计
            symbols = set(order['symbol'] for order in orders)
            statuses = {}
            for order in orders:
                status = order.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"      📊 涉及 {len(symbols)} 个交易对")
            print(f"      📊 状态分布: {statuses}")
            
            # 显示前3个
            print(f"\n      📄 示例订单:")
            for i, order in enumerate(orders[:3], 1):
                print(f"         {i}. {order['symbol']:<12} | {order['side']:<4} | {order['status']:<10} | {order.get('orderTime', 'N/A')}")
    except Exception as e:
        print(f"      ❌ 失败: {e}")
    
    print("\n  [2] adapter.fetch_open_orders(symbol=None)")
    try:
        orders = adapter.fetch_open_orders(symbol=None)
        print(f"      ✅ 成功: {len(orders)} 个开放订单")
    except Exception as e:
        print(f"      ❌ 失败: {e}")
    
    print("\n  [3] 查看智能推断的交易对")
    try:
        active_symbols = adapter._get_active_symbols_from_balance_smart()
        print(f"      ✅ 推断出 {len(active_symbols)} 个活跃交易对")
        for symbol in sorted(active_symbols)[:10]:
            print(f"         • {symbol}")
        if len(active_symbols) > 10:
            print(f"         ... 还有 {len(active_symbols) - 10} 个")
    except Exception as e:
        print(f"      ❌ 失败: {e}")

except Exception as e:
    print(f"  ❌ Adapter 初始化失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("✅ 对比完成")
print("="*80)
print()
print("💡 总结:")
print("   • 改进前：Binance 的 fetch_orders/fetch_closed_orders 必须传 symbol，否则报错")
print("   • 改进后：Adapter 会智能推断交易对，自动处理特殊情况")
print("   • 优势：统一的 API 接口，屏蔽各交易所差异")

