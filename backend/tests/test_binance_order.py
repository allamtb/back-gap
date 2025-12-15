"""
币安下单测试脚本

功能：
1. 测试现货限价单
2. 测试现货市价单
3. 测试合约限价单
4. 测试合约市价单
5. 测试订单查询
6. 测试订单取消

使用方法：
1. 设置环境变量 PROXY_URL（如需要）
2. 在代码中填入你的 API Key 和 Secret
3. 运行: python -m tests.test_binance_order
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from exchange_adapters import get_adapter
import ccxt


# ============================================================================
# 配置区域 - 请填入你的 API 凭证
# ============================================================================

BINANCE_CONFIG = {
    'apiKey': 'lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3',  # 🔑 替换为你的 Binance API Key
    'secret': 'mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a',  # 🔑 替换为你的 Binance API Secret
    'enableRateLimit': True,
    'timeout': 30000,
}

# 测试参数
TEST_SYMBOL = 'BTC/USDT'  # 测试交易对
TEST_AMOUNT = 0.001  # 测试数量（BTC）
TEST_PRICE_OFFSET = 0.7  # 限价单价格偏移（当前价格的 70%，确保不会成交）


# ============================================================================
# 测试函数
# ============================================================================

async def test_spot_limit_order():
    """测试现货限价买单"""
    print("\n" + "="*80)
    print("🧪 测试 1: 币安现货限价买单")
    print("="*80)
    
    try:
        # 创建现货适配器
        adapter = get_adapter(
            exchange_id='binance',
            market_type='spot',
            config=BINANCE_CONFIG
        )
        
        # 获取当前价格
        exchange = adapter.get_exchange()
        ticker = exchange.fetch_ticker(TEST_SYMBOL)
        current_price = ticker['last']
        
        # 设置一个很低的价格（确保不会成交）
        test_price = round(current_price * TEST_PRICE_OFFSET, 2)
        
        print(f"📊 当前价格: {current_price} USDT")
        print(f"📝 测试价格: {test_price} USDT (当前价格的 {TEST_PRICE_OFFSET*100}%)")
        print(f"📝 测试数量: {TEST_AMOUNT} BTC")
        
        # 创建限价买单
        print(f"\n⏳ 创建限价买单...")
        order = await adapter.create_order(
            symbol=TEST_SYMBOL,
            type='limit',
            side='buy',
            amount=TEST_AMOUNT,
            price=test_price
        )
        
        print(f"✅ 订单创建成功!")
        print(f"   订单 ID: {order.get('id')}")
        print(f"   状态: {order.get('status')}")
        print(f"   类型: {order.get('type')}")
        print(f"   方向: {order.get('side')}")
        print(f"   价格: {order.get('price')}")
        print(f"   数量: {order.get('amount')}")
        
        # 返回订单 ID 用于后续测试
        return order.get('id')
        
    except ccxt.InsufficientFunds as e:
        print(f"❌ 余额不足: {e}")
        return None
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_query_order(order_id: str):
    """测试查询订单"""
    print("\n" + "="*80)
    print(f"🧪 测试 2: 查询订单 (ID: {order_id})")
    print("="*80)
    
    try:
        adapter = get_adapter(
            exchange_id='binance',
            market_type='spot',
            config=BINANCE_CONFIG
        )
        
        exchange = adapter.get_exchange()
        
        print(f"⏳ 查询订单...")
        order = exchange.fetch_order(order_id, TEST_SYMBOL)
        
        print(f"✅ 查询成功!")
        print(f"   订单 ID: {order.get('id')}")
        print(f"   状态: {order.get('status')}")
        print(f"   类型: {order.get('type')}")
        print(f"   方向: {order.get('side')}")
        print(f"   价格: {order.get('price')}")
        print(f"   数量: {order.get('amount')}")
        print(f"   已成交: {order.get('filled', 0)}")
        print(f"   剩余: {order.get('remaining', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


async def test_cancel_order(order_id: str):
    """测试取消订单"""
    print("\n" + "="*80)
    print(f"🧪 测试 3: 取消订单 (ID: {order_id})")
    print("="*80)
    
    try:
        adapter = get_adapter(
            exchange_id='binance',
            market_type='spot',
            config=BINANCE_CONFIG
        )
        
        exchange = adapter.get_exchange()
        
        print(f"⏳ 取消订单...")
        result = exchange.cancel_order(order_id, TEST_SYMBOL)
        
        print(f"✅ 取消成功!")
        print(f"   订单 ID: {result.get('id')}")
        print(f"   状态: {result.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 取消失败: {e}")
        return False


async def test_fetch_balance():
    """测试查询余额"""
    print("\n" + "="*80)
    print("🧪 测试 4: 查询余额")
    print("="*80)
    
    try:
        adapter = get_adapter(
            exchange_id='binance',
            market_type='spot',
            config=BINANCE_CONFIG
        )
        
        print(f"⏳ 查询余额...")
        balance = adapter.fetch_balance()
        
        # 只显示有余额的币种
        print(f"✅ 查询成功!")
        print(f"\n💰 有余额的币种:")
        
        for currency, amounts in balance.items():
            if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
                continue
            
            total = amounts.get('total', 0)
            if total and float(total) > 0:
                free = amounts.get('free', 0)
                used = amounts.get('used', 0)
                print(f"   {currency:8s}: 总计={total:12.8f}  可用={free:12.8f}  冻结={used:12.8f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


async def test_fetch_open_orders():
    """测试查询开放订单"""
    print("\n" + "="*80)
    print("🧪 测试 5: 查询开放订单")
    print("="*80)
    
    try:
        adapter = get_adapter(
            exchange_id='binance',
            market_type='spot',
            config=BINANCE_CONFIG
        )
        
        print(f"⏳ 查询开放订单...")
        
        # 方法 1: 查询指定交易对
        orders_symbol = adapter.fetch_open_orders(symbol=TEST_SYMBOL)
        print(f"✅ {TEST_SYMBOL} 的开放订单: {len(orders_symbol)} 个")
        
        # 方法 2: 查询所有开放订单（使用 Adapter 的智能推断）
        orders_all = adapter.fetch_open_orders()
        print(f"✅ 所有开放订单: {len(orders_all)} 个")
        
        # 显示订单详情
        if orders_all:
            print(f"\n📋 订单列表:")
            for order in orders_all[:5]:  # 只显示前 5 个
                print(f"   {order.get('symbol'):12s} {order.get('side'):4s} "
                      f"{order.get('type'):6s} {order.get('amount'):10.8f} @ "
                      f"{order.get('price', 'market'):10s} - {order.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_futures_limit_order():
    """测试合约限价买单"""
    print("\n" + "="*80)
    print("🧪 测试 6: 币安合约限价买单")
    print("="*80)
    
    try:
        # 创建合约适配器
        adapter = get_adapter(
            exchange_id='binance',
            market_type='futures',
            config=BINANCE_CONFIG
        )
        
        # 获取当前价格
        exchange = adapter.get_exchange()
        ticker = exchange.fetch_ticker(TEST_SYMBOL)
        current_price = ticker['last']
        
        # 设置一个很低的价格（确保不会成交）
        test_price = round(current_price * TEST_PRICE_OFFSET, 2)
        
        print(f"📊 当前价格: {current_price} USDT")
        print(f"📝 测试价格: {test_price} USDT (当前价格的 {TEST_PRICE_OFFSET*100}%)")
        print(f"📝 测试数量: {TEST_AMOUNT} BTC")
        
        # 创建限价买单
        print(f"\n⏳ 创建合约限价买单...")
        order = await adapter.create_order(
            symbol=TEST_SYMBOL,
            type='limit',
            side='buy',
            amount=TEST_AMOUNT,
            price=test_price
        )
        
        print(f"✅ 订单创建成功!")
        print(f"   订单 ID: {order.get('id')}")
        print(f"   状态: {order.get('status')}")
        print(f"   类型: {order.get('type')}")
        print(f"   方向: {order.get('side')}")
        print(f"   价格: {order.get('price')}")
        print(f"   数量: {order.get('amount')}")
        
        # 自动取消订单
        print(f"\n⏳ 自动取消订单...")
        exchange.cancel_order(order.get('id'), TEST_SYMBOL)
        print(f"✅ 订单已取消")
        
        return order.get('id')
        
    except ccxt.InsufficientFunds as e:
        print(f"❌ 余额不足: {e}")
        return None
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# 主测试流程
# ============================================================================

async def main():
    """主测试流程"""
    print("\n" + "🚀"*40)
    print("币安下单完整测试")
    print("🚀"*40)
    
    # 检查配置
    if BINANCE_CONFIG['apiKey'] == 'YOUR_API_KEY':
        print("\n❌ 错误: 请先在脚本中配置你的 Binance API Key 和 Secret!")
        print("   编辑文件: backend/tests/test_binance_order.py")
        print("   修改 BINANCE_CONFIG 字典中的 apiKey 和 secret")
        return
    
    # 显示代理配置
    proxy_url = os.getenv('PROXY_URL')
    if proxy_url:
        print(f"\n🌐 代理配置: {proxy_url}")
    else:
        print(f"\n🌐 代理配置: 未设置（直连）")
    
    try:
        # 测试 1: 查询余额
        await test_fetch_balance()
        
        # 等待 1 秒
        await asyncio.sleep(1)
        
        # 测试 2: 查询开放订单
        await test_fetch_open_orders()
        
        # 等待 1 秒
        await asyncio.sleep(1)
        
        # 测试 3: 创建现货限价单
        order_id = await test_spot_limit_order()
        
        if order_id:
            # 等待 2 秒
            await asyncio.sleep(2)
            
            # 测试 4: 查询订单
            await test_query_order(order_id)
            
            # 等待 1 秒
            await asyncio.sleep(1)
            
            # 测试 5: 取消订单
            await test_cancel_order(order_id)
        
        # 等待 2 秒
        await asyncio.sleep(2)
        
        # 测试 6: 合约限价单（可选）
        # await test_futures_limit_order()
        
        print("\n" + "="*80)
        print("🎉 测试完成!")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())

