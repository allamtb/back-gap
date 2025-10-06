#!/usr/bin/env python3
"""
交易所符号映射工具 - 简化版

基于固化的规则快速生成任意币种的交易符号
只支持 spot 和 future 两种市场类型
"""

from typing import Optional, Dict, List
from exchangeRule.exchange_rules import EXCHANGE_RULES, get_exchange_rule


class SymbolMapper:
    """
    交易所符号映射器（简化版）
    
    特点：
    1. 使用固化的规则，不需要读取 JSON
    2. 支持任意币种，自动根据规律生成符号
    3. 只支持 spot 和 future 两种市场类型
    
    使用方法：
        mapper = SymbolMapper()
        
        # 获取任意币种的符号
        symbol = mapper.get_symbol('binance', 'BTC', 'spot')   # BTC/USDT
        symbol = mapper.get_symbol('binance', 'ETH', 'spot')   # ETH/USDT
        symbol = mapper.get_symbol('okx', 'BNB', 'future')     # BNB/USD
    """
    
    def __init__(self):
        """初始化映射器"""
        self.rules = EXCHANGE_RULES
        print(f"✅ 加载了 {len(self.rules)} 个交易所的规则")
    
    def get_symbol(self, exchange: str, coin: str, market_type: str = 'spot') -> Optional[str]:
        """
        获取交易符号
        
        Args:
            exchange: 交易所ID（如 'binance', 'okx'）
            coin: 币种代码（如 'BTC', 'ETH'，任意币种）
            market_type: 市场类型（'spot' 或 'future'）
            
        Returns:
            完整的交易符号，如果交易所不支持返回 None
            
        Examples:
            >>> mapper = SymbolMapper()
            >>> mapper.get_symbol('binance', 'BTC', 'spot')
            'BTC/USDT'
            >>> mapper.get_symbol('binance', 'ETH', 'spot')
            'ETH/USDT'
            >>> mapper.get_symbol('okx', 'BNB', 'future')
            'BNB/USD'
        """
        exchange = exchange.lower()
        coin = coin.upper()
        market_type = market_type.lower()
        
        # 获取规则
        rule = get_exchange_rule(exchange, market_type)
        
        if not rule:
            return None
        
        # 根据规则生成符号
        return self._generate_symbol(coin, rule)
    
    def _generate_symbol(self, coin: str, rule: Dict) -> str:
        """
        根据规则生成符号
        
        Args:
            coin: 币种代码
            rule: 格式规则
            
        Returns:
            生成的符号
        """
        separator = rule.get('separator', '/')
        quote = rule.get('quote', 'USDT')
        suffix = rule.get('suffix', '')
        
        # 构建符号
        symbol = f"{coin}{separator}{quote}{suffix}"
        
        return symbol
    
    def get_all_symbols(self, exchange: str, coin: str) -> Dict[str, str]:
        """
        获取指定币种在某交易所的所有市场类型符号
        
        Args:
            exchange: 交易所ID
            coin: 币种代码
            
        Returns:
            {market_type: symbol} 字典
            
        Examples:
            >>> mapper.get_all_symbols('binance', 'BTC')
            {'spot': 'BTC/USDT', 'future': 'BTC/USDT'}
            >>> mapper.get_all_symbols('okx', 'ETH')
            {'spot': 'ETH/USDT', 'future': 'ETH/USD'}
        """
        exchange = exchange.lower()
        coin = coin.upper()
        
        result = {}
        
        if exchange in self.rules:
            for market_type in ['spot', 'future']:
                symbol = self.get_symbol(exchange, coin, market_type)
                if symbol:
                    result[market_type] = symbol
        
        return result
    
    def get_supported_exchanges(self, market_type: str = 'spot') -> List[str]:
        """
        获取支持指定市场类型的交易所列表
        
        Args:
            market_type: 市场类型
            
        Returns:
            交易所ID列表
            
        Examples:
            >>> mapper.get_supported_exchanges('spot')
            ['binance', 'okx', 'bybit', ...]
        """
        market_type = market_type.lower()
        
        exchanges = []
        for exchange_id in self.rules.keys():
            if market_type in self.rules[exchange_id]:
                exchanges.append(exchange_id)
        
        return sorted(exchanges)
    
    def compare_symbols(self, coin: str, exchanges: List[str] = None):
        """
        对比多个交易所的符号格式
        
        Args:
            coin: 币种代码
            exchanges: 要对比的交易所列表，None 表示所有
        """
        coin = coin.upper()
        
        if exchanges is None:
            exchanges = sorted(self.rules.keys())
        
        print(f"\n{'=' * 80}")
        print(f"交易所符号对比：{coin}")
        print(f"{'=' * 80}\n")
        
        # 表头
        print(f"{'交易所':<15} {'现货 (Spot)':<30} {'合约 (Future)':<30}")
        print('-' * 80)
        
        # 数据行
        for exchange in exchanges:
            spot_symbol = self.get_symbol(exchange, coin, 'spot')
            future_symbol = self.get_symbol(exchange, coin, 'future')
            
            print(f"{exchange:<15} {spot_symbol if spot_symbol else 'N/A':<30} {future_symbol if future_symbol else 'N/A':<30}")
        
        print()
    
    def batch_get_symbols(self, queries: List[tuple]) -> List[Optional[str]]:
        """
        批量获取符号
        
        Args:
            queries: 查询列表，每个元素是 (exchange, coin, market_type) 元组
            
        Returns:
            符号列表
            
        Examples:
            >>> queries = [
            ...     ('binance', 'BTC', 'spot'),
            ...     ('okx', 'ETH', 'future'),
            ... ]
            >>> mapper.batch_get_symbols(queries)
            ['BTC/USDT', 'ETH/USD']
        """
        results = []
        for query in queries:
            if len(query) == 3:
                exchange, coin, market_type = query
                symbol = self.get_symbol(exchange, coin, market_type)
                results.append(symbol)
            else:
                results.append(None)
        return results


