"""
WebSocket 实时订阅工具模块

提供 WebSocket 连接管理和 K 线实时数据推送功能
使用 ccxt.pro 实现交易所 WebSocket 订阅
对于不支持的交易所（如 Backpack），使用自定义 WebSocket 客户端
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import ccxt.pro as ccxtpro
from util.market_cache import MarketCache
from util.backpack_websocket import BackpackWebSocketClient

logger = logging.getLogger(__name__)


# ============================================================================
# WebSocket 实时订阅管理
# ============================================================================

class WebSocketManager:
    """WebSocket 连接和订阅管理器"""
    
    def __init__(self, proxy_config: dict, market_cache: MarketCache):
        """
        初始化 WebSocket 管理器
        
        Args:
            proxy_config: 代理配置字典
            market_cache: 市场数据缓存管理器
        """
        self.proxy_config = proxy_config
        self.market_cache = market_cache
        
        # 打印详细的代理配置信息（用于调试）
        logger.info(f"🔍 DEBUG - WebSocketManager.__init__() 接收到的 proxy_config:")
        logger.info(f"  - Type: {type(proxy_config)}")
        logger.info(f"  - Value: {proxy_config}")
        logger.info(f"  - Is None: {proxy_config is None}")
        logger.info(f"  - Is Empty: {not proxy_config}")
        
        if proxy_config:
            logger.info(f"📡 WebSocketManager 代理配置: {proxy_config}")
            logger.info(f"  - http: {proxy_config.get('http', 'NOT SET')}")
            logger.info(f"  - https: {proxy_config.get('https', 'NOT SET')}")
            logger.info(f"  - ws: {proxy_config.get('ws', 'NOT SET')}")
        else:
            logger.warning(f"⚠️ WebSocketManager 初始化时 proxy_config 为空")
        
        # WebSocket 客户端集合
        self.ws_clients: Set[WebSocket] = set()
        
        # ✅ 订阅管理：记录每个订阅有哪些客户端
        # key: subscription_key (如 "binance_BTC/USDT_1m_spot")
        # value: Set[WebSocket] (订阅了该数据的客户端集合)
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        
        # ccxt.pro 交易所实例
        self.pro_exchanges: Dict[str, ccxtpro.Exchange] = {}
        
        # Backpack 自定义 WebSocket 客户端（改为共享模式）
        # key: f"backpack_{market_type}" (如 "backpack_spot", "backpack_futures")
        # value: BackpackWebSocketClient (共享的客户端实例)
        self.backpack_clients: Dict[str, BackpackWebSocketClient] = {}
        
        # Backpack 订阅元数据 (用于存储每个订阅的 market_type 等信息)
        # key: f"{exchange}:{symbol}:{stream_type}", value: {'market_type': 'spot/futures'}
        self.backpack_subscription_metadata: Dict[str, dict] = {}
        
        # 订阅任务管理
        self.ws_tasks: Dict[str, asyncio.Task] = {}  # subscription_key -> task
    
    def _process_proxy_url(self, proxy_url: str, protocol: str = 'socks5') -> str:
        """
        处理代理 URL，自动添加协议前缀
        
        Args:
            proxy_url: 原始代理 URL
            protocol: 默认协议 ('http' 或 'socks5')
            
        Returns:
            处理后的代理 URL
            
        示例：
            '127.0.0.1:1080' -> 'socks5://127.0.0.1:1080' (WebSocket)
            'http://127.0.0.1:7890' -> 'http://127.0.0.1:7890' (保持不变)
        """
        # 如果已经有协议前缀，直接返回
        if '://' in proxy_url:
            return proxy_url
        
        # 自动添加协议前缀
        return f"{protocol}://{proxy_url}"
    
    async def get_pro_exchange(self, exchange_name: str, market_type: str = 'spot') -> ccxtpro.Exchange:
        """
        获取或创建 ccxt.pro 交易所实例（用于 WebSocket）
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型 ('spot' 或 'futures')
            
        Returns:
            ccxt.pro 交易所实例
            
        Raises:
            ValueError: 如果 ccxt.pro 不支持该交易所
        """
        # 使用包含市场类型的key来区分不同的实例
        exchange_key = f"{exchange_name}_{market_type}"
        
        if exchange_key not in self.pro_exchanges:
            if not hasattr(ccxtpro, exchange_name):
                raise ValueError(f"ccxt.pro 不支持交易所: {exchange_name}")
            
            exchange_class = getattr(ccxtpro, exchange_name)
            
            # 根据交易所和市场类型设置 defaultType
            if market_type.lower() in ['futures', 'future']:
                # 币安使用 'future'，其他交易所（如 OKX、Gate）使用 'swap'
                if exchange_name.lower() == 'binance':
                    default_type = 'future'
                else:
                    default_type = 'swap'
            else:
                default_type = 'spot'
            
            # 创建配置
            config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': default_type,
                }
            }
            
            # ✅ CCXT.pro WebSocket 代理配置
            if self.proxy_config:
                # 优先使用 ws 字段作为 WebSocket 代理，如果没有则使用 http 作为备用
                ws_proxy = self.proxy_config.get('ws', '').strip()
                http_proxy = self.proxy_config.get('http', '').strip()
                
                # WebSocket 代理：优先使用 ws，如果没有则使用 http
                websocket_proxy = ws_proxy if ws_proxy else http_proxy
                
                # 只有当代理 URL 非空时才添加
                if websocket_proxy:
                    # ⚠️ 注意：对于 WebSocket 连接，使用 wsProxy 配置
                    # - wsProxy: WebSocket 专用代理配置（ccxt.pro 使用此参数）
                    # - httpProxy: REST API 代理（如果需要）
                    config['wsProxy'] = websocket_proxy
                    
                    # REST API 代理（如果需要）
                    if http_proxy:
                        config['httpProxy'] = http_proxy
                    
                    # 详细的代理日志
                    proxy_source = "ws字段" if ws_proxy else "http字段(备用)"
                    logger.info(f"🌐 {exchange_name} (pro-{market_type}) WebSocket 代理 ({proxy_source}): {websocket_proxy}")
                else:
                    logger.debug(f"ℹ️ {exchange_name} (pro-{market_type}) 未配置代理（直连）")
            else:
                logger.warning(f"⚠️ DEBUG - self.proxy_config 为空或 None")
            
            # 创建交易所实例
            exchange = exchange_class(config)
            
            # 🔍 DEBUG: 验证代理是否被正确设置
           
            
    
            # 加载市场数据
            try:
                # 尝试从缓存加载
                cached_markets = self.market_cache.load_from_cache(exchange_name)
                if cached_markets:
                    exchange.markets = cached_markets
                    logger.info(f"✅ {exchange_name} (pro-{market_type}) 已从缓存加载市场数据")
                else:
                    await exchange.load_markets()
                    self.market_cache.save_to_cache(exchange_name, exchange.markets)
                    logger.info(f"✅ {exchange_name} (pro-{market_type}) 已加载市场数据")
            except Exception as e:
                logger.warning(f"加载市场数据失败 {exchange_name} (pro-{market_type}): {e}")
            
            self.pro_exchanges[exchange_key] = exchange
        
        return self.pro_exchanges[exchange_key]
    
    def _get_default_depth_limit(self, exchange_name: str, market_type: str) -> int:
        """
        根据交易所和市场类型获取合适的订单簿深度默认值
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型 ('spot' 或 'futures')
            
        Returns:
            合适的 limit 值
        """
        # Bybit 现货市场只支持: [1, 50, 200, 1000]
        if exchange_name.lower() == 'bybit':
            if market_type.lower() in ['spot']:
                return 50
            # Bybit 合约市场支持更多选项
            return 25
        
        # OKX 的限制
        if exchange_name.lower() == 'okx':
            return 20
        
        # Binance 默认可以用 5-5000 之间的值
        if exchange_name.lower() == 'binance':
            return 20
        
        # 其他交易所默认值
        return 20
    
    def _adjust_depth_limit(self, exchange_name: str, market_type: str, limit: int) -> int:
        """
        调整订单簿深度值以符合交易所要求
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型 ('spot' 或 'futures')
            limit: 请求的 limit 值
            
        Returns:
            调整后的 limit 值
        """
        # Bybit 现货市场只支持: [1, 50, 200, 1000]
        if exchange_name.lower() == 'bybit' and market_type.lower() in ['spot']:
            allowed_limits = [1, 50, 200, 1000]
            # 找到最接近且不小于请求值的允许值
            for allowed in allowed_limits:
                if allowed >= limit:
                    return allowed
            # 如果都小于，返回最大值
            return allowed_limits[-1]
        
        # 其他交易所直接返回
        return limit
    
    async def watch_ticker_task(self, exchange_name: str, symbol: str, market_type: str = 'spot'):
        """
        监听 Ticker 数据并广播给所有客户端
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            market_type: 市场类型 ('spot' 或 'futures')
        """
        subscription_key = f"ticker_{exchange_name}_{symbol}_{market_type}"
        
        # Backpack 使用自定义 WebSocket 客户端
        if exchange_name.lower() == 'backpack':
            await self._watch_backpack_ticker(exchange_name, symbol, market_type, subscription_key)
            return
        
        retry_count = 0
        max_retries = 10
        
        try:
            exchange = await self.get_pro_exchange(exchange_name, market_type)
            
            # 首次连接日志
            logger.info(f"🔌 正在连接 {exchange_name} ticker WebSocket: {symbol}")
            first_connection = True
            
            while True:
                try:
                    # ✅ 检查是否有订阅者
                    if subscription_key not in self.subscriptions or len(self.subscriptions[subscription_key]) == 0:
                        logger.warning(f"⚠️ 没有订阅者，暂停 ticker 任务: {subscription_key}")
                        await asyncio.sleep(5)  # 等待订阅者
                        continue
                    
                    # 使用 ccxt.pro 的 watch_ticker 方法实时订阅（长连接，会持续等待数据）
                    ticker = await exchange.watch_ticker(symbol)
                    
                    # 首次连接成功日志
                    if first_connection:
                        logger.info(f"✅ {exchange_name} ticker WebSocket 连接成功: {symbol}")
                        first_connection = False
                    
                    # 重置重试计数
                    retry_count = 0
                    
                    if ticker:
                        # ✅ 精准推送：构造消息
                        message = {
                            'type': 'ticker_update',
                            'data': {
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'market_type': market_type,
                                'ticker': {
                                    'price': ticker.get('last'),
                                    'timestamp': ticker.get('timestamp'),
                                    'volume': ticker.get('baseVolume'),
                                    'change': ticker.get('change'),
                                    'percentage': ticker.get('percentage'),
                                    'bid': ticker.get('bid'),
                                    'ask': ticker.get('ask'),
                                    'high': ticker.get('high'),
                                    'low': ticker.get('low'),
                                }
                            }
                        }
                        
                        # ✅ 精准推送：只发送给订阅了该数据的客户端
                        if subscription_key in self.subscriptions:
                            subscribers = self.subscriptions[subscription_key]
                            
                            disconnected = set()
                            for client in subscribers:
                                try:
                                    await client.send_text(json.dumps(message))
                                except:
                                    disconnected.add(client)
                            
                            # 清理断开的客户端
                            for client in disconnected:
                                subscribers.discard(client)
                                for subs in self.subscriptions.values():
                                    subs.discard(client)
                    
                except asyncio.CancelledError:
                    logger.info(f"Ticker监听任务已取消: {subscription_key}")
                    raise
                except Exception as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = min(retry_count * 2, 30)
                        logger.warning(f"Ticker监听错误 {subscription_key} (重试 {retry_count}/{max_retries}): {e}，等待 {wait_time}秒...")
                        logger.warning(f"🔍 错误详情: {type(e).__name__}: {str(e)}")
                        import traceback
                        logger.debug(f"🔍 完整堆栈:\n{traceback.format_exc()}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Ticker达到最大重试次数 {subscription_key}: {e}")
                        import traceback
                        logger.error(f"🔍 完整堆栈:\n{traceback.format_exc()}")
                        raise
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Ticker监听任务失败 {subscription_key}: {e}")
        finally:
            # 清理任务
            if subscription_key in self.ws_tasks:
                del self.ws_tasks[subscription_key]
                logger.info(f"清理Ticker任务: {subscription_key}")
    
    async def watch_depth_task(self, exchange_name: str, symbol: str, market_type: str = 'spot', limit: int = 20):
        """
        监听订单薄(Depth)数据并广播给所有客户端
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            market_type: 市场类型 ('spot' 或 'futures')
            limit: 订单薄档位数量
        """
        subscription_key = f"depth_{exchange_name}_{symbol}_{market_type}"
        
        # Backpack 使用自定义 WebSocket 客户端
        if exchange_name.lower() == 'backpack':
            await self._watch_backpack_depth(exchange_name, symbol, market_type, subscription_key)
            return
        
        retry_count = 0
        max_retries = 10
        
        try:
            exchange = await self.get_pro_exchange(exchange_name, market_type)
            
            # 调整 limit 以符合交易所要求
            adjusted_limit = self._adjust_depth_limit(exchange_name, market_type, limit)
            if adjusted_limit != limit:
                logger.info(f"📊 {exchange_name} {market_type} 订单簿深度已调整: {limit} -> {adjusted_limit}")
            
            while True:
                try:
                    # 使用 ccxt.pro 的 watch_order_book 方法实时订阅
                    order_book = await exchange.watch_order_book(symbol, adjusted_limit)
                    
                    # 重置重试计数
                    retry_count = 0
                    
                    if order_book:
                        # ✅ 精准推送：构造消息
                        message = {
                            'type': 'depth_update',
                            'data': {
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'market_type': market_type,
                                'depth': {
                                    'bids': order_book.get('bids', [])[:adjusted_limit],  # [[price, amount], ...]
                                    'asks': order_book.get('asks', [])[:adjusted_limit],  # [[price, amount], ...]
                                    'timestamp': order_book.get('timestamp'),
                                }
                            }
                        }
                        
                        # ✅ 精准推送：只发送给订阅了该数据的客户端
                        if subscription_key in self.subscriptions:
                            subscribers = self.subscriptions[subscription_key]
                            
                            disconnected = set()
                            for client in subscribers:
                                try:
                                    await client.send_text(json.dumps(message))
                                except:
                                    disconnected.add(client)
                            
                            # 清理断开的客户端
                            for client in disconnected:
                                subscribers.discard(client)
                                for subs in self.subscriptions.values():
                                    subs.discard(client)
                    
                except asyncio.CancelledError:
                    logger.info(f"Depth监听任务已取消: {subscription_key}")
                    raise
                except Exception as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = min(retry_count * 2, 30)
                        logger.warning(f"Depth监听错误 {subscription_key} (重试 {retry_count}/{max_retries}): {e}，等待 {wait_time}秒...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Depth达到最大重试次数 {subscription_key}: {e}")
                        raise
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Depth监听任务失败 {subscription_key}: {e}")
        finally:
            # 清理任务
            if subscription_key in self.ws_tasks:
                del self.ws_tasks[subscription_key]
                logger.info(f"清理Depth任务: {subscription_key}")
    
    async def watch_klines_task(self, exchange_name: str, symbol: str, interval: str, market_type: str = 'spot'):
        """
        监听 K 线数据并广播给所有客户端
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            interval: K 线周期
            market_type: 市场类型 ('spot' 或 'futures')
        """
        subscription_key = f"{exchange_name}_{symbol}_{interval}_{market_type}"
        
        # Backpack 使用自定义 WebSocket 客户端
        if exchange_name.lower() == 'backpack':
            await self._watch_backpack_klines(exchange_name, symbol, interval, market_type, subscription_key)
            return
        
        retry_count = 0
        max_retries = 10
        
        try:
            exchange = await self.get_pro_exchange(exchange_name, market_type)
            
            while True:
                try:
                    # 使用 ccxt.pro 的 watch_ohlcv 方法实时订阅
                    ohlcv = await exchange.watch_ohlcv(symbol, interval)
                    
                    # 重置重试计数
                    retry_count = 0
                    
                    if ohlcv and len(ohlcv) > 0:
                        # 获取最新的 K 线
                        latest_kline = ohlcv[-1]
                        
                        kline_data = {
                            'time': latest_kline[0],
                            'open': float(latest_kline[1]),
                            'high': float(latest_kline[2]),
                            'low': float(latest_kline[3]),
                            'close': float(latest_kline[4]),
                            'volume': float(latest_kline[5])
                        }
                        
                        # ✅ 精准推送：构造包含 interval 的消息
                        message = {
                            'type': 'kline_update',
                            'data': {
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'interval': interval,  # ✅ 添加 interval 字段
                                'market_type': market_type,
                                'kline': kline_data
                            }
                        }
                        
                        # ✅ 精准推送：只发送给订阅了该数据的客户端
                        if subscription_key in self.subscriptions:
                            subscribers = self.subscriptions[subscription_key]
                            
                            disconnected = set()
                            for client in subscribers:
                                try:
                                    await client.send_text(json.dumps(message))
                                except:
                                    disconnected.add(client)
                            
                            # 清理断开的客户端
                            for client in disconnected:
                                subscribers.discard(client)
                                # 从所有订阅中移除
                                for subs in self.subscriptions.values():
                                    subs.discard(client)
                        else:
                            logger.warning(f"⚠️ 没有订阅者：{subscription_key}")
                    
                except asyncio.CancelledError:
                    logger.info(f"监听任务已取消: {subscription_key}")
                    raise
                except Exception as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = min(retry_count * 2, 30)
                        logger.warning(f"监听错误 {subscription_key} (重试 {retry_count}/{max_retries}): {e}，等待 {wait_time}秒...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"达到最大重试次数 {subscription_key}: {e}")
                        raise
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"监听任务失败 {subscription_key}: {e}")
        finally:
            # 清理任务
            if subscription_key in self.ws_tasks:
                del self.ws_tasks[subscription_key]
                logger.info(f"清理任务: {subscription_key}")
    
    async def handle_websocket(self, websocket: WebSocket):
        """
        处理 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接实例
        """
        await websocket.accept()
        self.ws_clients.add(websocket)
        logger.info(f"WebSocket 客户端已连接，当前连接数: {len(self.ws_clients)}")
        
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                
                if msg_type == "subscribe":
                    await self._handle_subscribe(websocket, message)
                
                elif msg_type == "subscribe_ticker":
                    await self._handle_subscribe_ticker(websocket, message)
                
                elif msg_type == "subscribe_depth":
                    await self._handle_subscribe_depth(websocket, message)
                    
                elif msg_type == "unsubscribe":
                    await self._handle_unsubscribe(websocket, message)
                
                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif msg_type == "status":
                    await self._handle_status(websocket)
                    
        except WebSocketDisconnect:
            logger.info("WebSocket 客户端断开连接")
        except Exception as e:
            logger.error(f"WebSocket 错误: {e}")
        finally:
            # 移除客户端
            self.ws_clients.discard(websocket)
            logger.info(f"WebSocket 客户端已移除，当前连接数: {len(self.ws_clients)}")
    
    async def _handle_subscribe(self, websocket: WebSocket, message: dict):
        """处理K线订阅请求（改进版：订阅管理）"""
        try:
            msg_data = message.get("data", {})
            exchange = msg_data.get("exchange_a")
            symbol = msg_data.get("symbol")
            interval = msg_data.get("interval", "1m")
            market_type = msg_data.get("market_type", "spot")
            
            if not exchange or not symbol:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "缺少 exchange 或 symbol 参数"
                }))
                return
            
            # 生成订阅 key
            sub_key = f"{exchange}_{symbol}_{interval}_{market_type}"
            
            market_type_label = "合约" if market_type.lower() in ['futures', 'future', 'swap'] else "现货"
            logger.info(f"📨 收到K线订阅请求: {sub_key} ({market_type_label})")
            
            # ✅ 记录订阅关系
            if sub_key not in self.subscriptions:
                self.subscriptions[sub_key] = set()
            self.subscriptions[sub_key].add(websocket)
            logger.info(f"✅ 已添加订阅关系: {sub_key}, 当前订阅者数量: {len(self.subscriptions[sub_key])}")
            
            # 如果任务不存在，创建新任务
            if sub_key not in self.ws_tasks:
                # 创建监听任务
                task = asyncio.create_task(
                    self.watch_klines_task(exchange, symbol, interval, market_type)
                )
                self.ws_tasks[sub_key] = task
                logger.info(f"✅ 已创建K线订阅任务: {sub_key}")
            else:
                logger.info(f"♻️ 复用现有K线订阅任务: {sub_key}")
            
            # 发送订阅确认
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "data": {
                    "exchange": exchange,
                    "symbol": symbol,
                    "interval": interval,
                    "market_type": market_type
                }
            }))
        except Exception as e:
            logger.error(f"❌ 处理K线订阅请求失败: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"订阅失败: {str(e)}"
                }))
            except:
                pass
    
    async def _handle_subscribe_ticker(self, websocket: WebSocket, message: dict):
        """处理Ticker订阅请求（改进版：订阅管理）"""
        try:
            msg_data = message.get("data", {})
            exchange = msg_data.get("exchange")
            symbol = msg_data.get("symbol")
            market_type = msg_data.get("market_type", "spot")
            
            if not exchange or not symbol:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "缺少 exchange 或 symbol 参数"
                }))
                return
            
            # 生成订阅 key
            sub_key = f"ticker_{exchange}_{symbol}_{market_type}"
            
            market_type_label = "合约" if market_type.lower() in ['futures', 'future', 'swap'] else "现货"
            logger.info(f"📈 收到Ticker订阅请求: {sub_key} ({market_type_label})")
            
            # ✅ 记录订阅关系
            if sub_key not in self.subscriptions:
                self.subscriptions[sub_key] = set()
            self.subscriptions[sub_key].add(websocket)
            logger.info(f"✅ 已添加Ticker订阅关系: {sub_key}, 当前订阅者数量: {len(self.subscriptions[sub_key])}")
            
            # 如果任务不存在，创建新任务
            if sub_key not in self.ws_tasks:
                # 创建监听任务
                task = asyncio.create_task(
                    self.watch_ticker_task(exchange, symbol, market_type)
                )
                self.ws_tasks[sub_key] = task
                logger.info(f"✅ 已创建Ticker订阅任务: {sub_key}")
            else:
                logger.info(f"♻️ 复用现有Ticker订阅任务: {sub_key}")
            
            # 发送订阅确认
            await websocket.send_text(json.dumps({
                "type": "ticker_subscription_confirmed",
                "data": {
                    "exchange": exchange,
                    "symbol": symbol,
                    "market_type": market_type
                }
            }))
        except Exception as e:
            logger.error(f"❌ 处理Ticker订阅请求失败: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Ticker订阅失败: {str(e)}"
                }))
            except:
                pass
    
    async def _handle_subscribe_depth(self, websocket: WebSocket, message: dict):
        """处理Depth订阅请求"""
        try:
            msg_data = message.get("data", {})
            exchange = msg_data.get("exchange")
            symbol = msg_data.get("symbol")
            market_type = msg_data.get("market_type", "spot")
            
            # 根据交易所和市场类型设置合适的 limit 默认值
            default_limit = self._get_default_depth_limit(exchange, market_type)
            limit = msg_data.get("limit", default_limit)
            
            if not exchange or not symbol:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "缺少 exchange 或 symbol 参数"
                }))
                return
            
            # 生成订阅 key
            sub_key = f"depth_{exchange}_{symbol}_{market_type}"
            
            market_type_label = "合约" if market_type.lower() in ['futures', 'future', 'swap'] else "现货"
            logger.info(f"📊 收到Depth订阅请求: {sub_key} ({market_type_label})")
            
            # ✅ 记录订阅关系
            if sub_key not in self.subscriptions:
                self.subscriptions[sub_key] = set()
            self.subscriptions[sub_key].add(websocket)
            logger.info(f"✅ 已添加Depth订阅关系: {sub_key}, 当前订阅者数量: {len(self.subscriptions[sub_key])}")
            
            # 如果任务不存在，创建新任务
            if sub_key not in self.ws_tasks:
                # 创建监听任务
                task = asyncio.create_task(
                    self.watch_depth_task(exchange, symbol, market_type, limit)
                )
                self.ws_tasks[sub_key] = task
                logger.info(f"✅ 已创建Depth订阅任务: {sub_key}")
            else:
                logger.info(f"♻️ 复用现有Depth订阅任务: {sub_key}")
            
            # 发送订阅确认
            await websocket.send_text(json.dumps({
                "type": "depth_subscription_confirmed",
                "data": {
                    "exchange": exchange,
                    "symbol": symbol,
                    "market_type": market_type,
                    "limit": limit
                }
            }))
        except Exception as e:
            logger.error(f"❌ 处理Depth订阅请求失败: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Depth订阅失败: {str(e)}"
                }))
            except:
                pass
    
    async def _handle_unsubscribe(self, websocket: WebSocket, message: dict):
        """处理取消订阅请求（改进版：订阅管理）"""
        msg_data = message.get("data", {})
        exchange = msg_data.get("exchange_a")
        symbol = msg_data.get("symbol")
        interval = msg_data.get("interval", "1m")
        market_type = msg_data.get("market_type", "spot")
        
        sub_key = f"{exchange}_{symbol}_{interval}_{market_type}"
        
        logger.info(f"📨 收到取消订阅请求: {sub_key}")
        
        # ✅ 移除订阅关系
        if sub_key in self.subscriptions:
            self.subscriptions[sub_key].discard(websocket)
            logger.info(f"✅ 已移除订阅关系: {sub_key}, 剩余订阅者数量: {len(self.subscriptions[sub_key])}")
            
            # ✅ 如果没有订阅者了，取消任务
            if len(self.subscriptions[sub_key]) == 0:
                # 取消任务
                if sub_key in self.ws_tasks:
                    self.ws_tasks[sub_key].cancel()
                    del self.ws_tasks[sub_key]
                    logger.info(f"❌ 无订阅者，已取消任务: {sub_key}")
                
                # 清理空的订阅列表
                del self.subscriptions[sub_key]
            else:
                logger.info(f"♻️ 保留任务（还有 {len(self.subscriptions[sub_key])} 个订阅者）: {sub_key}")
        
        # 发送取消订阅确认
        await websocket.send_text(json.dumps({
            "type": "unsubscription_confirmed",
            "data": {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "market_type": market_type
            }
        }))
    
    async def _handle_status(self, websocket: WebSocket):
        """处理状态查询请求"""
        await websocket.send_text(json.dumps({
            "type": "status_response",
            "data": {
                "connected_clients": len(self.ws_clients),
                "active_subscriptions": list(self.ws_tasks.keys()),
                "subscription_count": len(self.ws_tasks)
            }
        }))
    
    # ========================================================================
    # Backpack WebSocket 专用方法
    # ========================================================================
    
    async def _get_backpack_client(self, subscription_key: str, symbol: str, market_type: str) -> BackpackWebSocketClient:
        """
        获取或创建 Backpack WebSocket 客户端
        
        Args:
            subscription_key: 订阅键
            symbol: 交易对符号
            market_type: 市场类型 ('spot' 或 'futures')
            
        Returns:
            BackpackWebSocketClient 实例
        """
        if subscription_key not in self.backpack_clients:
            # 从 proxy_config 中提取 WebSocket 代理地址
            # 优先使用 ws 字段，如果没有则使用 http 作为备用
            proxy = None
            if self.proxy_config:
                ws_proxy = self.proxy_config.get('ws', '').strip()
                http_proxy = self.proxy_config.get('http', '').strip()
                # WebSocket 代理：优先使用 ws，如果没有则使用 http
                proxy = ws_proxy if ws_proxy else http_proxy
                if proxy:
                    proxy_source = "ws字段" if ws_proxy else "http字段(备用)"
                    logger.info(f"🌐 Backpack WebSocket 使用代理 ({proxy_source}): {proxy}")
            
            # 创建带有 symbol 和 market_type 的回调函数
            async def message_callback(stream_type: str, data: dict):
                await self._handle_backpack_message(stream_type, data, symbol=symbol, market_type=market_type)
            
            client = BackpackWebSocketClient(
                on_message=message_callback,
                proxy=proxy
            )
            await client.connect()
            self.backpack_clients[subscription_key] = client
            logger.info(f"✅ 创建 Backpack WebSocket 客户端: {subscription_key} (symbol={symbol}, market_type={market_type})")
        
        return self.backpack_clients[subscription_key]
    
    async def _handle_backpack_message(self, stream_type: str, data: dict, symbol: str = None, market_type: str = 'spot'):
        """
        处理 Backpack WebSocket 消息并精准推送
        
        Args:
            stream_type: 流类型 ('kline', 'ticker', 'depth')
            data: 消息数据（包含 symbol, interval 等）
            symbol: 交易对符号（备用）
            market_type: 市场类型 ('spot' 或 'futures'，备用）
        """
        logger.debug(f"🔍 _handle_backpack_message 被调用 - stream_type: {stream_type}, symbol: {symbol}, market_type: {market_type}, data keys: {list(data.keys())}")
        
        # 如果 data 中有 symbol，优先使用 data 中的
        actual_symbol = data.get('symbol') or symbol
        
        # 根据流类型构造消息和订阅 key
        if stream_type == 'kline':
            # ✅ 从 data 中提取 interval
            interval = data.get('interval', '1m')
            subscription_key = f"backpack_{actual_symbol}_{interval}_{market_type}"
            
            message = {
                'type': 'kline_update',
                'data': {
                    'exchange': 'backpack',
                    'symbol': actual_symbol,
                    'interval': interval,  # ✅ 添加 interval 字段
                    'market_type': market_type,
                    'kline': data.get('kline')
                }
            }
        elif stream_type == 'ticker':
            subscription_key = f"ticker_backpack_{actual_symbol}_{market_type}"
            
            message = {
                'type': 'ticker_update',
                'data': {
                    'exchange': 'backpack',
                    'symbol': actual_symbol,
                    'market_type': market_type,
                    'ticker': {
                        'price': data.get('price'),
                        'timestamp': data.get('timestamp'),
                        'volume': data.get('volume'),
                        'high': data.get('high'),
                        'low': data.get('low'),
                        'open': data.get('open'),
                    }
                }
            }
        elif stream_type == 'depth':
            subscription_key = f"depth_backpack_{actual_symbol}_{market_type}"
            
            message = {
                'type': 'depth_update',
                'data': {
                    'exchange': 'backpack',
                    'symbol': actual_symbol,
                    'market_type': market_type,
                    'depth': {
                        'bids': data.get('bids', []),
                        'asks': data.get('asks', []),
                        'timestamp': data.get('timestamp'),
                    }
                }
            }
        else:
            logger.warning(f"未知的 Backpack 流类型: {stream_type}")
            return
        
        # ✅ 精准推送：只发送给订阅了该数据的客户端
        if subscription_key in self.subscriptions:
            subscribers = self.subscriptions[subscription_key]
            logger.debug(f"🔍 精准推送给 {len(subscribers)} 个订阅者 - {subscription_key}")
            
            disconnected = set()
            for client in subscribers:
                try:
                    await client.send_text(json.dumps(message))
                    logger.debug(f"✅ 已发送消息给订阅者: {message['type']}")
                except Exception as e:
                    logger.error(f"❌ 发送消息失败: {e}")
                    disconnected.add(client)
            
            # 清理断开的客户端
            for client in disconnected:
                subscribers.discard(client)
                # 从所有订阅中移除
                for subs in self.subscriptions.values():
                    subs.discard(client)
        else:
            logger.warning(f"⚠️ 没有订阅者：{subscription_key}")
    
    async def _watch_backpack_klines(self, exchange_name: str, symbol: str, interval: str, market_type: str, subscription_key: str):
        """
        Backpack K线监听任务
        
        Args:
            exchange_name: 交易所名称 ('backpack')
            symbol: 交易对
            interval: K线周期
            market_type: 市场类型
            subscription_key: 订阅键
        """
        try:
            logger.info(f"📊 启动 Backpack K线订阅: {symbol} {interval} (market_type={market_type})")
            
            # 获取客户端
            client = await self._get_backpack_client(subscription_key, symbol, market_type)
            
            # 订阅 K线
            await client.subscribe_kline(symbol, interval, market_type)
            
            # 保持任务活跃（实际接收由客户端处理）
            while True:
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info(f"Backpack K线任务已取消: {subscription_key}")
            raise
        except Exception as e:
            logger.error(f"Backpack K线任务失败 {subscription_key}: {e}")
        finally:
            # 清理
            if subscription_key in self.ws_tasks:
                del self.ws_tasks[subscription_key]
            if subscription_key in self.backpack_clients:
                try:
                    await self.backpack_clients[subscription_key].disconnect()
                    del self.backpack_clients[subscription_key]
                except Exception as e:
                    logger.error(f"断开 Backpack 客户端失败: {e}")
    
    async def _watch_backpack_ticker(self, exchange_name: str, symbol: str, market_type: str, subscription_key: str):
        """
        Backpack Ticker监听任务
        
        Args:
            exchange_name: 交易所名称 ('backpack')
            symbol: 交易对
            market_type: 市场类型
            subscription_key: 订阅键
        """
        try:
            logger.info(f"📈 启动 Backpack Ticker订阅: {symbol} (market_type={market_type})")
            
            # 获取客户端
            client = await self._get_backpack_client(subscription_key, symbol, market_type)
            
            # 订阅 Ticker
            await client.subscribe_ticker(symbol, market_type)
            
            # 保持任务活跃
            while True:
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info(f"Backpack Ticker任务已取消: {subscription_key}")
            raise
        except Exception as e:
            logger.error(f"Backpack Ticker任务失败 {subscription_key}: {e}")
        finally:
            # 清理
            if subscription_key in self.ws_tasks:
                del self.ws_tasks[subscription_key]
            if subscription_key in self.backpack_clients:
                try:
                    await self.backpack_clients[subscription_key].disconnect()
                    del self.backpack_clients[subscription_key]
                except Exception as e:
                    logger.error(f"断开 Backpack 客户端失败: {e}")
    
    async def _watch_backpack_depth(self, exchange_name: str, symbol: str, market_type: str, subscription_key: str):
        """
        Backpack Depth监听任务
        
        Args:
            exchange_name: 交易所名称 ('backpack')
            symbol: 交易对
            market_type: 市场类型
            subscription_key: 订阅键
        """
        try:
            logger.info(f"📊 启动 Backpack Depth订阅: {symbol} (market_type={market_type})")
            
            # 获取客户端
            client = await self._get_backpack_client(subscription_key, symbol, market_type)
            
            # 订阅 Depth (使用200ms聚合以减少数据量)
            await client.subscribe_depth(symbol, aggregate='200ms', market_type=market_type)
            
            # 保持任务活跃
            while True:
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info(f"Backpack Depth任务已取消: {subscription_key}")
            raise
        except Exception as e:
            logger.error(f"Backpack Depth任务失败 {subscription_key}: {e}")
        finally:
            # 清理
            if subscription_key in self.ws_tasks:
                del self.ws_tasks[subscription_key]
            if subscription_key in self.backpack_clients:
                try:
                    await self.backpack_clients[subscription_key].disconnect()
                    del self.backpack_clients[subscription_key]
                except Exception as e:
                    logger.error(f"断开 Backpack 客户端失败: {e}")
    
    # ========================================================================
    # 清理方法
    # ========================================================================
    
    async def cleanup(self):
        """清理所有资源"""
        logger.info("🛑 WebSocket 管理器关闭中...")
        
        # 取消所有订阅任务
        for sub_key, task in list(self.ws_tasks.items()):
            logger.info(f"取消任务: {sub_key}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.ws_tasks.clear()
        
        # 关闭所有 Backpack WebSocket 客户端
        for client_key, client in list(self.backpack_clients.items()):
            logger.info(f"关闭 Backpack 客户端: {client_key}")
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"关闭 Backpack 客户端失败 {client_key}: {e}")
        self.backpack_clients.clear()
        
        # 关闭所有 ccxt.pro 交易所连接
        for exchange_name, exchange in list(self.pro_exchanges.items()):
            logger.info(f"关闭交易所连接: {exchange_name}")
            try:
                await exchange.close()
            except Exception as e:
                logger.error(f"关闭交易所失败 {exchange_name}: {e}")
        self.pro_exchanges.clear()
        
        logger.info("✅ WebSocket 资源清理完成")

