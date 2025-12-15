"""
Gap Trader Backend - 应用入口

职责：
1. 创建 FastAPI 应用
2. 配置中间件和 CORS
3. 注册所有路由
4. 处理应用生命周期事件
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# 导入路由模块
from routers import (
    system_router,
    exchange_router,
    market_router,
    order_router,
    trump_router,
    trading_link_router,
    websocket_router,
    cookie_router,
)

# 导入后台任务
from background_tasks import start_background_tasks

# 配置日志（降低到 INFO，静音 ccxt DEBUG 输出）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 降低 ccxt 及其子模块日志级别，避免输出 HTTP DEBUG
for name in [
    'ccxt',
    'ccxt.base.exchange',
    'ccxt.base.throttle',
    'ccxt.async_support',
    'ccxt.pro'
]:
    logging.getLogger(name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI 应用创建
# ============================================================================

app = FastAPI(title="Gap Trader Backend", version="1.0.0")


# ============================================================================
# 中间件配置
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# 添加安全响应头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 路由注册
# ============================================================================

# 注册所有路由
app.include_router(system_router)
app.include_router(exchange_router)
app.include_router(market_router)
app.include_router(order_router)
app.include_router(trump_router)
app.include_router(trading_link_router)
app.include_router(websocket_router)
app.include_router(cookie_router)

logger.info("✅ 所有路由已注册")


# ============================================================================
# 应用生命周期事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    from app_config import market_cache
    
    logger.info("🚀 应用启动中...")
    
    # 显示缓存统计信息
    cache_info = market_cache.get_cache_info()
    logger.info(f"📊 缓存状态: {cache_info['total_exchanges']} 个交易所已缓存 "
                f"({cache_info['total_size_mb']} MB)")
    
    for exchange_info in cache_info['cached_exchanges']:
        status = "✅ 有效" if exchange_info['valid'] else "⏰ 已过期"
        logger.info(f"  - {exchange_info['exchange']}: {exchange_info['count']} 个交易对, {status}")
    
    # 启动后台任务
    start_background_tasks()
    
    logger.info("✅ 应用启动完成，可以正常接收请求")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    from app_config import ws_manager
    
    logger.info("🛑 应用关闭中...")
    await ws_manager.cleanup()
    logger.info("✅ 资源清理完成")


# ============================================================================
# 应用启动
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
