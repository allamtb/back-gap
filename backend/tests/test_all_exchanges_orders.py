"""
完整测试：对比各交易所的订单获取能力（使用 Adapter）
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

GATEIO_CONFIG = {
    'apiKey': "50b3601fccedd8fa41b9a5fc21f1bcff",
    'secret': "9c19fef6ece1a57ec9473fc4a52ac58e9da60c44fcd6bc92a9eb75b0aff0efcb",
    'enableRateLimit': True,
    'proxies': {
        'http': "http://127.0.0.1:1080",
        'https': "http://127.0.0.1:1080",
    }
}

OKX_CONFIG = {
    'apiKey': "97e03d11-20ed-4699-892c-2ff5aee0b3d6",
    'secret': "4D12A7D2F54E4B2C2CE90C6BFD6208F4",
    'password': "Abc123456!",
    'enableRateLimit': True,
    'proxies': {
        'http': "http://127.0.0.1:1080",
        'https': "http://127.0.0.1:1080",
    }
}

EXCHANGES = [
    ('binance', 'spot', BINANCE_CONFIG),
    ('binance', 'futures', BINANCE_CONFIG),
    ('gate', 'spot', GATEIO_CONFIG),
    ('okx', 'spot', OKX_CONFIG),
]

print("="*80)
print("🧪 完整测试：各交易所订单获取（使用改进后的 Adapter）")
print("="*80)
print()

for exchange_id, market_type, config in EXCHANGES:
    print(f"📌 {exchange_id.upper()} - {market_type}")
    print("-"*80)
    
    try:
        adapter = get_adapter(exchange_id, market_type, config)
        
        # 测试 1: fetch_orders(symbol=None)
        print("  [1] fetch_orders(symbol=None)")
        try:
            orders = adapter.fetch_orders(symbol=None, since=None, limit=50)
            print(f"      ✅ 成功: {len(orders)} 个订单")
            
            if orders:
                # 统计订单状态
                status_counts = {}
                symbols = set()
                for order in orders:
                    status = order.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    symbols.add(order.get('symbol', 'unknown'))
                
                print(f"      📊 状态分布: {status_counts}")
                print(f"      📊 涉及交易对: {len(symbols)} 个")
                
                # 显示前2个订单
                print(f"      📄 示例订单:")
                for i, order in enumerate(orders[:2], 1):
                    print(f"         {i}. {order['symbol']} | {order['side']} {order['type']} | {order['status']} | {order.get('orderTime', 'N/A')}")
        except Exception as e:
            print(f"      ❌ 失败: {e}")
        
        # 测试 2: fetch_open_orders(symbol=None)
        print("  [2] fetch_open_orders(symbol=None)")
        try:
            orders = adapter.fetch_open_orders(symbol=None)
            print(f"      ✅ 成功: {len(orders)} 个开放订单")
        except Exception as e:
            print(f"      ❌ 失败: {e}")
        
        print()
    
    except Exception as e:
        print(f"  ❌ Adapter 创建失败: {e}")
        print()

print("="*80)
print("✅ 测试完成")
print("="*80)

