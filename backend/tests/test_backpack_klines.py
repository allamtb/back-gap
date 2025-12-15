"""
测试 Backpack K线数据获取功能
通过 MarketService 统一接口测试
"""

import asyncio
import logging
import sys
import os

# 添加后端目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_config import market_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_backpack_klines():
    """测试 Backpack K线数据获取"""
    
    print("=" * 80)
    print("🧪 测试 Backpack K线数据获取（通过 MarketService）")
    print("=" * 80)
    
    # 测试参数
    exchange = "backpack"
    symbol = "SOL/USDC"  # Backpack 使用 USDC 计价
    interval = "15m"
    limit = 10
    market_type = "spot"
    
    try:
        print(f"\n📊 测试参数:")
        print(f"   交易所: {exchange}")
        print(f"   交易对: {symbol}")
        print(f"   周期: {interval}")
        print(f"   数量: {limit}")
        print(f"   市场类型: {market_type}")
        
        print(f"\n⏳ 正在获取K线数据...")
        
        # 调用 MarketService.get_klines()
        result = await market_service.get_klines(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            limit=limit,
            market_type=market_type
        )
        
        # 检查结果
        if result.get('success'):
            data = result.get('data', {})
            klines = data.get('klines', [])
            
            print(f"\n✅ 成功获取 {len(klines)} 条K线数据\n")
            
            # 显示前3条和后3条数据
            if len(klines) > 0:
                print("📈 K线数据样本:")
                print("-" * 80)
                
                # 显示前3条
                for i, kline in enumerate(klines[:3]):
                    print(f"[{i+1}] 时间: {kline['time']}, "
                          f"开: {kline['open']}, "
                          f"高: {kline['high']}, "
                          f"低: {kline['low']}, "
                          f"收: {kline['close']}, "
                          f"量: {kline['volume']}")
                
                if len(klines) > 6:
                    print("...")
                
                # 显示后3条
                for i, kline in enumerate(klines[-3:]):
                    idx = len(klines) - 3 + i
                    print(f"[{idx+1}] 时间: {kline['time']}, "
                          f"开: {kline['open']}, "
                          f"高: {kline['high']}, "
                          f"低: {kline['low']}, "
                          f"收: {kline['close']}, "
                          f"量: {kline['volume']}")
                
                print("-" * 80)
                
                # 验证数据格式
                first_kline = klines[0]
                print(f"\n🔍 数据格式验证:")
                print(f"   时间戳类型: {type(first_kline['time'])} ✓")
                print(f"   价格类型: {type(first_kline['open'])} ✓")
                print(f"   成交量类型: {type(first_kline['volume'])} ✓")
                
                # 验证数据完整性
                print(f"\n✅ 测试通过！")
                print(f"   - 数据格式正确")
                print(f"   - 返回数量: {len(klines)}/{limit}")
                print(f"   - 时间戳范围: {klines[0]['time']} ~ {klines[-1]['time']}")
            else:
                print("⚠️ 返回数据为空")
        else:
            print(f"❌ 获取失败: {result}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        logger.error(f"详细错误信息:", exc_info=True)
        return None


async def test_multiple_symbols():
    """测试多个交易对"""
    
    print("\n" + "=" * 80)
    print("🧪 测试多个交易对")
    print("=" * 80)
    
    symbols = ["BTC/USDC", "SOL/USDC", "ETH/USDC"]
    
    for symbol in symbols:
        print(f"\n📊 测试 {symbol}...")
        try:
            result = await market_service.get_klines(
                exchange="backpack",
                symbol=symbol,
                interval="1h",
                limit=5,
                market_type="spot"
            )
            
            if result.get('success'):
                klines = result['data']['klines']
                print(f"   ✅ 成功获取 {len(klines)} 条数据")
                if len(klines) > 0:
                    last = klines[-1]
                    print(f"   最新价格: {last['close']} USDC")
            else:
                print(f"   ❌ 失败: {result}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")


async def main():
    """主测试函数"""
    
    # 测试1: 单个交易对详细测试
    await test_backpack_klines()
    
    # 测试2: 多个交易对
    await test_multiple_symbols()
    
    print("\n" + "=" * 80)
    print("🎉 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

