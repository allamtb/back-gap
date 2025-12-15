"""
路由模块

集中导出所有路由，方便 main.py 导入
"""

from .system_routes import router as system_router
from .exchange_routes import router as exchange_router
from .market_routes import router as market_router
from .order_routes import router as order_router
from .trump_routes import router as trump_router
from .trading_link_routes import router as trading_link_router
from .websocket_routes import router as websocket_router
from .cookie_routes import router as cookie_router

__all__ = [
    'system_router',
    'exchange_router',
    'market_router',
    'order_router',
    'trump_router',
    'trading_link_router',
    'websocket_router',
    'cookie_router',
]

