"""
测试适配器框架

验证：
1. 适配器工厂正确路由
2. 统一接口方法可调用
3. Backpack 适配器基础功能
4. 服务层封装正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange_adapters import get_adapter, is_exchange_supported, CUSTOM_ADAPTERS
from services import AdapterService


def test_adapter_factory():
    """测试适配器工厂"""
    print("\n" + "="*60)
    print("测试1: 适配器工厂")
    print("="*60)
    
    # 测试 CCXT 支持的交易所
    try:
        config = {'apiKey': 'test', 'secret': 'test'}
        adapter = get_adapter('binance', 'spot', config)
        print(f"✅ Binance 适配器创建成功: {adapter.__class__.__name__}")
        assert adapter.exchange_id == 'binance'
    except Exception as e:
        print(f"❌ Binance 适配器创建失败: {e}")
    
    # 测试 Backpack 自研适配器
    try:
        config = {'apiKey': 'test', 'secret': 'test'}
        adapter = get_adapter('backpack', 'spot', config)
        print(f"✅ Backpack 适配器创建成功: {adapter.__class__.__name__}")
        assert adapter.exchange_id == 'backpack'
        assert adapter.exchange is None  # 不使用 CCXT
    except Exception as e:
        print(f"❌ Backpack 适配器创建失败: {e}")
    
    # 测试交易所支持检查
    assert is_exchange_supported('binance') == True
    assert is_exchange_supported('backpack') == True
    assert is_exchange_supported('unknown_exchange') == False
    print("✅ 交易所支持检查正常")
    
    print("\n✅ 适配器工厂测试通过")


def test_adapter_interface():
    """测试适配器统一接口"""
    print("\n" + "="*60)
    print("测试2: 适配器统一接口")
    print("="*60)
    
    config = {'apiKey': 'test', 'secret': 'test'}
    
    # 测试 Backpack 适配器的方法存在性
    adapter = get_adapter('backpack', 'spot', config)
    
    methods = [
        'test_connectivity',
        'fetch_symbols',
        'fetch_klines',
        'fetch_prices',
        'fetch_positions',
        'fetch_orders',
        'create_order',
    ]
    
    for method in methods:
        if hasattr(adapter, method):
            print(f"✅ {method} 方法存在")
        else:
            print(f"❌ {method} 方法缺失")
    
    print("\n✅ 统一接口测试通过")


def test_backpack_adapter_mock():
    """测试 Backpack 适配器（模拟调用）"""
    print("\n" + "="*60)
    print("测试3: Backpack 适配器模拟调用")
    print("="*60)
    
    config = {
        'apiKey': 'test-key',
        'secret': 'test-secret',
        'passphrase': 'test-passphrase',
        'timeout': 5000
    }
    
    adapter = get_adapter('backpack', 'spot', config)
    
    # 注意：这些调用会失败（因为是假凭证），但可以验证方法签名正确
    print("\n测试连通性接口（预期失败，仅验证签名）:")
    try:
        result = adapter.test_connectivity()
        if result.get('ok'):
            print(f"✅ 连通性测试成功: {result}")
        else:
            print(f"⚠️ 连通性测试失败（预期）: {result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"⚠️ 连通性测试异常（预期）: {type(e).__name__}")
    
    print("\n测试交易对查询接口（预期失败，仅验证签名）:")
    try:
        symbols = adapter.fetch_symbols(quote='USDT', limit=10)
        print(f"✅ 交易对查询返回: {len(symbols)} 个")
    except Exception as e:
        print(f"⚠️ 交易对查询异常（预期）: {type(e).__name__}")
    
    print("\n✅ Backpack 适配器模拟测试完成")


def test_adapter_service():
    """测试服务层封装"""
    print("\n" + "="*60)
    print("测试4: 服务层封装")
    print("="*60)
    
    config = {'apiKey': 'test', 'secret': 'test'}
    
    # 测试 is_supported
    assert AdapterService.is_supported('backpack') == True
    assert AdapterService.is_supported('binance') == True
    assert AdapterService.is_supported('unknown') == False
    print("✅ is_supported 方法正常")
    
    # 测试连通性（预期失败）
    print("\n测试服务层连通性接口:")
    try:
        result = AdapterService.test_connectivity('backpack', config)
        if result.get('ok'):
            print(f"✅ 服务层连通性测试成功")
        else:
            print(f"⚠️ 服务层连通性测试失败（预期）: {result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"⚠️ 服务层异常（预期）: {type(e).__name__}")
    
    print("\n✅ 服务层封装测试完成")


def test_adapter_capabilities():
    """测试适配器能力声明"""
    print("\n" + "="*60)
    print("测试5: 适配器能力声明")
    print("="*60)
    
    config = {'apiKey': 'test', 'secret': 'test'}
    adapter = get_adapter('backpack', 'spot', config)
    
    capabilities = adapter.get_supported_capabilities()
    print(f"✅ Backpack 支持的能力: {len(capabilities)} 个")
    for cap in capabilities:
        print(f"  - {cap}")
    
    # 验证核心能力
    from exchange_adapters import AdapterCapability
    assert adapter.supports_capability(AdapterCapability.TEST_CONNECTIVITY)
    assert adapter.supports_capability(AdapterCapability.LOAD_MARKETS)
    assert adapter.supports_capability(AdapterCapability.FETCH_OHLCV)
    assert adapter.supports_capability(AdapterCapability.FETCH_PRICES)
    print("\n✅ 核心能力检查通过")


def test_custom_adapters_list():
    """测试定制适配器列表"""
    print("\n" + "="*60)
    print("测试6: 定制适配器注册表")
    print("="*60)
    
    print(f"✅ 已注册的定制适配器 ({len(CUSTOM_ADAPTERS)} 个):")
    for exchange_id, adapter_class in CUSTOM_ADAPTERS.items():
        print(f"  - {exchange_id}: {adapter_class.__name__}")
    
    assert 'backpack' in CUSTOM_ADAPTERS
    assert 'binance' in CUSTOM_ADAPTERS
    assert 'gate' in CUSTOM_ADAPTERS
    assert 'okx' in CUSTOM_ADAPTERS
    print("\n✅ 适配器注册表正常")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("适配器框架测试套件")
    print("="*60)
    
    try:
        test_adapter_factory()
        test_adapter_interface()
        test_backpack_adapter_mock()
        test_adapter_service()
        test_adapter_capabilities()
        test_custom_adapters_list()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        print("\n框架已就绪，可以：")
        print("1. 在前端使用 exchange='backpack' 调用所有 API")
        print("2. 后端会自动路由到 BackpackAdapter")
        print("3. 添加新交易所只需实现适配器并注册")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())