# 全局单例
_mapper_instance = None

def get_mapper() -> SymbolMapper:
    """获取全局映射器实例"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = SymbolMapper()
    return _mapper_instance


def quick_get_symbol(exchange: str, coin: str, market_type: str = 'spot') -> Optional[str]:
    """
    快捷函数：获取交易符号
    
    Args:
        exchange: 交易所ID
        coin: 币种代码
        market_type: 市场类型
        
    Returns:
        交易符号
        
    Examples:
        >>> quick_get_symbol('binance', 'BTC', 'spot')
        'BTC/USDT'
    """
    mapper = get_mapper()
    return mapper.get_symbol(exchange, coin, market_type)


def main():
    """使用示例"""
    print("=" * 80)
    print("交易所符号映射工具 - 支持任意币种！")
    print("=" * 80)
    
    # 创建映射器
    mapper = SymbolMapper()
    
    # 示例 1: 获取各种币种的符号
    print("\n📌 示例 1: 获取任意币种的符号")
    coins = ['BTC', 'ETH', 'BNB', 'SOL', 'DOGE']
    
    for coin in coins:
        spot = mapper.get_symbol('binance', coin, 'spot')
        future = mapper.get_symbol('binance', coin, 'future')
        print(f"Binance {coin:<6} - 现货: {spot:<15} 合约: {future}")
    
    # 示例 2: 对比不同交易所
    print("\n📌 示例 2: 对比不同币种在不同交易所的符号")
    
    coins = ['BTC', 'ETH', 'BNB']
    exchanges = ['binance', 'okx', 'bybit']
    
    print(f"\n{'交易所':<12}", end='')
    for coin in coins:
        print(f"{coin} 现货{'':<10} {coin} 合约{'':<10}", end='')
    print()
    print('-' * 90)
    
    for exchange in exchanges:
        print(f"{exchange:<12}", end='')
        for coin in coins:
            spot = mapper.get_symbol(exchange, coin, 'spot')
            future = mapper.get_symbol(exchange, coin, 'future')
            print(f"{spot:<15} {future:<15}", end='')
        print()
    
    # 示例 3: 获取所有市场类型
    print("\n📌 示例 3: 获取所有市场类型符号")
    print("\nBinance ETH:")
    for market_type, symbol in mapper.get_all_symbols('binance', 'ETH').items():
        print(f"  {market_type}: {symbol}")
    
    print("\nOKX BNB:")
    for market_type, symbol in mapper.get_all_symbols('okx', 'BNB').items():
        print(f"  {market_type}: {symbol}")
    
    # 示例 4: 批量查询
    print("\n📌 示例 4: 批量查询")
    queries = [
        ('binance', 'BTC', 'spot'),
        ('binance', 'ETH', 'future'),
        ('okx', 'BNB', 'spot'),
        ('okx', 'SOL', 'future'),
        ('bybit', 'DOGE', 'spot'),
    ]
    
    results = mapper.batch_get_symbols(queries)
    for query, result in zip(queries, results):
        print(f"  {query[0]:<10} {query[1]:<6} {query[2]:<10} → {result}")
    
    # 示例 5: 对比功能
    print("\n📌 示例 5: 对比多个交易所")
    mapper.compare_symbols('BTC', ['binance', 'okx', 'bybit', 'gate', 'huobi'])
    
    # 示例 6: 获取支持的交易所
    print("\n📌 示例 6: 支持的交易所")
    spot_exchanges = mapper.get_supported_exchanges('spot')
    future_exchanges = mapper.get_supported_exchanges('future')
    print(f"支持现货的交易所 ({len(spot_exchanges)} 个): {', '.join(spot_exchanges)}")
    print(f"支持合约的交易所 ({len(future_exchanges)} 个): {', '.join(future_exchanges)}")
    
    # 示例 7: 使用快捷函数
    print("\n📌 示例 7: 使用快捷函数")
    print(f"quick_get_symbol('binance', 'BTC', 'spot') = {quick_get_symbol('binance', 'BTC', 'spot')}")
    print(f"quick_get_symbol('okx', 'ETH', 'future') = {quick_get_symbol('okx', 'ETH', 'future')}")


if __name__ == "__main__":
    main()
