"""
币安下单快速测试脚本（简化版）

使用方法：
1. 设置环境变量（可选）:
   set PROXY_URL=http://127.0.0.1:7890  # Windows
   export PROXY_URL=http://127.0.0.1:7890  # Linux/Mac

2. 运行测试:
   python backend/tests/quick_test_binance.py

测试流程：
- 查询余额
- 创建一个超低价的限价买单（不会成交）
- 查询订单
- 取消订单
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from exchange_adapters import get_adapter
import ccxt


def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


async def quick_test():
    """快速测试"""
    
    # ============================================================================
    # 🔑 配置 API 凭证
    # ============================================================================
    
    API_KEY = input("请输入 Binance API Key: ").strip()
    API_SECRET = input("请输入 Binance API Secret: ").strip()
    
    if not API_KEY or not API_SECRET:
        print("❌ API Key 和 Secret 不能为空!")
        return
    
    config = {
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
    }
    
    # 显示代理配置
    proxy = os.getenv('PROXY_URL', '未设置')
    print(f"\n🌐 代理: {proxy}")
    
    try:
        # ========================================================================
        # 步骤 1: 查询余额
        # ========================================================================
        
        print_section("📊 步骤 1: 查询余额")
        
        adapter = get_adapter('binance', 'spot', config)
        balance = adapter.fetch_balance()
        
        print("💰 有余额的币种:")
        for currency, amounts in balance.items():
            if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
                continue
            
            total = amounts.get('total', 0)
            if total and float(total) > 0:
                print(f"  {currency:8s}: {total:12.8f}")
        
        # ========================================================================
        # 步骤 2: 获取当前价格
        # ========================================================================
        
        print_section("📈 步骤 2: 获取 BTC/USDT 价格")
        
        exchange = adapter.get_exchange()
        ticker = exchange.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        
        print(f"  当前价格: {current_price} USDT")
        
        # ========================================================================
        # 步骤 3: 创建超低价限价单（不会成交）
        # ========================================================================
        
        print_section("📝 步骤 3: 创建测试订单")
        
        test_price = round(current_price * 0.5, 2)  # 当前价格的 50%
        test_amount = 0.001  # 0.001 BTC
        
        print(f"  交易对: BTC/USDT")
        print(f"  方向: 买入")
        print(f"  类型: 限价单")
        print(f"  价格: {test_price} USDT (当前价格的 50%，不会成交)")
        print(f"  数量: {test_amount} BTC")
        
        confirm = input("\n是否创建订单? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 已取消")
            return
        
        print("\n⏳ 创建订单中...")
        order = await adapter.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=test_amount,
            price=test_price
        )
        
        order_id = order.get('id')
        print(f"✅ 订单创建成功!")
        print(f"  订单 ID: {order_id}")
        print(f"  状态: {order.get('status')}")
        
        # ========================================================================
        # 步骤 4: 查询订单
        # ========================================================================
        
        print_section("🔍 步骤 4: 查询订单")
        
        await asyncio.sleep(1)  # 等待 1 秒
        
        order_info = exchange.fetch_order(order_id, 'BTC/USDT')
        print(f"  订单 ID: {order_info.get('id')}")
        print(f"  状态: {order_info.get('status')}")
        print(f"  价格: {order_info.get('price')}")
        print(f"  数量: {order_info.get('amount')}")
        print(f"  已成交: {order_info.get('filled', 0)}")
        
        # ========================================================================
        # 步骤 5: 取消订单
        # ========================================================================
        
        print_section("❌ 步骤 5: 取消订单")
        
        confirm = input("\n是否取消订单? (y/n): ").strip().lower()
        if confirm == 'y':
            print("\n⏳ 取消订单中...")
            result = exchange.cancel_order(order_id, 'BTC/USDT')
            print(f"✅ 订单已取消!")
            print(f"  订单 ID: {result.get('id')}")
        else:
            print(f"⚠️ 订单未取消，请手动取消 (ID: {order_id})")
        
        # ========================================================================
        # 完成
        # ========================================================================
        
        print_section("🎉 测试完成")
        print("所有步骤执行成功!")
        
    except ccxt.AuthenticationError as e:
        print(f"\n❌ 认证失败: {e}")
        print("   请检查 API Key 和 Secret 是否正确")
    
    except ccxt.InsufficientFunds as e:
        print(f"\n❌ 余额不足: {e}")
        print("   请确保账户有足够的 USDT")
    
    except ccxt.InvalidOrder as e:
        print(f"\n❌ 无效订单: {e}")
    
    except ccxt.NetworkError as e:
        print(f"\n❌ 网络错误: {e}")
        print("   请检查网络连接或代理配置")
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("      币安下单快速测试")
    print("🚀"*30)
    
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")

