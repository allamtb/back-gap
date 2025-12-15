"""
测试 Binance 智能推断交易对功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
print("🧪 Binance 智能推断交易对测试")
print("="*80)
print()

# === 测试现货账户 ===
print("📌 现货账户")
print("-"*80)
try:
    adapter = get_adapter('binance', 'spot', BINANCE_CONFIG)
    
    # 步骤 1: 查看余额
    print("  [1] 获取账户余额")
    balance = adapter.exchange.fetch_balance()
    
    nonzero_assets = []
    for currency, amounts in balance.items():
        if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
            continue
        total = float(amounts.get('total', 0))
        if total > 0:
            nonzero_assets.append((currency, total))
    
    print(f"      ✅ 有余额的币种: {len(nonzero_assets)} 个")
    for currency, amount in sorted(nonzero_assets, key=lambda x: x[1], reverse=True)[:10]:
        print(f"         • {currency}: {amount:.8f}")
    
    # 步骤 2: 智能推断交易对
    print("\n  [2] 智能推断活跃交易对")
    active_symbols = adapter._get_active_symbols_from_balance_smart()
    
    print(f"      ✅ 推断出 {len(active_symbols)} 个交易对:")
    for symbol in sorted(active_symbols)[:15]:
        print(f"         • {symbol}")
    if len(active_symbols) > 15:
        print(f"         ... 还有 {len(active_symbols) - 15} 个")
    
    # 步骤 3: 使用推断结果获取订单
    print("\n  [3] 使用推断结果获取订单")
    orders = adapter.fetch_orders(symbol=None, since=None, limit=50)
    
    print(f"      ✅ 获取到 {len(orders)} 个订单")
    if orders:
        # 统计
        order_symbols = set()
        status_counts = {}
        for order in orders:
            order_symbols.add(order['symbol'])
            status = order.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"      📊 涉及交易对: {len(order_symbols)} 个")
        print(f"      📊 状态分布: {status_counts}")
        
        # 显示示例
        print(f"\n      📄 订单示例:")
        for i, order in enumerate(orders[:5], 1):
            order_time = order.get('orderTime', 'N/A')
            print(f"         {i}. {order['symbol']:<12} | {order['side']:<4} {order['type']:<8} | {order['status']:<10} | {order_time}")
    
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()

# === 测试合约账户 ===
print("📌 合约账户")
print("-"*80)
try:
    adapter = get_adapter('binance', 'futures', BINANCE_CONFIG)
    
    # 步骤 1: 查看余额
    print("  [1] 获取账户余额")
    balance = adapter.exchange.fetch_balance()
    
    nonzero_assets = []
    for currency, amounts in balance.items():
        if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
            continue
        total = float(amounts.get('total', 0))
        if total > 0:
            nonzero_assets.append((currency, total))
    
    print(f"      ✅ 有余额的币种: {len(nonzero_assets)} 个")
    for currency, amount in sorted(nonzero_assets, key=lambda x: x[1], reverse=True)[:10]:
        print(f"         • {currency}: {amount:.8f}")
    
    # 步骤 2: 智能推断交易对
    print("\n  [2] 智能推断活跃交易对")
    active_symbols = adapter._get_active_symbols_from_balance_smart()
    
    print(f"      ✅ 推断出 {len(active_symbols)} 个交易对:")
    for symbol in sorted(active_symbols)[:15]:
        print(f"         • {symbol}")
    if len(active_symbols) > 15:
        print(f"         ... 还有 {len(active_symbols) - 15} 个")
    
    # 步骤 3: 使用推断结果获取订单
    print("\n  [3] 使用推断结果获取订单")
    orders = adapter.fetch_orders(symbol=None, since=None, limit=50)
    
    print(f"      ✅ 获取到 {len(orders)} 个订单")
    if orders:
        # 统计
        order_symbols = set()
        status_counts = {}
        for order in orders:
            order_symbols.add(order['symbol'])
            status = order.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"      📊 涉及交易对: {len(order_symbols)} 个")
        print(f"      📊 状态分布: {status_counts}")
        
        # 显示示例
        print(f"\n      📄 订单示例:")
        for i, order in enumerate(orders[:5], 1):
            order_time = order.get('orderTime', 'N/A')
            print(f"         {i}. {order['symbol']:<12} | {order['side']:<4} {order['type']:<8} | {order['status']:<10} | {order_time}")
    
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("✅ 测试完成")
print("="*80)

