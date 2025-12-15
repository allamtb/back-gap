import ccxt

# === 请填写你子账户的API信息 ===
api_key = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
api_secret = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"

# 初始化币安交易所
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'proxies': {
        'http': 'http://127.0.0.1:1080',
        'https': 'http://127.0.0.1:1080',
    }
})

try:
    # 1️⃣ 测试连接（获取服务器时间）
    server_time = exchange.public_get_time()
    print("✅ API连接成功，服务器时间：", server_time['serverTime'])

    # 2️⃣ 获取账户余额
    balance = exchange.fetch_balance()
    print("\n💰 子账户余额：")
    for coin, data in balance['total'].items():
        if data > 0:
            print(f"{coin}: {data}")

    # 3️⃣ （可选）测试下单（注意：这是真实下单！）
    # order = exchange.create_order(
    #     symbol='BTC/USDT',
    #     type='limit',
    #     side='buy',
    #     amount=0.001,
    #     price=30000
    # )
    # print("\n📦 下单成功：", order)

except ccxt.BaseError as e:
    print("❌ 出错了：", str(e))
