"""
测试适配器内置的市场数据缓存机制

验证点：
1. 适配器初始化时自动加载市场数据（使用缓存）
2. 缓存有效时使用缓存
3. 缓存无效时从 API 加载并缓存
4. reload_markets() 方法正常工作
"""

import pytest
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from exchange_adapters import get_adapter
from exchange_adapters.default_adapter import get_market_cache


class TestAdapterCache:
    """测试适配器缓存机制"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前后的设置和清理"""
        # 清理缓存
        cache = get_market_cache()
        cache.clear_cache('binance')
        cache.clear_cache('okx')
        
        yield
        
        # 清理缓存
        cache.clear_cache('binance')
        cache.clear_cache('okx')
    
    def test_adapter_loads_from_cache_on_init(self):
        """测试：适配器初始化时从缓存加载市场数据"""
        # 准备：预先创建缓存
        cache = get_market_cache()
        mock_markets = {
            'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
            'ETH/USDT': {'id': 'ETHUSDT', 'symbol': 'ETH/USDT'},
        }
        cache.save_to_cache('binance', mock_markets)
        
        # 执行：创建适配器
        with patch('ccxt.binance') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange.load_markets = Mock(return_value=mock_markets)
            mock_exchange_class.return_value = mock_exchange
            
            config = {'apiKey': 'test', 'secret': 'test'}
            adapter = get_adapter('binance', 'spot', config)
            
            # 验证：适配器的 exchange.markets 已设置
            assert adapter.exchange.markets == mock_markets
            
            # 验证：没有调用 load_markets()（因为使用了缓存）
            mock_exchange.load_markets.assert_not_called()
    
    def test_adapter_loads_from_api_when_cache_invalid(self):
        """测试：缓存无效时从 API 加载"""
        # 准备：确保没有缓存
        cache = get_market_cache()
        cache.clear_cache('binance')
        
        # 执行：创建适配器
        with patch('ccxt.binance') as mock_exchange_class:
            mock_markets = {
                'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
            }
            mock_exchange = MagicMock()
            mock_exchange.load_markets = Mock(return_value=mock_markets)
            mock_exchange_class.return_value = mock_exchange
            
            config = {'apiKey': 'test', 'secret': 'test'}
            adapter = get_adapter('binance', 'spot', config)
            
            # 验证：调用了 load_markets()
            mock_exchange.load_markets.assert_called_once()
            
            # 验证：数据已保存到缓存
            cached_markets = cache.load_from_cache('binance')
            assert cached_markets == mock_markets
    
    def test_reload_markets_with_force(self):
        """测试：强制重新加载市场数据"""
        # 准备：创建适配器并预先缓存数据
        cache = get_market_cache()
        old_markets = {
            'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
        }
        cache.save_to_cache('binance', old_markets)
        
        with patch('ccxt.binance') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange.markets = old_markets
            
            # 新的市场数据（模拟 API 返回）
            new_markets = {
                'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
                'ETH/USDT': {'id': 'ETHUSDT', 'symbol': 'ETH/USDT'},
            }
            mock_exchange.load_markets = Mock(return_value=new_markets)
            mock_exchange_class.return_value = mock_exchange
            
            config = {'apiKey': 'test', 'secret': 'test'}
            adapter = get_adapter('binance', 'spot', config)
            
            # 执行：强制重新加载
            adapter.reload_markets(force=True)
            
            # 验证：调用了 load_markets()
            mock_exchange.load_markets.assert_called()
            
            # 验证：缓存已更新
            cached_markets = cache.load_from_cache('binance')
            assert cached_markets == new_markets
    
    def test_reload_markets_without_force(self):
        """测试：非强制重新加载（使用缓存策略）"""
        # 准备：创建有效缓存
        cache = get_market_cache()
        cached_markets = {
            'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
        }
        cache.save_to_cache('binance', cached_markets)
        
        with patch('ccxt.binance') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange.markets = cached_markets
            mock_exchange.load_markets = Mock(return_value=cached_markets)
            mock_exchange_class.return_value = mock_exchange
            
            config = {'apiKey': 'test', 'secret': 'test'}
            adapter = get_adapter('binance', 'spot', config)
            
            # 重置 mock 计数
            mock_exchange.load_markets.reset_mock()
            
            # 执行：非强制重新加载
            adapter.reload_markets(force=False)
            
            # 验证：没有调用 load_markets()（因为缓存有效）
            mock_exchange.load_markets.assert_not_called()
    
    def test_multiple_adapters_share_cache(self):
        """测试：多个适配器实例共享同一个缓存"""
        # 准备：预先创建缓存
        cache = get_market_cache()
        mock_markets = {
            'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
        }
        cache.save_to_cache('binance', mock_markets)
        
        with patch('ccxt.binance') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange.load_markets = Mock(return_value=mock_markets)
            mock_exchange_class.return_value = mock_exchange
            
            config = {'apiKey': 'test', 'secret': 'test'}
            
            # 创建第一个适配器
            adapter1 = get_adapter('binance', 'spot', config)
            
            # 创建第二个适配器
            adapter2 = get_adapter('binance', 'futures', config)
            
            # 验证：两个适配器都使用了缓存
            assert adapter1.exchange.markets == mock_markets
            assert adapter2.exchange.markets == mock_markets
            
            # 验证：load_markets() 没有被调用（都使用了缓存）
            mock_exchange.load_markets.assert_not_called()
    
    def test_cache_isolation_between_exchanges(self):
        """测试：不同交易所的缓存是隔离的"""
        # 准备：为两个交易所创建不同的缓存
        cache = get_market_cache()
        
        binance_markets = {
            'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
        }
        okx_markets = {
            'BTC/USDT': {'id': 'BTC-USDT', 'symbol': 'BTC/USDT'},
        }
        
        cache.save_to_cache('binance', binance_markets)
        cache.save_to_cache('okx', okx_markets)
        
        # 验证：缓存是隔离的
        assert cache.load_from_cache('binance') == binance_markets
        assert cache.load_from_cache('okx') == okx_markets
        assert cache.load_from_cache('binance') != cache.load_from_cache('okx')
    
    def test_adapter_handles_cache_load_error_gracefully(self):
        """测试：缓存加载失败时适配器能优雅处理"""
        # 准备：模拟缓存加载失败
        with patch('ccxt.binance') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_markets = {'BTC/USDT': {'id': 'BTCUSDT'}}
            mock_exchange.load_markets = Mock(return_value=mock_markets)
            mock_exchange_class.return_value = mock_exchange
            
            # 模拟缓存加载失败
            with patch.object(get_market_cache(), 'load_from_cache', side_effect=Exception("Cache error")):
                config = {'apiKey': 'test', 'secret': 'test'}
                
                # 应该不抛出异常
                adapter = get_adapter('binance', 'spot', config)
                
                # 验证：适配器仍然可以工作
                assert adapter.exchange is not None


