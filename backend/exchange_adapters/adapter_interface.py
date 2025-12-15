"""
交易所适配器接口定义

设计原则：
1. 纯接口层 - 只定义抽象方法和工具方法
2. 不包含具体实现逻辑 - 业务逻辑下放到 DefaultAdapter
3. 提供通用工具方法 - 所有子类都可以使用
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdapterCapability:
    """适配器能力标记"""
    
    # 订单相关
    FETCH_SPOT_ORDERS = "fetch_spot_orders"
    FETCH_FUTURES_ORDERS = "fetch_futures_orders"
    FETCH_ORDER_BY_ID = "fetch_order_by_id"
    CREATE_ORDER = "create_order"
    CANCEL_ORDER = "cancel_order"
    
    # 持仓相关
    FETCH_SPOT_BALANCE = "fetch_spot_balance"
    FETCH_FUTURES_POSITIONS = "fetch_futures_positions"
    
    # 市场数据（通常 CCXT 已统一，不需要定制）
    FETCH_TICKER = "fetch_ticker"
    FETCH_OHLCV = "fetch_ohlcv"
    FETCH_ORDER_BOOK = "fetch_order_book"
    
    # 连通性测试
    TEST_CONNECTIVITY = "test_connectivity"
    
    # 价格查询（批量）
    FETCH_PRICES = "fetch_prices"
    
    # 交易对查询
    LOAD_MARKETS = "load_markets"


class NotImplementedByAdapter(Exception):
    """功能未由适配器实现（需要定制但尚未定制）"""
    pass


class AdapterInterface(ABC):
    """
    交易所适配器接口（抽象基类）
    
    职责：
    1. 定义所有适配器必须实现的抽象方法
    2. 提供通用工具方法（所有子类共享）
    3. 不包含任何业务逻辑
    
    继承关系：
    - DefaultAdapter 实现基于 CCXT 的通用逻辑
    - BackpackAdapter 等特殊交易所直接继承此接口，完全自定义
    """
    
    def __init__(self, market_type: str, config: dict):
        """
        初始化适配器
        
        Args:
            market_type: 市场类型 ('spot' 或 'futures')
            config: 交易所配置 {'apiKey': '...', 'secret': '...', 'proxies': {...}, ...}
        """
        # 验证 market_type
        if market_type not in ['spot', 'futures']:
            raise ValueError(f"❌ 无效的市场类型: {market_type}，必须是 'spot' 或 'futures'")
        
        self.market_type = market_type
        self.config = config
        self.exchange_id = self._get_exchange_id()
        
        # 子类声明支持的功能
        self._supported_capabilities: set = set()
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    def _get_exchange_id(self) -> str:
        """
        返回交易所 ID（如 'binance', 'gate'）
        
        子类必须实现此方法
        """
        pass
    
    @abstractmethod
    def _initialize_exchange(self):
        """
        初始化交易所实例
        
        子类必须实现此方法，负责：
        1. 创建交易所实例（CCXT 或自定义 HTTP 客户端）
        2. 配置 API 凭证
        3. 设置市场类型（spot/futures）
        """
        pass
    
    @abstractmethod
    def fetch_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 500,
        base_currencies: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        获取所有订单（包括开放的和已完成的）
        
        Args:
            symbol: 可选的交易对符号
            since: 起始时间戳（毫秒，None=获取完整历史）
            limit: 返回数量限制（默认500）
            base_currencies: 可选的币种列表（如 ['BTC', 'ETH']），用于优化查询
        
        Returns:
            标准化的订单列表
        """
        pass
    
    @abstractmethod
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取开放订单
        
        Args:
            symbol: 可选的交易对符号
        
        Returns:
            标准化的订单列表
        """
        pass
    
    @abstractmethod
    def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        获取持仓/余额
        
        Args:
            symbols: 可选的币种列表（如 ['BTC', 'ETH']）或交易对列表（如 ['BTC/USDT', 'ETH/USDT']）
                    用于过滤查询，减少 API 调用量。如果 adapter 不支持，则忽略此参数
        
        Returns:
            标准化的持仓/余额列表
        """
        pass
    
    def fetch_balance(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取账户余额（CCXT 格式）
        
        注意：此方法为可选实现，主要用于现货余额查询
        如果 adapter 未实现，position_service 会通过 fetch_positions 获取
        
        Args:
            symbols: 可选的币种列表（如 ['BTC', 'ETH']），用于过滤查询
                    如果 adapter 不支持，则忽略此参数
        
        Returns:
            {
                'info': {...},  # 原始数据
                'free': {'BTC': 1.2, 'USDT': 1000, ...},
                'used': {'BTC': 0.1, 'USDT': 100, ...},
                'total': {'BTC': 1.3, 'USDT': 1100, ...}
            }
        """
        # 默认实现：如果子类未实现，抛出异常提示
        raise NotImplementedError(
            f"❌ {self.exchange_id} 的 fetch_balance 方法未实现。"
            "如果 adapter 不支持此方法，position_service 会通过 fetch_positions 获取余额。"
        )
    
    @abstractmethod
    def fetch_klines(
        self,
        symbol: str,
        interval: str = '15m',
        limit: int = 100,
        since: Optional[int] = None
    ) -> List[List[Any]]:
        """
        获取 K线数据
        
        Args:
            symbol: 交易对（如 'BTC/USDT'）
            interval: 时间周期（如 '1m', '5m', '15m', '1h', '1d'）
            limit: 数据条数
            since: 起始时间戳（毫秒，可选）
        
        Returns:
            [[timestamp, open, high, low, close, volume], ...]
        """
        pass
    
    @abstractmethod
    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取交易对价格
        
        Args:
            symbols: 交易对列表（如 ['BTC/USDT', 'ETH/USDT']）
        
        Returns:
            {
                'BTC/USDT': {
                    'last': float,
                    'bid': float,
                    'ask': float,
                    'mark': float (可选，合约标记价格)
                },
                ...
            }
        """
        pass
    
    @abstractmethod
    def test_connectivity(self) -> Dict[str, Any]:
        """
        测试交易所连通性和鉴权有效性
        
        Returns:
            {
                'ok': bool,
                'serverTime': int (毫秒时间戳),
                'accountId': str (可选),
                'latencyMs': float (可选)
            }
        """
        pass
    
    @abstractmethod
    def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """
        加载市场数据（交易对信息）
        
        Args:
            reload: 是否强制重新加载（忽略缓存）
        
        Returns:
            {
                'BTC/USDT': {
                    'id': str,
                    'symbol': str,
                    'base': str,
                    'quote': str,
                    'active': bool,
                    'type': str,  # 'spot' 或 'swap'
                    'precision': {'price': int, 'amount': int},
                    'limits': {'amount': {...}, 'price': {...}, 'cost': {...}}
                },
                ...
            }
        """
        pass
    
    # ==================== 功能支持查询 ====================
    
    def supports_capability(self, capability: str) -> bool:
        """
        检查是否支持某个功能
        
        Args:
            capability: 功能名称（使用 AdapterCapability 常量）
        
        Returns:
            True if supported
        """
        return capability in self._supported_capabilities
    
    def get_supported_capabilities(self) -> List[str]:
        """返回所有支持的功能列表"""
        return list(self._supported_capabilities)
    
    # ==================== 工具方法（所有子类共享） ====================
    
    @staticmethod
    def _safe_float(value, default=0):
        """
        安全转换为 float，处理 None 值
        
        Args:
            value: 要转换的值
            default: 默认值（当 value 为 None 时返回）
        
        Returns:
            float 值
        """
        if value is None:
            return default
        return float(value)
    
    @staticmethod
    def _safe_int(value, default=0):
        """
        安全转换为 int，处理 None 值
        
        Args:
            value: 要转换的值
            default: 默认值（当 value 为 None 时返回）
        
        Returns:
            int 值
        """
        if value is None:
            return default
        return int(value)
    
    @staticmethod
    def _format_timestamp(timestamp: Optional[int]) -> str:
        """
        格式化时间戳为可读字符串
        
        Args:
            timestamp: 毫秒时间戳
        
        Returns:
            格式化的时间字符串（YYYY-MM-DD HH:MM:SS）
        """
        if not timestamp:
            return '-'
        try:
            return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return '-'
    
    def _get_default_market_type(self) -> str:
        """
        获取默认市场类型（辅助方法）
        
        Returns:
            当前市场类型 ('spot' 或 'futures')
        """
        return self.market_type
    
    # ==================== 可选实现的方法 ====================
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化币对符号（通用格式 → 交易所格式）
        
        Args:
            symbol: 通用格式的币对符号 (如 'BTC/USDT')
        
        Returns:
            交易所特定格式的币对符号
        
        说明：
            - 默认实现：现货不变，合约添加 :USDT 后缀
            - 子类可以重写此方法以实现特定交易所的符号格式
        
        Example:
            # 默认实现
            symbol = adapter.normalize_symbol('BTC/USDT')  # spot → 'BTC/USDT'
            symbol = adapter.normalize_symbol('BTC/USDT')  # futures → 'BTC/USDT:USDT'
        """
        if self.market_type == 'futures':
            # 合约：默认添加 :USDT 后缀（CCXT 标准格式）
            if ':' not in symbol:
                return f"{symbol}:USDT"
        return symbol
    
    def fetch_symbols(
        self,
        quote: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取交易对列表（带过滤）
        
        Args:
            quote: 报价币种过滤（如 'USDT'）
            limit: 返回数量限制
        
        Returns:
            [
                {
                    'symbol': str,
                    'base': str,
                    'quote': str,
                    'status': str,
                    'precision': {'price': int, 'amount': int},
                    'limits': {'minQty': float, 'minNotional': float}
                },
                ...
            ]
        
        说明：
            子类可以实现此方法，默认返回空列表
        """
        return []

