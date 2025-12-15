"""
Binance 交易所适配器（单实例架构）

特殊差异：
1. fetch_open_orders() 必须传 symbol 参数，需要逐个交易对查询
2. 需要特殊配置：options['warnOnFetchOpenOrdersWithoutSymbol'] = False
"""

import ccxt
import logging
from .default_adapter import DefaultAdapter
from .adapter_interface import AdapterCapability

logger = logging.getLogger(__name__)


class BinanceAdapter(DefaultAdapter):
    """
    Binance 交易所适配器（单实例架构）
    
    继承自 DefaultAdapter，只重写有差异的部分：
    1. _initialize_exchange() - 添加特殊配置
    2. 订单查询逻辑 - 必须传 symbol 参数
    """
    
    def __init__(self, market_type: str, config: dict):
        """初始化 Binance 适配器"""
        # 调用父类 DefaultAdapter 的 __init__，传入 exchange_id='binance'
        super().__init__(exchange_id='binance', market_type=market_type, config=config)
    
    def _get_exchange_id(self) -> str:
        return 'binance'
    
    def _initialize_exchange(self):
        """
        初始化 Binance 实例（单实例架构）
        
        根据 market_type 创建对应配置的实例
        """
        exchange_config = {
            'apiKey': self.config.get('apiKey', ''),
            'secret': self.config.get('secret', ''),
            'enableRateLimit': True,
            'enableTimeSync': True,  # 🔧 启用时间同步，解决时间戳错误
            'timeout': self.config.get('timeout', 30000),
            'options': {
                'warnOnFetchOpenOrdersWithoutSymbol': False,  # 关闭警告
            }
        }
        
        # 根据 market_type 设置 defaultType
        if self.market_type == 'futures':
            exchange_config['options']['defaultType'] = 'future'
        else:  # spot
            exchange_config['options']['defaultType'] = 'spot'
        
        if 'proxies' in self.config:
            exchange_config['proxies'] = self.config['proxies']
        
        self.exchange = ccxt.binance(exchange_config)
        
        # 🔧 手动触发时间同步（解决时间戳错误）
        try:
            # 获取 Binance 服务器时间并计算时间差
            if hasattr(self.exchange, 'fetch_time'):
                server_time = self.exchange.fetch_time()
                local_time = self.exchange.milliseconds()
                time_diff = server_time - local_time
                logger.info(f"🕐 Binance 时间同步: 服务器时间={server_time}, 本地时间={local_time}, 时间差={time_diff}ms")
                
                # 如果时间差超过 1000ms，记录警告
                if abs(time_diff) > 1000:
                    logger.warning(f"⚠️ Binance 时间差较大: {time_diff}ms，可能导致请求失败")
        except Exception as e:
            logger.warning(f"⚠️ Binance 时间同步失败（不影响使用）: {e}")
        
        # 声明支持的功能
        self._supported_capabilities = {
            AdapterCapability.FETCH_SPOT_ORDERS,
            AdapterCapability.FETCH_FUTURES_ORDERS,
            AdapterCapability.FETCH_SPOT_BALANCE,
            AdapterCapability.FETCH_FUTURES_POSITIONS,
        }
    
    # ==================== 订单查询（Binance 特殊处理） ====================
    
    def _fetch_orders_default(self, symbol=None, since=None, limit=500, base_currencies=None):
        """
        Binance 特殊处理：fetch_orders/fetch_closed_orders 必须传 symbol
        
        策略：
        1. 如果传了 symbol，直接查询
        2. 如果传了 base_currencies（币种列表或交易对列表），根据内容判断：
           - 如果元素包含 '/'，认为是交易对列表，直接使用
           - 否则认为是币种列表，根据币种推测交易对
        3. 如果都没传，从余额推断可能的交易对，逐个查询
        
        Args:
            symbol: 可选的交易对
            since: 起始时间戳（None=完整历史）
            limit: 每个交易对的订单数量限制（默认500）
            base_currencies: 可选的币种列表（如 ['BTC', 'ETH']）或交易对列表（如 ['BTC/USDT', 'PEOPLE/USDT:USDT']）
        """
        logger.info(f"🔍 Binance fetch_orders: symbol={symbol}, base_currencies={base_currencies}, market_type={self.market_type}")
        
        if symbol:
            # 有 symbol，直接使用父类的默认实现
            logger.info(f"   使用指定交易对查询: {symbol}")
            return super()._fetch_orders_default(symbol, since, limit)
        
        # 没有 symbol，需要推断活跃交易对
        all_orders = []
        
        try:
            # 🎯 根据 base_currencies 推测交易对或直接使用交易对列表
            if base_currencies:
                # 🔧 检查是否是交易对列表（元素包含 '/'）
                is_trading_pairs = any('/' in item for item in base_currencies)
                
                if is_trading_pairs:
                    # 直接使用交易对列表
                    active_symbols = base_currencies
                    logger.info(f"   检测到交易对列表，直接使用: {active_symbols}")
                else:
                    # 根据币种推测交易对
                    logger.info(f"   根据币种列表推测交易对: {base_currencies}")
                    active_symbols = self._get_symbols_from_base_currencies(base_currencies)
            else:
                logger.info(f"   未指定币种，从余额推断所有活跃交易对...")
                active_symbols = self._get_active_symbols_from_balance_smart()
            
            logger.info(f"🔍 Binance: 推断出 {len(active_symbols)} 个交易对: {active_symbols}")
            
            if not active_symbols:
                logger.warning(f"⚠️ Binance: 未能推断出任何交易对")
                return []
            
            # 逐个交易对查询订单
            for sym in active_symbols:
                try:
                    logger.debug(f"   查询交易对 {sym} 的订单...")
                    
                    # 获取开放订单
                    open_orders = self.exchange.fetch_open_orders(sym)
                    if open_orders:
                        logger.info(f"   ✅ {sym}: 找到 {len(open_orders)} 个开放订单")
                        all_orders.extend(open_orders)
                    
                    # 获取已完成订单
                    if hasattr(self.exchange, 'fetch_closed_orders'):
                        closed_orders = self.exchange.fetch_closed_orders(sym, since, limit)
                        if closed_orders:
                            logger.info(f"   ✅ {sym}: 找到 {len(closed_orders)} 个已完成订单")
                            all_orders.extend(closed_orders)
                    
                except Exception as e:
                    # 某个交易对查询失败不影响其他的
                    logger.debug(f"   ⚠️ {sym}: 查询失败 - {e}")
            
            logger.info(f"🎉 Binance: 总共获取到 {len(all_orders)} 个订单")
        
        except Exception as e:
            logger.error(f"❌ Binance 获取订单失败: {e}", exc_info=True)
        
        return all_orders
    
    def _fetch_open_orders_default(self, symbol=None):
        """
        Binance 特殊处理：fetch_open_orders() 必须传 symbol
        
        策略：
        1. 如果传了 symbol，直接查询
        2. 如果没传 symbol，从余额/持仓推断活跃交易对
        """
        logger.info(f"🔍 Binance fetch_open_orders: symbol={symbol}, market_type={self.market_type}")
        
        if symbol:
            # 有 symbol，直接查询
            logger.info(f"   使用指定交易对查询: {symbol}")
            return self.exchange.fetch_open_orders(symbol)
        
        # 没有 symbol，需要推断活跃交易对
        logger.info(f"   未指定交易对，开始智能推断...")
        orders = []
        
        try:
            active_symbols = self._get_active_symbols_from_balance_smart()
            logger.info(f"   推断出 {len(active_symbols)} 个活跃交易对: {active_symbols}")
            
            # 逐个交易对查询订单
            for sym in active_symbols:
                try:
                    symbol_orders = self.exchange.fetch_open_orders(sym)
                    if symbol_orders:
                        logger.info(f"   ✅ {sym}: 找到 {len(symbol_orders)} 个开放订单")
                        orders.extend(symbol_orders)
                except Exception as e:
                    logger.debug(f"   ⚠️ {sym}: 查询失败 - {e}")
        
        except Exception as e:
            logger.error(f"❌ Binance 获取开放订单失败: {e}", exc_info=True)
        
        return orders
    
    # ==================== 辅助方法 ====================
    
    def _get_symbols_from_base_currencies(self, base_currencies: list) -> list:
        """
        🎯 根据币种列表推测交易对
        
        策略：
        1. 对每个币种（如 BTC），尝试常见的计价币种（USDT, USDC, BUSD, FDUSD）
        2. 检查交易对是否存在且匹配当前市场类型
        
        Args:
            base_currencies: 币种列表（如 ['BTC', 'ETH', 'SOL']）
        
        Returns:
            交易对列表（如 ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']）
        """
        symbols = []
        
        try:
            # 🚀 使用缓存机制加载市场数据
            if not self.exchange.markets:
                logger.info(f"   市场数据未加载，正在加载（使用缓存）...")
                self.load_markets_safe()
                logger.info(f"   ✅ 市场数据已加载 ({len(self.exchange.markets)} 个交易对)")
            
            # 常见的计价币种（按优先级排序）
            quote_currencies = ['USDT', 'USDC', 'BUSD', 'FDUSD']
            
            for base in base_currencies:
                base = base.upper().strip()
                
                # 跳过稳定币
                if base in quote_currencies:
                    logger.debug(f"      ⏭️ 跳过稳定币: {base}")
                    continue
                
                found = False
                for quote in quote_currencies:
                    symbol = f"{base}/{quote}"
                    
                    # 检查交易对是否存在
                    if symbol in self.exchange.markets:
                        market = self.exchange.markets[symbol]
                        
                        # 检查市场类型是否匹配
                        if self.market_type == 'spot' and market.get('spot'):
                            symbols.append(symbol)
                            logger.debug(f"      ✅ {symbol} (现货)")
                            found = True
                            break  # 找到一个就够了，优先使用 USDT
                        elif self.market_type == 'futures' and market.get('future'):
                            symbols.append(symbol)
                            logger.debug(f"      ✅ {symbol} (合约)")
                            found = True
                            break  # 找到一个就够了，优先使用 USDT
                
                if not found:
                    logger.warning(f"      ⚠️ 未找到 {base} 的有效交易对")
            
            logger.info(f"   ✅ 根据 {len(base_currencies)} 个币种推测出 {len(symbols)} 个交易对: {symbols}")
        
        except Exception as e:
            logger.error(f"⚠️ 根据币种推测交易对失败: {e}", exc_info=True)
        
        return symbols
    
    def _get_active_symbols_from_balance_smart(self) -> list:
        """
        智能推断活跃交易对（你的思路 🎯）
        
        策略：
        1. 先获取账户余额
        2. 找出有余额的币种（排除稳定币）
        3. 构造可能的交易对（币种/USDT, 币种/BUSD等）
        4. 返回存在的交易对列表
        
        Returns:
            交易对列表（如 ['BTC/USDT', 'ETH/USDT']）
        """
        active_symbols = []
        
        try:
            # 🚀 使用缓存机制加载市场数据
            if not self.exchange.markets:
                logger.info(f"   市场数据未加载，正在加载（使用缓存）...")
                self.load_markets_safe()
                logger.info(f"   ✅ 市场数据已加载 ({len(self.exchange.markets)} 个交易对)")
            
            # 获取余额
            logger.debug(f"   正在获取账户余额...")
            balance = self.exchange.fetch_balance()
            logger.debug(f"   ✅ 余额获取成功")
            
            # 找出有余额的币种
            nonzero_assets = []
            for currency, amounts in balance.items():
                # 跳过特殊字段
                if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
                    continue
                
                # 跳过稳定币（它们不需要查询）
                if currency in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'USD']:
                    continue
                
                # 有余额的币种
                total_value = amounts.get('total', 0)
                # 处理 None 值
                if total_value is None:
                    total_value = 0
                
                total = float(total_value)
                if total > 0:
                    nonzero_assets.append(currency)
                    logger.debug(f"      {currency}: {total}")
            
            logger.info(f"   📊 找到 {len(nonzero_assets)} 个有余额的币种: {nonzero_assets}")
            
            # 构造可能的交易对
            quote_currencies = ['USDT', 'USDC', 'BUSD', 'FDUSD']
            
            for base in nonzero_assets:
                for quote in quote_currencies:
                    symbol = f"{base}/{quote}"
                    
                    # 检查交易对是否存在
                    if symbol in self.exchange.markets:
                        market = self.exchange.markets[symbol]
                        
                        # 检查市场类型是否匹配
                        if self.market_type == 'spot' and market.get('spot'):
                            active_symbols.append(symbol)
                            logger.debug(f"      ✅ {symbol} (现货)")
                        elif self.market_type == 'futures' and market.get('future'):
                            active_symbols.append(symbol)
                            logger.debug(f"      ✅ {symbol} (合约)")
            
            # 去重
            active_symbols = list(set(active_symbols))
            logger.info(f"   ✅ 最终推断出 {len(active_symbols)} 个活跃交易对")
        
        except Exception as e:
            logger.error(f"⚠️ Binance 智能推断交易对失败: {e}", exc_info=True)
        
        return active_symbols
    
    def _get_active_symbols_from_balance(self, balance: dict, market_type: str) -> list:
        """
        从余额推断活跃交易对
        
        Args:
            balance: CCXT balance 数据
            market_type: 'spot' or 'future'
        
        Returns:
            交易对列表（如 ['BTC/USDT', 'ETH/USDT']）
        """
        active_symbols = []
        
        try:
            # 🚀 使用缓存机制加载市场数据
            if not self.exchange.markets:
                self.load_markets_safe()
            
            # 获取有余额的币种
            active_currencies = []
            for currency, amounts in balance.items():
                if currency in ('info', 'free', 'used', 'total', 'timestamp', 'datetime'):
                    continue
                
                # 处理 None 值
                total_value = amounts.get('total', 0)
                if total_value is None:
                    total_value = 0
                
                total = float(total_value)
                if total > 0:
                    active_currencies.append(currency)
            
            # 构造可能的交易对
            quote_currencies = ['USDT', 'USDC', 'BUSD', 'USD']
            
            for base in active_currencies:
                for quote in quote_currencies:
                    symbol = f"{base}/{quote}"
                    
                    # 检查交易对是否存在
                    if symbol in self.exchange.markets:
                        market = self.exchange.markets[symbol]
                        
                        # 检查市场类型
                        if market_type == 'spot' and market.get('spot'):
                            active_symbols.append(symbol)
                        elif market_type == 'future' and market.get('future'):
                            active_symbols.append(symbol)
        
        except Exception as e:
            print(f"⚠️ 推断活跃交易对失败: {e}")
        
        return list(set(active_symbols))  # 去重
