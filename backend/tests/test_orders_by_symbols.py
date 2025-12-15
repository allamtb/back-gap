#!/usr/bin/env python3
"""
测试 /api/orders/by-symbols 端点
查询指定交易所的特定币种订单
"""

import sys
import os
import json
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_config():
    """从配置文件加载交易所凭证"""
    config_path = project_root / "data" / "config.json"
    
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        print("提示: 请创建 backend/data/config.json 并配置交易所 API 密钥")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return None


def find_exchange_credentials(config, exchange_name):
    """从配置中查找指定交易所的凭证"""
    if not config or 'exchanges' not in config:
        return None
    
    for exchange_config in config['exchanges']:
        if exchange_config.get('exchange', '').lower() == exchange_name.lower():
            return exchange_config
    
    return None


def test_orders_by_symbols(api_url="http://16.163.163:8000", api_key="", api_secret=""):
    """测试按币种查询订单"""
    
    print("=" * 80)
    print("🔍 测试 /api/orders/by-symbols 端点")
    print("=" * 80)
    print()
    
    # 检查是否提供了 API 密钥
    if not api_key or not api_secret:
        print("❌ 请提供 API 密钥")
        print()
        print("使用方法:")
        print("  python test_orders_by_symbols.py")
        print()
        print("然后在脚本中修改 main() 函数中的 api_key 和 api_secret 参数")
        return
    
    print(f"🔑 使用币安凭证 (API Key: {api_key[:8]}...)")
    print()
    
    # 构建请求
    url = f"{api_url}/api/orders/by-symbols"
    
    payload = {
        "symbols": ["ETH"],  # 查询 BTC 订单
        "credentials": [
            {
                "exchange": "binance",
                "apiKey": api_key,
                "apiSecret": api_secret
            }
        ],
        "limit": 50
    }
    
    print(f"📤 发送请求到: {url}")
    print(f"📋 查询币种: {payload['symbols']}")
    print(f"🏢 交易所: {payload['credentials'][0]['exchange']}")
    print()
    
    # 4. 发送请求
    try:
        print("⏳ 查询中...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return
        
        result = response.json()
        
        print()
        print("=" * 80)
        print("✅ 查询成功!")
        print("=" * 80)
        print()
        
        # 5. 显示结果
        if not result.get('success'):
            print("❌ 查询失败")
            print(f"错误: {result}")
            return
        
        orders = result.get('data', [])
        total = result.get('total', 0)
        elapsed = result.get('elapsed', 0)
        
        print(f"📊 统计信息:")
        print(f"   总订单数: {total}")
        print(f"   查询耗时: {elapsed:.2f} 秒")
        print()
        
        if total == 0:
            print("📭 未找到 BTC 订单")
            print()
            print("可能的原因:")
            print("1. 该账户确实没有 BTC 订单")
            print("2. BTC 订单已超出查询时间范围")
            print("3. 交易所 API 限制了历史订单查询")
            return
        
        # 6. 显示订单详情
        print(f"📋 BTC 订单列表 (共 {total} 条):")
        print("-" * 80)
        print(f"{'时间':<20} {'交易所':<10} {'市场':<8} {'交易对':<15} {'方向':<6} {'类型':<8} {'价格':<12} {'数量':<12} {'状态':<10}")
        print("-" * 80)
        
        for order in orders[:20]:  # 只显示前20条
            # 解析时间
            timestamp = order.get('timestamp', 0)
            if timestamp:
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = 'N/A'
            
            # 提取订单信息
            exchange = order.get('exchange', 'N/A')
            market_type = order.get('marketType', 'N/A')
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A')
            order_type = order.get('type', 'N/A')
            price = order.get('price', 0)
            amount = order.get('amount', 0)
            status = order.get('status', 'N/A')
            
            # 格式化价格和数量
            price_str = f"{price:,.2f}" if price else 'market'
            amount_str = f"{amount:.6f}"
            
            # 方向标识
            side_icon = "🟢" if side == "buy" else "🔴"
            side_display = f"{side_icon} {side.upper()}"
            
            # 状态标识
            status_map = {
                'closed': '✅ 已成交',
                'open': '⏳ 未成交',
                'canceled': '❌ 已取消',
                'cancelled': '❌ 已取消'
            }
            status_display = status_map.get(status.lower(), status)
            print(order)
            print(f"{time_str:<20} {exchange:<10} {market_type:<8} {symbol:<15} {side_display:<6} {order_type:<8} {price_str:<12} {amount_str:<12} {status_display:<10}")
        
        if total > 20:
            print(f"\n... 还有 {total - 20} 条订单未显示")
        
        print("-" * 80)
        print()
        
        # 7. 统计分析
        buy_count = sum(1 for o in orders if o.get('side') == 'buy')
        sell_count = sum(1 for o in orders if o.get('side') == 'sell')
        closed_count = sum(1 for o in orders if o.get('status') in ['closed', 'filled'])
        
        spot_count = sum(1 for o in orders if o.get('marketType') == 'spot')
        futures_count = sum(1 for o in orders if o.get('marketType') == 'futures')
        
        print("📈 订单分析:")
        print(f"   买入订单: {buy_count}")
        print(f"   卖出订单: {sell_count}")
        print(f"   已成交: {closed_count} ({closed_count/total*100:.1f}%)" if total > 0 else "   已成交: 0")
        print()
        print(f"   现货订单: {spot_count}")
        print(f"   合约订单: {futures_count}")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 无法连接到后端服务")
        print("提示: 请确保后端服务已启动 (python backend/run.py)")
    except requests.exceptions.Timeout:
        print("❌ 请求超时: 查询时间过长")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print()
    
    # ============================================================================
    # 配置参数 - 请在这里修改你的 API 密钥
    # ============================================================================
    API_URL = "http://16.163.163.204:8000"
    
    # 币安 API 密钥 - 请替换为你的实际密钥
    BINANCE_API_KEY = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
    BINANCE_API_SECRET = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"

    
    # ============================================================================
    
    # 检查后端是否运行
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
            print()
        else:
            print("⚠️ 后端服务可能未正常运行")
            print()
    except:
        print("❌ 无法连接到后端服务")
        print(f"提示: 请确保后端服务已在 {API_URL} 启动")
        print()
        return
    
    # 运行测试
    test_orders_by_symbols(
        api_url=API_URL,
        api_key=BINANCE_API_KEY,
        api_secret=BINANCE_API_SECRET
    )
    
    print()
    print("=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()

