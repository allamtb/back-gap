#!/usr/bin/env python3
"""
CCXT Demo - 展示 ccxt 库的主要功能
CCXT 是一个统一的加密货币交易库，支持 100+ 交易所
"""

import ccxt
import asyncio
import json
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_exchange_config():
    """获取交易所配置，包括代理设置"""
    config = {
        'sandbox': True,  # 使用测试网
        'rateLimit': 1200,  # 请求限制
        'enableRateLimit': True,
    }
    
    # 添加代理配置
    proxy_url = os.getenv("PROXY_URL", "")
    if proxy_url:
        config['proxies'] = {
            'http': proxy_url,
            'https': proxy_url,
        }
        print(f"使用代理: {proxy_url}")
    
    return config

def demo_basic_exchange_info():
    """演示基本的交易所信息获取"""
    print("=" * 60)
    print("1. 基本交易所信息")
    print("=" * 60)
    
    # 创建币安交易所实例
    exchange = ccxt.binance(get_exchange_config())
    
    print(f"交易所名称: {exchange.name}")
    print(f"交易所ID: {exchange.id}")
    print(f"是否支持现货交易: {exchange.has.get('spot', False)}")
    print(f"是否支持期货交易: {exchange.has.get('futures', False)}")
    print(f"是否支持WebSocket: {exchange.has.get('ws', False)}")
    print(f"是否支持杠杆交易: {exchange.has.get('margin', False)}")
    print(f"支持的交易对数量: {len(exchange.symbols) if exchange.symbols else '未知'}")
    
    return exchange

def demo_market_data(exchange):
    """演示市场数据获取"""
    print("\n" + "=" * 60)
    print("2. 市场数据获取")
    print("=" * 60)
    
    try:
        print("正在加载市场数据...")
        # 获取所有交易对
        markets = exchange.load_markets()
        print(f"✅ 支持的交易对总数: {len(markets)}")
        time.sleep(0.5)
        
        # 显示前5个交易对
        print("\n前5个交易对:")
        for i, symbol in enumerate(list(markets.keys())[:5]):
            market = markets[symbol]
            print(f"  {i+1}. {symbol}: {market['base']}/{market['quote']}")
        
        # 获取特定交易对的ticker
        symbol = 'BTC/USDT'
        if symbol in markets:
            print(f"\n正在获取 {symbol} 实时价格...")
            time.sleep(0.5)
            ticker = exchange.fetch_ticker(symbol)
            print(f"✅ {symbol} 实时价格:")
            print(f"  当前价格: ${ticker['last']}")
            print(f"  24h涨跌: {ticker['change']} ({ticker['percentage']}%)")
            print(f"  24h最高: ${ticker['high']}")
            print(f"  24h最低: ${ticker['low']}")
            print(f"  24h成交量: {ticker['baseVolume']} {ticker['base']}")
        else:
            print(f"❌ 交易对 {symbol} 不可用")
        
    except Exception as e:
        print(f"❌ 获取市场数据失败: {e}")

def demo_klines_data(exchange):
    """演示K线数据获取"""
    print("\n" + "=" * 60)
    print("3. K线数据获取")
    print("=" * 60)
    
    try:
        symbol = 'BTC/USDT'
        timeframe = '1m'  # 1分钟K线
        
        # 获取最近的K线数据
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=5)
        
        print(f"{symbol} 最近5根{timeframe}K线:")
        print("时间戳\t\t开盘价\t最高价\t最低价\t收盘价\t成交量")
        print("-" * 70)
        
        for candle in ohlcv:
            timestamp, open_price, high, low, close, volume = candle
            dt = datetime.fromtimestamp(timestamp / 1000)
            print(f"{dt.strftime('%H:%M:%S')}\t${open_price}\t${high}\t${low}\t${close}\t{volume:.2f}")
            
    except Exception as e:
        print(f"获取K线数据失败: {e}")

def demo_orderbook_data(exchange):
    """演示订单簿数据获取"""
    print("\n" + "=" * 60)
    print("4. 订单簿数据获取")
    print("=" * 60)
    
    try:
        symbol = 'BTC/USDT'
        orderbook = exchange.fetch_order_book(symbol, limit=5)
        
        print(f"{symbol} 订单簿 (前5档):")
        print("\n买单 (Bids):")
        print("价格\t\t数量")
        print("-" * 25)
        for bid in orderbook['bids'][:5]:
            price, amount = bid
            print(f"${price}\t\t{amount}")
        
        print("\n卖单 (Asks):")
        print("价格\t\t数量")
        print("-" * 25)
        for ask in orderbook['asks'][:5]:
            price, amount = ask
            print(f"${price}\t\t{amount}")
            
    except Exception as e:
        print(f"获取订单簿失败: {e}")

