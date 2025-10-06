#!/usr/bin/env python3
"""
WebSocket 客户端测试脚本
用于测试后端WebSocket连接和数据流
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket():
    """测试WebSocket连接"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket连接成功")
            
            # 发送订阅消息
            subscribe_msg = {
                "type": "subscribe",
                "data": {
                    "channels": ["kline", "opportunity", "portfolio"]
                }
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info("已发送订阅消息")
            
            # 接收消息
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"收到消息: {data['type']}")
                    
                    if data['type'] == 'kline':
                        kline = data['data']
                        logger.info(f"K线数据: {kline['symbol']} - 价格: {kline['close']}")
                    
                    elif data['type'] == 'opportunity':
                        opp = data['data']
                        logger.info(f"套利机会: {opp['symbol']} - 价差: {opp['gapPercent']:.2f}%")
                    
                    elif data['type'] == 'portfolio':
                        portfolio = data['data']
                        logger.info(f"投资组合: 总余额: {portfolio['total_balance']}")
                    
                except json.JSONDecodeError:
                    logger.error(f"无法解析消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket连接已关闭")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")

if __name__ == "__main__":
    print("启动WebSocket测试客户端...")
    print("请确保后端服务正在运行 (python run.py)")
    print("按 Ctrl+C 退出")
    
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n测试已停止")

