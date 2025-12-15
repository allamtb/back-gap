"""
Gate.io 交易操作脚本 - 下单、平仓

功能：
- 现货买入（市价/限价）
- 现货卖出（市价/限价）
- 合约开仓（做多/做空，市价/限价）
- 合约平仓（平多/平空）
- 取消订单
"""

from gate_complete_example import GateTrading
from datetime import datetime

# ============ 配置区域 ============
API_KEY = "a324a7f1a8b7c3fa9fb6713eaceb666a"
SECRET = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"
PROXY = "http://127.0.0.1:1080"
# ===================================


class TradingClient:
    """交易客户端"""
    
    def __init__(self, api_key, secret, proxy=None):
        self.spot_client = GateTrading(api_key, secret, 'spot', proxy)
        self.futures_client = GateTrading(api_key, secret, 'futures', proxy)
        
        print("\n" + "=" * 70)
        print("  💼 Gate.io 交易客户端")
        print("=" * 70 + "\n")
    
    def format_time(self):
        """格式化当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ==================== 现货交易 ====================
    
    def spot_buy_market(self, symbol: str, amount: float):
        """现货市价买入"""
        print(f"\n[{self.format_time()}] 🟢 现货市价买入")
        print(f"  交易对: {symbol}")
        print(f"  数量: {amount}")
        
        try:
            order = self.spot_client.create_market_order(symbol, 'buy', amount)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            print(f"     成交量: {order.get('filled', 0)}")
            return order
        except Exception as e:
            print(f"  ❌ 下单失败: {e}")
            return None
    
    def spot_buy_limit(self, symbol: str, amount: float, price: float):
        """现货限价买入"""
        print(f"\n[{self.format_time()}] 🟢 现货限价买入")
        print(f"  交易对: {symbol}")
        print(f"  数量: {amount}")
        print(f"  价格: {price}")
        
        try:
            order = self.spot_client.create_limit_order(symbol, 'buy', amount, price)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            return order
        except Exception as e:
            print(f"  ❌ 下单失败: {e}")
            return None
    
    def spot_sell_market(self, symbol: str, amount: float):
        """现货市价卖出"""
        print(f"\n[{self.format_time()}] 🔴 现货市价卖出")
        print(f"  交易对: {symbol}")
        print(f"  数量: {amount}")
        
        try:
            order = self.spot_client.create_market_order(symbol, 'sell', amount)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            print(f"     成交量: {order.get('filled', 0)}")
            return order
        except Exception as e:
            print(f"  ❌ 下单失败: {e}")
            return None
    
    def spot_sell_limit(self, symbol: str, amount: float, price: float):
        """现货限价卖出"""
        print(f"\n[{self.format_time()}] 🔴 现货限价卖出")
        print(f"  交易对: {symbol}")
        print(f"  数量: {amount}")
        print(f"  价格: {price}")
        
        try:
            order = self.spot_client.create_limit_order(symbol, 'sell', amount, price)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            return order
        except Exception as e:
            print(f"  ❌ 下单失败: {e}")
            return None
    
    # ==================== 合约交易 ====================
    
    def futures_open_long_market(self, symbol: str, contracts: float):
        """合约市价开多"""
        print(f"\n[{self.format_time()}] 🟢 合约市价开多")
        print(f"  交易对: {symbol}")
        print(f"  数量: {contracts}")
        
        try:
            order = self.futures_client.create_market_order(symbol, 'buy', contracts)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            print(f"     成交量: {order.get('filled', 0)}")
            return order
        except Exception as e:
            print(f"  ❌ 开仓失败: {e}")
            return None
    
    def futures_open_long_limit(self, symbol: str, contracts: float, price: float):
        """合约限价开多"""
        print(f"\n[{self.format_time()}] 🟢 合约限价开多")
        print(f"  交易对: {symbol}")
        print(f"  数量: {contracts}")
        print(f"  价格: {price}")
        
        try:
            order = self.futures_client.create_limit_order(symbol, 'buy', contracts, price)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            return order
        except Exception as e:
            print(f"  ❌ 开仓失败: {e}")
            return None
    
    def futures_open_short_market(self, symbol: str, contracts: float):
        """合约市价开空"""
        print(f"\n[{self.format_time()}] 🔴 合约市价开空")
        print(f"  交易对: {symbol}")
        print(f"  数量: {contracts}")
        
        try:
            order = self.futures_client.create_market_order(symbol, 'sell', contracts)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            print(f"     成交量: {order.get('filled', 0)}")
            return order
        except Exception as e:
            print(f"  ❌ 开仓失败: {e}")
            return None
    
    def futures_open_short_limit(self, symbol: str, contracts: float, price: float):
        """合约限价开空"""
        print(f"\n[{self.format_time()}] 🔴 合约限价开空")
        print(f"  交易对: {symbol}")
        print(f"  数量: {contracts}")
        print(f"  价格: {price}")
        
        try:
            order = self.futures_client.create_limit_order(symbol, 'sell', contracts, price)
            print(f"  ✅ 订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            return order
        except Exception as e:
            print(f"  ❌ 开仓失败: {e}")
            return None
    
    def futures_close_long(self, symbol: str, contracts: float = None):
        """平多仓（市价）"""
        print(f"\n[{self.format_time()}] 🔒 平多仓")
        print(f"  交易对: {symbol}")
        print(f"  数量: {'全部' if contracts is None else contracts}")
        
        try:
            # 如果没有指定数量，查询当前持仓
            if contracts is None:
                positions = self.futures_client.get_positions(symbol)
                for pos in positions:
                    if pos['side'] == 'long' and pos['contracts'] > 0:
                        contracts = pos['contracts']
                        break
                
                if contracts is None or contracts == 0:
                    print(f"  ⚠️ 没有找到多仓")
                    return None
            
            # 平仓就是反向操作：平多 = 卖出
            order = self.futures_client.create_market_order(symbol, 'sell', contracts, 
                                                           params={'reduceOnly': True})
            print(f"  ✅ 平仓订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            print(f"     成交量: {order.get('filled', 0)}")
            return order
        except Exception as e:
            print(f"  ❌ 平仓失败: {e}")
            return None
    
    def futures_close_short(self, symbol: str, contracts: float = None):
        """平空仓（市价）"""
        print(f"\n[{self.format_time()}] 🔒 平空仓")
        print(f"  交易对: {symbol}")
        print(f"  数量: {'全部' if contracts is None else contracts}")
        
        try:
            # 如果没有指定数量，查询当前持仓
            if contracts is None:
                positions = self.futures_client.get_positions(symbol)
                for pos in positions:
                    if pos['side'] == 'short' and pos['contracts'] > 0:
                        contracts = abs(pos['contracts'])
                        break
                
                if contracts is None or contracts == 0:
                    print(f"  ⚠️ 没有找到空仓")
                    return None
            
            # 平仓就是反向操作：平空 = 买入
            order = self.futures_client.create_market_order(symbol, 'buy', contracts,
                                                           params={'reduceOnly': True})
            print(f"  ✅ 平仓订单已提交")
            print(f"     订单ID: {order['id']}")
            print(f"     状态: {order['status']}")
            print(f"     成交量: {order.get('filled', 0)}")
            return order
        except Exception as e:
            print(f"  ❌ 平仓失败: {e}")
            return None
    
    def futures_close_all(self):
        """一键平所有仓"""
        print(f"\n[{self.format_time()}] 🔒 一键平所有仓")
        
        try:
            orders = self.futures_client.close_all_positions()
            print(f"  ✅ 已提交 {len(orders)} 个平仓订单")
            for order in orders:
                print(f"     {order.get('symbol')} - 订单ID: {order.get('id')}")
            return orders
        except Exception as e:
            print(f"  ❌ 平仓失败: {e}")
            return None
    
    # ==================== 订单管理 ====================
    
    def cancel_order(self, order_id: str, symbol: str, market_type: str = 'spot'):
        """取消订单"""
        print(f"\n[{self.format_time()}] ❌ 取消订单")
        print(f"  订单ID: {order_id}")
        print(f"  交易对: {symbol}")
        print(f"  市场: {market_type}")
        
        try:
            client = self.spot_client if market_type == 'spot' else self.futures_client
            result = client.cancel_order(order_id, symbol)
            print(f"  ✅ 订单已取消")
            return result
        except Exception as e:
            print(f"  ❌ 取消失败: {e}")
            return None
    
    def cancel_all_orders(self, symbol: str = None, market_type: str = 'spot'):
        """取消所有订单"""
        print(f"\n[{self.format_time()}] ❌ 取消所有订单")
        print(f"  交易对: {symbol if symbol else '全部'}")
        print(f"  市场: {market_type}")
        
        try:
            client = self.spot_client if market_type == 'spot' else self.futures_client
            result = client.cancel_all_orders(symbol)
            print(f"  ✅ 订单已全部取消")
            return result
        except Exception as e:
            print(f"  ❌ 取消失败: {e}")
            return None
    
    # ==================== 查询功能 ====================
    
    def show_balance(self):
        """显示余额"""
        print(f"\n[{self.format_time()}] 💰 账户余额")
        print("\n现货余额:")
        self.spot_client.print_balance()
        print("\n合约余额:")
        self.futures_client.print_balance()
    
    def show_positions(self):
        """显示持仓"""
        print(f"\n[{self.format_time()}] 📊 合约持仓")
        self.futures_client.print_positions()
    
    def show_orders(self, symbol: str = None, market_type: str = 'spot'):
        """显示未成交订单"""
        print(f"\n[{self.format_time()}] 📝 未成交订单")
        print(f"  市场: {market_type}")
        
        try:
            client = self.spot_client if market_type == 'spot' else self.futures_client
            orders = client.get_open_orders(symbol)
            if orders:
                client.print_orders(orders[:20])  # 最多显示 20 个
            else:
                print("  📭 当前无未成交订单")
        except Exception as e:
            print(f"  ❌ 查询失败: {e}")


def print_menu():
    """打印菜单"""
    print("\n" + "=" * 70)
    print("  📋 操作菜单")
    print("=" * 70)
    print("\n  现货交易:")
    print("    1 - 现货市价买入")
    print("    2 - 现货限价买入")
    print("    3 - 现货市价卖出")
    print("    4 - 现货限价卖出")
    print("\n  合约交易:")
    print("    5 - 合约市价开多")
    print("    6 - 合约限价开多")
    print("    7 - 合约市价开空")
    print("    8 - 合约限价开空")
    print("\n  平仓操作:")
    print("    9 - 平多仓")
    print("   10 - 平空仓")
    print("   11 - 一键平所有仓")
    print("\n  查询功能:")
    print("   12 - 查看余额")
    print("   13 - 查看持仓")
    print("   14 - 查看现货订单")
    print("   15 - 查看合约订单")
    print("\n  订单管理:")
    print("   16 - 取消现货所有订单")
    print("   17 - 取消合约所有订单")
    print("\n    0 - 退出")
    print("=" * 70)


def main():
    """主函数"""
    # 检查 API 配置
    if API_KEY == "YOUR_API_KEY":
        print("\n❌ 错误: 请先配置你的 API Key 和 Secret!")
        print("请修改文件顶部的 API_KEY 和 SECRET\n")
        exit(1)
    
    # 创建交易客户端
    client = TradingClient(API_KEY, SECRET, PROXY)
    
    while True:
        print_menu()
        choice = input("\n请选择操作 (0-17): ").strip()
        
        try:
            if choice == "0":
                print("\n👋 再见!")
                break
            
            elif choice == "1":
                symbol = input("  交易对 (如 BTC/USDT): ").strip()
                amount = float(input("  买入数量: "))
                client.spot_buy_market(symbol, amount)
            
            elif choice == "2":
                symbol = input("  交易对 (如 BTC/USDT): ").strip()
                amount = float(input("  买入数量: "))
                price = float(input("  买入价格: "))
                client.spot_buy_limit(symbol, amount, price)
            
            elif choice == "3":
                symbol = input("  交易对 (如 BTC/USDT): ").strip()
                amount = float(input("  卖出数量: "))
                client.spot_sell_market(symbol, amount)
            
            elif choice == "4":
                symbol = input("  交易对 (如 BTC/USDT): ").strip()
                amount = float(input("  卖出数量: "))
                price = float(input("  卖出价格: "))
                client.spot_sell_limit(symbol, amount, price)
            
            elif choice == "5":
                symbol = input("  交易对 (如 BTC/USDT:USDT): ").strip()
                contracts = float(input("  合约数量: "))
                client.futures_open_long_market(symbol, contracts)
            
            elif choice == "6":
                symbol = input("  交易对 (如 BTC/USDT:USDT): ").strip()
                contracts = float(input("  合约数量: "))
                price = float(input("  开仓价格: "))
                client.futures_open_long_limit(symbol, contracts, price)
            
            elif choice == "7":
                symbol = input("  交易对 (如 BTC/USDT:USDT): ").strip()
                contracts = float(input("  合约数量: "))
                client.futures_open_short_market(symbol, contracts)
            
            elif choice == "8":
                symbol = input("  交易对 (如 BTC/USDT:USDT): ").strip()
                contracts = float(input("  合约数量: "))
                price = float(input("  开仓价格: "))
                client.futures_open_short_limit(symbol, contracts, price)
            
            elif choice == "9":
                symbol = input("  交易对 (如 BTC/USDT:USDT): ").strip()
                contracts_input = input("  平仓数量 (回车=全部): ").strip()
                contracts = float(contracts_input) if contracts_input else None
                client.futures_close_long(symbol, contracts)
            
            elif choice == "10":
                symbol = input("  交易对 (如 BTC/USDT:USDT): ").strip()
                contracts_input = input("  平仓数量 (回车=全部): ").strip()
                contracts = float(contracts_input) if contracts_input else None
                client.futures_close_short(symbol, contracts)
            
            elif choice == "11":
                confirm = input("  ⚠️ 确认平掉所有持仓? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    client.futures_close_all()
                else:
                    print("  已取消")
            
            elif choice == "12":
                client.show_balance()
            
            elif choice == "13":
                client.show_positions()
            
            elif choice == "14":
                client.show_orders(market_type='spot')
            
            elif choice == "15":
                client.show_orders(market_type='futures')
            
            elif choice == "16":
                confirm = input("  ⚠️ 确认取消所有现货订单? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    client.cancel_all_orders(market_type='spot')
                else:
                    print("  已取消")
            
            elif choice == "17":
                confirm = input("  ⚠️ 确认取消所有合约订单? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    client.cancel_all_orders(market_type='futures')
                else:
                    print("  已取消")
            
            else:
                print("  ❌ 无效选项")
        
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n  ❌ 操作失败: {e}")
            import traceback
            traceback.print_exc()
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    main()

