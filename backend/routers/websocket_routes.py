"""
WebSocket 路由

负责 WebSocket 连接接口：
- K线实时数据
"""

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点 - K 线实时数据"""
    from app_config import ws_manager
    await ws_manager.handle_websocket(websocket)

