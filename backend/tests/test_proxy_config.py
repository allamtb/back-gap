#!/usr/bin/env python3
"""
代理配置测试脚本

用于验证：
1. PROXY_URL 环境变量是否正确读取
2. CCXT.pro 是否正确应用代理配置
3. Backpack WebSocket 是否正确应用代理配置

使用方法：
1. 设置环境变量（可选）：
   Windows (PowerShell): $env:PROXY_URL="http://127.0.0.1:7890"
   Windows (CMD): set PROXY_URL=http://127.0.0.1:7890
   Linux/Mac: export PROXY_URL=http://127.0.0.1:7890

2. 运行测试：
   python backend/tests/test_proxy_config.py
"""

import os
import sys
import asyncio
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from util.market_cache import MarketCache
from util.websocket_util import WebSocketManager
from util.backpack_websocket import BackpackWebSocketClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_proxy_config_reading():
    """测试 1：环境变量读取"""
    print("\n" + "="*80)
    print("📋 测试 1：环境变量读取")
    print("="*80)
    
    proxy_url = os.getenv('PROXY_URL', '').strip()
    
    if proxy_url:
        print(f"✅ PROXY_URL 已设置: {proxy_url}")
        proxy_config = {
            'http': proxy_url,
            'https': proxy_url
        }
    else:
        print("ℹ️ PROXY_URL 未设置（将使用直连）")
        proxy_config = {}
    
    return proxy_config


async def test_ccxt_pro_proxy(proxy_config):
    """测试 2：CCXT.pro 代理配置"""
    print("\n" + "="*80)
    print("📋 测试 2：CCXT.pro 代理配置")
    print("="*80)
    
    try:
        # 创建市场缓存
        market_cache = MarketCache(cache_dir="data/market_cache", cache_ttl=21600)
        
        # 创建 WebSocketManager
        ws_manager = WebSocketManager(proxy_config, market_cache)
        
        print(f"🔍 WebSocketManager proxy_config: {ws_manager.proxy_config}")
        
        # 尝试获取 Binance CCXT.pro 实例
        print("\n📡 测试创建 Binance CCXT.pro 实例...")
        exchange = await ws_manager.get_pro_exchange('binance', 'spot')
        
        # 检查代理配置
        if hasattr(exchange, 'proxies'):
            if exchange.proxies:
                print(f"✅ Binance CCXT.pro 代理配置成功: {exchange.proxies}")
            else:
                print("ℹ️ Binance CCXT.pro 未配置代理（直连模式）")
        else:
            print("⚠️ Binance CCXT.pro 实例没有 proxies 属性")
        
        # 关闭交易所
        await exchange.close()
        
        return True
    
    except Exception as e:
        print(f"❌ CCXT.pro 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backpack_proxy(proxy_config):
    """测试 3：Backpack WebSocket 代理配置"""
    print("\n" + "="*80)
    print("📋 测试 3：Backpack WebSocket 代理配置")
    print("="*80)
    
    try:
        # 提取代理地址
        proxy = None
        if proxy_config:
            proxy = proxy_config.get('http') or proxy_config.get('https')
        
        print(f"🔍 Backpack proxy 参数: {proxy}")
        
        # 创建 Backpack WebSocket 客户端
        async def dummy_callback(stream_type, data):
            pass
        
        client = BackpackWebSocketClient(
            on_message=dummy_callback,
            proxy=proxy
        )
        
        print("📡 测试连接 Backpack WebSocket...")
        
        # 尝试连接（设置超时 5 秒）
        try:
            await asyncio.wait_for(client.connect(), timeout=5.0)
            
            if client.websocket and not client.websocket.closed:
                print("✅ Backpack WebSocket 连接成功")
                if proxy:
                    print(f"✅ 使用代理: {proxy}")
                else:
                    print("✅ 使用直连")
                
                # 断开连接
                await client.disconnect()
                return True
            else:
                print("❌ Backpack WebSocket 连接失败")
                return False
        
        except asyncio.TimeoutError:
            print("⏱️ Backpack WebSocket 连接超时（5秒）")
            print("💡 提示：")
            if not proxy:
                print("   - 如果在国内，可能需要设置代理")
                print("   - 设置方式：set PROXY_URL=http://127.0.0.1:7890")
            else:
                print("   - 检查代理软件是否启动")
                print("   - 检查代理地址是否正确")
            return False
    
    except Exception as e:
        print(f"❌ Backpack 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """打印测试总结"""
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    print(f"\n✅ 环境变量读取: {'成功' if results['env'] else '失败'}")
    print(f"{'✅' if results['ccxt'] else '❌'} CCXT.pro 代理配置: {'成功' if results['ccxt'] else '失败'}")
    print(f"{'✅' if results['backpack'] else '❌'} Backpack WebSocket 代理配置: {'成功' if results['backpack'] else '失败'}")
    
    if all(results.values()):
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")
    
    print("\n💡 提示：")
    print("  - 如果未设置代理，CCXT.pro 和 Backpack 都应该能正常工作（直连）")
    print("  - 如果设置了代理，请确保代理软件已启动")
    print("  - 代理地址格式：http://127.0.0.1:7890")


async def main():
    """主函数"""
    print("🚀 开始代理配置测试...")
    
    results = {
        'env': False,
        'ccxt': False,
        'backpack': False
    }
    
    # 测试 1：环境变量读取
    proxy_config = test_proxy_config_reading()
    results['env'] = True
    
    # 测试 2：CCXT.pro 代理配置
    results['ccxt'] = await test_ccxt_pro_proxy(proxy_config)
    
    # 测试 3：Backpack WebSocket 代理配置
    results['backpack'] = await test_backpack_proxy(proxy_config)
    
    # 打印总结
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())

