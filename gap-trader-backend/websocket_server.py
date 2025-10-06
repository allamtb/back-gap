"""
WebSocket server for real-time K-line data streaming
使用 CCXT Pro 进行实时数据订阅
"""

import asyncio
import json
import logging
from typing import Dict, Set, List
import ccxt.pro as ccxtpro
from websockets import serve, WebSocketServerProtocol
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KlineWebSocketServer:
    def __init__(self):
        self.clients: Set[WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Dict] = {}
        self.exchanges: Dict[str, ccxtpro.Exchange] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 支持的交易所配置
        self.exchange_configs = {
            'binance': {
                'class': ccxtpro.binance,
                'options': {
                    'sandbox': False,  # 生产环境设为 False
                    'rateLimit': 1200,
                }
            },
            'bybit': {
                'class': ccxtpro.bybit,
                'options': {
                    'sandbox': False,
                    'rateLimit': 1200,
                }
            },
            'okx': {
                'class': ccxtpro.okx,
                'options': {
                    'sandbox': False,
                    'rateLimit': 100,
                }
            }
        }

    async def register_client(self, websocket: WebSocketServerProtocol):
        """注册新的WebSocket客户端"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """注销WebSocket客户端"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    def get_exchange(self, exchange_name: str) -> ccxtpro.Exchange:
        """获取或创建交易所实例"""
        if exchange_name not in self.exchanges:
            config = self.exchange_configs.get(exchange_name)
            if not config:
                raise ValueError(f"Unsupported exchange: {exchange_name}")
            
            self.exchanges[exchange_name] = config['class'](config['options'])
            logger.info(f"Created exchange instance: {exchange_name}")
        
        return self.exchanges[exchange_name]

    async def subscribe_kline_data(self, exchange_name: str, symbol: str, interval: str):
        """订阅K线数据"""
        try:
            exchange = self.get_exchange(exchange_name)
            subscription_key = f"{exchange_name}_{symbol}_{interval}"
            
            if subscription_key in self.running_tasks:
                logger.info(f"Already subscribed to {subscription_key}")
                return
            
            logger.info(f"Starting subscription: {subscription_key}")
            
            # 启动订阅任务
            task = asyncio.create_task(
                self._watch_klines(exchange, exchange_name, symbol, interval)
            )
            self.running_tasks[subscription_key] = task
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {exchange_name} {symbol} {interval}: {e}")

    async def _watch_klines(self, exchange: ccxtpro.Exchange, exchange_name: str, symbol: str, interval: str):
        """监听K线数据并广播给客户端"""
        try:
            while True:
                try:
                    # 使用 CCXT Pro 的 watch_ohlcv 方法
                    ohlcv = await exchange.watch_ohlcv(symbol, interval)
                    
                    if ohlcv and len(ohlcv) > 0:
                        # 获取最新的K线数据
                        latest_kline = ohlcv[-1]
                        
                        # 转换为标准格式
                        kline_data = {
                            'time': latest_kline[0],  # 时间戳
                            'open': float(latest_kline[1]),   # 开盘价
                            'high': float(latest_kline[2]),   # 最高价
                            'low': float(latest_kline[3]),    # 最低价
                            'close': float(latest_kline[4]),  # 收盘价
                            'volume': float(latest_kline[5])  # 成交量
                        }
                        
                        # 广播给所有客户端
                        await self.broadcast_kline_update(exchange_name, symbol, interval, kline_data)
                        
                except Exception as e:
                    logger.error(f"Error in kline watch loop for {exchange_name}: {e}")
                    await asyncio.sleep(5)  # 等待5秒后重试
                    
        except Exception as e:
            logger.error(f"Kline watch task failed for {exchange_name}: {e}")
        finally:
            # 清理任务
            subscription_key = f"{exchange_name}_{symbol}_{interval}"
            if subscription_key in self.running_tasks:
                del self.running_tasks[subscription_key]

    async def broadcast_kline_update(self, exchange: str, symbol: str, interval: str, kline_data: dict):
        """广播K线更新给所有客户端"""
        message = {
            'type': 'kline_update',
            'data': {
                'exchange': exchange,
                'symbol': symbol,
                'interval': interval,
                'kline': kline_data,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # 发送给所有连接的客户端
        if self.clients:
            disconnected_clients = set()
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to client: {e}")
                    disconnected_clients.add(client)
            
            # 清理断开的客户端
            for client in disconnected_clients:
                await self.unregister_client(client)

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                subscription_data = data.get('data', {})
                exchange_a = subscription_data.get('exchange_a')
                exchange_b = subscription_data.get('exchange_b')
                symbol = subscription_data.get('symbol')
                interval = subscription_data.get('interval')
                
                logger.info(f"Client subscription: {exchange_a} vs {exchange_b} - {symbol} ({interval})")
                
                # 订阅两个交易所的数据
                if exchange_a:
                    await self.subscribe_kline_data(exchange_a, symbol, interval)
                if exchange_b:
                    await self.subscribe_kline_data(exchange_b, symbol, interval)
                
                # 发送确认消息
                await websocket.send(json.dumps({
                    'type': 'subscription_confirmed',
                    'data': {
                        'exchange_a': exchange_a,
                        'exchange_b': exchange_b,
                        'symbol': symbol,
                        'interval': interval
                    }
                }))
                
            elif message_type == 'unsubscribe':
                # 处理取消订阅逻辑
                logger.info("Client unsubscribed")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理WebSocket客户端连接"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self.unregister_client(websocket)

    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up WebSocket server...")
        
        # 关闭所有交易所连接
        for exchange in self.exchanges.values():
            try:
                await exchange.close()
            except Exception as e:
                logger.error(f"Error closing exchange: {e}")
        
        # 取消所有运行中的任务
        for task in self.running_tasks.values():
            task.cancel()
        
        self.exchanges.clear()
        self.running_tasks.clear()

# 全局服务器实例
kline_server = KlineWebSocketServer()

async def main():
    """启动WebSocket服务器"""
    logger.info("Starting K-line WebSocket server on localhost:8000")
    
    try:
        async with serve(kline_server.handle_client, "localhost", 8000):
            logger.info("WebSocket server started successfully")
            await asyncio.Future()  # 保持服务器运行
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await kline_server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
