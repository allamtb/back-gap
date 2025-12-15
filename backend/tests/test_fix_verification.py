"""
验证 logger 错误修复

使用方法：
    python backend/tests/test_fix_verification.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exchange_adapters import get_adapter

# Binance 配置
config = {
    'apiKey': "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3",
    'secret': "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a",
    'enableRateLimit': True,
    'proxies': {
        'http': "http://127.0.0.1:1080",
        'https': "http://127.0.0.1:1080",
    }
}

def test_logger_fix():
    """测试 logger 错误是否已修复"""
    print("🧪 测试 logger 错误修复")
    print("="*70)
    
    try:
        print("\n[1/3] 创建 Binance Adapter...")
        adapter = get_adapter('binance', 'spot', config)
        print("    ✅ Adapter 创建成功")
        
        print("\n[2/3] 测试 fetch_orders(symbol=None)...")
        orders = adapter.fetch_orders(symbol=None, limit=10)
        print(f"    ✅ 成功！获取到 {len(orders)} 个订单")
        
        if orders:
            print(f"    📋 示例订单:")
            for i, order in enumerate(orders[:3], 1):
                print(f"       {i}. {order['symbol']:<15} {order['side']:<4} {order['status']}")
        
        print("\n[3/3] 测试 fetch_open_orders(symbol=None)...")
        open_orders = adapter.fetch_open_orders(symbol=None)
        print(f"    ✅ 成功！获取到 {len(open_orders)} 个开放订单")
        
        print("\n" + "="*70)
        print("✅ 所有测试通过！logger 错误已修复")
        return True
        
    except NameError as e:
        if 'logger' in str(e):
            print(f"\n❌ logger 错误仍然存在: {e}")
            return False
        else:
            raise
    
    except Exception as e:
        print(f"\n❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_logger_fix()
    exit(0 if success else 1)

