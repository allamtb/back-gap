import ccxt
import datetime
import time

# === 1. 填入你的币安 API 信息 ===
api_key = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
api_secret = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"

# === 2. 是否使用代理 ===
use_proxy = True
proxy_url = "http://127.0.0.1:1080"  # 改成你的代理地址

# === 3. 初始化交易所对象 ===
exchange = ccxt.binance({
    "apiKey": api_key,
    "secret": api_secret,
    "enableRateLimit": True,
})

if use_proxy:
    exchange.proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

# === 4. 第一步：获取余额中非零资产 ===
print("📊 正在获取账户余额...")
balances = exchange.fetch_balance()

nonzero_assets = [asset for asset, amount in balances['total'].items() if amount and amount > 0]
print(f"账户中存在余额的资产: {nonzero_assets}\n")

# === 5. 第二步：尝试组合交易对并检查是否有成交记录 ===
print("🔍 正在检测这些币种是否有交易历史...\n")

possible_symbols = []
for asset in nonzero_assets:
    if asset in ["USDT", "BUSD", "FDUSD"]:  # 稳定币不用查
        continue

    # 构造常见交易对
    for quote in ["USDT", "BUSD", "FDUSD"]:
        symbol = f"{asset}/{quote}"
        if symbol in exchange.load_markets():
            possible_symbols.append(symbol)

traded_symbols = []

for symbol in possible_symbols:
    try:
        trades = exchange.fetch_my_trades(symbol, limit=3)
        if trades:
            traded_symbols.append(symbol)
            print(f"✅ 你交易过: {symbol} （最近 {len(trades)} 条）")
        time.sleep(0.3)  # 限速保护
    except ccxt.BaseError:
        continue

# === 6. 输出结果 ===
if traded_symbols:
    print("\n=== ✅ 你曾经交易过的交易对 ===")
    for s in traded_symbols:
        print(s)
else:
    print("\n⚠️ 未检测到任何交易记录。")

print("\n完成时间：", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
