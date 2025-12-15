import ccxt
import time

# === 请填写你的Gate.io API信息 ===
api_key = "a324a7f1a8b7c3fa9fb6713eaceb666a"
api_secret = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"

# 初始化Gate.io交易所（注意：是 ccxt.gate，不是 gateio）
exchange = ccxt.gate({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'proxies': {
        'http': 'http://127.0.0.1:1080',
        'https': 'http://127.0.0.1:1080',
    },
    'timeout': 30000,  # 30秒超时
})

print("🔧 开始测试Gate.io API连接...\n")

try:
    # 1️⃣ 测试连接（获取市场数据 - 公开API）
    print("📡 测试公开API...")
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"✅ 公开API连接成功！")
    print(f"   BTC/USDT 当前价格: ${ticker['last']}")
    print(f"   24h最高: ${ticker['high']}, 24h最低: ${ticker['low']}")

    # 2️⃣ 测试私有API（获取账户余额）
    print("\n💰 获取账户余额...")
    balance = exchange.fetch_balance()

    print("✅ 私有API连接成功！")
    print("\n账户余额（仅显示非零余额）：")

    has_balance = False
    for coin, data in balance['total'].items():
        if data > 0:
            has_balance = True
            free = balance['free'].get(coin, 0)
            used = balance['used'].get(coin, 0)
            print(f"  {coin:8s}: 总计 {data:>15.8f}  (可用: {free:>15.8f}, 冻结: {used:>15.8f})")

    if not has_balance:
        print("  ⚠️ 账户余额为空")

    # 3️⃣ 获取账户信息
    print("\n📊 获取账户信息...")
    try:
        # Gate.io的账户信息方法
        if 'info' in balance:
            info = balance['info']
            # info可能是字典或列表，需要适配
            if isinstance(info, dict):
                print(f"✅ 账户信息: {list(info.keys())[:5]}")
            elif isinstance(info, list):
                print(f"✅ 账户信息: 包含 {len(info)} 个币种")
            else:
                print(f"✅ 账户信息获取成功")
        else:
            print("ℹ️ 余额信息中不包含详细账户数据")
    except Exception as e:
        print(f"⚠️ 无法获取详细账户信息: {e}")

    # 4️⃣ 测试获取持仓（如果有）
    print("\n📈 检查持仓...")
    try:
        # 尝试获取未完成订单
        open_orders = exchange.fetch_open_orders()
        if open_orders:
            print(f"✅ 发现 {len(open_orders)} 个未完成订单")
            for order in open_orders[:5]:  # 只显示前5个
                print(f"  - {order['symbol']}: {order['side']} {order['amount']} @ {order['price']}")
        else:
            print("  ℹ️ 没有未完成订单")
    except Exception as e:
        print(f"  ⚠️ 无法获取订单信息: {e}")

    # 5️⃣ 测试市场数据
    print("\n📋 测试市场数据...")
    try:
        markets = exchange.load_markets()
        spot_markets = [s for s, m in markets.items() if m.get('spot')]
        print(f"✅ Gate.io 支持 {len(spot_markets)} 个现货交易对")
        print(f"   示例交易对: {', '.join(list(markets.keys())[:5])}")
    except Exception as e:
        print(f"⚠️ 无法加载市场数据: {e}")

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！Gate.io API配置正确。")
    print("=" * 60)

except ccxt.AuthenticationError as e:
    print(f"\n❌ 认证失败：API Key或Secret错误")
    print(f"   错误详情: {str(e)}")
    print("\n💡 请检查：")
    print("   1. API Key和Secret是否正确")
    print("   2. API权限是否包含'查看余额'")
    print("   3. IP白名单设置（如果启用）")

except ccxt.NetworkError as e:
    print(f"\n❌ 网络错误：无法连接到Gate.io")
    print(f"   错误详情: {str(e)}")
    print("\n💡 请检查：")
    print("   1. 代理设置是否正确（127.0.0.1:1080）")
    print("   2. 代理是否正在运行")
    print("   3. 网络连接是否正常")

except ccxt.ExchangeError as e:
    print(f"\n❌ 交易所错误：{str(e)}")
    print("\n💡 可能的原因：")
    print("   1. API权限不足")
    print("   2. API被限流")
    print("   3. 交易所服务异常")

except Exception as e:
    print(f"\n❌ 未知错误：{str(e)}")
    print(f"   错误类型: {type(e).__name__}")
    import traceback

    print("\n详细错误信息：")
    traceback.print_exc()

