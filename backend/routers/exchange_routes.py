"""
交易所管理路由

负责交易所相关接口：
- 获取交易所列表
- 测试交易所连接
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class TestExchangeRequest(BaseModel):
    """测试交易所连接的请求模型"""
    exchange: str
    apiKey: str
    apiSecret: str
    password: Optional[str] = None


@router.get("/api/exchanges")
async def get_exchanges():
    """获取所有支持的交易所列表"""
    from app_config import exchange_service
    return exchange_service.get_exchange_list()


@router.post("/api/test-exchange")
async def test_exchange_connection(request: TestExchangeRequest):
    """测试交易所连接并获取账户余额"""
    from app_config import exchange_service
    
    result = await exchange_service.test_exchange_connection(
        request.exchange,
        request.apiKey,
        request.apiSecret,
        request.password
    )
    return result

