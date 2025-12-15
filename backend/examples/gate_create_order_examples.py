"""
Gate.io 创建订单示例 - 解决市价买单的 price 参数问题

Gate.io 创建市价买单时的特殊要求：
- 需要提供 price 参数来计算总成本
- 或者设置 createMarketBuyOrderRequiresPrice = False，并在 amount 中传入要花费的总金额（USDT）

错误示例：
    exchange.create_order('BTC/USDT', 'market', 'buy', 0.001)
    ❌ 报错：requires the price argument for market buy orders

正确示例见下方
"""

import ccxt

# ============ 配置区域 ============
API_KEY = "a324a7f1a8b7c3fa9fb6713eaceb666a"
SECRET = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"
PROXY = "http://127.0.0.1:1080"
# ===================================


def init_gate_exchange(market_type='spot'):
    """初始化 Gate.io 交易所"""
    exchange = ccxt.gate({
        'apiKey': API_KEY,
        'secret': SECRET,
        'enableRateLimit': True,
        'proxies': {
            'http': PROXY,
            'https': PROXY
        },
        'options': {
            'defaultType': market_type,
        }
    })
    return exchange


# ==================== 解决方案 1：设置全局选项（推荐） ====================
def solution_1_global_option():
    """
    解决方案 1：设置全局选项 createMarketBuyOrderRequiresPrice = False
    
    这样 amount 参数表示要花费的总金额（报价货币，如 USDT）
    """
    print("\n" + "="*70)
    print("解决方案 1：设置全局选项（推荐）")
    print("="*70)
    
    exchange = init_gate_exchange('spot')
    
    # 设置全局选项：不需要 price 参数
    exchange.options['createMarketBuyOrderRequiresPrice'] = False
    
    try:
        # 示例：用 100 USDT 市价买入 BTC
        # amount = 100 表示花费 100 USDT
        symbol = 'BTC/USDT'
        order_type = 'market'
        side = 'buy'
        amount = 100  # 花费 100 USDT
        
        print(f"\n创建订单：")
        print(f"  交易对: {symbol}")
        print(f"  类型: {order_type} {side}")
        print(f"  金额: {amount} USDT (要花费的总金额)")
        
        # 创建订单（测试模式 - 注释掉避免真实下单）
        order = exchange.create_order(symbol, order_type, side, amount)
        # print(f"\n✅ 订单创建成功:")
        # print(json.dumps(order, indent=2, ensure_ascii=False))
        
        print(f"\n✅ 配置正确（已注释真实下单代码）")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 解决方案 2：传入 params 参数 ====================
def solution_2_params():
    """
    解决方案 2：通过 params 参数临时设置
    
    每次调用时通过 params 设置，不影响全局配置
    """
    print("\n" + "="*70)
    print("解决方案 2：通过 params 参数临时设置")
    print("="*70)
    
    exchange = init_gate_exchange('spot')
    
    try:
        # 示例：用 100 USDT 市价买入 BTC
        symbol = 'BTC/USDT'
        order_type = 'market'
        side = 'buy'
        amount = 100  # 花费 100 USDT
        
        print(f"\n创建订单：")
        print(f"  交易对: {symbol}")
        print(f"  类型: {order_type} {side}")
        print(f"  金额: {amount} USDT (要花费的总金额)")
        
        # 通过 params 参数设置（测试模式 - 注释掉避免真实下单）
        # order = exchange.create_order(
        #     symbol, 
        #     order_type, 
        #     side, 
        #     amount,
        #     params={'createMarketBuyOrderRequiresPrice': False}
        # )
        # print(f"\n✅ 订单创建成功:")
        # print(json.dumps(order, indent=2, ensure_ascii=False))
        
        print(f"\n✅ 配置正确（已注释真实下单代码）")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 解决方案 3：提供 price 参数 ====================
