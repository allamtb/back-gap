import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import random
import time
import asyncio
from fastapi import WebSocket

logger = logging.getLogger(__name__)

def generate_mock_kline(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """生成模拟K线数据"""
    current_time = int(time.time() * 1000)
    base_price = random.uniform(40000, 50000)
    
    return {
        "symbol": symbol,
        "openTime": current_time,
        "closeTime": current_time + 60000,
        "open": round(base_price, 2),
        "high": round(base_price * random.uniform(1.01, 1.05), 2),
        "low": round(base_price * random.uniform(0.95, 0.99), 2),
        "close": round(base_price * random.uniform(0.98, 1.02), 2),
        "volume": round(random.uniform(100, 1000), 2),
        "quoteVolume": round(random.uniform(1000000, 10000000), 2),
        "trades": random.randint(100, 1000),
        "takerBuyBaseVolume": round(random.uniform(50, 500), 2),
        "takerBuyQuoteVolume": round(random.uniform(500000, 5000000), 2)
    }

def generate_mock_opportunity(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """生成模拟套利机会数据"""
    spot_price = random.uniform(40000, 50000)
    gap_percent = random.uniform(-5, 5)
    futures_price = spot_price * (1 + gap_percent / 100)
    gap = futures_price - spot_price
    
    return {
        "symbol": symbol,
        "spotPrice": round(spot_price, 2),
        "futuresPrice": round(futures_price, 2),
        "gap": round(gap, 2),
        "gapPercent": round(gap_percent, 2),
        "timestamp": int(time.time() * 1000)
    }

def generate_mock_portfolio() -> Dict[str, Any]:
    """生成模拟投资组合数据"""
    return {
        "total_balance": round(random.uniform(10000, 100000), 2),
        "available_balance": round(random.uniform(5000, 50000), 2),
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "size": round(random.uniform(0.1, 1.0), 4),
                "entryPrice": round(random.uniform(40000, 50000), 2),
                "markPrice": round(random.uniform(40000, 50000), 2),
                "pnl": round(random.uniform(-1000, 1000), 2),
                "pnlPercent": round(random.uniform(-10, 10), 2)
            }
        ],
        "pnl": round(random.uniform(-5000, 5000), 2),
        "timestamp": int(time.time() * 1000)
    }

def format_websocket_message(message_type: str, data: Dict[str, Any] = None, message: str = None) -> str:
    """格式化WebSocket消息"""
    payload = {"type": message_type}
    
    if data:
        payload["data"] = data
    if message:
        payload["message"] = message
    
    return json.dumps(payload)

def calculate_gap_percent(spot_price: float, futures_price: float) -> float:
    """计算价差百分比"""
    if spot_price == 0:
        return 0
    return ((futures_price - spot_price) / spot_price) * 100

def is_arbitrage_opportunity(gap_percent: float, min_gap: float = 0.5, max_gap: float = 10.0) -> bool:
    """判断是否为套利机会"""
    return abs(gap_percent) >= min_gap and abs(gap_percent) <= max_gap

def log_websocket_event(event_type: str, details: str = ""):
    """记录WebSocket事件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{timestamp}] WebSocket {event_type}: {details}")

def validate_symbol(symbol: str) -> bool:
    """验证交易对格式"""
    if not symbol or len(symbol) < 6:
        return False
    
    # 简单的格式验证：应该包含基础货币和计价货币
    return symbol.isupper() and len(symbol) >= 6


# ============================================================================
# 交易所相关辅助函数
# ============================================================================

def create_exchange_with_proxy(exchange_class, proxy_config=None):
    """创建带代理配置的交易所实例"""
    if proxy_config and (proxy_config.get('http') or proxy_config.get('https')):
        # 设置代理
        exchange = exchange_class({
            'proxies': proxy_config,
            'timeout': 30000,  # 30秒超时
            'rateLimit': 1000,  # 请求间隔1秒
        })
        logger.info(f"已为 {exchange_class.__name__} 设置代理: {proxy_config}")
    else:
        exchange = exchange_class({
            'timeout': 30000,
            'rateLimit': 1000,
        })
        logger.info(f"未设置代理，使用 {exchange_class.__name__} 默认配置")
    
    return exchange


# ============================================================================
# WebSocket 连接管理器
# ============================================================================

class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)


# ============================================================================
# 模拟数据生成器
# ============================================================================

class DataGenerator:
    """模拟数据生成器"""
    def __init__(self, manager: ConnectionManager):
        self.is_running = False
        self.task = None
        self.manager = manager

    async def start_generating(self):
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self._generate_data())
            logger.info("数据生成已启动")

    async def stop_generating(self):
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            logger.info("数据生成已停止")

    async def _generate_data(self):
        while self.is_running:
            try:
                # 生成模拟的K线数据
                kline_data = {
                    "type": "kline",
                    "data": {
                        "symbol": "BTCUSDT",
                        "openTime": int(time.time() * 1000),
                        "closeTime": int(time.time() * 1000) + 60000,
                        "open": round(random.uniform(40000, 50000), 2),
                        "high": round(random.uniform(45000, 55000), 2),
                        "low": round(random.uniform(35000, 45000), 2),
                        "close": round(random.uniform(40000, 50000), 2),
                        "volume": round(random.uniform(100, 1000), 2),
                        "quoteVolume": round(random.uniform(1000000, 10000000), 2),
                        "trades": random.randint(100, 1000),
                        "takerBuyBaseVolume": round(random.uniform(50, 500), 2),
                        "takerBuyQuoteVolume": round(random.uniform(500000, 5000000), 2)
                    }
                }
                
                # 生成模拟的套利机会数据
                opportunity_data = {
                    "type": "opportunity",
                    "data": {
                        "symbol": "BTCUSDT",
                        "spotPrice": round(random.uniform(40000, 50000), 2),
                        "futuresPrice": round(random.uniform(40000, 50000), 2),
                        "gap": round(random.uniform(-1000, 1000), 2),
                        "gapPercent": round(random.uniform(-5, 5), 2),
                        "timestamp": int(time.time() * 1000)
                    }
                }
                
                # 广播数据
                await self.manager.broadcast(json.dumps(kline_data))
                await self.manager.broadcast(json.dumps(opportunity_data))
                
                await asyncio.sleep(1)  # 每秒发送一次数据
                
            except Exception as e:
                logger.error(f"数据生成错误: {e}")
                await asyncio.sleep(1)

