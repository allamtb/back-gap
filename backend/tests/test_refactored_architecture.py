"""
测试重构后的统一 Adapter 架构

验证点：
1. MarketService.get_klines() 统一走 Adapter
2. PriceService 使用 Adapter
3. ExchangeService 不依赖 EXCHANGES 字典
4. 所有交易所（CCXT + 自定义）都能正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from services.market_service import MarketService
from services.price_service import PriceService
from services.exchange_service import ExchangeService


def test_market_service_klines():
    """测试 MarketService 统一使用 Adapter 获取 K线"""
    print("\n" + "=" * 60)
    print("测试 1: MarketService.get_klines() - 统一 Adapter 架构")
    print("=" * 60)
    
    # 初始化服务（使用空字典，不依赖 EXCHANGES）
    market_service = MarketService(
        exchanges={},  # 空字典
        market_cache=None,
        markets_loaded=set(),
        markets_loading=set(),
        priority_exchanges=[],
        proxy_config={'http': '', 'https': ''}
    )
    
    async def test():
        try:
            # 测试 CCXT 交易所（Binance）
            print("\n📊 测试 Binance (CCXT 交易所)...")
            result = await market_service.get_klines(
                exchange='binance',
                symbol='BTC/USDT',
                interval='1h',
                limit=5,
                market_type='spot'
            )
            assert result['success'] == True
            assert len(result['data']['klines']) > 0
            print(f"✅ Binance K线获取成功: {len(result['data']['klines'])} 条")
            
            # 测试自定义 Adapter 交易所（Backpack）
            print("\n📊 测试 Backpack (自定义 Adapter)...")
            result = await market_service.get_klines(
                exchange='backpack',
                symbol='BTC_USDC',
                interval='1h',
                limit=5,
                market_type='spot'
            )
            assert result['success'] == True
            assert len(result['data']['klines']) > 0
            print(f"✅ Backpack K线获取成功: {len(result['data']['klines'])} 条")
            
            print("\n✅ MarketService 统一 Adapter 架构测试通过！")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return asyncio.run(test())


def test_price_service():
    """测试 PriceService 使用 Adapter"""
    print("\n" + "=" * 60)
    print("测试 2: PriceService - Adapter 架构")
    print("=" * 60)
    
    # 初始化服务（不再需要 exchanges 字典）
    price_service = PriceService(
        proxy_config={'http': '', 'https': ''}
    )
    
    async def test():
        try:
            print("\n💰 测试多交易所价格查询...")
            result = await price_service.get_prices([
                {'exchange': 'binance', 'symbol': 'BTC/USDT'},
                {'exchange': 'okx', 'symbol': 'BTC/USDT'},
            ])
            
            assert result['success'] == True
            assert 'binance' in result['data']
            assert 'okx' in result['data']
            
            print(f"✅ Binance BTC/USDT: ${result['data']['binance']['BTC/USDT']}")
            print(f"✅ OKX BTC/USDT: ${result['data']['okx']['BTC/USDT']}")
            
            print("\n✅ PriceService Adapter 架构测试通过！")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return asyncio.run(test())


def test_exchange_service():
    """测试 ExchangeService 不依赖 EXCHANGES 字典"""
    print("\n" + "=" * 60)
    print("测试 3: ExchangeService - 不依赖 EXCHANGES 字典")
    print("=" * 60)
    
    # 初始化服务（不再需要 exchanges 字典）
    exchange_service = ExchangeService(
        proxy_config={'http': '', 'https': ''}
    )
    
    # 测试获取交易所列表
    print("\n📋 测试获取支持的交易所列表...")
    exchange_list = exchange_service.get_exchange_list()
    
    print(f"✅ 支持的交易所总数: {len(exchange_list)}")
    print(f"   定制 Adapter: {exchange_list[:5]}")
    print(f"   默认 Adapter: {exchange_list[5:10] if len(exchange_list) > 5 else '无'}")
    
    assert 'binance' in exchange_list
    assert 'backpack' in exchange_list
    assert 'okx' in exchange_list
    
    print("\n✅ ExchangeService 测试通过！")
    return True


def test_adapter_auto_market_loading():
    """测试 Adapter 自动加载市场数据"""
    print("\n" + "=" * 60)
    print("测试 4: Adapter 自动市场数据加载")
    print("=" * 60)
    
    from exchange_adapters import get_adapter
    
    try:
        # 创建 Adapter（应该自动加载市场数据）
        print("\n🔄 创建 Binance Adapter（应该自动加载市场数据）...")
        adapter = get_adapter('binance', 'spot', {
            'apiKey': '',
            'secret': '',
        })
        
        # 检查市场数据是否已加载
        assert adapter.exchange is not None
        assert adapter.exchange.markets is not None
        assert len(adapter.exchange.markets) > 0
        
        print(f"✅ 市场数据已自动加载: {len(adapter.exchange.markets)} 个交易对")
        
        # 测试交易对符号标准化
        normalized_symbol = adapter.normalize_symbol('BTC/USDT')
        print(f"✅ 符号标准化: BTC/USDT → {normalized_symbol}")
        
        print("\n✅ Adapter 自动市场数据加载测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 重构后架构验证测试")
    print("=" * 60)
    print("\n测试目标：")
    print("1. ✅ 所有服务统一走 Adapter")
    print("2. ✅ 移除对 EXCHANGES 字典的依赖")
    print("3. ✅ 移除 MARKETS_LOADED 全局状态")
    print("4. ✅ Adapter 自动处理市场数据加载")
    
    results = []
    
    # 运行测试
    results.append(("MarketService", test_market_service_klines()))
    results.append(("PriceService", test_price_service()))
    results.append(("ExchangeService", test_exchange_service()))
    results.append(("Adapter 市场数据", test_adapter_auto_market_loading()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} - {status}")
    
    print("\n" + "=" * 60)
    if passed == total:
        print(f"🎉 全部测试通过！({passed}/{total})")
        print("\n✅ 重构成功！架构已统一为 Adapter 模式。")
    else:
        print(f"⚠️ 部分测试失败 ({passed}/{total})")
    print("=" * 60)