def demo_trades_data(exchange):
    """演示交易历史数据获取"""
    print("\n" + "=" * 60)
    print("5. 交易历史数据获取")
    print("=" * 60)
    
    try:
        symbol = 'BTC/USDT'
        trades = exchange.fetch_trades(symbol, limit=5)
        
        print(f"{symbol} 最近5笔交易:")
        print("时间\t\t价格\t\t数量\t\t方向")
        print("-" * 50)
        
        for trade in trades:
            dt = datetime.fromtimestamp(trade['timestamp'] / 1000)
            side = "买入" if trade['side'] == 'buy' else "卖出"
            print(f"{dt.strftime('%H:%M:%S')}\t${trade['price']}\t\t{trade['amount']}\t\t{side}")
            
    except Exception as e:
        print(f"获取交易历史失败: {e}")

def demo_futures_data():
    """演示期货数据获取"""
    print("\n" + "=" * 60)
    print("6. 期货数据获取")
    print("=" * 60)
    
    try:
        # 创建币安期货交易所实例
        futures_exchange = ccxt.binance({
            'sandbox': True,
            'options': {
                'defaultType': 'future'  # 使用期货API
            }
        })
        
        symbol = 'BTC/USDT'
        
        # 获取期货ticker
        ticker = futures_exchange.fetch_ticker(symbol)
        print(f"{symbol} 期货价格:")
        print(f"  当前价格: ${ticker['last']}")
        print(f"  24h涨跌: {ticker['change']} ({ticker['percentage']}%)")
        
        # 获取期货K线
        ohlcv = futures_exchange.fetch_ohlcv(symbol, '1m', limit=3)
        print(f"\n{symbol} 期货最近3根1分钟K线:")
        for candle in ohlcv:
            timestamp, open_price, high, low, close, volume = candle
            dt = datetime.fromtimestamp(timestamp / 1000)
            print(f"  {dt.strftime('%H:%M:%S')}: 开盘${open_price}, 收盘${close}")
            
    except Exception as e:
        print(f"获取期货数据失败: {e}")

def demo_spot_futures_arbitrage():
    """演示现货期货套利机会检测"""
    print("\n" + "=" * 60)
    print("7. 现货期货套利机会检测")
    print("=" * 60)
    
    try:
        # 现货交易所
        spot_exchange = ccxt.binance({'sandbox': True})
        
        # 期货交易所
        futures_exchange = ccxt.binance({
            'sandbox': True,
            'options': {'defaultType': 'future'}
        })
        
        symbol = 'BTC/USDT'
        
        # 获取现货价格
        spot_ticker = spot_exchange.fetch_ticker(symbol)
        spot_price = spot_ticker['last']
        
        # 获取期货价格
        futures_ticker = futures_exchange.fetch_ticker(symbol)
        futures_price = futures_ticker['last']
        
        # 计算价差
        gap = futures_price - spot_price
        gap_percent = (gap / spot_price) * 100
        
        print(f"{symbol} 套利分析:")
        print(f"  现货价格: ${spot_price}")
        print(f"  期货价格: ${futures_price}")
        print(f"  价差: ${gap:.2f}")
        print(f"  价差百分比: {gap_percent:.2f}%")
        
        # 判断套利机会
        if abs(gap_percent) > 0.1:  # 价差超过0.1%
            direction = "期货做空，现货做多" if gap > 0 else "期货做多，现货做空"
            print(f"  🎯 发现套利机会: {direction}")
        else:
            print(f"  ⚪ 暂无套利机会")
            
    except Exception as e:
        print(f"套利分析失败: {e}")

