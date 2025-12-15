"""
系统状态路由

负责系统基础接口：
- 根路径
- 健康检查
- 系统状态
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def root():
    """根路径"""
    return {"message": "Gap Trader Backend API", "status": "running"}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/api/status")
async def get_status():
    """获取系统状态（Adapter 架构）"""
    from app_config import data_generator, manager
    from exchange_adapters import CUSTOM_ADAPTERS, DEFAULT_SUPPORTED_EXCHANGES
    
    return {
        "is_generating": data_generator.is_running,
        "active_connections": len(manager.active_connections),
        "total_exchanges": len(CUSTOM_ADAPTERS) + len(DEFAULT_SUPPORTED_EXCHANGES),
        "custom_adapters": len(CUSTOM_ADAPTERS),
        "default_adapters": len(DEFAULT_SUPPORTED_EXCHANGES),
        "timestamp": datetime.now().isoformat()
    }

