"""
最简单的 Gate.io 测试脚本

直接运行即可测试各项功能
"""

from gate_complete_example import GateTrading

# ============ 填入你的配置 ============
API_KEY = "a324a7f1a8b7c3fa9fb6713eaceb666a"
SECRET = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"
PROXY = "http://127.0.0.1:1080"  # 使用代理访问
# =====================================

def test_spot():
    """测试现货功能"""
    print("\n" + "=" * 60)
    print("  测试现货功能")
    print("=" * 60 + "\n")
    
    # 创建现货客户端
    client = GateTrading(
        api_key=API_KEY,
        secret=SECRET,
        market_type='spot',
        proxy=PROXY
    )
    
    # 1. 查询余额
    print("\n1️⃣ 查询余额:")
    client.print_balance()
    
    # 2. 查询价格
    print("\n2️⃣ 查询 BTC/USDT 价格:")
    ticker = client.get_ticker('BTC/USDT')
    print(f"最新价: {ticker['last']}")
    print(f"买一价: {ticker['bid']}")
    print(f"卖一价: {ticker['ask']}")
    
    # 3. 查询未成交订单
    print("\n3️⃣ 查询未成交订单:")
    orders = client.get_open_orders('BTC/USDT')
    if orders:
        client.print_orders(orders[:3])  # 只显示前3个
    else:
        print("  📭 当前无未成交订单")
    
    print("\n✅ 现货测试完成")


def test_futures():
    """测试合约功能"""
    print("\n" + "=" * 60)
    print("  测试合约功能")
    print("=" * 60 + "\n")
    
    # 创建合约客户端
    client = GateTrading(
        api_key=API_KEY,
        secret=SECRET,
        market_type='futures',
        proxy=PROXY
    )
    
    # 1. 查询余额
    print("\n1️⃣ 查询合约账户余额:")
    client.print_balance()
    
    # 2. 查询持仓
    print("\n2️⃣ 查询当前持仓:")
    client.print_positions()
    
    # 3. 查询未成交订单
    print("\n3️⃣ 查询未成交订单:")
    orders = client.get_open_orders('BTC/USDT:USDT')
    if orders:
        client.print_orders(orders[:3])
    else:
        print("  📭 当前无未成交订单")
    
    print("\n✅ 合约测试完成")


def test_trading():
    """测试下单功能（已注释）"""
    print("\n" + "=" * 60)
    print("  测试下单功能")
    print("=" * 60 + "\n")
    
    client = GateTrading(
        api_key=API_KEY,
        secret=SECRET,
        market_type='spot',
        proxy=PROXY
    )
    
    # ⚠️ 取消注释以执行真实下单
    
    # 限价买单示例
    # print("📝 创建限价买单...")
    # order = client.create_limit_order(
    #     symbol='BTC/USDT',
    #     side='buy',
    #     amount=0.001,
    #     price=30000
    # )
    # print(f"✅ 订单ID: {order['id']}, 状态: {order['status']}")
    
    # 市价卖单示例
    # print("\n📝 创建市价卖单...")
    # order = client.create_market_order(
    #     symbol='BTC/USDT',
    #     side='sell',
    #     amount=0.001
    # )
    # print(f"✅ 订单ID: {order['id']}, 状态: {order['status']}")
    
    print("⚠️ 下单代码已注释，取消注释以执行真实下单")
    print("✅ 下单测试完成（已跳过）")


def test_close_position():
    """测试平仓功能（已注释）"""
    print("\n" + "=" * 60)
    print("  测试平仓功能")
    print("=" * 60 + "\n")
    
    client = GateTrading(
        api_key=API_KEY,
        secret=SECRET,
        market_type='futures',
        proxy=PROXY
    )
    
    # ⚠️ 取消注释以执行真实平仓
    
    # 平掉指定持仓
    # print("🔒 平掉 BTC 多仓...")
    # order = client.close_position(
    #     symbol='BTC/USDT:USDT',
    #     side='long'
    # )
    # print(f"✅ 平仓订单ID: {order.get('id')}")
    
    # 一键平所有仓
    # print("\n🔒 一键平所有仓...")
    # orders = client.close_all_positions()
    # print(f"✅ 已提交 {len(orders)} 个平仓订单")
    
    print("⚠️ 平仓代码已注释，取消注释以执行真实平仓")
    print("✅ 平仓测试完成（已跳过）")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🚀 Gate.io 简单测试")
    print("=" * 60)
    
    # 检查 API 配置
    if API_KEY == "YOUR_API_KEY":
        print("\n❌ 错误: 请先配置你的 API Key 和 Secret!")
        print("请修改文件顶部的 API_KEY 和 SECRET\n")
        exit(1)
    
    print("\n请选择测试项目:")
    print("  1 - 测试现货功能")
    print("  2 - 测试合约功能")
    print("  3 - 测试下单功能（已注释）")
    print("  4 - 测试平仓功能（已注释）")
    print("  0 - 运行所有测试")
    print()
    
    choice = input("请输入选项 (0-4): ").strip()
    
    try:
        if choice == "0":
            test_spot()
            test_futures()
            test_trading()
            test_close_position()
        elif choice == "1":
            test_spot()
        elif choice == "2":
            test_futures()
        elif choice == "3":
            test_trading()
        elif choice == "4":
            test_close_position()
        else:
            print("❌ 无效选项")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("  ✅ 测试完成")
    print("=" * 60 + "\n")

