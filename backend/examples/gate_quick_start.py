"""
Gate.io 快速开始示例 - 最简单的使用方式

只需修改 API Key，即可快速运行！
"""

import asyncio
from gate_complete_example import GateTrading


# ============ 配置区域 ============
# 🔑 填入你的 Gate.io API 凭证
API_KEY = "a324a7f1a8b7c3fa9fb6713eaceb666a"
SECRET = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"

# 🌐 代理设置（不需要就设为 None）
PROXY = "http://127.0.0.1:7890"  # 使用代理访问

# 📊 交易市场类型
MARKET_TYPE = 'spot'  # 'spot' 现货 或 'futures' 合约

# 📈 测试交易对
SYMBOL = "BTC/USDT"  # 现货格式
# SYMBOL = "BTC/USDT:USDT"  # 合约格式
# ===================================


def example_1_查询余额():
    """示例1: 查询账户余额"""
    print("\n" + "=" * 60)
    print("  示例1: 查询账户余额")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    client.print_balance()


def example_2_查询价格():
    """示例2: 查询当前价格"""
    print("\n" + "=" * 60)
    print("  示例2: 查询当前价格")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    ticker = client.get_ticker(SYMBOL)
    print(f"\n交易对: {SYMBOL}")
    print(f"最新价: {ticker['last']}")
    print(f"买一价: {ticker['bid']}")
    print(f"卖一价: {ticker['ask']}")
    print(f"24h涨跌幅: {ticker.get('percentage', 0)}%")


def example_3_查询订单():
    """示例3: 查询未成交订单"""
    print("\n" + "=" * 60)
    print("  示例3: 查询未成交订单")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    orders = client.get_open_orders(SYMBOL)
    client.print_orders(orders)


def example_4_下单_限价单():
    """示例4: 下限价单（已注释，取消注释以执行）"""
    print("\n" + "=" * 60)
    print("  示例4: 下限价单")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    # ⚠️ 取消下面的注释以执行下单
    # order = client.create_limit_order(
    #     symbol=SYMBOL,
    #     side='buy',      # 买入
    #     amount=0.001,    # 数量
    #     price=40000      # 价格
    # )
    # print(f"\n✅ 订单创建成功!")
    # print(f"订单ID: {order['id']}")
    # print(f"状态: {order['status']}")
    
    print("\n⚠️ 下单代码已注释，取消注释以执行真实下单")


def example_5_下单_市价单():
    """示例5: 下市价单（已注释，取消注释以执行）"""
    print("\n" + "=" * 60)
    print("  示例5: 下市价单")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    # ⚠️ 取消下面的注释以执行下单
    # order = client.create_market_order(
    #     symbol=SYMBOL,
    #     side='sell',     # 卖出
    #     amount=0.001     # 数量
    # )
    # print(f"\n✅ 订单创建成功!")
    # print(f"订单ID: {order['id']}")
    # print(f"状态: {order['status']}")
    
    print("\n⚠️ 下单代码已注释，取消注释以执行真实下单")


def example_6_查询持仓():
    """示例6: 查询持仓（仅合约）"""
    print("\n" + "=" * 60)
    print("  示例6: 查询持仓")
    print("=" * 60)
    
    if MARKET_TYPE != 'futures':
        print("\n⚠️ 此功能仅适用于合约市场")
        print("请将 MARKET_TYPE 改为 'futures' 并使用合约交易对")
        return
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    client.print_positions()


def example_7_平仓():
    """示例7: 平仓（仅合约，已注释）"""
    print("\n" + "=" * 60)
    print("  示例7: 平仓")
    print("=" * 60)
    
    if MARKET_TYPE != 'futures':
        print("\n⚠️ 此功能仅适用于合约市场")
        return
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    # ⚠️ 取消下面的注释以执行平仓
    # 平掉指定持仓
    # order = client.close_position(
    #     symbol=SYMBOL,
    #     side='long'  # 平多仓（或 'short' 平空仓）
    # )
    # print(f"\n✅ 平仓成功!")
    # print(f"订单ID: {order.get('id')}")
    
    # 一键平所有仓
    # orders = client.close_all_positions()
    # print(f"\n✅ 已提交 {len(orders)} 个平仓订单")
    
    print("\n⚠️ 平仓代码已注释，取消注释以执行真实平仓")


async def example_8_监控余额():
    """示例8: 实时监控余额变化（按 Ctrl+C 停止）"""
    print("\n" + "=" * 60)
    print("  示例8: 实时监控余额变化")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    print("\n开始监控账户余额...")
    print("提示: 按 Ctrl+C 停止监控\n")
    
    try:
        await client.monitor_balance(interval=5)
    except KeyboardInterrupt:
        print("\n✅ 监控已停止")