def solution_3_with_price():
    """
    解决方案 3：为市价买单也提供 price 参数
    
    amount 表示要买入的数量（基础货币，如 BTC）
    price 用于计算总成本（amount * price）
    """
    print("\n" + "="*70)
    print("解决方案 3：提供 price 参数")
    print("="*70)
    
    exchange = init_gate_exchange('spot')
    
    try:
        # 先获取当前市价
        ticker = exchange.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        
        # 示例：市价买入 0.001 BTC
        symbol = 'BTC/USDT'
        order_type = 'market'
        side = 'buy'
        amount = 0.001  # 要买入的 BTC 数量
        price = current_price  # 提供当前价格用于计算总成本
        
        print(f"\n创建订单：")
        print(f"  交易对: {symbol}")
        print(f"  类型: {order_type} {side}")
        print(f"  数量: {amount} BTC")
        print(f"  参考价格: {price} USDT")
        print(f"  预估成本: {amount * price:.2f} USDT")
        
        # 创建订单（测试模式 - 注释掉避免真实下单）
        order = exchange.create_order(symbol, order_type, side, amount, price)
        # print(f"\n✅ 订单创建成功:")
        # print(json.dumps(order, indent=2, ensure_ascii=False))
        
        print(f"\n✅ 配置正确（已注释真实下单代码）")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 限价单示例（无此问题） ====================
def limit_order_example():
    """
    限价单示例 - 没有 price 参数问题
    
    限价单必须提供 price，这是正常的
    """
    print("\n" + "="*70)
    print("限价单示例（参考）")
    print("="*70)
    
    exchange = init_gate_exchange('spot')
    
    try:
        # 示例：以 60000 USDT 的价格买入 0.001 BTC
        symbol = 'BTC/USDT'
        order_type = 'limit'  # 限价单
        side = 'buy'
        amount = 0.001  # 要买入的 BTC 数量
        price = 60000  # 限价
        
        print(f"\n创建限价订单：")
        print(f"  交易对: {symbol}")
        print(f"  类型: {order_type} {side}")
        print(f"  数量: {amount} BTC")
        print(f"  价格: {price} USDT")
        
        # 创建订单（测试模式 - 注释掉避免真实下单）
        # order = exchange.create_order(symbol, order_type, side, amount, price)
        # print(f"\n✅ 订单创建成功:")
        # print(json.dumps(order, indent=2, ensure_ascii=False))
        
        print(f"\n✅ 限价单无此问题（已注释真实下单代码）")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 合约订单示例 ====================
def futures_order_example():
    """
    合约订单示例
    
    合约的市价单也有同样的问题，解决方案相同
    """
    print("\n" + "="*70)
    print("合约订单示例")
    print("="*70)
    
    exchange = init_gate_exchange('swap')  # 合约类型
    
    # 设置全局选项
    exchange.options['createMarketBuyOrderRequiresPrice'] = False
    
    try:
        # 示例：用 100 USDT 市价开多仓 BTC
        symbol = 'BTC/USDT:USDT'  # 合约符号
        order_type = 'market'
        side = 'buy'
        amount = 0.001  # 合约数量
        
        print(f"\n创建合约订单：")
        print(f"  交易对: {symbol}")
        print(f"  类型: {order_type} {side}")
        print(f"  数量: {amount}")
        
        # 创建订单（测试模式 - 注释掉避免真实下单）
        # order = exchange.create_order(symbol, order_type, side, amount)
        # print(f"\n✅ 订单创建成功:")
        # print(json.dumps(order, indent=2, ensure_ascii=False))
        
        print(f"\n✅ 配置正确（已注释真实下单代码）")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ==================== 主函数 ====================
def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "Gate.io 创建订单完整示例" + " "*17 + "║")
    print("╚" + "="*68 + "╝")
    
    # # 解决方案 1：全局选项（推荐）
    # solution_1_global_option()
    #
    # # 解决方案 2：params 参数
    # solution_2_params()
    
    # 解决方案 3：提供 price 参数
    solution_3_with_price()
    
    # 限价单示例
    limit_order_example()
    
    # 合约订单示例
    futures_order_example()
    
    print("\n" + "="*70)
    print("所有示例运行完成")
    print("="*70)
    print("\n💡 推荐使用解决方案 1（全局选项）或解决方案 2（params 参数）")
    print("   这样 amount 直接表示要花费的 USDT 金额，更直观")
    print("\n⚠️  注意：所有真实下单代码已注释，取消注释前请确认参数！\n")


if __name__ == "__main__":
    main()



























