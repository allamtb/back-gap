"""
Backpack 订单历史快速测试脚本

用于测试历史订单和成交记录查询功能
"""

import sys
import asyncio
from datetime import datetime, timedelta

# 导入主模块
from backpack_complete_example import (
    BackpackAPI,
    analyze_orders,
    print_order_stats,
    format_timestamp
)


def print_separator(char="-", length=60):
    """打印分隔线"""
    print(char * length)


def test_order_history(api: BackpackAPI, symbol: str = None, limit: int = 20):
    """测试历史订单查询"""
    print("\n" + "=" * 60)
    print("📋 测试：历史订单查询")
    print("=" * 60)
    
    try:
        # 查询订单
        orders = api.get_order_history(symbol=symbol, limit=limit)
        
        if not orders:
            print("⚠️ 未找到历史订单")
            return
        
        print(f"\n✅ 成功查询到 {len(orders)} 条订单\n")
        
        # 显示统计
        stats = analyze_orders(orders)
        print_order_stats(stats)
        
        # 显示前3条订单详情
        print(f"\n\n📝 订单详情（显示前3条）:")
        print_separator()
        
        for i, order in enumerate(orders[:3], 1):
            order_id = order.get('id', order.get('orderId', 'N/A'))
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A')
            order_type = order.get('orderType', order.get('type', 'N/A'))
            price = order.get('price', 'N/A')
            quantity = order.get('quantity', order.get('origQty', 'N/A'))
            executed_qty = order.get('executedQuantity', order.get('executedQty', '0'))
            status = order.get('status', 'N/A')
            timestamp = order.get('timestamp', order.get('createdAt'))
            
            # 计算成交率
            try:
                fill_rate = (float(executed_qty) / float(quantity)) * 100
                fill_rate_str = f"{fill_rate:.2f}%"
            except:
                fill_rate_str = "N/A"
            
            print(f"\n订单 #{i}")
            print(f"  ID: {order_id}")
            print(f"  交易对: {symbol}")
            print(f"  {side} | {order_type} | {status}")
            print(f"  价格: {price}")
            print(f"  数量: {quantity} (成交: {executed_qty}, {fill_rate_str})")
            print(f"  时间: {format_timestamp(timestamp)}")
        
        return orders
        
    except Exception as e:
        print(f"\n❌ 订单查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fills(api: BackpackAPI, symbol: str = None, limit: int = 10):
    """测试成交历史查询"""
    print("\n" + "=" * 60)
    print("💱 测试：成交历史查询")
    print("=" * 60)
    
    try:
        # 查询成交记录
        fills = api.get_fills(symbol=symbol, limit=limit)
        
        if not fills:
            print("⚠️ 未找到成交记录")
            return
        
        print(f"\n✅ 成功查询到 {len(fills)} 条成交记录\n")
        
        # 统计信息
        total_qty = 0
        total_fee = 0
        maker_count = 0
        buy_count = 0
        sell_count = 0
        
        for fill in fills:
            try:
                qty = float(fill.get('quantity', fill.get('qty', 0)))
                fee = float(fill.get('fee', fill.get('commission', 0)))
                is_maker = fill.get('isMaker', False)
                side = fill.get('side', '')
                
                total_qty += qty
                total_fee += fee
                if is_maker:
                    maker_count += 1
                if side == 'Bid':
                    buy_count += 1
                else:
                    sell_count += 1
            except:
                pass
        
        # 显示统计
        print("📊 成交统计:")
        print(f"  总成交笔数: {len(fills)}")
        print(f"  总成交量: {total_qty:.4f}")
        print(f"  总手续费: {total_fee:.6f}")
        print(f"  Maker 比例: {maker_count}/{len(fills)} ({maker_count/len(fills)*100:.1f}%)")
        print(f"  买入/卖出: {buy_count}/{sell_count}")
        
        # 显示前5条成交详情
        print(f"\n\n📝 成交详情（显示前5条）:")
        print_separator()
        
        for i, fill in enumerate(fills[:5], 1):
            trade_id = fill.get('id', fill.get('tradeId', 'N/A'))
            order_id = fill.get('orderId', 'N/A')
            symbol = fill.get('symbol', 'N/A')
            side = fill.get('side', 'N/A')
            price = fill.get('price', 'N/A')
            quantity = fill.get('quantity', fill.get('qty', 'N/A'))
            fee = fill.get('fee', fill.get('commission', 'N/A'))
            fee_asset = fill.get('feeAsset', fill.get('commissionAsset', 'N/A'))
            is_maker = fill.get('isMaker', False)
            timestamp = fill.get('timestamp', fill.get('time'))
            
            print(f"\n成交 #{i}")
            print(f"  ID: {trade_id} (订单: {order_id})")
            print(f"  {symbol} | {side} | {'Maker' if is_maker else 'Taker'}")
            print(f"  价格: {price} | 数量: {quantity}")
            print(f"  手续费: {fee} {fee_asset}")
            print(f"  时间: {format_timestamp(timestamp)}")
        
        return fills
        
    except Exception as e:
        print(f"\n❌ 成交历史查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_time_range_fills(api: BackpackAPI, symbol: str, days: int = 7):
    """测试指定时间范围的成交查询"""
    print("\n" + "=" * 60)
    print(f"🕒 测试：最近 {days} 天的成交记录")
    print("=" * 60)
    
    try:
        # 计算时间范围（毫秒时间戳）
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        print(f"\n查询时间范围:")
        print(f"  开始: {format_timestamp(start_time)}")
        print(f"  结束: {format_timestamp(end_time)}")
        
        # 查询
        fills = api.get_fills(
            symbol=symbol,
            from_timestamp=start_time,
            to_timestamp=end_time,
            limit=100
        )
        
        if fills:
            print(f"\n✅ 找到 {len(fills)} 条成交记录")
            
            # 按日期统计
            daily_stats = {}
            for fill in fills:
                try:
                    ts = fill.get('timestamp', fill.get('time'))
                    if ts:
                        # 转换为日期
                        if ts > 1e12:
                            ts = ts / 1000
                        dt = datetime.fromtimestamp(ts)
                        date_str = dt.strftime('%Y-%m-%d')
                        
                        if date_str not in daily_stats:
                            daily_stats[date_str] = {'count': 0, 'volume': 0}
                        
                        daily_stats[date_str]['count'] += 1
                        qty = float(fill.get('quantity', fill.get('qty', 0)))
                        daily_stats[date_str]['volume'] += qty
                except:
                    pass
            
            # 显示每日统计
            print(f"\n📅 每日成交统计:")
            for date in sorted(daily_stats.keys(), reverse=True):
                stats = daily_stats[date]
                print(f"  {date}: {stats['count']} 笔, 成交量 {stats['volume']:.4f}")
        else:
            print(f"\n⚠️ 未找到成交记录")
        
        return fills
        
    except Exception as e:
        print(f"\n❌ 时间范围查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pagination(api: BackpackAPI, symbol: str = None):
    """测试分页查询"""
    print("\n" + "=" * 60)
    print("📄 测试：分页查询")
    print("=" * 60)
    
    try:
        # 第一页
        page1 = api.get_order_history(symbol=symbol, limit=5, offset=0)
        print(f"\n第 1 页: {len(page1)} 条订单")
        if page1:
            print(f"  第一条订单ID: {page1[0].get('id', 'N/A')}")
            print(f"  最后订单ID: {page1[-1].get('id', 'N/A')}")
        
        # 第二页
        page2 = api.get_order_history(symbol=symbol, limit=5, offset=5)
        print(f"\n第 2 页: {len(page2)} 条订单")
        if page2:
            print(f"  第一条订单ID: {page2[0].get('id', 'N/A')}")
            print(f"  最后订单ID: {page2[-1].get('id', 'N/A')}")
        
        # 检查是否重复
        if page1 and page2:
            id1 = set(o.get('id', o.get('orderId')) for o in page1)
            id2 = set(o.get('id', o.get('orderId')) for o in page2)
            overlap = id1 & id2
            if overlap:
                print(f"\n⚠️ 警告: 发现 {len(overlap)} 条重复订单")
            else:
                print(f"\n✅ 分页正常，无重复订单")
        
        return page1, page2
        
    except Exception as e:
        print(f"\n❌ 分页查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def main():
    """主测试函数"""
    print("=" * 60)
    print("  Backpack 订单历史功能测试")
    print("=" * 60)
    
    # ========== 配置 ==========
    API_KEY = "whLRx2oL9k6nsNMNrBSX/oKCk6xktT1fkMY8fTrnMYk="
    SECRET = "ueV+p51iQunTdUI4nNpV4xRHCQlxthpn4dqLZiQkShM="
    PROXY = "http://127.0.0.1:1080"
    SYMBOL = "SOL_USDC"
    
    # 检查配置
    if API_KEY == "你的_BASE64_编码的公钥":
        print("\n❌ 错误: 请先配置 API_KEY 和 SECRET")
        print("请在脚本中填写你的 Backpack API 凭证")
        return
    
    # 初始化 API 客户端
    print(f"\n🔧 初始化 Backpack API 客户端...")
    print(f"   代理: {PROXY}")
    print(f"   测试交易对: {SYMBOL}")
    
    api = BackpackAPI(api_key=API_KEY, secret=SECRET, proxy=PROXY)
    
    # 运行测试
    print("\n" + "🚀" * 30)
    print("开始测试...")
    print("🚀" * 30)
    
    # 1. 基础订单查询
    test_order_history(api, symbol=SYMBOL, limit=20)
    
    # 2. 成交历史查询
    test_fills(api, symbol=SYMBOL, limit=10)
    
    # 3. 时间范围查询
    test_time_range_fills(api, symbol=SYMBOL, days=7)
    
    # 4. 分页查询
    test_pagination(api, symbol=SYMBOL)
    
    # 完成
    print("\n" + "=" * 60)
    print("  ✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

