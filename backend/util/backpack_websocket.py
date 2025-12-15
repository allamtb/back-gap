"""
Backpack Exchange WebSocket 客户端

实现 Backpack 的 WebSocket 流订阅：
- K线 (kline)
- 实时价格 (ticker)
- 订单簿 (depth)

官方文档：https://docs.backpack.exchange/#tag/Streams
"""

import asyncio
import json
import logging
import aiohttp
from typing import Callable, Dict, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class BackpackWebSocketClient:
    """
    Backpack WebSocket 客户端
    
    支持的流类型：
    - kline.<interval>.<symbol>  - K线数据
    - ticker.<symbol>            - 实时价格
    - depth.<symbol>             - 订单簿（实时）
    - depth.200ms.<symbol>       - 订单簿（200ms 聚合）
    - depth.600ms.<symbol>       - 订单簿（600ms 聚合）
    - depth.1000ms.<symbol>      - 订单簿（1000ms 聚合）
    """
    
    # Backpack WebSocket URL (官方文档格式，不带末尾斜杠)
    WS_URL = "wss://ws.backpack.exchange"
    
    # K线周期映射 (统一格式 -> Backpack 格式)
    INTERVAL_MAP = {
        '1m': '1m',
        '3m': '3m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '2h': '2h',
        '4h': '4h',
        '6h': '6h',
        '8h': '8h',
        '12h': '12h',
        '1d': '1d',
        '3d': '3d',
        '1w': '1w',
        '1M': '1M',
    }
    
    def __init__(self, on_message: Optional[Callable] = None, proxy: Optional[str] = None):
        """
        初始化 Backpack WebSocket 客户端
        
        Args:
            on_message: 消息回调函数 callback(stream_type, data)
            proxy: 代理地址 (例如 'http://127.0.0.1:1080')
        """
        self.on_message = on_message
        self.proxy = proxy
        self.websocket = None
        self.session = None
        self.subscriptions: Set[str] = set()
        self.pending_subscriptions: Dict[int, str] = {}  # {id: stream} 跟踪待确认的订阅
        self.subscription_id_counter = 0  # 订阅消息ID计数器
        self.running = False
        self._receive_task = None
        
        # 订单簿状态管理（用于增量更新）
        # 格式：{ 'SOL/USDC': { 'bids': {price: amount}, 'asks': {price: amount}, 'lastUpdateId': 123 } }
        self._orderbooks: Dict[str, Dict] = {}
    
    def _convert_symbol(self, symbol: str, market_type: str = 'spot') -> str:
        """
        转换交易对格式：SOL/USDC -> SOL_USDC (现货) 或 SOL_USDC_PERP (合约)
        
        Args:
            symbol: 标准格式交易对 (SOL/USDC)
            market_type: 市场类型 ('spot' 或 'futures')
            
        Returns:
            Backpack 格式交易对 (SOL_USDC 或 SOL_USDC_PERP)
        """
        backpack_symbol = symbol.replace('/', '_')
        
        # 如果是合约交易且 symbol 不包含 _PERP，则添加后缀
        if market_type.lower() in ['futures', 'future', 'swap', 'perp'] and not backpack_symbol.endswith('_PERP'):
            backpack_symbol = f"{backpack_symbol}_PERP"
        
        return backpack_symbol
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化交易对格式：SOL_USDC -> SOL/USDC, SOL_USDC_PERP -> SOL/USDC
        
        Args:
            symbol: Backpack 格式交易对 (SOL_USDC 或 SOL_USDC_PERP)
            
        Returns:
            标准格式交易对 (SOL/USDC)
        """
        # 移除 _PERP 后缀（如果存在）
        if symbol.endswith('_PERP'):
            symbol = symbol[:-5]  # 移除 '_PERP'
        
        return symbol.replace('_', '/')
    
    async def connect(self):
        """建立 WebSocket 连接"""
        if self.websocket:
            logger.warning("WebSocket 已连接")
            return
        
        try:
            # 创建 aiohttp session
            self.session = aiohttp.ClientSession()
            
            # 连接 WebSocket（使用代理）
            self.websocket = await self.session.ws_connect(
                self.WS_URL,
                proxy=self.proxy,
                timeout=aiohttp.ClientTimeout(total=30),
                heartbeat=20
            )
            self.running = True
            
            # 启动接收消息任务
            self._receive_task = asyncio.create_task(self._receive_messages())
            
            proxy_info = f"(代理: {self.proxy})" if self.proxy else "(直连)"
            logger.info(f"✅ Backpack WebSocket 已连接 {proxy_info}: {self.WS_URL}")
        except Exception as e:
            logger.error(f"❌ Backpack WebSocket 连接失败: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            raise
    
    async def disconnect(self):
        """断开 WebSocket 连接"""
        self.running = False
        
        # 取消任务
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # 关闭连接
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # 关闭 session
        if self.session:
            await self.session.close()
            self.session = None
        
        self.subscriptions.clear()
        logger.info("✅ Backpack WebSocket 已断开")
    
    async def subscribe_kline(self, symbol: str, interval: str = '1m', market_type: str = 'spot'):
        """
        订阅 K线流
        
        Args:
            symbol: 交易对 (例如 'SOL/USDC')
            interval: K线周期 (例如 '1m', '5m', '1h')
            market_type: 市场类型 ('spot' 或 'futures')
        """
        if not self.websocket:
            raise RuntimeError("WebSocket 未连接")
        
        # 转换格式
        backpack_symbol = self._convert_symbol(symbol, market_type)
        backpack_interval = self.INTERVAL_MAP.get(interval, interval)
        
        # 流名称: kline.<interval>.<symbol>
        stream = f"kline.{backpack_interval}.{backpack_symbol}"
        
        if stream in self.subscriptions:
            logger.warning(f"⚠️ 已订阅 K线流: {stream}")
            return
        
        # 发送订阅消息
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream]
        }
        
        await self.websocket.send_json(subscribe_msg)
        self.subscriptions.add(stream)
        
        logger.info(f"📊 已订阅 Backpack K线流: {stream}")
    
    async def subscribe_ticker(self, symbol: str, market_type: str = 'spot'):
        """
        订阅实时价格流
        
        Args:
            symbol: 交易对 (例如 'SOL/USDC')
            market_type: 市场类型 ('spot' 或 'futures')
            
        Returns:
            bool: 订阅是否成功（如果交易对不存在，返回 False）
        """
        if not self.websocket:
            raise RuntimeError("WebSocket 未连接")
        
        # 转换格式
        backpack_symbol = self._convert_symbol(symbol, market_type)
        
        # 流名称: ticker.<symbol>
        stream = f"ticker.{backpack_symbol}"
        
        if stream in self.subscriptions:
            logger.warning(f"⚠️ 已订阅 Ticker流: {stream}")
            return True
        
        # 生成订阅ID
        self.subscription_id_counter += 1
        subscribe_id = self.subscription_id_counter
        
        # 发送订阅消息
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream],
            "id": subscribe_id
        }
        
        try:
            await self.websocket.send_json(subscribe_msg)
            # 先添加到订阅列表和待确认列表（如果后续收到错误，会在 _handle_message 中处理）
            self.subscriptions.add(stream)
            self.pending_subscriptions[subscribe_id] = stream
            logger.info(f"📈 已发送 Backpack Ticker流订阅请求: {stream} (id: {subscribe_id})")
            return True
        except Exception as e:
            logger.error(f"❌ 订阅 Ticker流失败 {stream}: {e}")
            return False
    
    async def subscribe_depth(self, symbol: str, aggregate: Optional[str] = None, market_type: str = 'spot'):
        """
        订阅订单簿流
        
        Args:
            symbol: 交易对 (例如 'SOL/USDC')
            aggregate: 聚合周期 (None='实时', '200ms', '600ms', '1000ms')
            market_type: 市场类型 ('spot' 或 'futures')
        """
        if not self.websocket:
            raise RuntimeError("WebSocket 未连接")
        
        # 转换格式
        backpack_symbol = self._convert_symbol(symbol, market_type)
        
        # 流名称: depth.<symbol> 或 depth.<aggregate>.<symbol>
        if aggregate:
            stream = f"depth.{aggregate}.{backpack_symbol}"
        else:
            stream = f"depth.{backpack_symbol}"
        
        if stream in self.subscriptions:
            logger.warning(f"⚠️ 已订阅 Depth流: {stream}")
            return
        
        # 发送订阅消息
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream]
        }
        
        await self.websocket.send_json(subscribe_msg)
        self.subscriptions.add(stream)
        
        logger.info(f"📊 已订阅 Backpack Depth流: {stream}")
    
    async def unsubscribe(self, stream: str):
        """
        取消订阅
        
        Args:
            stream: 流名称 (例如 'kline.1m.SOL_USDC')
        """
        if not self.websocket:
            raise RuntimeError("WebSocket 未连接")
        
        if stream not in self.subscriptions:
            logger.warning(f"⚠️ 未订阅该流: {stream}")
            return
        
        # 发送取消订阅消息
        unsubscribe_msg = {
            "method": "UNSUBSCRIBE",
            "params": [stream]
        }
        
        await self.websocket.send_json(unsubscribe_msg)
        self.subscriptions.discard(stream)
        
        logger.info(f"❌ 已取消订阅: {stream}")
    
    async def _receive_messages(self):
        """接收并处理 WebSocket 消息"""
        while self.running:
            try:
                msg = await self.websocket.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    # 处理消息
                    await self._handle_message(data)
                    
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("WebSocket 连接错误")
                    self.running = False
                    break
                    
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE):
                    logger.warning("WebSocket 连接已关闭")
                    self.running = False
                    break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"接收消息失败: {e}")
    
    async def _handle_message(self, data: dict):
        """
        处理接收到的消息
        
        官方格式：
        {
          "stream": "depth.SOL_USDC",
          "data": {
            "bids": [...],
            "asks": [...]
          }
        }
        
        或错误消息：
        {
          "error": {...}
        }
        
        或订阅响应：
        {
          "result": null,
          "id": 1
        }
        
        Args:
            data: 消息数据
        """
        # 处理错误消息
        if 'error' in data:
            error_info = data['error']
            error_code = error_info.get('code', 'UNKNOWN')
            error_message = error_info.get('message', 'Unknown error')
            error_id = data.get('id')  # 获取错误对应的订阅ID
            
            # 如果是无效市场错误（4005），从订阅列表中移除并记录警告
            if error_code == 4005:
                # 通过ID找到对应的流
                if error_id is not None and error_id in self.pending_subscriptions:
                    failed_stream = self.pending_subscriptions[error_id]
                    self.subscriptions.discard(failed_stream)
                    del self.pending_subscriptions[error_id]
                    logger.warning(f"⚠️ Backpack 不支持该交易对，已取消订阅: {failed_stream} (code: {error_code}, message: {error_message})")
                else:
                    logger.warning(f"⚠️ Backpack 不支持该交易对: {error_message} (code: {error_code})")
            else:
                # 其他错误，也尝试移除对应的订阅
                if error_id is not None and error_id in self.pending_subscriptions:
                    failed_stream = self.pending_subscriptions[error_id]
                    self.subscriptions.discard(failed_stream)
                    del self.pending_subscriptions[error_id]
                    logger.error(f"❌ Backpack WebSocket 订阅失败，已取消: {failed_stream} - {error_info}")
                else:
                    logger.error(f"❌ Backpack WebSocket 错误: {error_info}")
            return
        
        # 检查是否是订阅响应（成功）
        if 'result' in data and 'id' in data:
            # 订阅成功响应：{"result": null, "id": 1}
            response_id = data.get('id')
            if response_id is not None and response_id in self.pending_subscriptions:
                confirmed_stream = self.pending_subscriptions[response_id]
                del self.pending_subscriptions[response_id]
                logger.debug(f"✅ 订阅确认成功: {confirmed_stream}")
            else:
                logger.debug(f"✅ 订阅确认: {data}")
            return
        
        # 检查是否是流数据
        stream = data.get('stream')
        if not stream:
            # 可能是其他系统消息
            logger.debug(f"收到系统消息: {data}")
            return
        
        # 提取流数据
        stream_data = data.get('data', {})
        
        # 🔍 DEBUG: 打印接收到的原始数据
        logger.debug(f"🔍 收到 Backpack 消息 - stream: {stream}, data keys: {list(stream_data.keys())}")
        
        # 调用回调函数
        if self.on_message:
            try:
                # 判断流类型
                if stream.startswith('kline.'):
                    await self._handle_kline(stream, stream_data)
                elif stream.startswith('ticker.'):
                    await self._handle_ticker(stream, stream_data)
                elif stream.startswith('depth.'):
                    await self._handle_depth(stream, stream_data)
                else:
                    logger.debug(f"未处理的流类型: {stream}")
            except Exception as e:
                logger.error(f"处理消息回调失败: {e}", exc_info=True)
    
    async def _handle_kline(self, stream: str, data: dict):
        """
        处理 K线数据
        
        官方格式：
        stream = "kline.1m.SOL_USDC"
        data = {
          "start": "2024-10-23T10:00:00",
          "end": "2024-10-23T10:01:00",
          "open": "18.75",
          "high": "19.80",
          "low": "18.50",
          "close": "19.25",
          "volume": "32123",
          "trades": 93828
        }
        
        注意：官方文档可能使用不同的字段名，需要根据实际响应调整
        """
        # 从 stream 中提取交易对
        # kline.1m.SOL_USDC
        parts = stream.split('.')
        if len(parts) >= 3:
            backpack_symbol = parts[-1]
            symbol = self._normalize_symbol(backpack_symbol)
        else:
            symbol = "UNKNOWN"
        
        # 解析时间戳（ISO 8601 转毫秒）
        start_time_str = data.get('start') or data.get('t', '')
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            timestamp = int(start_time.timestamp() * 1000)
        except:
            timestamp = int(datetime.now().timestamp() * 1000)
        
        kline_data = {
            'time': timestamp,
            'open': float(data.get('open') or data.get('o', 0)),
            'high': float(data.get('high') or data.get('h', 0)),
            'low': float(data.get('low') or data.get('l', 0)),
            'close': float(data.get('close') or data.get('c', 0)),
            'volume': float(data.get('volume') or data.get('v', 0)),
            'is_closed': data.get('is_closed', data.get('X', False)),
            'trades': data.get('trades', data.get('n', 0))
        }
        
        # 从 stream 中提取 interval
        # stream = "kline.1m.BTC_USDT"
        interval = parts[1] if len(parts) >= 2 else '1m'
        
        logger.debug(f"🔍 K线数据解析完成 - symbol: {symbol}, interval: {interval}, kline: {kline_data}")
        
        # ✅ 传递完整信息给回调（包含 interval）
        await self.on_message('kline', {
            'symbol': symbol,
            'interval': interval,  # ✅ 新增 interval 字段
            'kline': kline_data,
            '_stream': stream  # ✅ 原始流名称（用于调试）
        })
    
    async def _handle_ticker(self, stream: str, data: dict):
        """
        处理 Ticker 数据
        
        官方格式：
        stream = "ticker.SOL_USDC"
        data = {
          "symbol": "SOL_USDC",
          "firstPrice": "18.75",     // 开盘价
          "lastPrice": "19.24",      // 最新价
          "priceChange": "0.49",     // 价格变化
          "priceChangePercent": "2.61",
          "high": "19.80",           // 最高价
          "low": "18.50",            // 最低价
          "volume": "32123",         // 成交量（基础币种）
          "trades": 93828            // 交易笔数
        }
        
        注意：字段名根据实际响应调整
        """
        # 从 stream 中提取交易对
        # ticker.SOL_USDC
        parts = stream.split('.')
        if len(parts) >= 2:
            backpack_symbol = parts[-1]
            symbol = self._normalize_symbol(backpack_symbol)
        else:
            symbol = "UNKNOWN"
        
        ticker_data = {
            'symbol': symbol,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'price': float(data.get('lastPrice') or data.get('c', 0)),
            'open': float(data.get('firstPrice') or data.get('o', 0)),
            'high': float(data.get('high') or data.get('h', 0)),
            'low': float(data.get('low') or data.get('l', 0)),
            'volume': float(data.get('volume') or data.get('v', 0)),
            'quote_volume': float(data.get('quoteVolume') or data.get('V', 0)),
            'trades': data.get('trades', data.get('n', 0))
        }
        
        logger.debug(f"🔍 Ticker数据解析完成 - {ticker_data}")
        
        await self.on_message('ticker', ticker_data)
    
    async def _handle_depth(self, stream: str, data: dict):
        """
        处理订单簿增量更新数据
        
        官方格式：
        stream = "depth.SOL_USDC" 或 "depth.200ms.SOL_USDC"
        data = {
          "e": "depth",             // Event type
          "E": 1694687965941000,    // Event time in microseconds
          "s": "SOL_USDC",          // Symbol
          "a": [["18.70", "0.000"]], // Asks (注意：字段名是 "a" 不是 "asks")
          "b": [["18.67", "0.832"]], // Bids (注意：字段名是 "b" 不是 "bids")
          "U": 94978271,            // First update ID in event
          "u": 94978271,            // Last update ID in event
          "T": 1694687965940999     // Engine timestamp in microseconds
        }
        
        注意：这是增量更新，不是完整快照。数量为 0 表示删除该价格档位。
        """
        # 从 data 中提取交易对（优先使用 data 中的 symbol）
        symbol = data.get('s', '')
        if symbol:
            symbol = self._normalize_symbol(symbol)
        else:
            # 备用：从 stream 中提取
            parts = stream.split('.')
            if len(parts) >= 2:
                backpack_symbol = parts[-1]
                symbol = self._normalize_symbol(backpack_symbol)
            else:
                symbol = "UNKNOWN"
        
        # 获取或初始化订单簿
        if symbol not in self._orderbooks:
            self._orderbooks[symbol] = {
                'bids': {},  # {price: amount}
                'asks': {},  # {price: amount}
                'lastUpdateId': 0
            }
        
        orderbook = self._orderbooks[symbol]
        
        # 获取更新 ID
        first_update_id = data.get('U', 0)
        last_update_id = data.get('u', 0)
        
        # 验证更新序列（可选）
        if orderbook['lastUpdateId'] > 0:
            # 检查是否连续
            if first_update_id != orderbook['lastUpdateId'] + 1:
                logger.warning(f"⚠️ {symbol} 订单簿更新序列不连续: 期望 {orderbook['lastUpdateId'] + 1}, 收到 {first_update_id}")
                # 可以选择重新获取快照，这里暂时忽略
        
        # 应用增量更新到 bids
        raw_bids = data.get('b', [])
        for price_str, amount_str in raw_bids:
            price = float(price_str)
            amount = float(amount_str)
            if amount == 0:
                # 删除该价格档位
                orderbook['bids'].pop(price, None)
            else:
                # 更新该价格档位
                orderbook['bids'][price] = amount
        
        # 应用增量更新到 asks
        raw_asks = data.get('a', [])
        for price_str, amount_str in raw_asks:
            price = float(price_str)
            amount = float(amount_str)
            if amount == 0:
                # 删除该价格档位
                orderbook['asks'].pop(price, None)
            else:
                # 更新该价格档位
                orderbook['asks'][price] = amount
        
        # 更新 lastUpdateId
        orderbook['lastUpdateId'] = last_update_id
        
        # 转换为排序的列表格式
        # Bids: 从高到低排序 (买单价格越高越好)
        sorted_bids = sorted(orderbook['bids'].items(), key=lambda x: x[0], reverse=True)
        # Asks: 从低到高排序 (卖单价格越低越好)
        sorted_asks = sorted(orderbook['asks'].items(), key=lambda x: x[0])
        
        # 只取前 20 档（可配置）
        max_depth = 20
        bids_list = [[price, amount] for price, amount in sorted_bids[:max_depth]]
        asks_list = [[price, amount] for price, amount in sorted_asks[:max_depth]]
        
        # 使用 Backpack 的事件时间（微秒转毫秒）
        event_time = data.get('E', 0)
        if event_time > 0:
            timestamp = int(event_time / 1000)  # 微秒转毫秒
        else:
            timestamp = int(datetime.now().timestamp() * 1000)
        
        # 构造完整订单簿数据发送给前端
        depth_data = {
            'symbol': symbol,
            'timestamp': timestamp,
            'bids': bids_list,
            'asks': asks_list,
        }
        
        logger.debug(f"🔍 Depth更新 - {symbol}: bids={len(bids_list)}, asks={len(asks_list)}, updateId={last_update_id}")
        
        await self.on_message('depth', depth_data)


# ============================================================================
# 订阅管理器（集成到 WebSocketManager）
# ============================================================================

class BackpackSubscriptionManager:
    """
    Backpack 订阅管理器
    
    管理多个交易对的订阅，支持自动重连
    """
    
    def __init__(self):
        self.clients: Dict[str, BackpackWebSocketClient] = {}
        self.message_handlers: Dict[str, Callable] = {}
    
    async def subscribe_kline(self, symbol: str, interval: str, handler: Callable):
        """
        订阅 K线
        
        Args:
            symbol: 交易对
            interval: K线周期
            handler: 消息处理函数
        """
        key = f"kline_{symbol}_{interval}"
        
        if key not in self.clients:
            client = BackpackWebSocketClient(on_message=self._create_handler(handler))
            await client.connect()
            await client.subscribe_kline(symbol, interval)
            self.clients[key] = client
            self.message_handlers[key] = handler
    
    async def subscribe_ticker(self, symbol: str, handler: Callable):
        """订阅实时价格"""
        key = f"ticker_{symbol}"
        
        if key not in self.clients:
            client = BackpackWebSocketClient(on_message=self._create_handler(handler))
            await client.connect()
            await client.subscribe_ticker(symbol)
            self.clients[key] = client
            self.message_handlers[key] = handler
    
    async def subscribe_depth(self, symbol: str, handler: Callable, aggregate: Optional[str] = None):
        """订阅订单簿"""
        key = f"depth_{symbol}_{aggregate or 'realtime'}"
        
        if key not in self.clients:
            client = BackpackWebSocketClient(on_message=self._create_handler(handler))
            await client.connect()
            await client.subscribe_depth(symbol, aggregate)
            self.clients[key] = client
            self.message_handlers[key] = handler
    
    def _create_handler(self, handler: Callable):
        """创建消息处理器包装"""
        async def wrapper(stream_type: str, data: dict):
            await handler(stream_type, data)
        return wrapper
    
    async def cleanup(self):
        """清理所有连接"""
        for key, client in list(self.clients.items()):
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"断开连接失败 {key}: {e}")
        
        self.clients.clear()
        self.message_handlers.clear()
        logger.info("✅ Backpack 订阅管理器已清理")

