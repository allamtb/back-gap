#!/usr/bin/env python3
"""
简单的 CCXT 订单查询工具
直接使用 CCXT 查询指定交易所的现货订单
"""

import ccxt
import os
from datetime import datetime


def query_orders(exchange_name, api_key, api_secret, coin="BTC", password=None):
    """
    查询指定交易所的现货订单
    
    参数:
        exchange_name: 交易所名称，如 'binance', 'okx', 'gate'
        api_key: API 密钥
        api_secret: API 密钥密码
        coin: 币种，如 'BTC', 'ETH'
        password: 部分交易所需要的密码（如 OKX）
    """
    print("=" * 80)
    print(f"🔍 查询 {exchange_name.upper()} 现货 {coin} 订单")
    print("=" * 80)
    print()
    
    try:
        # 1. 创建交易所实例
        print(f"📡 连接到 {exchange_name}...")
        exchange_class = getattr(ccxt, exchange_name)
        
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # 现货市场
            }
        }
        
        # 如果有密码，添加到配置
        if password:
            config['password'] = password
        
        # 如果有代理，使用代理
        proxy_url = os.getenv('PROXY_URL', 'http://127.0.0.1:1080')
        if proxy_url:
            config['proxies'] = {
                'http': proxy_url,
                'https': proxy_url,
            }
            print(f"🌐 使用代理: {proxy_url}")
        
        exchange = exchange_class(config)
        
        # 2. 加载市场数据
        print("📥 加载市场数据...")
        exchange.load_markets()
        print(f"✅ 已加载 {len(exchange.markets)} 个交易对")
        print()
        
        # 3. 查找包含该币种的交易对
        print(f"🔎 查找 {coin} 相关的交易对...")
        symbols = []
        for symbol in exchange.markets:
            if symbol.startswith(f"{coin}/"):
                symbols.append(symbol)
        
        if not symbols:
            print(f"❌ 未找到 {coin} 相关的交易对")
            return
        
        print(f"✅ 找到 {len(symbols)} 个交易对: {', '.join(symbols[:5])}")
        if len(symbols) > 5:
            print(f"   ... 还有 {len(symbols) - 5} 个")
        print()
        
        # 4. 查询所有订单
        print("⏳ 查询订单中...")
        all_orders = []
        
        for symbol in symbols:
            try:
                # 获取所有订单（包括 open 和 closed）
                orders = exchange.fetch_orders(symbol)
                if orders:
                    all_orders.extend(orders)
                    print(f"  ✓ {symbol}: {len(orders)} 条订单")
            except Exception as e:
                # 某些交易对可能无法查询，跳过
                if "does not have market symbol" not in str(e):
                    print(f"  ⚠ {symbol}: {str(e)[:50]}")
        
        print()
        
        # 5. 显示结果
        if not all_orders:
            print(f"📭 未找到 {coin} 订单")
            print()
            print("可能的原因:")
            print("1. 该账户确实没有该币种的订单")
            print("2. 订单已超出查询时间范围")
            print("3. 交易所 API 限制了历史订单查询")
            return
        
        print("=" * 80)
        print(f"✅ 查询成功! 共找到 {len(all_orders)} 条订单")
        print("=" * 80)
        print()
        
        # 6. 统计分析
        open_orders = [o for o in all_orders if o['status'] == 'open']
        closed_orders = [o for o in all_orders if o['status'] == 'closed']
        canceled_orders = [o for o in all_orders if o['status'] in ['canceled', 'cancelled']]
        
        buy_orders = [o for o in all_orders if o['side'] == 'buy']
        sell_orders = [o for o in all_orders if o['side'] == 'sell']
        
        print(f"📊 统计信息:")
        print(f"   总订单数: {len(all_orders)}")
        print(f"   未成交: {len(open_orders)} ⏳")
        print(f"   已成交: {len(closed_orders)} ✅")
        print(f"   已取消: {len(canceled_orders)} ❌")
        print()
        print(f"   买入: {len(buy_orders)}")
        print(f"   卖出: {len(sell_orders)}")
        print()
        
        # 7. 显示订单详情
        print("📋 订单列表:")
        print("-" * 120)
        print(f"{'时间':<20} {'交易对':<15} {'方向':<8} {'类型':<10} {'价格':<15} {'数量':<15} {'状态':<12}")
        print("-" * 120)
        
        # 按时间倒序排序
        all_orders.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        for order in all_orders[:50]:  # 只显示前50条
            # 解析时间
            timestamp = order.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = 'N/A'
            
            # 提取订单信息
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A')
            order_type = order.get('type', 'N/A')
            price = order.get('price', 0)
            amount = order.get('amount', 0)
            status = order.get('status', 'N/A')
            
            # 格式化
            price_str = f"{price:,.2f}" if price else 'market'
            amount_str = f"{amount:.8f}".rstrip('0').rstrip('.')
            
            # 方向标识
            side_icon = "🟢" if side == "buy" else "🔴"
            side_display = f"{side_icon} {side.upper()}"
            
            # 状态标识
            status_map = {
                'open': '⏳ 未成交',
                'closed': '✅ 已成交',
                'canceled': '❌ 已取消',
                'cancelled': '❌ 已取消'
            }
            status_display = status_map.get(status, status)
            
            print(f"{time_str:<20} {symbol:<15} {side_display:<8} {order_type:<10} {price_str:<15} {amount_str:<15} {status_display:<12}")
        
        if len(all_orders) > 50:
            print(f"\n... 还有 {len(all_orders) - 50} 条订单未显示")
        
        print("-" * 120)
        print()
        
        # 8. 显示未成交订单详情
        if open_orders:
            print("⏳ 未成交订单详情:")
            print("-" * 120)
            for order in open_orders[:20]:
                timestamp = order.get('timestamp', 0)
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = 'N/A'
                
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                price = order.get('price', 0)
                amount = order.get('amount', 0)
                filled = order.get('filled', 0)
                remaining = order.get('remaining', amount - filled)
                
                side_icon = "🟢" if side == "buy" else "🔴"
                
                print(f"  {time_str} | {symbol:<15} | {side_icon} {side.upper():<6} | "
                      f"价格: {price:,.2f} | 数量: {amount:.8f} | 已成交: {filled:.8f} | 剩余: {remaining:.8f}")
            
            if len(open_orders) > 20:
                print(f"  ... 还有 {len(open_orders) - 20} 条未成交订单")
            print("-" * 120)
            print()
        
    except ccxt.AuthenticationError as e:
        print(f"❌ 认证失败: {e}")
        print("提示: 请检查 API Key 和 Secret 是否正确")
    except ccxt.NetworkError as e:
        print(f"❌ 网络错误: {e}")
        print("提示: 请检查网络连接和代理设置")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("🚀 CCXT 订单查询工具")
    print("=" * 80)
    print()
    
    # ============================================================================
    # 配置参数 - 请在这里修改你的参数
    # ============================================================================
    
    EXCHANGE = "binance"  # 交易所: binance, okx, gate, bybit 等
    API_KEY = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
    API_SECRET = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"
    COIN = "BTC"  # 要查询的币种
    PASSWORD = None  # 部分交易所需要（如 OKX、KuCoin）
    
    # ============================================================================
    
    # 运行查询
    query_orders(
        exchange_name=EXCHANGE,
        api_key=API_KEY,
        api_secret=API_SECRET,
        coin=COIN,
        password=PASSWORD
    )
    
    print()
    print("=" * 80)
    print("✅ 查询完成!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()

