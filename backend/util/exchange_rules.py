"""
交易所币种规则配置工具
与前端 src/utils/exchangeRules.js 保持一致

定义不同交易所对于不同市场类型的交易对规则
"""

# 默认规则配置（与前端 DEFAULT_EXCHANGE_RULES 保持一致）
DEFAULT_EXCHANGE_RULES = {
    'backpack': {
        'spot': {
            'quote': 'USDC',      # 计价货币
            'separator': '/',     # 分隔符
            'suffix': '',         # 后缀
        },
        'future': {
            'quote': 'USDC',
            'separator': '/',
            'suffix': '',
        },
    },
    'binance': {
        'spot': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
        'future': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
    },
    'okx': {
        'spot': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
        'future': {
            'quote': 'USD',
            'separator': '/',
            'suffix': '',
        },
    },
    'bybit': {
        'spot': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
        'future': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
    },
    'gateio': {
        'spot': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
        'future': {
            'quote': 'USDT',
            'separator': '/',
            'suffix': '',
        },
    },
    'kraken': {
        'spot': {
            'quote': 'USD',
            'separator': '/',
            'suffix': '',
        },
        'future': {
            'quote': 'USD',
            'separator': '/',
            'suffix': '',
        },
    },
}


def get_exchange_rule(exchange: str, market_type: str = 'spot') -> dict:
    """
    获取指定交易所和市场类型的规则
    
    Args:
        exchange: 交易所 ID（如 'binance', 'backpack'）
        market_type: 市场类型（'spot' 或 'futures'/'future'）
    
    Returns:
        规则字典，包含 'quote', 'separator', 'suffix'
        如果未找到，返回默认规则 {'quote': 'USDT', 'separator': '/', 'suffix': ''}
    """
    exchange_id = exchange.lower()
    market_type_key = market_type.lower()
    
    # 统一 'futures' 和 'future' 为 'future'
    if market_type_key == 'futures':
        market_type_key = 'future'
    
    # 获取规则
    rule = DEFAULT_EXCHANGE_RULES.get(exchange_id, {}).get(market_type_key)
    
    if not rule:
        # 返回默认规则
        return {
            'quote': 'USDT',
            'separator': '/',
            'suffix': ''
        }
    
    return rule


def generate_symbol(base_currency: str, exchange: str, market_type: str = 'spot') -> str:
    """
    根据币种代码、交易所和市场类型生成完整交易对
    
    Args:
        base_currency: 币种代码（如 'BTC', 'PEOPLE'）
        exchange: 交易所 ID（如 'backpack', 'binance'）
        market_type: 市场类型（'spot' 或 'futures'/'future'）
    
    Returns:
        完整交易对（如 'BTC/USDC', 'PEOPLE/USDT'）
    
    Example:
        generate_symbol('BTC', 'backpack', 'spot')  # => 'BTC/USDC'
        generate_symbol('ETH', 'binance', 'spot')   # => 'ETH/USDT'
        generate_symbol('SOL', 'okx', 'future')     # => 'SOL/USD'
        generate_symbol('PEOPLE', 'binance', 'futures')  # => 'PEOPLE/USDT'
    """
    rule = get_exchange_rule(exchange, market_type)
    base_upper = base_currency.upper().strip()
    
    quote = rule['quote']
    separator = rule['separator']
    suffix = rule['suffix']
    
    # 拼接完整交易对: BTC + / + USDC + (空) = BTC/USDC
    return f"{base_upper}{separator}{quote}{suffix}"


def get_quote_currency(exchange: str, market_type: str = 'spot') -> str:
    """
    获取指定交易所和市场类型的报价货币
    
    Args:
        exchange: 交易所 ID
        market_type: 市场类型
    
    Returns:
        报价货币（如 'USDT', 'USDC', 'USD'）
    """
    rule = get_exchange_rule(exchange, market_type)
    return rule['quote']

