"""
默认交易所适配器（基于 CCXT 的通用实现）

用于处理大部分遵循 CCXT 标准接口的交易所
如果某个交易所有特殊差异，再单独创建适配器继承此类
"""

import ccxt
import logging
import os
import time
from typing import List, Dict, Optional, Any
from .adapter_interface import AdapterInterface, AdapterCapability, NotImplementedByAdapter

logger = logging.getLogger(__name__)

# 全局市场数据缓存实例（延迟初始化）
_market_cache_instance = None

def get_market_cache():
    """获取全局市场数据缓存实例（单例模式）"""
    global _market_cache_instance
    if _market_cache_instance is None:
        from util.market_cache import MarketCache
        _market_cache_instance = MarketCache()
        logger.info("✅ 初始化全局市场数据缓存")
    return _market_cache_instance


class DefaultAdapter(AdapterInterface):
    """
    默认适配器（基于 CCXT 的通用实现）
    
    适用于：
    - 大部分遵循 CCXT 标准的交易所
    - fetch_open_orders() 不需要 symbol 参数的交易所
    - 支持通过 options['defaultType'] 切换现货/合约的交易所
    
    示例：OKX, Bybit, Huobi, Kraken 等
    
    继承关系：
    - 继承自 AdapterInterface（接口层）
    - 实现基于 CCXT 的通用逻辑
    - BinanceAdapter 等特殊交易所继承此类，只重写差异部分
    """
    
    def __init__(self, exchange_id: str, market_type: str, config: dict):
        """
        初始化默认适配器
        
        Args:
            exchange_id: 交易所 ID（如 'okx', 'bybit'）
            market_type: 市场类型 ('spot' 或 'futures')
            config: 交易所配置
        """
        self._custom_exchange_id = exchange_id
        
        # CCXT 实例（只有一个，根据 market_type 配置）
        self.exchange: Optional[ccxt.Exchange] = None
        
        # 市场数据缓存（全局单例）
        self._market_cache = get_market_cache()
        
        # 调用父类初始化（会调用 _get_exchange_id 和 _initialize_exchange）
        super().__init__(market_type, config)
        
        # 🌐 自动添加代理配置（如果环境变量中有设置）
        self._add_proxy_config()
        
        # 初始化交易所（在 super().__init__() 后调用，确保 exchange_id 已设置）
        self._initialize_exchange()
        
        # 🚀 自动加载市场数据（使用缓存）
        self._load_markets_with_cache()
    
    def _get_exchange_id(self) -> str:
        """返回交易所 ID"""
        return self._custom_exchange_id
    
    # ==================== 内部辅助方法 ====================
    
    def _add_proxy_config(self):
        """
        自动添加代理配置（如果环境变量中有设置）
        
        从环境变量 PROXY_URL 读取代理地址，并自动添加到 config 中。
        如果 config 中已经有 proxies 配置，则不会覆盖。
        
        使用场景：
        - 国内用户访问 Binance 等国外交易所
        - 提高连接稳定性
        
        配置方式：
        在 .env 文件中设置：
            PROXY_URL=127.0.0.1:1080  (简化格式，自动添加协议)
            或
            PROXY_URL=http://127.0.0.1:7890  (完整格式，保持不变)
        
        协议自动处理：
        - REST API: 自动添加 http:// 前缀
        - WebSocket: 自动添加 socks5:// 前缀（在 websocket_util.py 中处理）
        """
        # 如果 config 中已经有 proxies 配置，不覆盖
        if 'proxies' in self.config and self.config['proxies']:
            logger.debug(f"✅ {self.exchange_id} 使用用户提供的代理配置")
            return
        
        # 从环境变量读取代理配置
        proxy_url = os.getenv('PROXY_URL', '').strip()
        
        if proxy_url:
            # 智能处理代理 URL
            processed_url = self._process_proxy_url(proxy_url, protocol='http')
            
            self.config['proxies'] = {
                'http': processed_url,
                'https': processed_url,
            }
            logger.info(f"🌐 {self.exchange_id} REST API 已配置代理: {processed_url}")
        else:
            logger.debug(f"ℹ️ {self.exchange_id} 未配置代理（直连）")
    
    def _process_proxy_url(self, proxy_url: str, protocol: str = 'http') -> str:
        """
        处理代理 URL，自动添加协议前缀
        
        Args:
            proxy_url: 原始代理 URL
            protocol: 默认协议 ('http' 或 'socks5')
            
        Returns:
            处理后的代理 URL
            
        示例：
            '127.0.0.1:1080' -> 'http://127.0.0.1:1080' (REST API)
            '127.0.0.1:1080' -> 'socks5://127.0.0.1:1080' (WebSocket)
            'http://127.0.0.1:7890' -> 'http://127.0.0.1:7890' (保持不变)
        """
        # 如果已经有协议前缀，直接返回
        if '://' in proxy_url:
            return proxy_url
        
        # 自动添加协议前缀
        return f"{protocol}://{proxy_url}"
    
    def _initialize_exchange(self):
        """
        初始化 CCXT 实例（单实例架构）
        
        策略：
        1. 创建一个 CCXT 实例
        2. 根据 market_type 设置 options['defaultType']
        """
        try:
            # 检查交易所是否被 CCXT 支持
            if self.exchange_id not in ccxt.exchanges:
                raise ValueError(f"CCXT 不支持交易所: {self.exchange_id}")
            
            # 创建交易所类
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # 基础配置
            exchange_config = {
                'apiKey': self.config.get('apiKey', ''),
                'secret': self.config.get('secret', ''),
                'enableRateLimit': True,
                'timeout': self.config.get('timeout', 30000),
            }
            
            # 可选配置
            if 'password' in self.config:
                exchange_config['password'] = self.config['password']
            
            if 'proxies' in self.config:
                exchange_config['proxies'] = self.config['proxies']
            
            # 根据 market_type 设置 defaultType
            if self.market_type == 'futures':
                # 币安使用 'future'，其他交易所（如 OKX、Gate）使用 'swap'
                default_type = 'future' if self.exchange_id == 'binance' else 'swap'
                exchange_config['options'] = {'defaultType': default_type}
            elif self.market_type == 'spot':
                exchange_config['options'] = {'defaultType': 'spot'}
            
            # 创建实例
            self.exchange = exchange_class(exchange_config)
            
            # 声明支持的功能（默认都支持）
            self._supported_capabilities = {
                AdapterCapability.FETCH_SPOT_ORDERS,
                AdapterCapability.FETCH_FUTURES_ORDERS,
                AdapterCapability.FETCH_SPOT_BALANCE,
                AdapterCapability.FETCH_FUTURES_POSITIONS,
            }
            
        except Exception as e:
            raise ValueError(f"初始化 {self.exchange_id} 失败: {e}")
    
    # ==================== 市场数据缓存（CCXT 特有） ====================
    
    def _load_markets_with_cache(self):
        """
        使用缓存加载市场数据（自动调用，无需手动调用）
        
        策略：
        1. 尝试从缓存加载
        2. 如果缓存有效，直接使用
        3. 如果缓存无效，从 API 加载并缓存
        
        注意：此方法在 __init__ 中自动调用，子类无需关心
        """
        if self.exchange is None:
            logger.warning(f"⚠️ {self.exchange_id} 交易所未初始化，跳过市场数据加载")
            return
        
        try:
            # 🚀 尝试从缓存加载
            cached_markets = self._market_cache.load_from_cache(self.exchange_id)
            
            if cached_markets:
                # 缓存有效，直接使用
                self.exchange.markets = cached_markets
                logger.info(f"✅ {self.exchange_id} 使用缓存的市场数据 ({len(cached_markets)} 个交易对)")
            else:
                # 缓存无效，从 API 加载
                logger.info(f"📥 {self.exchange_id} 缓存无效，从 API 加载市场数据...")
                markets = self.exchange.load_markets()
                
                # 保存到缓存
                self._market_cache.save_to_cache(self.exchange_id, markets)
                logger.info(f"✅ {self.exchange_id} 市场数据已加载并缓存 ({len(markets)} 个交易对)")
                
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 加载市场数据失败: {e}")
            # 不抛出异常，允许适配器继续工作（可能某些功能不需要市场数据）
    
    def reload_markets(self, force: bool = False):
        """
        重新加载市场数据
        
        Args:
            force: 是否强制从 API 加载（忽略缓存）
        
        使用场景：
        - 需要最新的市场数据时
        - 缓存数据可能过期时
        """
        if self.exchange is None:
            raise ValueError(f"❌ {self.exchange_id} 交易所未初始化")
        
        try:
            if force:
                # 强制从 API 加载
                logger.info(f"🔄 {self.exchange_id} 强制从 API 重新加载市场数据...")
                markets = self.exchange.load_markets()
                self._market_cache.save_to_cache(self.exchange_id, markets)
                logger.info(f"✅ {self.exchange_id} 市场数据已重新加载 ({len(markets)} 个交易对)")
            else:
                # 使用缓存策略
                self._load_markets_with_cache()
                
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 重新加载市场数据失败: {e}")
            raise
    
    def load_markets(self, reload: bool = False):
        """
        加载市场数据（CCXT 兼容接口）
        """
        if self.exchange:
            self.exchange.load_markets(reload)
    
    # ==================== 直接访问底层 CCXT 实例 ====================
    
    def get_exchange(self) -> ccxt.Exchange:
        """
        获取 CCXT 交易所实例（用于调用适配器未封装的 API）
        
        Returns:
            CCXT 交易所实例
        """
        if self.exchange is None:
            raise ValueError(f"❌ {self.exchange_id} 交易所未初始化")
        return self.exchange
    
    def __getattr__(self, name: str):
        """
        透传机制：自动转发到 CCXT 实例
        
        单实例架构下，透传非常明确：
        - 只有一个 exchange 实例
        - 所有未定义的方法都转发到这个实例
        - 不会有歧义（因为 market_type 已经在初始化时确定）
        """
        # 避免无限递归
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        # 转发到 CCXT 实例（单实例架构，非常明确）
        if self.exchange is not None and hasattr(self.exchange, name):
            return getattr(self.exchange, name)
        
        # 方法不存在
        raise AttributeError(
            f"❌ '{self.__class__.__name__}' 和底层 CCXT 实例都没有方法 '{name}'\n"
            f"\n"
            f"💡 当前市场类型：{self.market_type}\n"
            f"💡 交易所：{self.exchange_id}\n"
            f"📖 请检查 CCXT 文档确认是否支持此方法\n"
            f"📖 查看支持的功能：adapter.get_supported_capabilities()\n"
        )
    
    # ==================== 订单相关接口实现 ====================
    
    def fetch_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 500,
        base_currencies: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        获取所有订单（包括开放的和已完成的）
        """
        # 检查是否支持
        capability = (AdapterCapability.FETCH_SPOT_ORDERS 
                     if self.market_type == 'spot' 
                     else AdapterCapability.FETCH_FUTURES_ORDERS)
        
        if not self.supports_capability(capability):
            raise NotImplementedByAdapter(
                f"❌ {self.exchange_id} 的{self.market_type}订单查询功能需要定制适配，但尚未实现"
            )
        
        try:
            logger.debug(f"🔧 {self.exchange_id} ({self.market_type}) fetch_orders: symbol={symbol}, base_currencies={base_currencies}, since={since}, limit={limit}")
            
            # 默认实现：尝试使用 CCXT 的 fetch_orders
            all_orders = self._fetch_orders_default(symbol, since, limit, base_currencies)
            logger.debug(f"   原始订单数量: {len(all_orders)}")
            
            normalized = self._normalize_orders(all_orders, self.market_type)
            logger.debug(f"   标准化后订单数量: {len(normalized)}")
            
            return normalized
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 获取{self.market_type}订单失败: {e}")
            logger.error(f"   错误详情:", exc_info=True)
            return []
    
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取开放订单
        """
        # 检查是否支持
        capability = (AdapterCapability.FETCH_SPOT_ORDERS 
                     if self.market_type == 'spot' 
                     else AdapterCapability.FETCH_FUTURES_ORDERS)
        
        if not self.supports_capability(capability):
            raise NotImplementedByAdapter(
                f"❌ {self.exchange_id} 的{self.market_type}订单查询功能需要定制适配，但尚未实现"
            )
        
        try:
            # 默认实现：直接调用 CCXT
            open_orders = self._fetch_open_orders_default(symbol)
            return self._normalize_orders(open_orders, self.market_type)
        except Exception as e:
            print(f"❌ {self.exchange_id} 获取{self.market_type}开放订单失败: {e}")
            return []
    
    # ==================== 默认实现（子类可重写） ====================
    
    def _fetch_orders_default(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 500,
        base_currencies: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        获取所有订单的默认实现（包括开放和已完成）
        
        子类可以重写此方法来处理特殊情况
        """
        # 方法1：优先尝试 fetch_orders（最全面）
        if hasattr(self.exchange, 'fetch_orders'):
            logger.debug(f"   使用 fetch_orders 方法")
            try:
                orders = self.exchange.fetch_orders(symbol, since, limit, {})
                logger.debug(f"   fetch_orders 返回 {len(orders)} 条")
                return orders
            except Exception as e:
                logger.warning(f"   fetch_orders 失败: {e}，尝试降级方案")
        
        # 方法2：分别获取开放订单和已完成订单
        all_orders = []
        
        # 获取开放订单
        if hasattr(self.exchange, 'fetch_open_orders'):
            logger.debug(f"   使用 fetch_open_orders 方法")
            try:
                if symbol:
                    open_orders = self.exchange.fetch_open_orders(symbol)
                else:
                    open_orders = self.exchange.fetch_open_orders()
                logger.debug(f"   fetch_open_orders 返回 {len(open_orders)} 条")
                all_orders.extend(open_orders)
            except Exception as e:
                logger.warning(f"   fetch_open_orders 失败: {e}")
        
        # 获取已完成订单
        if hasattr(self.exchange, 'fetch_closed_orders'):
            logger.debug(f"   使用 fetch_closed_orders 方法")
            try:
                closed_orders = self.exchange.fetch_closed_orders(symbol, since, limit)
                logger.debug(f"   fetch_closed_orders 返回 {len(closed_orders)} 条")
                all_orders.extend(closed_orders)
            except Exception as e:
                logger.warning(f"   fetch_closed_orders 失败: {e}")
        
        logger.debug(f"   总共获取到 {len(all_orders)} 条原始订单")
        return all_orders
    
    def _fetch_open_orders_default(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取开放订单的默认实现（直接调用 CCXT）
        
        子类可以重写此方法来处理特殊情况（如 Binance）
        """
        if symbol:
            return self.exchange.fetch_open_orders(symbol)
        return self.exchange.fetch_open_orders()
    
    # ==================== 持仓相关接口实现 ====================
    
    def fetch_balance(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取账户余额（CCXT 格式）
        
        Args:
            symbols: 可选的币种列表，用于过滤查询
                    如果提供，会传递给 CCXT 的 fetch_balance() 方法
        
        Returns:
            {
                'info': {...},
                'free': {'BTC': 1.2, 'USDT': 1000, ...},
                'used': {'BTC': 0.1, 'USDT': 100, ...},
                'total': {'BTC': 1.3, 'USDT': 1100, ...}
            }
        """
        if not self.supports_capability(AdapterCapability.FETCH_SPOT_BALANCE):
            raise NotImplementedByAdapter(
                f"❌ {self.exchange_id} 的现货余额查询功能需要定制适配，但尚未实现"
            )
        
        try:
            # CCXT 的 fetch_balance() 通常不支持 symbols 参数
            # 大多数交易所（如 Binance）的 fetch_balance() 不接受额外参数
            # 过滤会在 position_service 的格式化方法中进行
            balance_data = self.exchange.fetch_balance()
            return balance_data
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 获取现货余额失败: {e}")
            return {
                'info': {},
                'free': {},
                'used': {},
                'total': {}
            }
    
    def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        获取持仓/余额
        
        Args:
            symbols: 可选的币种列表或交易对列表，用于过滤查询
                    如果提供，会传递给 CCXT 的 fetch_positions() 方法
        
        Returns:
            标准化的持仓/余额列表
        """
        capability = (AdapterCapability.FETCH_SPOT_BALANCE 
                     if self.market_type == 'spot' 
                     else AdapterCapability.FETCH_FUTURES_POSITIONS)
        
        if not self.supports_capability(capability):
            raise NotImplementedByAdapter(
                f"❌ {self.exchange_id} 的{self.market_type}持仓查询功能需要定制适配，但尚未实现"
            )
        
        try:
            if self.market_type == 'spot':
                # 现货：使用 fetch_balance
                balance_data = self.exchange.fetch_balance()
                return self._normalize_spot_balance(balance_data)
            else:  # futures
                # 合约：获取持仓
                # CCXT 的 fetch_positions(symbols=None, params={}) 支持 symbols 参数
                # symbols 可以是字符串、字符串列表或 None
                positions_data = self.exchange.fetch_positions(symbols)
                return self._normalize_futures_positions(positions_data)
        except TypeError as e:
            # 如果传递 symbols 导致 TypeError，说明该交易所不支持，回退到不传参数
            try:
                if self.market_type == 'spot':
                    balance_data = self.exchange.fetch_balance()
                    return self._normalize_spot_balance(balance_data)
                else:
                    positions_data = self.exchange.fetch_positions()
                    return self._normalize_futures_positions(positions_data)
            except Exception as e2:
                logger.error(f"❌ {self.exchange_id} 获取{self.market_type}持仓失败: {e2}")
                return []
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 获取{self.market_type}持仓失败: {e}")
            return []
    
    # ==================== K线数据接口实现 ====================
    
    def fetch_klines(
        self,
        symbol: str,
        interval: str = '15m',
        limit: int = 100,
        since: Optional[int] = None
    ) -> List[List[Any]]:
        """
        获取 K线数据
        """
        try:
            # 确保市场数据已加载（normalize_symbol 可能需要市场信息）
            if not self.exchange.markets:
                logger.warning(f"⚠️ {self.exchange_id} 市场数据未加载，尝试加载...")
                self._load_markets_with_cache()
            
            normalized_symbol = self.normalize_symbol(symbol)
            
            ohlcv = self.exchange.fetch_ohlcv(
                normalized_symbol,
                timeframe=interval,
                since=since,
                limit=limit
            )
            
            return ohlcv
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 获取K线失败 {symbol}/{interval}: {e}")
            return []
    
    # ==================== 价格查询接口实现 ====================
    
    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取交易对价格
        """
        # 确保市场数据已加载（normalize_symbol 可能需要市场信息）
        if not self.exchange.markets:
            logger.warning(f"⚠️ {self.exchange_id} 市场数据未加载，尝试加载...")
            self._load_markets_with_cache()
        
        result = {}
        
        for symbol in symbols:
            try:
                normalized_symbol = self.normalize_symbol(symbol)
                ticker = self.exchange.fetch_ticker(normalized_symbol)
                
                result[symbol] = {
                    'last': self._safe_float(ticker.get('last', 0)),
                    'bid': self._safe_float(ticker.get('bid', 0)),
                    'ask': self._safe_float(ticker.get('ask', 0)),
                    'mark': self._safe_float(ticker.get('last', 0))  # 现货无标记价格，用 last 代替
                }
            except Exception as e:
                logger.warning(f"❌ 获取 {symbol} 价格失败: {e}")
                result[symbol] = {
                    'last': 0,
                    'bid': 0,
                    'ask': 0,
                    'mark': 0
                }
        
        return result
    
    # ==================== 连通性测试接口实现 ====================
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        测试交易所连通性和鉴权有效性
        
        Returns:
            包含测试结果和余额数据的字典
        """
        try:
            start_time = time.time()
            
            # 尝试获取余额来验证鉴权
            balance = self.exchange.fetch_balance()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 提取余额信息（只包含有余额的币种）
            balance_data = {}
            for currency, amounts in balance.items():
                if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
                    continue
                total = amounts.get('total', 0)
                if total and float(total) > 0:
                    balance_data[currency] = str(total)
            
            return {
                'ok': True,
                'serverTime': int(time.time() * 1000),
                'accountId': None,  # CCXT 不提供统一的 accountId
                'latencyMs': round(latency_ms, 2),
                'balance': balance_data  # 返回余额数据
            }
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 连通性测试失败: {e}")
            return {
                'ok': False,
                'error': str(e),
                'serverTime': int(time.time() * 1000)
            }
    
    # ==================== 交易对查询接口实现 ====================
    
    def fetch_symbols(
        self,
        quote: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取交易对列表（带过滤）
        """
        if not self.exchange or not self.exchange.markets:
            logger.warning(f"⚠️ {self.exchange_id} 市场数据未加载")
            return []
        
        symbols_list = []
        
        for symbol, market in self.exchange.markets.items():
            # 过滤报价币种
            if quote and market.get('quote') != quote:
                continue
            
            # 只返回活跃的交易对
            if not market.get('active', True):
                continue
            
            symbols_list.append({
                'symbol': symbol,
                'base': market.get('base', ''),
                'quote': market.get('quote', ''),
                'status': 'TRADING' if market.get('active', True) else 'HALTED',
                'precision': {
                    'price': market.get('precision', {}).get('price', 8),
                    'amount': market.get('precision', {}).get('amount', 8)
                },
                'limits': {
                    'minQty': self._safe_float(market.get('limits', {}).get('amount', {}).get('min', 0)),
                    'minNotional': self._safe_float(market.get('limits', {}).get('cost', {}).get('min', 0))
                }
            })
            
            # 数量限制
            if limit and len(symbols_list) >= limit:
                break
        
        return symbols_list
    
    # ==================== 数据标准化辅助方法 ====================
    
    def _normalize_orders(self, raw_orders: List[Dict], order_type: str) -> List[Dict]:
        """
        标准化订单数据格式
        
        Args:
            raw_orders: CCXT 原始订单数据
            order_type: 'spot' or 'futures'
        
        Returns:
            统一格式的订单列表
        """
        normalized = []
        
        for order in raw_orders:
            # 安全获取 fee 数据
            fee_data = order.get('fee', {})
            fee_cost_value = fee_data.get('cost', 0) if fee_data else 0
            fee_cost = self._safe_float(fee_cost_value)
            
            normalized.append({
                'orderId': str(order.get('id', '')),
                'exchange': self.exchange_id,
                'marketType': order_type,
                'order_type': order_type,  # 兼容旧字段
                'symbol': order.get('symbol', ''),
                'side': order.get('side', ''),
                'type': order.get('type', ''),
                'price': self._safe_float(order.get('price', 0)),
                'amount': self._safe_float(order.get('amount', 0)),
                'filled': self._safe_float(order.get('filled', 0)),
                'remaining': self._safe_float(order.get('remaining', 0)),
                'total': self._safe_float(order.get('cost', 0)),
                'fee': fee_cost,
                'feeCurrency': fee_data.get('currency', '') if fee_data else '',
                'status': order.get('status', 'unknown'),
                'orderTime': self._format_timestamp(order.get('timestamp')),
                'updateTime': self._format_timestamp(order.get('lastTradeTimestamp')),
            })
        
        return normalized
    
    def _normalize_spot_balance(self, balance_data: Dict) -> List[Dict]:
        """
        标准化现货余额数据
        """
        positions = []
        
        for currency, amounts in balance_data.items():
            if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
                continue
            
            total = self._safe_float(amounts.get('total', 0))
            if total > 0:
                positions.append({
                    'exchange': self.exchange_id,
                    'type': 'spot',
                    'symbol': currency,
                    'free': self._safe_float(amounts.get('free', 0)),
                    'used': self._safe_float(amounts.get('used', 0)),
                    'total': total,
                })
        
        return positions
    
    def _normalize_futures_positions(self, positions_data: List[Dict]) -> List[Dict]:
        """
        标准化合约持仓数据
        """
        positions = []
        
        for pos in positions_data:
            contracts = self._safe_float(pos.get('contracts', 0))
            if contracts != 0:  # 只返回有持仓的
                positions.append({
                    'exchange': self.exchange_id,
                    'type': 'futures',
                    'symbol': pos.get('symbol', ''),
                    'side': pos.get('side', ''),
                    'contracts': contracts,
                    'contractSize': self._safe_float(pos.get('contractSize', 1), 1),
                    'entryPrice': self._safe_float(pos.get('entryPrice', 0)),
                    'markPrice': self._safe_float(pos.get('markPrice', 0)),
                    'unrealizedPnl': self._safe_float(pos.get('unrealizedPnl', 0)),
                    'leverage': self._safe_float(pos.get('leverage', 1), 1),
                    'marginType': pos.get('marginType', 'cross'),
                })
        
        return positions
    
    # ==================== 市场数据接口 ====================
    
    def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """
        加载市场数据（交易对信息）
        
        Args:
            reload: 是否强制重新加载（忽略缓存）
        
        Returns:
            市场数据字典 {symbol: market_info}
        """
        if self.exchange is None:
            logger.warning(f"⚠️ {self.exchange_id} 交易所未初始化")
            return {}
        
        try:
            if reload:
                # 强制重新加载
                logger.info(f"🔄 {self.exchange_id} 强制重新加载市场数据...")
                markets = self.exchange.load_markets(reload=True)
                # 更新缓存
                self._market_cache.save_to_cache(self.exchange_id, markets)
                logger.info(f"✅ {self.exchange_id} 市场数据已重新加载 ({len(markets)} 个交易对)")
                return markets
            else:
                # 使用缓存（如果 exchange.markets 已经有数据，直接返回）
                if hasattr(self.exchange, 'markets') and self.exchange.markets:
                    logger.debug(f"✅ {self.exchange_id} 使用已加载的市场数据 ({len(self.exchange.markets)} 个交易对)")
                    return self.exchange.markets
                
                # 尝试从缓存加载
                cached_markets = self._market_cache.load_from_cache(self.exchange_id)
                if cached_markets:
                    self.exchange.markets = cached_markets
                    logger.info(f"✅ {self.exchange_id} 从缓存加载市场数据 ({len(cached_markets)} 个交易对)")
                    return cached_markets
                
                # 从 API 加载
                logger.info(f"📥 {self.exchange_id} 从 API 加载市场数据...")
                markets = self.exchange.load_markets()
                self._market_cache.save_to_cache(self.exchange_id, markets)
                logger.info(f"✅ {self.exchange_id} 市场数据已加载 ({len(markets)} 个交易对)")
                return markets
        
        except Exception as e:
            logger.error(f"❌ {self.exchange_id} 加载市场数据失败: {e}")
            # 返回空字典而不是抛异常
            return {}
    
    # ==================== CCXT 标准接口（直接透传） ====================
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> List[List]:
        """获取 K线数据（CCXT 标准接口）"""
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    def fetch_ticker(self, symbol: str) -> Dict:
        """获取 Ticker 数据（CCXT 标准接口）"""
        return self.exchange.fetch_ticker(symbol)
    
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """获取订单簿（CCXT 标准接口）"""
        return self.exchange.fetch_order_book(symbol, limit)