async def example_9_监控订单():
    """示例9: 实时监控订单变化（按 Ctrl+C 停止）"""
    print("\n" + "=" * 60)
    print("  示例9: 实时监控订单变化")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    print(f"\n开始监控订单: {SYMBOL}")
    print("提示: 按 Ctrl+C 停止监控\n")
    
    try:
        await client.monitor_orders(symbol=SYMBOL, interval=2)
    except KeyboardInterrupt:
        print("\n✅ 监控已停止")


async def example_10_监控持仓():
    """示例10: 实时监控持仓变化（按 Ctrl+C 停止，仅合约）"""
    print("\n" + "=" * 60)
    print("  示例10: 实时监控持仓变化")
    print("=" * 60)
    
    if MARKET_TYPE != 'futures':
        print("\n⚠️ 此功能仅适用于合约市场")
        return
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    print("\n开始监控持仓...")
    print("提示: 按 Ctrl+C 停止监控\n")
    
    try:
        await client.monitor_positions(interval=3)
    except KeyboardInterrupt:
        print("\n✅ 监控已停止")


async def example_11_全面监控():
    """示例11: 同时监控余额、订单和持仓（按 Ctrl+C 停止）"""
    print("\n" + "=" * 60)
    print("  示例11: 全面监控")
    print("=" * 60)
    
    client = GateTrading(API_KEY, SECRET, MARKET_TYPE, PROXY)
    
    print("\n开始全面监控...")
    print("- 余额监控: 每5秒")
    print("- 订单监控: 每2秒")
    if MARKET_TYPE == 'futures':
        print("- 持仓监控: 每3秒")
    print("\n提示: 按 Ctrl+C 停止监控\n")
    
    try:
        tasks = [
            client.monitor_balance(interval=5),
            client.monitor_orders(symbol=SYMBOL, interval=2)
        ]
        
        if MARKET_TYPE == 'futures':
            tasks.append(client.monitor_positions(interval=3))
        
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n✅ 监控已停止")


def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 60)
    print("  🚀 Gate.io 快速开始示例")
    print("=" * 60)
    print(f"\n市场类型: {MARKET_TYPE.upper()}")
    print(f"交易对: {SYMBOL}")
    print(f"代理: {PROXY or '不使用'}\n")
    
    # 检查 API 配置
    if API_KEY == "YOUR_API_KEY" or SECRET == "YOUR_SECRET":
        print("❌ 错误: 请先配置你的 API Key 和 Secret!")
        print("请在文件顶部的配置区域填入正确的凭证\n")
        return
    
    print("请选择要运行的示例:\n")
    print("查询类:")
    print("  1 - 查询账户余额")
    print("  2 - 查询当前价格")
    print("  3 - 查询未成交订单")
    print("  6 - 查询持仓（仅合约）")
    print("\n交易类:")
    print("  4 - 下限价单（已注释）")
    print("  5 - 下市价单（已注释）")
    print("  7 - 平仓（仅合约，已注释）")
    print("\n监控类:")
    print("  8 - 实时监控余额")
    print("  9 - 实时监控订单")
    print(" 10 - 实时监控持仓（仅合约）")
    print(" 11 - 全面监控（余额+订单+持仓）")
    print("\n  0 - 运行所有查询示例")
    print()
    
    choice = input("请输入选项 (0-11): ").strip()
    
    if choice == "0":
        # 运行所有查询示例
        example_1_查询余额()
        example_2_查询价格()
        example_3_查询订单()
        if MARKET_TYPE == 'futures':
            example_6_查询持仓()
    
    elif choice == "1":
        example_1_查询余额()
    
    elif choice == "2":
        example_2_查询价格()
    
    elif choice == "3":
        example_3_查询订单()
    
    elif choice == "4":
        example_4_下单_限价单()
    
    elif choice == "5":
        example_5_下单_市价单()
    
    elif choice == "6":
        example_6_查询持仓()
    
    elif choice == "7":
        example_7_平仓()
    
    elif choice == "8":
        asyncio.run(example_8_监控余额())
    
    elif choice == "9":
        asyncio.run(example_9_监控订单())
    
    elif choice == "10":
        asyncio.run(example_10_监控持仓())
    
    elif choice == "11":
        asyncio.run(example_11_全面监控())
    
    else:
        print("❌ 无效选项")
        return
    
    print("\n" + "=" * 60)
    print("  ✅ 示例完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

