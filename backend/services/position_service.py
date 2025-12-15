"""
持仓管理服务
使用 Adapter 架构处理现货和合约持仓数据获取
"""

import logging
import time
import asyncio
from typing import Dict, List, Any
from exchange_adapters import get_adapter
from util.exchange_rules import generate_symbol

logger = logging.getLogger(__name__)


class PositionService:
    """持仓管理服务 - 使用 Adapter 架构"""
    
    def __init__(self, proxy_config: Dict[str, str] = None):
        """
        初始化持仓服务
        
        Args:
            proxy_config: 代理配置（可选）
        """
        self.proxy_config = proxy_config or {}
        logger.info("持仓服务初始化完成（使用 Adapter 架构）")
    
    async def get_positions(
        self, 
        credentials: List[Dict[str, str]], 
        symbols: List[str] = None,
        symbol_pairs: Dict[str, List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取多个交易所的持仓数据
        支持现货和合约，通过 marketType 区分
        
        Args:
            credentials: 交易所凭证列表，每个包含：
                - exchange: 交易所 ID
                - marketType: 市场类型 ('spot' 或 'futures')
                - apiKey: API Key
                - apiSecret: API Secret
                - password: 密码（可选，某些交易所需要）
            symbols: 可选的币种列表（如 ['BTC', 'ETH', 'PEOPLE']），用于过滤持仓
                     如果提供，只返回匹配的币种持仓，可以大幅提升查询速度
            
        Returns:
            {
                "success": True,
                "data": [...],  # 持仓列表
                "total": 10,
                "elapsed": 1.23
            }
        """
        service_start_time = time.time()
        
        try:
            if not credentials:
                return {"success": True, "data": [], "total": 0}
            
            # 如果提供了 symbol_pairs（前端生成的交易对映射），使用它
            # 否则使用 symbols（基础货币列表，向后兼容）
            if symbol_pairs:
                logger.info(f"🔍 持仓查询使用前端传递的交易对映射: {list(symbol_pairs.keys())}")
            else:
                # 构建币种集合（统一大写，用于快速匹配）
                symbol_set = None
                if symbols:
                    symbol_set = {s.strip().upper() for s in symbols if s}
                    logger.info(f"🔍 持仓查询过滤币种: {list(symbol_set)}")
            
            # 并发获取所有交易所的持仓
            fetch_start_time = time.time()
            tasks = [
                self._fetch_single_exchange_positions(cred, symbol_set=None, symbol_pairs=symbol_pairs) 
                for cred in credentials
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            fetch_elapsed = time.time() - fetch_start_time
            
            # 合并所有结果
            merge_start_time = time.time()
            all_positions = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"获取持仓异常: {result}")
                elif isinstance(result, list):
                    all_positions.extend(result)
            merge_elapsed = time.time() - merge_start_time
            
            elapsed = time.time() - service_start_time
            logger.info(f"🎉 总共获取到 {len(all_positions)} 个持仓，总耗时 {elapsed:.3f}秒 (并发查询: {fetch_elapsed:.3f}秒, 结果合并: {merge_elapsed:.3f}秒)")
            
            # 如果服务层耗时超过0.5秒，打印警告
            if elapsed > 0.5:
                logger.warning(f"⚠️ [性能警告] 持仓服务耗时过长: {elapsed:.3f}秒 (超过0.5秒阈值)")
            
            return {
                "success": True,
                "data": all_positions,
                "total": len(all_positions),
                "elapsed": round(elapsed, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ 获取持仓失败: {e}")
            raise
    
    def _convert_symbol_set_to_list(self, symbol_set: set = None, exchange_id: str = None, market_type: str = None) -> List[str]:
        """
        将基础货币集合转换为交易对列表，用于传递给 adapter
        
        使用 exchange_rules 工具来根据交易所配置生成正确的交易对格式
        
        Args:
            symbol_set: 基础货币集合（如 {'BTC', 'ETH', 'PEOPLE'}），None 表示不过滤
            exchange_id: 交易所 ID（如 'binance', 'bybit'）
            market_type: 市场类型 ('spot' 或 'futures')
        
        Returns:
            交易对列表（如 ['BTC/USDT', 'ETH/USDT', 'PEOPLE/USDT']），如果 symbol_set 为 None 则返回 None
        """
        if symbol_set is None or len(symbol_set) == 0:
            return None
        
        if not exchange_id or not market_type:
            logger.warning(f"⚠️ 缺少交易所ID或市场类型，无法生成交易对，使用默认 USDT")
            # 回退到默认逻辑
            symbols_list = [f"{base.upper()}/USDT" for base in symbol_set if base.upper() not in ['USDT', 'USDC', 'USD', 'BUSD', 'FDUSD']]
            return symbols_list if symbols_list else None
        
        # 使用 exchange_rules 工具生成交易对
        symbols_list = []
        for base_currency in symbol_set:
            base_upper = base_currency.upper().strip()
            
            # 跳过稳定币（它们通常是报价货币，不是基础货币）
            if base_upper in ['USDT', 'USDC', 'USD', 'BUSD', 'FDUSD']:
                continue
            
            # 使用规则配置生成交易对
            try:
                symbol = generate_symbol(base_upper, exchange_id, market_type)
                symbols_list.append(symbol)
            except Exception as e:
                logger.warning(f"⚠️ 生成交易对失败 {base_upper}@{exchange_id}/{market_type}: {e}，使用默认 USDT")
                # 回退到默认格式
                symbols_list.append(f"{base_upper}/USDT")
        
        logger.debug(f"🔍 将基础货币 {list(symbol_set)} 转换为交易对: {symbols_list} (交易所: {exchange_id}, 市场: {market_type})")
        return symbols_list if symbols_list else None
    
    async def _fetch_single_exchange_positions(
        self, 
        cred: Dict[str, str], 
        symbol_set: set = None,
        symbol_pairs: Dict[str, List[str]] = None
    ) -> List[dict]:
        """
        获取单个交易所的持仓数据
        使用 Adapter 统一接口
        
        Args:
            cred: 交易所凭证
            symbol_set: 可选的币种集合（用于过滤），None 表示不过滤（向后兼容）
            symbol_pairs: 可选的交易对映射 {exchange_marketType: [symbols]}，优先使用此参数
        """
        exchange_id = cred.get('exchange', '').lower()
        market_type = cred.get('marketType', 'spot').lower()
        api_key = cred.get('apiKey', '')
        api_secret = cred.get('apiSecret', '')
        password = cred.get('password')
        
        # 如果提供了 symbol_pairs，从中获取对应的交易对列表
        symbols_list = None
        if symbol_pairs:
            key = f"{exchange_id}_{market_type}"
            if key in symbol_pairs:
                symbols_list = symbol_pairs[key]
                logger.debug(f"✅ 使用前端传递的交易对列表: {symbols_list}")
            else:
                # 如果没有找到对应的 key，尝试其他可能的格式
                # 统一账户可能使用 'unified' 作为 market_type
                if market_type == 'unified':
                    # 统一账户需要分别获取现货和合约的交易对
                    spot_key = f"{exchange_id}_spot"
                    futures_key = f"{exchange_id}_futures"
                    # 这里暂时不处理，让后续逻辑处理
                    pass
        
        exchange_start_time = time.time()
        positions = []
        
        try:
            # 构建配置
            config = {
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'timeout': 10000,
            }
            
            if password:
                config['password'] = password
            
            # 应用代理配置
            if self.proxy_config.get('http') or self.proxy_config.get('https'):
                config['proxies'] = self.proxy_config
            
            # 🎯 统一账户模式：一次性获取现货和合约数据
            if market_type == 'unified':
                logger.info(f"🎯 {exchange_id} 统一账户模式：一次性获取现货和合约数据")
                
                # 如果提供了 symbol_pairs，从中获取交易对列表
                if symbol_pairs:
                    symbols_list_spot = symbol_pairs.get(f"{exchange_id}_spot")
                    symbols_list_futures = symbol_pairs.get(f"{exchange_id}_futures")
                else:
                    # 向后兼容：转换 symbol_set 为交易对列表
                    symbols_list_spot = self._convert_symbol_set_to_list(symbol_set, exchange_id, 'spot')
                    symbols_list_futures = self._convert_symbol_set_to_list(symbol_set, exchange_id, 'futures')
                
                # 使用 spot 类型的 adapter 获取余额（现货）
                spot_adapter = get_adapter(exchange_id, 'spot', config)
                loop = asyncio.get_event_loop()
                
                # 获取现货余额
                try:
                    spot_start = time.time()
                    balance = await loop.run_in_executor(None, lambda: spot_adapter.fetch_balance(symbols=symbols_list_spot))
                    spot_elapsed = time.time() - spot_start
                    spot_positions = self._format_spot_balance(balance, exchange_id, 'spot', symbol_set)
                    positions.extend(spot_positions)
                    logger.info(f"✅ {exchange_id} (统一账户-现货) 余额: {len(spot_positions)} 个币种, 耗时: {spot_elapsed:.3f}秒")
                except Exception as e:
                    logger.error(f"❌ {exchange_id} (统一账户-现货) 获取余额失败: {e}")
                
                # 获取合约持仓
                try:
                    futures_start = time.time()
                    futures_adapter = get_adapter(exchange_id, 'futures', config)
                    futures_positions = await loop.run_in_executor(None, lambda: futures_adapter.fetch_positions(symbols=symbols_list_futures))
                    futures_elapsed = time.time() - futures_start
                    formatted_futures = self._format_futures_positions(futures_positions, exchange_id, 'futures', symbol_set)
                    positions.extend(formatted_futures)
                    logger.info(f"✅ {exchange_id} (统一账户-合约) 持仓: {len(formatted_futures)} 个, 耗时: {futures_elapsed:.3f}秒")
                except Exception as e:
                    logger.error(f"❌ {exchange_id} (统一账户-合约) 获取持仓失败: {e}")
                
                exchange_elapsed = time.time() - exchange_start_time
                logger.info(f"⏱️ [性能监控] {exchange_id} (统一账户) 总耗时: {exchange_elapsed:.3f}秒")
                
                return positions
            
            # 🔄 分离账户模式：按 market_type 分别获取
            # 🎯 使用 Adapter 创建交易所实例
            adapter = get_adapter(exchange_id, market_type, config)
            
            loop = asyncio.get_event_loop()
            
            # 如果提供了 symbol_pairs，直接使用；否则转换 symbol_set
            if not symbols_list:
                symbols_list = self._convert_symbol_set_to_list(symbol_set, exchange_id, market_type)
            
            # 根据市场类型调用不同的方法
            if market_type == 'spot':
                # 现货：获取余额
                spot_start = time.time()
                balance = await loop.run_in_executor(None, lambda: adapter.fetch_balance(symbols=symbols_list))
                spot_elapsed = time.time() - spot_start
                positions = self._format_spot_balance(balance, exchange_id, market_type, symbol_set)
                logger.info(f"✅ {exchange_id} ({market_type}) 现货余额: {len(positions)} 个币种, 耗时: {spot_elapsed:.3f}秒")
                
            else:  # futures
                # 合约：获取持仓
                # 传递交易对格式（如 ['PEOPLE/USDT']）给 CCXT
                futures_start = time.time()
                futures_positions = await loop.run_in_executor(None, lambda: adapter.fetch_positions(symbols=symbols_list))
                futures_elapsed = time.time() - futures_start
                positions = self._format_futures_positions(futures_positions, exchange_id, market_type, symbol_set)
                logger.info(f"✅ {exchange_id} ({market_type}) 合约持仓: {len(positions)} 个, 耗时: {futures_elapsed:.3f}秒")
                
                # # 同时获取合约账户余额（某些交易所需要）
                # try:
                #     balance_start = time.time()
                #     futures_balance = await loop.run_in_executor(None, lambda: adapter.fetch_balance(symbols=symbols_list))
                #     balance_elapsed = time.time() - balance_start
                #     balance_positions = self._format_spot_balance(
                #         futures_balance,
                #         exchange_id,
                #         'futures_balance',
                #         symbol_set
                #     )
                #     positions.extend(balance_positions)
                #     logger.info(f"✅ {exchange_id} ({market_type}) 合约账户余额: {len(balance_positions)} 个币种, 耗时: {balance_elapsed:.3f}秒")
                # except Exception as e:
                #     logger.warning(f"⚠️ {exchange_id} 获取合约账户余额失败: {e}")
            
            exchange_elapsed = time.time() - exchange_start_time
            logger.info(f"⏱️ [性能监控] {exchange_id} ({market_type}) 总耗时: {exchange_elapsed:.3f}秒")
            
            # 如果单个交易所查询耗时超过0.3秒，打印警告
            if exchange_elapsed > 0.3:
                logger.warning(f"⚠️ [性能警告] {exchange_id} ({market_type}) 查询耗时过长: {exchange_elapsed:.3f}秒 (超过0.3秒阈值)")
            
            return positions
            
        except Exception as e:
            logger.error(f"❌ {exchange_id} ({market_type}) 获取持仓失败: {e}")
            return []
    
    def _format_spot_balance(
        self, 
        balance: dict, 
        exchange_id: str, 
        position_type: str,
        symbol_set: set = None
    ) -> List[dict]:
        """
        格式化现货余额数据
        
        Args:
            balance: CCXT balance 对象
            exchange_id: 交易所 ID
            position_type: 持仓类型 ('spot' 或 'futures_balance')
            symbol_set: 可选的币种集合（用于过滤），None 表示不过滤
        
        Returns:
            格式化的持仓列表
        """
        positions = []
        total_balance = balance.get('total', {})
        
        # 过滤出有余额的币种
        for currency, amount in total_balance.items():
            if amount and float(amount) > 0:
                # 如果指定了币种过滤，检查是否匹配
                if symbol_set is not None:
                    currency_upper = currency.upper()
                    if currency_upper not in symbol_set:
                        continue  # 跳过不匹配的币种
                
                positions.append({
                    'exchange': exchange_id,
                    'marketType': position_type,  # 标注市场类型
                    'symbol': currency,
                    'type': position_type,
                    'amount': float(amount),
                    'free': float(balance.get('free', {}).get(currency, 0)),
                    'used': float(balance.get('used', {}).get(currency, 0)),
                })
        
        return positions
    
    def _format_futures_positions(
        self, 
        positions_data: list, 
        exchange_id: str,
        market_type: str,
        symbol_set: set = None
    ) -> List[dict]:
        """
        格式化合约持仓数据
        
        Args:
            positions_data: CCXT positions 列表
            exchange_id: 交易所 ID
            market_type: 市场类型
            symbol_set: 可选的币种集合（用于过滤），None 表示不过滤
        
        Returns:
            格式化的持仓列表
        """
        positions = []
        
        # 过滤出有持仓的合约
        for pos in positions_data:
            contracts = float(pos.get('contracts', 0))
            if contracts != 0:
                symbol = pos.get('symbol', '')
                
                # 如果指定了币种过滤，检查是否匹配
                if symbol_set is not None:
                    # 从交易对中提取基础货币（如 "BTC/USDT" -> "BTC"）
                    base_currency = symbol.split('/')[0].upper() if '/' in symbol else symbol.upper()
                    if base_currency not in symbol_set:
                        continue  # 跳过不匹配的币种
                
                side = pos.get('side', '')
                amount = contracts if side == 'long' else -contracts
                
                positions.append({
                    'exchange': exchange_id,
                    'marketType': market_type,  # 标注市场类型
                    'symbol': symbol,
                    'type': 'futures',
                    'amount': amount,
                    'side': side,
                    'notional': float(pos.get('notional', 0)),
                    'unrealizedPnl': float(pos.get('unrealizedPnl', 0)),
                    'leverage': float(pos.get('leverage', 1)),
                    'entryPrice': float(pos.get('entryPrice', 0)),
                    'markPrice': float(pos.get('markPrice', 0)),
                })
        
        return positions