class TestCachePerformance:
    """测试缓存性能"""
    
    def test_cache_improves_initialization_speed(self):
        """测试：缓存显著提升初始化速度"""
        cache = get_market_cache()
        cache.clear_cache('binance')
        
        mock_markets = {
            'BTC/USDT': {'id': 'BTCUSDT', 'symbol': 'BTC/USDT'},
        }
        
        with patch('ccxt.binance') as mock_exchange_class:
            mock_exchange = MagicMock()
            
            # 模拟 load_markets() 需要 1 秒
            def slow_load_markets():
                time.sleep(0.1)  # 模拟网络延迟
                return mock_markets
            
            mock_exchange.load_markets = Mock(side_effect=slow_load_markets)
            mock_exchange_class.return_value = mock_exchange
            
            config = {'apiKey': 'test', 'secret': 'test'}
            
            # 第一次：从 API 加载（慢）
            start = time.time()
            adapter1 = get_adapter('binance', 'spot', config)
            first_time = time.time() - start
            
            # 第二次：从缓存加载（快）
            mock_exchange.load_markets.reset_mock()
            start = time.time()
            adapter2 = get_adapter('binance', 'futures', config)
            second_time = time.time() - start
            
            # 验证：第二次明显更快
            assert second_time < first_time
            print(f"第一次（API）: {first_time:.3f}秒")
            print(f"第二次（缓存）: {second_time:.3f}秒")
            print(f"性能提升: {first_time / second_time:.1f}x")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

