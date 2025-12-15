"""
订单管理服务
使用 Adapter 架构处理订单查询和格式化
"""

import logging
import time
import asyncio
from typing import Dict, List, Any
from exchange_adapters import get_adapter

logger = logging.getLogger(__name__)


class OrderService:
    """订单管理服务 - 使用 Adapter 架构"""
    
    def __init__(self, proxy_config: Dict[str, str] = None):
        """
        初始化订单服务
        
        Args:
            proxy_config: 代理配置（可选）
        """
        self.proxy_config = proxy_config or {}
        logger.info("订单服务初始化完成（使用 Adapter 架构）")
    
    async def get_orders(self, credentials: List[Dict[str, str]], symbols: List[str] = None, symbol_pairs: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        获取多个交易所的订单列表
        支持现货和合约，通过 marketType 区分
        
        Args:
            credentials: 交易所凭证列表，每个包含：
                - exchange: 交易所 ID
                - marketType: 市场类型 ('spot' 或 'futures')
                - apiKey: API Key
                - apiSecret: API Secret
                - password: 密码（可选）
            symbols: 可选的币种列表（如 ['BTC', 'ETH']），用于优化查询
            
        Returns:
            {
                "success": True,
                "data": [...],  # 订单列表
                "total": 10,
                "elapsed": 1.23
            }
        """
        start_time = time.time()
        
        try:
            if not credentials:
                return {"success": True, "data": [], "total": 0}
            
            # 并发获取所有交易所的订单
            tasks = [
                self._fetch_single_exchange_orders(cred, symbols, symbol_pairs) 
                for cred in credentials
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并所有结果
            all_orders = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"获取订单异常: {result}")
                elif isinstance(result, list):
                    all_orders.extend(result)
            
            elapsed = time.time() - start_time
            logger.info(f"🎉 总共获取到 {len(all_orders)} 个订单，耗时 {elapsed:.2f}秒")
            
            return {
                "success": True,
                "data": all_orders,
                "total": len(all_orders),
                "elapsed": round(elapsed, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ 获取订单失败: {e}")
            raise
    
    async def _fetch_single_exchange_orders(self, cred: Dict[str, str], symbols: List[str] = None, symbol_pairs: Dict[str, List[str]] = None) -> List[dict]:
        """
        获取单个交易所的订单列表
        使用 Adapter 统一接口
        
        Args:
            cred: 交易所凭证
            symbols: 可选的币种列表（如 ['BTC', 'ETH']），用于优化查询
        """
        exchange_id = cred.get('exchange', '').lower()
        market_type = cred.get('marketType', 'spot').lower()
        api_key = cred.get('apiKey', '')
        api_secret = cred.get('apiSecret', '')
        password = cred.get('password')
        
        orders = []
        
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
            
            # 🎯 统一账户模式：一次性获取现货和合约订单
            if market_type == 'unified':
                logger.info(f"🎯 {exchange_id} 统一账户模式：一次性获取现货和合约订单")
                
                loop = asyncio.get_event_loop()
                since = None
                limit = 500
                
                # 获取现货订单
                try:
                    spot_adapter = get_adapter(exchange_id, 'spot', config)
                    if symbols:
                        logger.info(f"🔍 {exchange_id} (统一账户-现货) - 筛选币种: {symbols}")
                    else:
                        logger.info(f"🔍 {exchange_id} (统一账户-现货) - 所有币种")
                    
                    spot_orders = await loop.run_in_executor(
                        None,
                        spot_adapter.fetch_orders,
                        None, since, limit, symbols
                    )
                    orders.extend(spot_orders)
                    logger.info(f"✅ {exchange_id} (统一账户-现货) 获取到 {len(spot_orders)} 个订单")
                except Exception as e:
                    logger.error(f"❌ {exchange_id} (统一账户-现货) 获取订单失败: {e}")
                
                # 🔧 获取合约订单
                try:
                    futures_adapter = get_adapter(exchange_id, 'futures', config)
                    if symbols:
                        logger.info(f"🔍 {exchange_id} (统一账户-合约) - 筛选币种: {symbols}")
                    else:
                        logger.info(f"🔍 {exchange_id} (统一账户-合约) - 所有币种")
                    
                    futures_orders = await loop.run_in_executor(
                        None,
                        futures_adapter.fetch_orders,
                        None, since, limit, symbols
                    )
                    orders.extend(futures_orders)
                    logger.info(f"✅ {exchange_id} (统一账户-合约) 获取到 {len(futures_orders)} 个订单")
                except Exception as e:
                    logger.error(f"❌ {exchange_id} (统一账户-合约) 获取订单失败: {e}")
                
                return orders
            
            # 🔄 分离账户模式：按 market_type 分别获取
            # ✅ 添加详细日志
            
            # 🔧 如果提供了 symbol_pairs，优先使用交易对列表
            symbols_list = None
            if symbol_pairs:
                key = f"{exchange_id}_{market_type}"
                if key in symbol_pairs:
                    symbols_list = symbol_pairs[key]
                    logger.info(f"🔍 开始获取订单: {exchange_id} ({market_type}) - 使用交易对列表: {symbols_list}")
                else:
                    logger.info(f"🔍 开始获取订单: {exchange_id} ({market_type}) - symbol_pairs 中未找到 {key}")
            elif symbols:
                logger.info(f"🔍 开始获取订单: {exchange_id} ({market_type}) - 筛选币种: {symbols}")
            else:
                logger.info(f"🔍 开始获取订单: {exchange_id} ({market_type}) - 所有币种")
            logger.info(f"   API Key: {api_key[:8]}..." if api_key else "   API Key: (空)")
            logger.info(f"   Market Type: {market_type}")
            
            # 🎯 使用 Adapter 创建交易所实例
            try:
                adapter = get_adapter(exchange_id, market_type, config)
                logger.info(f"   ✅ Adapter 创建成功: {exchange_id} ({market_type})")
            except Exception as e:
                logger.error(f"   ❌ Adapter 创建失败: {exchange_id} ({market_type}): {e}")
                return orders
            
            loop = asyncio.get_event_loop()
            
            # 🔧 使用 Adapter 的 fetch_orders 接口获取所有订单
            # since 参数：None 表示获取完整历史（由交易所决定）
            since = None  # 获取完整历史订单
            limit = 500   # 增加订单数量限制
            
            try:
                # 🔧 如果提供了交易对列表，直接传递交易对；否则传递币种列表让 adapter 推测
                if symbols_list:
                    logger.info(f"   📞 调用 adapter.fetch_orders(symbols={symbols_list}, since={since}, limit={limit})")
                    # 传递交易对列表（作为 symbols 参数）
                    all_orders = await loop.run_in_executor(
                        None,
                        adapter.fetch_orders,
                        None,   # symbol=None 表示不指定单个交易对
                        since,  # 起始时间（None=完整历史）
                        limit,  # 订单数量限制
                        symbols_list  # 直接传递交易对列表（如 ['PEOPLE/USDT', 'PEOPLE/USDT:USDT']）
                    )
                else:
                    logger.info(f"   📞 调用 adapter.fetch_orders(symbol=None, base_currencies={symbols}, since={since}, limit={limit})")
                    # ✅ 通过 Adapter 统一接口获取订单（包括开放的和已完成的）
                    # 🎯 传递 base_currencies 参数，让 adapter 根据币种推测交易对
                    all_orders = await loop.run_in_executor(
                        None,
                        adapter.fetch_orders,
                        None,   # symbol=None 表示不指定单个交易对
                        since,  # 起始时间（None=完整历史）
                        limit,  # 订单数量限制
                        symbols # base_currencies 币种列表（如 ['BTC', 'ETH']）
                    )
                
                # ✅ Adapter 已经返回完全标准化的订单格式（包含 exchange 和 marketType）
                orders.extend(all_orders)
                
                if len(all_orders) > 0:
                    logger.info(f"✅ {exchange_id} ({market_type}) 获取到 {len(all_orders)} 个历史订单")
                    # 显示订单的市场类型分布
                    spot_count = sum(1 for o in all_orders if (o.get('marketType') == 'spot' or o.get('order_type') == 'spot'))
                    futures_count = sum(1 for o in all_orders if (o.get('marketType') == 'futures' or o.get('order_type') == 'futures'))
                    logger.info(f"   📊 订单分布: 现货={spot_count}, 合约={futures_count}")
                    if all_orders:
                        logger.info(f"   订单示例: {all_orders[0]}")
                else:
                    logger.info(f"ℹ️  {exchange_id} ({market_type}) 无历史订单")
                
            except Exception as e:
                logger.error(f"❌ {exchange_id} ({market_type}) 获取订单失败: {e}")
                logger.error(f"   错误详情:", exc_info=True)
            
            return orders
            
        except Exception as e:
            logger.error(f"❌ {exchange_id} ({market_type}) 创建交易所实例失败: {e}")
            return []
    
