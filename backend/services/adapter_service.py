"""
适配器服务层 - 统一封装交易所适配器功能

提供统一的接口，屏蔽底层适配器差异
"""

import logging
from typing import Dict, List, Optional, Any
from exchange_adapters import get_adapter, is_exchange_supported

logger = logging.getLogger(__name__)


class AdapterService:
    """
    适配器服务 - 统一调用接口
    
    设计原则：
        1. 服务层统一接口调用适配器方法
        2. 前端 API 通过服务层访问，不直接依赖适配器
        3. 支持动态交易所（CCXT + 自研适配器）
    """
    
    @staticmethod
    def test_connectivity(exchange_id: str, config: dict) -> Dict[str, Any]:
        """
        测试交易所连通性
        
        Args:
            exchange_id: 交易所 ID
            config: 配置 {'apiKey': '...', 'secret': '...', 'password': '...'}
        
        Returns:
            {'ok': bool, 'serverTime': int, 'accountId': str, 'latencyMs': float}
        """
        try:
            adapter = get_adapter(exchange_id, 'spot', config)
            return adapter.test_connectivity()
        except Exception as e:
            logger.error(f"❌ {exchange_id} 连通性测试失败: {e}")
            return {'ok': False, 'error': str(e)}
    
    @staticmethod
    def fetch_symbols(
        exchange_id: str,
        market_type: str,
        config: dict,
        quote: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取交易对列表
        
        Args:
            exchange_id: 交易所 ID
            market_type: 市场类型 ('spot' 或 'futures')
            config: 配置
            quote: 报价币种过滤
            limit: 返回数量限制
        
        Returns:
            [{'symbol': 'BTC/USDT', 'base': 'BTC', 'quote': 'USDT', ...}, ...]
        """
        try:
            adapter = get_adapter(exchange_id, market_type, config)
            return adapter.fetch_symbols(quote=quote, limit=limit)
        except Exception as e:
            logger.error(f"❌ {exchange_id} 获取交易对失败: {e}")
            return []
    
    @staticmethod
    def fetch_klines(
        exchange_id: str,
        market_type: str,
        config: dict,
        symbol: str,
        interval: str = '15m',
        limit: int = 100,
        since: Optional[int] = None
    ) -> List[List[Any]]:
        """
        获取 K线数据
        
        Args:
            exchange_id: 交易所 ID
            market_type: 市场类型
            config: 配置
            symbol: 交易对
            interval: 时间周期
            limit: 数据条数
            since: 起始时间戳（毫秒）
        
        Returns:
            [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            adapter = get_adapter(exchange_id, market_type, config)
            return adapter.fetch_klines(symbol, interval, limit, since)
        except Exception as e:
            logger.error(f"❌ {exchange_id} 获取K线失败 {symbol}/{interval}: {e}")
            return []
    
    @staticmethod
    def fetch_prices(
        exchange_id: str,
        market_type: str,
        config: dict,
        symbols: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取价格
        
        Args:
            exchange_id: 交易所 ID
            market_type: 市场类型
            config: 配置
            symbols: 交易对列表
        
        Returns:
            {'BTC/USDT': {'last': 50000, 'bid': 49999, 'ask': 50001, 'mark': 50000}, ...}
        """
        try:
            adapter = get_adapter(exchange_id, market_type, config)
            return adapter.fetch_prices(symbols)
        except Exception as e:
            logger.error(f"❌ {exchange_id} 批量获取价格失败: {e}")
            return {s: {'last': 0, 'bid': 0, 'ask': 0, 'mark': 0} for s in symbols}
    
    @staticmethod
    def fetch_positions(
        exchange_id: str,
        market_type: str,
        config: dict,
        symbols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取持仓/余额
        
        Args:
            exchange_id: 交易所 ID
            market_type: 市场类型
            config: 配置
            symbols: 交易对过滤（可选）
        
        Returns:
            现货：[{'exchange': '...', 'type': 'spot', 'symbol': 'BTC', 'free': 1.0, 'used': 0, 'total': 1.0}, ...]
            合约：[{'exchange': '...', 'type': 'futures', 'symbol': 'BTC/USDT', 'size': 10, 'entryPrice': 50000, ...}, ...]
        """
        try:
            adapter = get_adapter(exchange_id, market_type, config)
            
            # 对于 Backpack 等非 CCXT 适配器，直接调用 fetch_positions
            if hasattr(adapter, 'fetch_positions') and adapter.exchange is None:
                return adapter.fetch_positions(symbols)
            
            # 对于 CCXT 适配器，调用标准方法
            return adapter.fetch_positions()
        except Exception as e:
            logger.error(f"❌ {exchange_id} 获取持仓失败: {e}")
            return []
    
    @staticmethod
    def fetch_orders(
        exchange_id: str,
        market_type: str,
        config: dict,
        symbols: Optional[List[str]] = None,
        since: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        获取订单
        
        Args:
            exchange_id: 交易所 ID
            market_type: 市场类型
            config: 配置
            symbols: 交易对列表（可选）
            since: 起始时间戳（毫秒）
            limit: 返回数量限制
        
        Returns:
            [{'orderId': '...', 'symbol': 'BTC/USDT', 'side': 'buy', 'type': 'limit', ...}, ...]
        """
        try:
            adapter = get_adapter(exchange_id, market_type, config)
            
            # 如果有多个交易对，循环查询
            if symbols:
                all_orders = []
                for symbol in symbols:
                    orders = adapter.fetch_orders(symbol=symbol, since=since, limit=limit)
                    all_orders.extend(orders)
                return all_orders
            else:
                return adapter.fetch_orders(since=since, limit=limit)
        except Exception as e:
            logger.error(f"❌ {exchange_id} 获取订单失败: {e}")
            return []
    
    @staticmethod
    def create_order(
        exchange_id: str,
        market_type: str,
        config: dict,
        symbol: str,
        side: str,
        type_: str,
        amount: float,
        price: Optional[float] = None,
        time_in_force: Optional[str] = None,
        reduce_only: Optional[bool] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            exchange_id: 交易所 ID
            market_type: 市场类型
            config: 配置
            symbol: 交易对
            side: 方向 ('buy' 或 'sell')
            type_: 类型 ('market', 'limit', 'stop', etc.)
            amount: 数量
            price: 价格（限价单必填）
            time_in_force: 有效期类型
            reduce_only: 仅减仓
            client_order_id: 客户端订单 ID
        
        Returns:
            {'id': '...', 'clientOrderId': '...', 'status': '...', 'filled': 0, ...}
        """
        try:
            adapter = get_adapter(exchange_id, market_type, config)
            
            # 对于 Backpack 等非 CCXT 适配器
            if hasattr(adapter, 'create_order') and adapter.exchange is None:
                return adapter.create_order(
                    symbol, side, type_, amount, price,
                    time_in_force, reduce_only, client_order_id
                )
            
            # 对于 CCXT 适配器（透传机制）
            order_params = {}
            if time_in_force:
                order_params['timeInForce'] = time_in_force
            if reduce_only is not None:
                order_params['reduceOnly'] = reduce_only
            if client_order_id:
                order_params['clientOrderId'] = client_order_id
            
            raw_order = adapter.create_order(
                symbol=symbol,
                type=type_,
                side=side,
                amount=amount,
                price=price,
                params=order_params
            )
            
            # 标准化返回
            return {
                'id': raw_order.get('id'),
                'clientOrderId': raw_order.get('clientOrderId'),
                'status': raw_order.get('status', '').lower(),
                'filled': float(raw_order.get('filled', 0)),
                'remaining': float(raw_order.get('remaining', 0)),
                'avgPrice': float(raw_order.get('average', raw_order.get('price', 0)) or 0),
                'ts': raw_order.get('timestamp')
            }
        except Exception as e:
            logger.error(f"❌ {exchange_id} 创建订单失败: {e}")
            raise
    
    @staticmethod
    def is_supported(exchange_id: str) -> bool:
        """
        检查交易所是否被支持
        
        Args:
            exchange_id: 交易所 ID
        
        Returns:
            True if supported
        """
        return is_exchange_supported(exchange_id)



