"""
测试 Binance 智能订单获取（使用改进后的 Adapter）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exchange_adapters import get_adapter

# === 配置 ===
api_key = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
api_secret = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"
proxy_url = "http://127.0.0.1:1080"

config = {
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'proxies': {
        'http': proxy_url,
        'https': proxy_url,
    }
}

print("="*80)
print("🧪 Binance Adapter 智能订单获取测试")
print("="*80)
print()

# === 测试 1: 使用 Adapter 获取现货订单（symbol=None）===
print("📌 测试 1: Adapter.fetch_orders(symbol=None) - 现货")
print("-"*80)
try:
    adapter = get_adapter('binance', 'spot', config)
    
    # 不传 symbol，让 Adapter 自动推断
    orders = adapter.fetch_orders(symbol=None, since=None, limit=50)
    
    print(f"✅ 成功获取 {len(orders)} 个订单")
    
    if orders:
        print(f"\n示例订单:")
        for i, order in enumerate(orders[:3], 1):  # 显示前3个
            print(f"  {i}. {order['symbol']} | {order['side']} | {order['status']} | {order['orderTime']}")
    else:
        print("  ℹ️  最近无订单记录")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()

# === 测试 2: 使用 Adapter 获取合约订单 ===
print("📌 测试 2: Adapter.fetch_orders(symbol=None) - 合约")
print("-"*80)
try:
    adapter = get_adapter('binance', 'futures', config)
    
    orders = adapter.fetch_orders(symbol=None, since=None, limit=50)
    
    print(f"✅ 成功获取 {len(orders)} 个订单")
    
    if orders:
        print(f"\n示例订单:")
        for i, order in enumerate(orders[:3], 1):
            print(f"  {i}. {order['symbol']} | {order['side']} | {order['status']} | {order['orderTime']}")
    else:
        print("  ℹ️  最近无订单记录")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()

# === 测试 3: 测试智能推断方法 ===
print("📌 测试 3: 智能推断活跃交易对")
print("-"*80)
try:
    adapter = get_adapter('binance', 'spot', config)
    
    # 调用内部方法查看推断结果
    active_symbols = adapter._get_active_symbols_from_balance_smart()
    
    print(f"✅ 推断出 {len(active_symbols)} 个活跃交易对:")
    for symbol in active_symbols:
        print(f"  • {symbol}")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("✅ 测试完成")
print("="*80)

