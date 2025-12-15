"""
OKX 交易所适配器

特殊差异：
1. 需要 password 参数（API passphrase）
2. 如果没有提供 password，会抛出明确的错误提示
"""

import ccxt
from .default_adapter import DefaultAdapter
from .adapter_interface import AdapterCapability


class OKXAdapter(DefaultAdapter):
    """
    OKX 交易所适配器
    
    继承自 DefaultAdapter，只重写有差异的部分
    """
    
    def __init__(self, market_type: str, config: dict):
        """初始化 OKX 适配器"""
        super().__init__(exchange_id='okx', market_type=market_type, config=config)
    
    def _get_exchange_id(self) -> str:
        return 'okx'
    
    def _initialize_exchange(self):
        """
        初始化 OKX 实例
        
        OKX 特殊要求：
        - 必须提供 password（API passphrase）
        - 如果没有提供，抛出明确的错误
        """
        # 检查是否提供了 password
        if 'password' not in self.config or not self.config.get('password'):
            raise ValueError(
                "❌ OKX 交易所需要 API Passphrase\n"
                "请在前端配置中提供 password 字段（OKX 的 API Passphrase）"
            )
        
        # 基础配置
        exchange_config = {
            'apiKey': self.config.get('apiKey', ''),
            'secret': self.config.get('secret', ''),
            'password': self.config.get('password'),  # OKX 必需
            'enableRateLimit': True,
            'timeout': self.config.get('timeout', 30000),
        }
        
        # 代理配置
        if 'proxies' in self.config:
            exchange_config['proxies'] = self.config['proxies']
        
        # 根据 market_type 设置 defaultType
        if self.market_type == 'futures':
            exchange_config['options'] = {'defaultType': 'swap'}
        else:  # spot
            exchange_config['options'] = {'defaultType': 'spot'}
        
        # 创建实例
        self.exchange = ccxt.okx(exchange_config)
        
        # 声明支持的功能
        self._supported_capabilities = {
            AdapterCapability.FETCH_SPOT_ORDERS,
            AdapterCapability.FETCH_FUTURES_ORDERS,
            AdapterCapability.FETCH_SPOT_BALANCE,
            AdapterCapability.FETCH_FUTURES_POSITIONS,
        }

