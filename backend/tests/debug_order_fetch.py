"""
调试订单获取问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from services.order_service import OrderService

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_order_fetch():
    """测试订单获取"""
    
    # 测试凭证（使用空的，仅测试代码流程）
    credentials = [
        {
            'exchange': 'binance',
            'marketType': 'spot',
            'apiKey': 'test_key',
            'apiSecret': 'test_secret',
        },
        {
            'exchange': 'binance',
            'marketType': 'futures',
            'apiKey': 'test_key',
            'apiSecret': 'test_secret',
        },
    ]
    
    logger.info(f"\n{'='*80}")
    logger.info("开始测试订单获取")
    logger.info(f"{'='*80}\n")
    
    # 创建服务
    service = OrderService()
    
    try:
        # 获取订单
        result = await service.get_orders(credentials)
        
        logger.info(f"\n{'='*80}")
        logger.info("获取结果:")
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Total: {result.get('total')}")
        logger.info(f"Elapsed: {result.get('elapsed')}s")
        logger.info(f"Data length: {len(result.get('data', []))}")
        
        if result.get('data'):
            logger.info(f"\n第一条订单示例:")
            first_order = result['data'][0]
            for key, value in first_order.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("⚠️ 没有获取到任何订单数据")
        
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)


async def test_adapter_direct():
    """直接测试 Adapter"""
    from exchange_adapters import get_adapter
    
    logger.info(f"\n{'='*80}")
    logger.info("直接测试 Adapter")
    logger.info(f"{'='*80}\n")
    
    config = {
        'apiKey': 'test',
        'secret': 'test',
        'enableRateLimit': True,
    }
    
    try:
        # 测试 Binance Spot
        logger.info("测试 Binance Spot Adapter...")
        adapter = get_adapter('binance', 'spot', config)
        
        # 检查方法
        logger.info(f"✅ Adapter 类型: {adapter.__class__.__name__}")
        logger.info(f"✅ 有 fetch_orders 方法: {hasattr(adapter, 'fetch_orders')}")
        logger.info(f"✅ 有 _fetch_orders_default 方法: {hasattr(adapter, '_fetch_orders_default')}")
        logger.info(f"✅ 有 _normalize_orders 方法: {hasattr(adapter, '_normalize_orders')}")
        
        # 检查底层 CCXT
        if adapter.exchange:
            logger.info(f"✅ CCXT 实例: {adapter.exchange.__class__.__name__}")
            logger.info(f"✅ CCXT 有 fetch_orders: {hasattr(adapter.exchange, 'fetch_orders')}")
            logger.info(f"✅ CCXT 有 fetch_open_orders: {hasattr(adapter.exchange, 'fetch_open_orders')}")
            logger.info(f"✅ CCXT 有 fetch_closed_orders: {hasattr(adapter.exchange, 'fetch_closed_orders')}")
            
            # 尝试调用（会因为凭证无效而失败，但可以看到调用路径）
            try:
                logger.info("\n尝试调用 adapter.fetch_orders()...")
                orders = adapter.fetch_orders(None, None, 10)
                logger.info(f"✅ 成功返回: {len(orders)} 条订单")
            except Exception as e:
                logger.warning(f"⚠️ 调用失败（预期中，因为凭证无效）: {e}")
        
    except Exception as e:
        logger.error(f"❌ Adapter 测试失败: {e}", exc_info=True)


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔍 订单获取调试工具")
    print("="*80 + "\n")
    
    # 测试 Adapter
    asyncio.run(test_adapter_direct())
    
    # 测试服务
    asyncio.run(test_order_fetch())
    
    print("\n" + "="*80)
    print("✅ 调试完成")
    print("="*80 + "\n")

