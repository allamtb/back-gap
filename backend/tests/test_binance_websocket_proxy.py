"""
测试币安 WebSocket (CCXT Pro) 的代理配置

验证：
1. WebSocket 管理器接收到的 proxy_config
2. 币安 CCXT Pro 实例使用的代理配置
3. 代理协议自动处理（http:// -> socks5://）
"""

import asyncio
import logging
import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.websocket_util import WebSocketManager
from util.market_cache import MarketCache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_binance_websocket_proxy():
    """测试币安 WebSocket 代理配置"""
    
    print("\n" + "="*70)
    print("测试币安 WebSocket (CCXT Pro) 代理配置")
    print("="*70 + "\n")
    
    # 1. 测试简化格式代理（127.0.0.1:1080）
    print("【测试 1】简化格式代理: 127.0.0.1:1080")
    print("-" * 70)
    
    proxy_config_1 = {
        'http': '127.0.0.1:1080',
        'https': '127.0.0.1:1080',
        'ws': '127.0.0.1:1080'
    }
    
    market_cache = MarketCache(cache_dir="data/market_cache", cache_ttl=21600)
    ws_manager_1 = WebSocketManager(proxy_config_1, market_cache)
    
    print(f"\n📡 传入 WebSocketManager 的 proxy_config:")
    print(f"   {proxy_config_1}")
    
    try:
        print(f"\n🔄 创建币安 CCXT Pro 实例...")
        binance_pro = await ws_manager_1.get_pro_exchange('binance', 'spot')
        
        print(f"\n✅ 币安 CCXT Pro 配置:")
        if hasattr(binance_pro, 'aiohttp_proxy'):
            print(f"   aiohttp_proxy: {binance_pro.aiohttp_proxy}")
        else:
            print(f"   aiohttp_proxy: (未设置)")
        
        # 关闭连接
        await binance_pro.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    
    # 2. 测试完整格式代理（http://127.0.0.1:7890）
    print("\n【测试 2】完整格式代理: http://127.0.0.1:7890")
    print("-" * 70)
    
    proxy_config_2 = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890',
        'ws': 'http://127.0.0.1:7890'
    }
    
    ws_manager_2 = WebSocketManager(proxy_config_2, market_cache)
    
    print(f"\n📡 传入 WebSocketManager 的 proxy_config:")
    print(f"   {proxy_config_2}")
    
    try:
        print(f"\n🔄 创建币安 CCXT Pro 实例...")
        binance_pro = await ws_manager_2.get_pro_exchange('binance', 'spot')
        
        print(f"\n✅ 币安 CCXT Pro 配置:")
        if hasattr(binance_pro, 'aiohttp_proxy'):
            print(f"   aiohttp_proxy: {binance_pro.aiohttp_proxy}")
        else:
            print(f"   aiohttp_proxy: (未设置)")
        
        # 关闭连接
        await binance_pro.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    
    # 3. 测试 socks5:// 代理
    print("\n【测试 3】SOCKS5 代理: socks5://127.0.0.1:1080")
    print("-" * 70)
    
    proxy_config_3 = {
        'http': 'socks5://127.0.0.1:1080',
        'https': 'socks5://127.0.0.1:1080',
        'ws': 'socks5://127.0.0.1:1080'
    }
    
    ws_manager_3 = WebSocketManager(proxy_config_3, market_cache)
    
    print(f"\n📡 传入 WebSocketManager 的 proxy_config:")
    print(f"   {proxy_config_3}")
    
    try:
        print(f"\n🔄 创建币安 CCXT Pro 实例...")
        binance_pro = await ws_manager_3.get_pro_exchange('binance', 'spot')
        
        print(f"\n✅ 币安 CCXT Pro 配置:")
        if hasattr(binance_pro, 'aiohttp_proxy'):
            print(f"   aiohttp_proxy: {binance_pro.aiohttp_proxy}")
        else:
            print(f"   aiohttp_proxy: (未设置)")
        
        # 关闭连接
        await binance_pro.close()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("\n🎉 测试完成！")
    print("\n预期结果:")
    print("  测试 1: 原始配置 127.0.0.1:1080 → 实际使用 socks5://127.0.0.1:1080")
    print("  测试 2: 原始配置 http://127.0.0.1:7890 → 实际使用 http://127.0.0.1:7890 (保持不变)")
    print("  测试 3: 原始配置 socks5://127.0.0.1:1080 → 实际使用 socks5://127.0.0.1:1080 (保持不变)")


if __name__ == "__main__":
    asyncio.run(test_binance_websocket_proxy())

