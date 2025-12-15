"""
市场数据服务
处理K线数据、交易对列表、市场缓存管理等
"""

import logging
import time
from typing import Dict, List, Any, Set, Optional
from util.market_cache import MarketCache, load_markets_with_cache
from exchange_adapters import get_adapter

logger = logging.getLogger(__name__)


class MarketService:
    """市场数据服务（基于 Adapter 架构）"""
    
    def __init__(
        self,
        exchanges: Dict[str, Any],  # 保留用于 get_symbols 等遗留接口
        market_cache: MarketCache,
        markets_loaded: Set[str],  # 保留用于遗留接口
        markets_loading: Set[str],  # 保留用于遗留接口
        priority_exchanges: List[str],
        proxy_config: Dict[str, str]
    ):
        """
        初始化市场数据服务
        
        Args:
            exchanges: 交易所实例字典（遗留，将逐步移除）
            market_cache: 市场缓存管理器
            markets_loaded: 已加载市场数据的交易所集合（遗留）
            markets_loading: 正在加载中的交易所集合（遗留）
            priority_exchanges: 优先交易所列表
            proxy_config: 代理配置
        """
        self.exchanges = exchanges
        self.market_cache = market_cache
        self.markets_loaded = markets_loaded
        self.markets_loading = markets_loading
        self.priority_exchanges = priority_exchanges
        self.proxy_config = proxy_config
        logger.info("市场数据服务初始化完成（Adapter 架构）")
    
    async def get_klines(
        self,
        exchange: str,
        symbol: str,
        interval: str = "15m",
        limit: int = 100,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        获取K线数据（统一使用 Adapter 架构）
        
        Args:
            exchange: 交易所名称
            symbol: 交易对符号
            interval: K线周期
            limit: 数据条数限制
            market_type: 市场类型 ('spot' 或 'futures')
            
        Returns:
            K线数据字典
        """
        try:
            exchange_name = exchange.lower()
            market_type_label = "合约" if market_type.lower() in ['futures', 'future', 'swap'] else "现货"
            
            logger.info(f"📊 获取K线 - 交易所: {exchange_name}, 交易对: {symbol}, 周期: {interval}, 市场: {market_type_label}")
            
            # 🎯 统一使用 Adapter 获取数据（K线是公开数据，不需要 API 凭证）
            config = {
                'apiKey': '',
                'secret': '',
            }
            
            # 添加代理配置
            if self.proxy_config.get('http') or self.proxy_config.get('https'):
                config['proxies'] = self.proxy_config
            
            # ✅ 所有交易所统一走 Adapter（自动处理市场数据加载、代理配置等）
            adapter = get_adapter(exchange_name, market_type, config)
            ohlcv = adapter.fetch_klines(symbol, interval, limit)
            
            # 统一转换数据格式
            klines = []
            for candle in ohlcv:
                klines.append({
                    'time': candle[0],
                    'open': str(candle[1]),
                    'high': str(candle[2]),
                    'low': str(candle[3]),
                    'close': str(candle[4]),
                    'volume': str(candle[5])
                })
            
            return {
                'success': True,
                'data': {
                    'exchange': exchange_name,
                    'symbol': symbol,
                    'interval': interval,
                    'klines': klines,
                    'count': len(klines)
                },
                'timestamp': int(time.time() * 1000)
            }
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {str(e)}")
            raise
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取市场数据缓存统计信息
        
        Returns:
            缓存统计信息
        """
        try:
            cache_info = self.market_cache.get_cache_info()
            return {
                "success": True,
                "data": cache_info
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            raise

    def get_markets_status(self) -> Dict[str, Any]:
        """
        获取市场数据加载状态

        Returns:
            加载状态信息
        """
        return {
            "success": True,
            "data": {
                "loaded": list(self.markets_loaded),
                "loading": list(self.markets_loading),
                "total": len(self.exchanges),
                "loaded_count": len(self.markets_loaded),
                "loading_count": len(self.markets_loading),
                "progress": f"{len(self.markets_loaded)}/{len(self.priority_exchanges)} 优先交易所"
            }
        }
    
    async def get_symbols(
        self,
        exchange: str = "binance",
        quote: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取指定交易所的交易对列表
        
        Args:
            exchange: 交易所名称
            quote: 可选的计价币种过滤
            limit: 返回数量限制
            
        Returns:
            交易对列表
        """
        exchange_id = exchange.lower()
        
        if exchange_id not in self.exchanges:
            raise ValueError(f"交易所 {exchange_id} 不存在")
        
        try:
            exchange_instance = self.exchanges[exchange_id]
            
            # 确保市场数据已加载
            if exchange_id not in self.markets_loaded:
                logger.info(f"⏳ 正在加载 {exchange_id} 市场数据...")
                try:
                    load_markets_with_cache(exchange_instance, exchange_id, self.market_cache)
                    self.markets_loaded.add(exchange_id)
                except Exception as e:
                    logger.warning(f"市场数据加载失败: {e}")
            
            markets = exchange_instance.markets or {}
            
            # 过滤现货交易对，只返回币种代码（不包含计价货币）
            coin_codes = set()  # 使用 set 去重
            
            for symbol, market in markets.items():
                # 只获取现货交易对
                if market.get('spot') and market.get('active', True):
                    # 如果指定了计价币种，进行过滤
                    if quote:
                        if market.get('quote') == quote.upper():
                            # 提取 base 币种（如 BTC/USDT → BTC）
                            base = market.get('base') or symbol.split('/')[0]
                            coin_codes.add(base)
                    else:
                        base = market.get('base') or symbol.split('/')[0]
                        coin_codes.add(base)
            
            # 转换为列表并排序
            coin_list = sorted(list(coin_codes))
            
            # 限制返回数量
            coin_list = coin_list[:limit]
            
            logger.info(f"✅ 返回 {len(coin_list)} 个币种代码（{exchange_id}）")
            
            return {
                "success": True,
                "data": {
                    "exchange": exchange_id,
                    "coins": coin_list,  # 改为 coins 字段
                    "total": len(coin_list),
                    "quote_filter": quote
                }
            }
        except Exception as e:
            logger.error(f"获取交易对失败: {e}")
            raise

