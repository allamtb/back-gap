from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLAlchemy Base
Base = declarative_base()

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


# ===== 订单相关模型 =====

class OrderRequest(BaseModel):
    """订单查询请求"""
    exchanges: Optional[List[str]] = None  # 交易所列表（从localStorage配置获取）
    symbol: Optional[str] = None  # 交易对过滤
    status: Optional[str] = None  # 订单状态过滤
    order_type: Optional[str] = None  # 订单类型（spot/futures）
    side: Optional[str] = None  # 买卖方向
    start_time: Optional[int] = None  # 开始时间戳
    end_time: Optional[int] = None  # 结束时间戳
    limit: int = 100  # 返回数量限制


class OrderResponse(BaseModel):
    """订单响应数据"""
    orderId: str
    exchange: str
    order_type: str  # spot/futures
    symbol: str
    side: str  # buy/sell
    price: float
    amount: float
    filled: float
    total: float
    fee: float
    status: str
    orderTime: str
    fillTime: Optional[str] = None


# ===== 交易网站链接管理模型 =====

class TradingWebsiteLink(BaseModel):
    """交易网站链接"""
    id: str  # 唯一标识符
    name: str  # 链接名称
    url: str  # 链接地址
    description: Optional[str] = None  # 描述（可选）
    category: Optional[str] = None  # 分类（可选）
    createdAt: Optional[str] = None  # 创建时间
    updatedAt: Optional[str] = None  # 更新时间


class TradingWebsiteLinkCreate(BaseModel):
    """创建交易网站链接的请求"""
    name: str
    url: str
    description: Optional[str] = None
    category: Optional[str] = None


class TradingWebsiteLinkUpdate(BaseModel):
    """更新交易网站链接的请求"""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


# ===== Cookie 数据模型 =====

class BaiduCookieData(Base):
    """百度 Cookie 数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "baidu_cookies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    afd_ip = Column(String(255), unique=True, index=True, nullable=False, comment="AFD_IP Cookie值（唯一键）")
    baidulocnew = Column(String(255), nullable=True, comment="BAIDULOCNEW Cookie值")
    url = Column(String(1024), nullable=True, comment="请求URL")
    timestamp = Column(String(50), nullable=True, comment="时间戳")
    headers = Column(String, nullable=True, comment="请求头（JSON格式）")
    # 代理 IP 信息
    proxy_ip = Column(String(50), nullable=True, comment="代理IP地址")
    proxy_port = Column(Integer, nullable=True, comment="代理端口")
    proxy_city = Column(String(255), nullable=True, comment="代理IP城市")
    proxy_addr = Column(String(255), nullable=True, comment="代理IP经纬度")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class BaiduCookieRequest(BaseModel):
    """百度 Cookie 请求模型（Pydantic，用于接收 API 请求）"""
    afd_ip: Optional[str] = None
    baidulocnew: Optional[str] = None
    url: str
    timestamp: str
    headers: Optional[dict] = None
    # 代理 IP 信息
    proxy_ip: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_city: Optional[str] = None
    proxy_addr: Optional[str] = None


class BaiduCookieResponse(BaseModel):
    """百度 Cookie 响应模型（Pydantic，用于 API 响应）"""
    id: int
    afd_ip: Optional[str]
    baidulocnew: Optional[str]
    url: str
    timestamp: str
    headers: Optional[dict] = None
    # 代理 IP 信息
    proxy_ip: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_city: Optional[str] = None
    proxy_addr: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 语法（替代 orm_mode）