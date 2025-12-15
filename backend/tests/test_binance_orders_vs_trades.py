"""
对比测试：Binance 的 fetch_orders vs fetch_my_trades
"""

import ccxt
import datetime

# === 配置 ===
api_key = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
api_secret = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"
proxy_url = "http://127.0.0.1:1080"

# === 初始化 ===
exchange = ccxt.binance({
    "apiKey": api_key,
    "secret": api_secret,
    "enableRateLimit": True,
    "proxies": {
        "http": proxy_url,
        "https": proxy_url,
    }
})

print("="*80)
print("🧪 Binance API 方法对比测试")
print("="*80)
print()

# === 测试 1: fetch_my_trades（你的测试代码，成功的）===
print("📌 测试 1: fetch_my_trades('ETH/USDT')")
print("-"*80)
try:
    trades = exchange.fetch_my_trades("ETH/USDT")
    print(f"✅ 成功获取 {len(trades)} 条成交记录")
    if trades:
        print(f"   最新一条: {trades[0]['datetime']} | {trades[0]['side']} | {trades[0]['amount']} @ {trades[0]['price']}")
except Exception as e:
    print(f"❌ 失败: {e}")
print()

# === 测试 2: fetch_orders with symbol（订单查询 - 指定交易对）===
print("📌 测试 2: fetch_orders('ETH/USDT', since=24h)")
print("-"*80)
try:
    since = int((datetime.datetime.now().timestamp() - 86400) * 1000)  # 24小时前
    orders = exchange.fetch_orders("ETH/USDT", since=since, limit=50)
    print(f"✅ 成功获取 {len(orders)} 个订单")
    if orders:
        print(f"   最新一条: {orders[0]['datetime']} | {orders[0]['type']} | {orders[0]['status']} | {orders[0]['amount']}")
except Exception as e:
    print(f"❌ 失败: {e}")
print()

# === 测试 3: fetch_orders without symbol（订单查询 - 所有交易对）===
print("📌 测试 3: fetch_orders(None, since=24h) ← 后端用的方法")
print("-"*80)
try:
    since = int((datetime.datetime.now().timestamp() - 86400) * 1000)
    orders = exchange.fetch_orders(None, since=since, limit=50)  # ← 后端的调用方式
    print(f"✅ 成功获取 {len(orders)} 个订单")
    if orders:
        print(f"   最新一条: {orders[0]['datetime']} | {orders[0]['symbol']} | {orders[0]['type']}")
except Exception as e:
    print(f"❌ 失败: {e}")
print()

# === 测试 4: fetch_open_orders without symbol ===
print("📌 测试 4: fetch_open_orders(None)")
print("-"*80)
try:
    open_orders = exchange.fetch_open_orders()
    print(f"✅ 成功获取 {len(open_orders)} 个开放订单")
    if open_orders:
        print(f"   第一个: {open_orders[0]['datetime']} | {open_orders[0]['symbol']}")
except Exception as e:
    print(f"❌ 失败: {e}")
print()

# === 测试 5: fetch_closed_orders without symbol ===
print("📌 测试 5: fetch_closed_orders(None, since=24h)")
print("-"*80)
try:
    since = int((datetime.datetime.now().timestamp() - 86400) * 1000)
    closed_orders = exchange.fetch_closed_orders(None, since=since, limit=50)
    print(f"✅ 成功获取 {len(closed_orders)} 个已完成订单")
    if closed_orders:
        print(f"   第一个: {closed_orders[0]['datetime']} | {closed_orders[0]['symbol']}")
except Exception as e:
    print(f"❌ 失败: {e}")
print()

# === 测试 6: 检查 CCXT 的 has 属性 ===
print("📌 测试 6: 检查 Binance 支持哪些方法")
print("-"*80)
print(f"has['fetchOrders']: {exchange.has.get('fetchOrders', False)}")
print(f"has['fetchOpenOrders']: {exchange.has.get('fetchOpenOrders', False)}")
print(f"has['fetchClosedOrders']: {exchange.has.get('fetchClosedOrders', False)}")
print(f"has['fetchMyTrades']: {exchange.has.get('fetchMyTrades', False)}")
print()

# === 结论 ===
print("="*80)
print("🎯 结论")
print("="*80)
print("""
如果测试 3 失败，说明：
  - Binance 的 fetch_orders 不支持 symbol=None
  - 后端代码需要调整策略

如果测试 3 成功但返回 0 条，说明：
  - API 方法正常，但最近24小时确实没有订单
  - 可以尝试扩大时间范围

如果测试 2 成功但测试 3 失败，说明：
  - 必须指定 symbol 才能查询订单
  - 后端需要改为遍历所有交易对
""")

