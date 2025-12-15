"""
Gate.io 交易所适配器（单实例架构）

特殊差异：
1. 合约符号格式特殊：BTC/USDT → BTC_USDT
2. fetch_open_orders() 不需要 symbol 参数（可一次获取全部）
"""

import ccxt
from .default_adapter import DefaultAdapter
from .adapter_interface import AdapterCapability


class GateAdapter(DefaultAdapter):
    """
    Gate.io 适配器（单实例架构）
    
    继承自 DefaultAdapter，只重写有差异的部分
    """
    
    def __init__(self, market_type: str, config: dict):
        """初始化 Gate.io 适配器"""
        super().__init__(exchange_id='gate', market_type=market_type, config=config)
    
    def _get_exchange_id(self) -> str:
        return 'gate'
    
    def _initialize_exchange(self):
        """
        初始化 Gate.io 交易所实例（单实例架构）
        
        根据 market_type 创建对应的实例
        """
        base_config = {
            'apiKey': self.config.get('apiKey', ''),
            'secret': self.config.get('secret', ''),
            'enableRateLimit': True,
            'timeout': self.config.get('timeout', 30000),
        }
        
        if 'proxies' in self.config:
            base_config['proxies'] = self.config['proxies']
        
        # 根据 market_type 设置 defaultType
        if self.market_type == 'futures':
            base_config['options'] = {'defaultType': 'swap'}
        else:  # spot
            base_config['options'] = {'defaultType': 'spot'}
        
        # 创建实例
        self.exchange = ccxt.gate(base_config)
        
        # 声明支持的功能
        self._supported_capabilities = {
            AdapterCapability.FETCH_SPOT_ORDERS,
            AdapterCapability.FETCH_FUTURES_ORDERS,
            AdapterCapability.FETCH_SPOT_BALANCE,
            AdapterCapability.FETCH_FUTURES_POSITIONS,
        }
    
    # ==================== Symbol 标准化（Gate.io 特殊处理） ====================
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Gate.io 特殊的符号格式
        
        Args:
            symbol: 通用格式 'BTC/USDT'
        
        Returns:
            Gate.io 格式：
            - 现货：'BTC/USDT' (不变)
            - 合约：'BTC_USDT' (替换 / 为 _)
        """
        if self.market_type == 'futures':
            # Gate.io 合约：BTC/USDT → BTC_USDT
            return symbol.replace('/', '_')
        return symbol
 