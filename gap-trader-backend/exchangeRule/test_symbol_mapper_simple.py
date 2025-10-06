#!/usr/bin/env python3
"""
简单的符号映射测试示例
"""

from symbol_mapper import SymbolMapper, quick_get_symbol

def main():
    print("=" * 80)
    print("交易所符号映射工具 - 简单示例")
    print("=" * 80)
    
    # 创建映射器
    mapper = SymbolMapper()
    
    # 示例 1: 获取任意币种的符号
    print("\n【示例 1】获取不同币种的符号\n")
    
    test_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE']
    
    for coin in test_coins:
        binance_spot = mapper.get_symbol('binance', coin, 'spot')
        binance_future = mapper.get_symbol('binance', coin, 'future')
        okx_spot = mapper.get_symbol('okx', coin, 'spot')
        okx_future = mapper.get_symbol('okx', coin, 'future')
        
        print(f"{coin:8} | Binance: {binance_spot:15} (spot), {binance_future:15} (future)")
        print(f"{'':8} | OKX:     {okx_spot:15} (spot), {okx_future:15} (future)")
        print()
    
    # 示例 2: 对比不同交易所
    print("\n【示例 2】对比多个交易所 - BTC 符号格式\n")
    
    exchanges = ['binance', 'okx', 'bybit', 'gate', 'huobi', 'kucoin', 'coinbase']
    coin = 'BTC'
    
    print(f"{'交易所':<15} {'现货 (Spot)':<20} {'合约 (Future)':<20}")
    print("-" * 60)
    
    for exchange in exchanges:
        spot = mapper.get_symbol(exchange, coin, 'spot')
        future = mapper.get_symbol(exchange, coin, 'future')
        print(f"{exchange:<15} {spot if spot else 'N/A':<20} {future if future else 'N/A':<20}")
    
    # 示例 3: 使用快捷函数
    print("\n【示例 3】使用快捷函数\n")
    
    queries = [
        ('binance', 'BTC', 'spot'),
        ('okx', 'ETH', 'future'),
        ('bybit', 'BNB', 'spot'),
        ('gate', 'SOL', 'future'),
    ]
    
    for exchange, coin, market_type in queries:
        symbol = quick_get_symbol(exchange, coin, market_type)
        print(f"  {exchange:10} {coin:8} {market_type:8} → {symbol}")
    
    # 示例 4: 批量查询
    print("\n【示例 4】批量查询\n")
    
    batch_queries = [
        ('binance', 'BTC', 'spot'),
        ('binance', 'ETH', 'spot'),
        ('okx', 'BNB', 'future'),
        ('bybit', 'SOL', 'spot'),
        ('gate', 'XRP', 'future'),
    ]
    
    results = mapper.batch_get_symbols(batch_queries)
    
    for query, result in zip(batch_queries, results):
        exchange, coin, market_type = query
        print(f"  {exchange:10} {coin:8} {market_type:8} → {result}")
    
    # 示例 5: 获取支持的交易所
    print("\n【示例 5】支持的交易所统计\n")
    
    spot_exchanges = mapper.get_supported_exchanges('spot')
    future_exchanges = mapper.get_supported_exchanges('future')
    
    print(f"支持现货的交易所数量: {len(spot_exchanges)}")
    print(f"支持合约的交易所数量: {len(future_exchanges)}")
    print(f"\n前 10 个支持现货的交易所:")
    print(f"  {', '.join(spot_exchanges[:10])}")
    print(f"\n前 10 个支持合约的交易所:")
    print(f"  {', '.join(future_exchanges[:10])}")


if __name__ == "__main__":
    main()

