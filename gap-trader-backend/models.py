from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class KlineData(BaseModel):
    symbol: str
    openTime: int
    closeTime: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quoteVolume: float
    trades: int
    takerBuyBaseVolume: float
    takerBuyQuoteVolume: float

class OpportunityData(BaseModel):
    symbol: str
    spotPrice: float
    futuresPrice: float
    gap: float
    gapPercent: float
    timestamp: int

class WebSocketMessage(BaseModel):
    type: str
    data: Optional[dict] = None
    message: Optional[str] = None

class StatusResponse(BaseModel):
    is_generating: bool
    active_connections: int
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str

class TradeSignal(BaseModel):
    symbol: str
    action: str  # "buy" or "sell"
    price: float
    quantity: float
    timestamp: int
    reason: str

class Portfolio(BaseModel):
    total_balance: float
    available_balance: float
    positions: List[dict]
    pnl: float
    timestamp: int


# ===== 数据模型 =====

class ExchangeConfig(BaseModel):
    """交易所配置"""
    exchange: str
    apiKey: str
    apiSecret: str


class Account(BaseModel):
    """账户"""
    name: str
    exchanges: List[ExchangeConfig]


class Config(BaseModel):
    """完整配置"""
    accounts: List[Account]