def demo_multiple_exchanges():
    """演示多交易所数据对比"""
    print("\n" + "=" * 60)
    print("8. 多交易所价格对比")
    print("=" * 60)
    
    # 使用更稳定的配置
    exchanges = {
        'Binance': ccxt.binance({
            'sandbox': True,
            'rateLimit': 2000,
            'enableRateLimit': True,
            'timeout': 10000,
        }),
        'OKX': ccxt.okx({
            'sandbox': False,  # OKX测试网可能不稳定，使用主网
            'rateLimit': 2000,
            'enableRateLimit': True,
            'timeout': 10000,
        }),
        'Bybit': ccxt.bybit({
            'sandbox': False,  # Bybit测试网可能不稳定，使用主网
            'rateLimit': 2000,
            'enableRateLimit': True,
            'timeout': 10000,
        }),
    }
    
    symbol = 'BTC/USDT'
    prices = {}
    
    for name, exchange in exchanges.items():
        try:
            print(f"正在获取 {name} 数据...")
            # 先加载市场数据
            exchange.load_markets()
            time.sleep(1)  # 添加延迟
            
            # 获取ticker
            ticker = exchange.fetch_ticker(symbol)
            prices[name] = ticker['last']
            print(f"✅ {name}: ${ticker['last']}")
            time.sleep(1)  # 请求间隔
            
        except Exception as e:
            print(f"❌ {name}: 获取失败 - {str(e)[:100]}...")
            time.sleep(1)
    
    if len(prices) > 1:
        max_price = max(prices.values())
        min_price = min(prices.values())
        spread = max_price - min_price
        spread_percent = (spread / min_price) * 100
        
        print(f"\n📊 价格分析:")
        print(f"  最高价: ${max_price}")
        print(f"  最低价: ${min_price}")
        print(f"  价差: ${spread:.2f} ({spread_percent:.2f}%)")
        
        if spread_percent > 0.1:
            print(f"  🎯 发现套利机会！价差超过0.1%")
    else:
        print(f"\n⚠️  只有 {len(prices)} 个交易所数据可用，无法进行价格对比")

async def demo_websocket_data():
    """演示WebSocket实时数据 (如果支持)"""
    print("\n" + "=" * 60)
    print("9. WebSocket实时数据 (演示)")
    print("=" * 60)
    
    print("注意: WebSocket功能需要额外的配置和认证")
    print("这里展示如何设置WebSocket连接:")
    
    try:
        exchange = ccxt.binance({
            'sandbox': True,
            'enableRateLimit': True,
        })
        
        if exchange.has['ws']:
            print("✅ 该交易所支持WebSocket")
            print("可以订阅:")
            print("  - 实时价格更新")
            print("  - 订单簿变化")
            print("  - 交易执行")
            print("  - K线数据")
        else:
            print("❌ 该交易所不支持WebSocket")
            
    except Exception as e:
        print(f"WebSocket检查失败: {e}")

def main():
    """主函数"""
    print("CCXT 加密货币交易库功能演示")
    print("=" * 60)
    print("CCXT 是一个统一的加密货币交易库，支持 100+ 交易所")
    print("主要功能包括:")
    print("  - 统一的多交易所API接口")
    print("  - 实时市场数据获取")
    print("  - 历史数据查询")
    print("  - 订单管理")
    print("  - 套利机会检测")
    print("  - WebSocket实时数据")
    
    try:
        # 1. 基本交易所信息
        exchange = demo_basic_exchange_info()
        
        # 2. 市场数据
        demo_market_data(exchange)

        # 3. K线数据
        demo_klines_data(exchange)
        
        # 4. 订单簿数据
        demo_orderbook_data(exchange)
        
        # 5. 交易历史
        demo_trades_data(exchange)
        
        # 6. 期货数据
        demo_futures_data()
        
        # 7. 套利机会检测
        demo_spot_futures_arbitrage()
        
        # 8. 多交易所对比
        demo_multiple_exchanges()
        
        # 9. WebSocket演示
        asyncio.run(demo_websocket_data())
        
        print("\n" + "=" * 60)
        print("演示完成!")
        print("=" * 60)
        print("CCXT 主要优势:")
        print("  ✅ 统一接口 - 一套代码支持多个交易所")
        print("  ✅ 丰富数据 - 价格、K线、订单簿、交易历史")
        print("  ✅ 实时更新 - 支持WebSocket实时数据")
        print("  ✅ 套利支持 - 现货期货价差分析")
        print("  ✅ 类型安全 - 完整的数据验证")
        print("  ✅ 文档完善 - 详细的API文档")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        print("请检查网络连接和API配置")

if __name__ == "__main__":
    main()
