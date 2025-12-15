"""
价格查询服务
处理多个币种的价格获取
"""

import logging
import time
from typing import Dict, List, Any, Set
from exchange_adapters import get_adapter

logger = logging.getLogger(__name__)


class PriceService:
    """价格查询服务（基于 Adapter 架构）"""
    
    def __init__(self, proxy_config: Dict[str, str]):
        """
        初始化价格服务
        
        Args:
            proxy_config: 代理配置
        """
        self.proxy_config = proxy_config
        logger.info("价格服务初始化完成（Adapter 架构）")
    
    async def get_prices(self, symbols_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        获取多个币种的价格（使用 Adapter 架构）
        
        Args:
            symbols_list: 交易对列表，格式为 [{"exchange": "binance", "symbol": "BTC/USDT"}, ...]
            
        Returns:
            价格数据字典
        """
        try:
            if not symbols_list:
                raise ValueError("symbols 参数不能为空")
            
            prices = {}
            
            # 按交易所分组
            exchange_symbols = {}
            for item in symbols_list:
                exchange_id = item.get('exchange', '').lower()
                symbol = item.get('symbol', '')
                
                if not exchange_id or not symbol:
                    continue
                    
                if exchange_id not in exchange_symbols:
                    exchange_symbols[exchange_id] = []
                exchange_symbols[exchange_id].append(symbol)
            
            # 🎯 使用 Adapter 获取价格（逐个交易所）
            for exchange_id, symbols in exchange_symbols.items():
                try:
                    # 配置（价格查询是公开 API）
                    config = {
                        'apiKey': '',
                        'secret': '',
                    }
                    
                    if self.proxy_config.get('http') or self.proxy_config.get('https'):
                        config['proxies'] = self.proxy_config
                    
                    # 获取 Adapter（默认现货市场）
                    adapter = get_adapter(exchange_id, 'spot', config)
                    prices[exchange_id] = {}
                    
                    # 获取每个交易对的价格
                    for symbol in symbols:
                        try:
                            ticker = adapter.fetch_ticker(symbol)
                            # 使用最新成交价
                            prices[exchange_id][symbol] = ticker.get('last', 0)
                        except Exception as e:
                            logger.warning(f"获取 {exchange_id} {symbol} 价格失败: {e}")
                            prices[exchange_id][symbol] = 0
                            
                except Exception as e:
                    logger.error(f"初始化 {exchange_id} Adapter 失败: {e}")
                    prices[exchange_id] = {}
            
            return {
                "success": True,
                "data": prices,
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            logger.error(f"获取价格失败: {str(e)}")
            raise

