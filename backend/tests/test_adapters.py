"""
交易所适配器测试（新架构）

测试各个适配器是否正确实现了接口
"""

import pytest
from exchange_adapters import get_adapter, CUSTOM_ADAPTERS
from exchange_adapters.adapter_interface import AdapterInterface


def test_adapter_registry():
    """测试适配器注册表"""
    assert 'binance' in CUSTOM_ADAPTERS
    assert 'gate' in CUSTOM_ADAPTERS
    assert 'okx' in CUSTOM_ADAPTERS


def test_get_adapter_binance_spot():
    """测试获取 Binance 现货适配器"""
    config = {'apiKey': 'test', 'secret': 'test'}
    adapter = get_adapter('binance', 'spot', config)
    
    assert isinstance(adapter, AdapterInterface)
    assert adapter.exchange_id == 'binance'
    assert adapter.market_type == 'spot'


def test_get_adapter_binance_futures():
    """测试获取 Binance 合约适配器"""
    config = {'apiKey': 'test', 'secret': 'test'}
    adapter = get_adapter('binance', 'futures', config)
    
    assert isinstance(adapter, AdapterInterface)
    assert adapter.exchange_id == 'binance'
    assert adapter.market_type == 'futures'


def test_get_adapter_gate():
    """测试获取 Gate.io 适配器"""
    config = {'apiKey': 'test', 'secret': 'test'}
    adapter = get_adapter('gate', 'spot', config)
    
    assert isinstance(adapter, AdapterInterface)
    assert adapter.exchange_id == 'gate'


def test_get_adapter_unsupported():
    """测试不支持的交易所"""
    with pytest.raises(ValueError, match="不支持的交易所"):
        get_adapter('unknown_exchange', 'spot', {})


def test_adapter_interface():
    """测试适配器接口完整性"""
    config = {'apiKey': 'test', 'secret': 'test'}
    adapter = get_adapter('binance', 'spot', config)
    
    # 检查必需的方法
    assert hasattr(adapter, 'fetch_orders')
    assert hasattr(adapter, 'fetch_open_orders')
    assert hasattr(adapter, 'fetch_positions')
    assert hasattr(adapter, 'fetch_klines')
    assert hasattr(adapter, 'fetch_prices')
    assert hasattr(adapter, 'test_connectivity')


def test_binance_adapter_specifics():
    """测试 Binance 适配器特性（单实例架构）"""
    config = {'apiKey': 'test', 'secret': 'test'}
    
    # 测试现货实例
    spot_adapter = get_adapter('binance', 'spot', config)
    assert spot_adapter.exchange is not None
    assert spot_adapter.exchange.options['defaultType'] == 'spot'
    assert spot_adapter.exchange.options['warnOnFetchOpenOrdersWithoutSymbol'] is False
    
    # 测试合约实例
    futures_adapter = get_adapter('binance', 'futures', config)
    assert futures_adapter.exchange is not None
    assert futures_adapter.exchange.options['defaultType'] == 'future'
    assert futures_adapter.exchange.options['warnOnFetchOpenOrdersWithoutSymbol'] is False


def test_gate_adapter_specifics():
    """测试 Gate.io 适配器特性（单实例架构）"""
    config = {'apiKey': 'test', 'secret': 'test'}
    
    # 测试现货实例
    spot_adapter = get_adapter('gate', 'spot', config)
    assert spot_adapter.exchange is not None
    assert spot_adapter.exchange.options['defaultType'] == 'spot'
    
    # 测试合约实例
    futures_adapter = get_adapter('gate', 'futures', config)
    assert futures_adapter.exchange is not None
    assert futures_adapter.exchange.options['defaultType'] == 'swap'


# ==================== 集成测试（需要真实 API Key）====================

@pytest.mark.skip(reason="需要真实 API Key")
def test_binance_fetch_orders_integration():
    """Binance 订单获取集成测试（新架构）"""
    import os
    
    config = {
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_SECRET'),
    }
    
    # 测试现货订单
    spot_adapter = get_adapter('binance', 'spot', config)
    spot_orders = spot_adapter.fetch_orders()
    assert isinstance(spot_orders, list)
    
    # 测试合约订单
    futures_adapter = get_adapter('binance', 'futures', config)
    futures_orders = futures_adapter.fetch_orders()
    assert isinstance(futures_orders, list)


@pytest.mark.skip(reason="需要真实 API Key")
def test_gate_fetch_orders_integration():
    """Gate.io 订单获取集成测试（新架构）"""
    import os
    
    config = {
        'apiKey': os.getenv('GATE_API_KEY'),
        'secret': os.getenv('GATE_SECRET'),
    }
    
    # 测试获取订单
    adapter = get_adapter('gate', 'spot', config)
    orders = adapter.fetch_orders()
    assert isinstance(orders, list)
    
    # 验证数据格式
    if orders:
        order = orders[0]
        assert 'orderId' in order
        assert 'exchange' in order
        assert order['exchange'] == 'gate'
        assert 'marketType' in order
        assert order['marketType'] in ('spot', 'futures')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

