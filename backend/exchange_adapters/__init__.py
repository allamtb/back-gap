"""
交易所适配器模块

设计原则：
1. ✅ 所有交易所都走适配器 - 统一入口
2. ✅ 默认使用 CCXT 实现 - 不需要每个交易所都写代码
3. ✅ 按需定制特殊逻辑 - 只在有差异时才写适配器
4. ✅ 明确告知哪些功能未适配 - 抛出 NotImplementedByAdapter 异常

架构分层：
- AdapterInterface: 纯接口定义（抽象方法 + 工具方法）
- DefaultAdapter: 基于 CCXT 的通用实现
- BinanceAdapter 等: 继承 DefaultAdapter，只重写差异部分
- BackpackAdapter: 继承 AdapterInterface，完全自定义（非 CCXT）
"""

from .adapter_interface import AdapterInterface, AdapterCapability, NotImplementedByAdapter
from .default_adapter import DefaultAdapter
from .binance_adapter import BinanceAdapter
from .gate_adapter import GateAdapter
from .okx_adapter import OKXAdapter
from .backpack_adapter import BackpackAdapter

# ==================== 适配器注册表 ====================

# 已定制适配器的交易所（有特殊差异）
CUSTOM_ADAPTERS = {
    'binance': BinanceAdapter,  # 特殊：fetch_open_orders 需要 symbol
    'gate': GateAdapter,         # 特殊：现货和合约需要分离实例
    'okx': OKXAdapter,           # 特殊：需要 password (API passphrase)
    'backpack': BackpackAdapter, # 特殊：CCXT 不支持，直接对接 REST API
}

# CCXT 支持的交易所（将使用默认适配器）
# 这些交易所可以直接使用 CCXT 的标准接口
DEFAULT_SUPPORTED_EXCHANGES = [
    'bybit',
    'huobi',
    'kucoin',
    'kraken',
    'bitfinex',
    'mexc',
    'coinbase',
    'bitstamp',
    'phemex',      # ← 看，加一个新交易所只需要这一行！
    # ... 可以继续添加 CCXT 支持的任何交易所
]


def get_adapter(exchange_id: str, market_type: str, config: dict) -> AdapterInterface:
    """
    获取交易所适配器实例（单实例架构）
    
    Args:
        exchange_id: 交易所 ID (如 'binance', 'gate', 'okx')
        market_type: 市场类型 ('spot' 或 'futures')
        config: 交易所配置 (apiKey, secret, proxies 等)
    
    Returns:
        交易所适配器实例（只初始化指定的市场类型）
    
    Raises:
        ValueError: 不支持的交易所或无效的市场类型
    
    工作流程：
        1. 验证 market_type 参数
        2. 检查是否有定制适配器 → 使用定制适配器
        3. 检查是否在支持列表中 → 使用默认适配器
        4. 检查 CCXT 是否支持 → 尝试使用默认适配器
        5. 都不支持 → 抛出异常
    """
    exchange_id = exchange_id.lower()
    
    # 验证 market_type
    if market_type not in ['spot', 'futures']:
        raise ValueError(f"❌ 无效的市场类型: {market_type}，必须是 'spot' 或 'futures'")
    
    # 1. 优先使用定制适配器
    if exchange_id in CUSTOM_ADAPTERS:
        adapter_class = CUSTOM_ADAPTERS[exchange_id]
        return adapter_class(market_type, config)
    
    # 2. 使用默认适配器（显式支持）
    if exchange_id in DEFAULT_SUPPORTED_EXCHANGES:
        return DefaultAdapter(exchange_id, market_type, config)
    
    # 3. 尝试用默认适配器（CCXT 支持但未明确声明）
    import ccxt
    if exchange_id in ccxt.exchanges:
        print(f"⚠️ {exchange_id} 未在支持列表中，尝试使用默认适配器...")
        try:
            return DefaultAdapter(exchange_id, market_type, config)
        except Exception as e:
            raise ValueError(
                f"❌ {exchange_id} 使用默认适配器失败: {e}\n"
                f"提示：此交易所可能需要定制适配器"
            )
    
    # 4. 完全不支持
    raise ValueError(
        f"❌ 不支持的交易所: {exchange_id}\n"
        f"已定制适配器: {list(CUSTOM_ADAPTERS.keys())}\n"
        f"默认支持: {DEFAULT_SUPPORTED_EXCHANGES}\n"
        f"提示：如需支持此交易所，请添加到 DEFAULT_SUPPORTED_EXCHANGES 或创建定制适配器"
    )


def list_supported_exchanges() -> dict:
    """
    列出所有支持的交易所
    
    Returns:
        {
            'custom': ['binance', 'gate'],  # 有定制适配器
            'default': ['okx', 'bybit', ...],  # 使用默认适配器
        }
    """
    return {
        'custom': list(CUSTOM_ADAPTERS.keys()),
        'default': DEFAULT_SUPPORTED_EXCHANGES,
    }


def is_exchange_supported(exchange_id: str) -> bool:
    """
    检查交易所是否被支持
    
    Args:
        exchange_id: 交易所 ID
    
    Returns:
        True if supported
    """
    exchange_id = exchange_id.lower()
    return (
        exchange_id in CUSTOM_ADAPTERS or 
        exchange_id in DEFAULT_SUPPORTED_EXCHANGES
    )


__all__ = [
    # 基础类
    'AdapterInterface',
    'DefaultAdapter',
    'AdapterCapability',
    'NotImplementedByAdapter',
    
    # 定制适配器
    'BinanceAdapter',
    'GateAdapter',
    'OKXAdapter',
    'BackpackAdapter',
    
    # 工具函数
    'get_adapter',
    'list_supported_exchanges',
    'is_exchange_supported',
    
    # 配置
    'CUSTOM_ADAPTERS',
    'DEFAULT_SUPPORTED_EXCHANGES',
]
