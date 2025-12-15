"""
全局配置和初始化模块

负责：
1. 代理配置
2. 交易所实例管理
3. 服务层实例化
4. 全局变量管理
"""

import logging
import ccxt
import os
from typing import Optional

from util.utils import ConnectionManager, DataGenerator, create_exchange_with_proxy
from util.market_cache import MarketCache
from util.websocket_util import WebSocketManager

from services import (
    ExchangeService,
    MarketService,
    PositionService,
    OrderService,
    PriceService
)

from trump.sentiment_analyzer import TrumpSentimentAnalyzer
from trump.post_archiver import TrumpPostArchiver

# 从 Adapter 模块导入支持的交易所列表（统一配置源）
from exchange_adapters import CUSTOM_ADAPTERS, DEFAULT_SUPPORTED_EXCHANGES

logger = logging.getLogger(__name__)

# ============================================================================
# 全局配置
# ============================================================================

def _get_proxy_config():
    """
    获取代理配置，如果未设置则返回空字典
    
    Returns:
        dict: 代理配置 {'http': url, 'https': url}，如果未设置则为空字典
    """
    proxy_url = os.getenv('PROXY_URL', '').strip()
    
    if proxy_url:
        logger.info(f"🌐 使用代理: {proxy_url}")
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    else:
        logger.info("ℹ️ 未配置代理，使用直连")
        return {}

# 代理配置
PROXY_CONFIG = _get_proxy_config()

# 优先加载的交易所列表（从 Adapter 配置自动生成）
# 定制适配器的交易所优先级更高，因为它们经过特殊优化
PRIORITY_EXCHANGES = list(CUSTOM_ADAPTERS.keys()) + DEFAULT_SUPPORTED_EXCHANGES

# ============================================================================
# 全局变量
# ============================================================================

# WebSocket 管理器
manager = ConnectionManager()
data_generator = DataGenerator(manager)

# 市场数据缓存管理器（Adapter 内部会使用）
market_cache = MarketCache(
    cache_dir="data/market_cache",
    cache_ttl=21600
)

# WebSocket 管理器
ws_manager = WebSocketManager(PROXY_CONFIG, market_cache)

# 服务层实例
exchange_service = None
market_service = None
position_service = None
order_service = None
price_service = None
symbol_mapper = None

# 特朗普情绪分析服务
sentiment_analyzer: Optional[TrumpSentimentAnalyzer] = None
post_archiver: Optional[TrumpPostArchiver] = None

# ============================================================================
# 初始化函数
# ============================================================================
# 
# 注意：不再需要 init_exchanges()
# 所有交易所通过 Adapter 按需创建，自动处理：
# - 市场数据缓存
# - 代理配置
# - 实例管理


def init_services():
    """初始化所有服务层实例（Adapter 架构）"""
    global exchange_service, market_service, position_service, order_service, price_service, symbol_mapper
    
    # 交易所服务（不再需要 EXCHANGES 字典）
    exchange_service = ExchangeService(PROXY_CONFIG)
    
    # 市场数据服务（保留部分遗留参数用于过渡）
    # TODO: 后续可以完全移除 exchanges, markets_loaded 等参数
    market_service = MarketService(
        {},  # exchanges - 空字典，不再使用
        market_cache,
        set(),  # markets_loaded - 空集合，Adapter 自己管理
        set(),  # markets_loading - 空集合
        PRIORITY_EXCHANGES,
        PROXY_CONFIG
    )
    
    # 持仓服务（Adapter 架构）
    position_service = PositionService(
        proxy_config=PROXY_CONFIG
    )
    
    # 订单服务（Adapter 架构）
    order_service = OrderService(
        proxy_config=PROXY_CONFIG
    )
    
    # 价格服务（Adapter 架构）
    price_service = PriceService(PROXY_CONFIG)
    
    logger.info("✅ 所有服务已初始化（Adapter 架构）")


def init_all():
    """初始化所有全局实例"""
    init_services()


# 启动时自动初始化
init_all()

