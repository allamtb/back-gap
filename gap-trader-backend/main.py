from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
import ccxt
import os

# 导入辅助类和函数
from models import Config
from utils import ConnectionManager, DataGenerator, create_exchange_with_proxy
from config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gap Trader Backend", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化全局实例
manager = ConnectionManager()
data_generator = DataGenerator(manager)
# 代理配置
PROXY_CONFIG = {
    'http': os.getenv('PROXY_URL', ''),
    'https': os.getenv('PROXY_URL', ''),
}

# 从ccxt动态加载所有支持的交易所
# 优先加载交易量较大的主流交易所（按交易量排序）
PRIORITY_EXCHANGES = [
    'binance',        # 币安 - 全球最大
    'okx',            # 欧易
    'bybit',          # Bybit
    'gate',           # 芝麻开门（Gate.io）
    'coinbase',       # Coinbase
    'kraken',         # Kraken
    'kucoin',         # KuCoin
    'huobi',          # 火币（HTX）
    'bitfinex',       # Bitfinex
    'cryptocom',      # Crypto.com
]

EXCHANGES = {}

# 先加载优先交易所
for exchange_id in PRIORITY_EXCHANGES:
    if exchange_id in ccxt.exchanges:
        try:
            exchange_class = getattr(ccxt, exchange_id)
            EXCHANGES[exchange_id] = create_exchange_with_proxy(exchange_class, PROXY_CONFIG)
            logger.info(f"已加载优先交易所: {exchange_id}")
        except Exception as e:
            logger.warning(f"无法加载交易所 {exchange_id}: {str(e)}")

# 再加载其他交易所
for exchange_id in ccxt.exchanges:
    if exchange_id not in EXCHANGES:  # 避免重复加载
        try:
            exchange_class = getattr(ccxt, exchange_id)
            EXCHANGES[exchange_id] = create_exchange_with_proxy(exchange_class, PROXY_CONFIG)
        except Exception as e:
            logger.warning(f"无法加载交易所 {exchange_id}: {str(e)}")


# ============================================================================
# API 路由处理函数
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Gap Trader Backend API", "status": "running"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# 创建配置管理器
config_manager = ConfigManager("data/config.json")




@app.get("/api/config")
async def get_config():
    """
    获取当前配置
    
    Returns:
        配置对象，如果不存在返回 404
    """
    config = config_manager.load_config()
    
    if config is None:
        raise HTTPException(status_code=404, detail="配置文件不存在")
    
    return config


@app.post("/api/config")
async def save_config(config: Config):
    """
    保存配置（全量替换）
    
    Args:
        config: 完整的配置对象
        
    Returns:
        成功消息
    """
    try:
        # 转换为字典并保存
        config_dict = config.dict()
        config_manager.save_config(config_dict, create_backup=True)
        
        return {
            "success": True,
            "message": "配置保存成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "is_generating": data_generator.is_running,
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/exchanges")
async def get_exchanges():
    """
    获取所有支持的交易所列表（全局）
    
    返回所有 ccxt 支持的交易所名称列表
    """
    # 返回可用的交易所列表
    available_exchanges = list(EXCHANGES.keys())
    return available_exchanges


@app.get("/api/accounts")
async def get_accounts():
    """
    获取所有账户信息
    
    返回所有账户及其配置的交易所（不包含敏感信息）
    """
    try:
        accounts = config_manager.get_all_accounts()
        return {
            "success": True,
            "data": accounts
        }
    except Exception as e:
        logger.error(f"获取账户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")


@app.get("/api/accounts/{account_name}/exchanges")
async def get_account_exchanges(account_name: str):
    """
    获取指定账户下配置的交易所列表
    
    Args:
        account_name: 账户名称
        
    Returns:
        该账户下的交易所列表
    """
    try:
        exchanges = config_manager.get_account_exchanges(account_name)
        return {
            "success": True,
            "account": account_name,
            "exchanges": exchanges
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取账户交易所失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取账户交易所失败: {str(e)}")


@app.get("/api/klines")
async def get_klines(
    exchange: str = Query(..., description="交易所名称"),
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("15m", description="K线周期"),
    limit: int = Query(100, description="数据条数限制")
):
    """
    获取K线数据
    
    - **exchange**: 交易所名称 (binance, bybit, okx, huobi, kraken)
    - **symbol**: 交易对符号 (如: BTC/USDT)
    - **interval**: K线周期 (1m, 5m, 15m, 1h, 4h, 1d)
    - **limit**: 数据条数限制 (默认100)
    """
    try:
        # 验证参数
        exchange_name = exchange.lower()
        if exchange_name not in EXCHANGES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的交易所: {exchange_name}. 支持的交易所: {list(EXCHANGES.keys())}"
            )
        
        # 获取交易所实例
        exchange_instance = EXCHANGES[exchange_name]
        
        # 记录代理状态
        proxy_status = "已启用" if (PROXY_CONFIG.get('http') or PROXY_CONFIG.get('https')) else "未启用"
        logger.info(f"获取K线数据 - 交易所: {exchange_name}, 交易对: {symbol}, 周期: {interval}")
        
        # 获取K线数据
        ohlcv = exchange_instance.fetch_ohlcv(symbol, interval, limit=limit)
        
        # 转换数据格式
        klines = []
        for candle in ohlcv:
            klines.append({
                'time': candle[0],  # 时间戳（毫秒）
                'open': str(candle[1]),  # 开盘价
                'high': str(candle[2]),  # 最高价
                'low': str(candle[3]),   # 最低价
                'close': str(candle[4]), # 收盘价
                'volume': str(candle[5]) # 成交量
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取K线数据失败: {str(e)}"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "start":
                await data_generator.start_generating()
                await manager.send_personal_message(
                    json.dumps({"type": "status", "message": "数据生成已启动"}), 
                    websocket
                )
            elif message.get("type") == "stop":
                await data_generator.stop_generating()
                await manager.send_personal_message(
                    json.dumps({"type": "status", "message": "数据生成已停止"}), 
                    websocket
                )
            elif message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}), 
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)


# ============================================================================
# 应用启动
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
