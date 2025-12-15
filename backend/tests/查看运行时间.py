import ccxt
import time
import pandas as pd

# 记录开始时间
start_time = time.time()

# 创建币安交易所实例（启用速率限制）
exchange = ccxt.binance({
    'enableRateLimit': True,  # 启用API请求频率限制[6](@ref)
    'proxies': {
        'http': 'http://127.0.0.1:1080',
        'https': 'http://127.0.0.1:1080',
    }
})

# 获取BTC/USDT的100条1小时K线数据
symbol = 'BTC/USDT'
timeframe = '1h'  # 时间周期：1小时
limit = 100  # 数据条数

try:
    # 获取OHLCV数据（开盘价、最高价、最低价、收盘价、成交量）
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    # 转换为DataFrame便于查看
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')  # 转换时间戳

    # 计算耗时
    end_time = time.time()
    elapsed_time = end_time - start_time

    # 显示结果
    print(f"获取{limit}条数据耗时: {elapsed_time:.2f}秒")
    print(f"数据时间范围: {df['timestamp'].iloc[0]} 到 {df['timestamp'].iloc[-1]}")
    print("\n前5条数据:")
    print(df.head())

except Exception as e:
    print(f"获取数据时出错: {e}")