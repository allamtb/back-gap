"""
Gate.io 账户监控脚本 - 持续监控账户状态

功能：
- 持续监控现货余额
- 持续监控合约余额
- 持续监控合约持仓
- 持续监控未成交订单
- 直接打印原始数据
"""

import time
import json
from datetime import datetime
import ccxt

# ============ 配置区域 ============
API_KEY = "a324a7f1a8b7c3fa9fb6713eaceb666a"
SECRET = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"
PROXY = "http://127.0.0.1:1080"

# 监控间隔（秒）
MONITOR_INTERVAL = 5

# 要监控的交易对（可选，为空则监控所有）
WATCH_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT']
# ===================================


class AccountMonitor:
    """账户监控器 - 直接使用 ccxt"""
    
    def __init__(self, api_key, secret, proxy=None):
        # 初始化现货交易所
        self.spot_exchange = ccxt.gate({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        
        # 初始化合约交易所
        self.futures_exchange = ccxt.gate({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
            }
        })
        
        # 设置代理
        if proxy:
            self.spot_exchange.proxies = {
                'http': proxy,
                'https': proxy
            }
            self.futures_exchange.proxies = {
                'http': proxy,
                'https': proxy
            }
        
        print("\n" + "=" * 70)
        print("  🔍 Gate.io 账户监控已启动")
        print("=" * 70)
        print(f"  监控间隔: {MONITOR_INTERVAL} 秒")
        print(f"  监控交易对: {WATCH_SYMBOLS if WATCH_SYMBOLS else '全部'}")
        print("=" * 70 + "\n")
    
    def format_time(self):
        """格式化当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def check_spot_balance(self):
        """检查现货余额"""
        try:
            print(f"\n[{self.format_time()}] 🔍 现货余额原始数据:")
            balance = self.spot_exchange.fetch_balance()
            # 直接打印原始数据
            print(json.dumps(balance, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"[{self.format_time()}] ❌ 现货余额查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_futures_balance(self):
        """检查合约余额"""
        try:
            # 直接打印原始数据
            print(f"\n[{self.format_time()}] 🔍 合约余额原始数据:")
            balance = self.futures_exchange.fetch_balance({'type': 'swap'})
            print(json.dumps(balance, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"[{self.format_time()}] ❌ 合约余额查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_positions(self):
        """检查合约持仓"""
        try:

            # 直接打印原始数据
            print(f"\n[{self.format_time()}] 🔍 合约持仓原始数据:")
            positions = self.futures_exchange.fetch_positions()
            print(json.dumps(positions, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"[{self.format_time()}] ❌ 持仓查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_spot_orders(self):
        """检查现货未成交订单"""

        print(f"检查现货未成交订单")
        try:
            all_orders = []
            
            # 如果指定了监控交易对，只查询这些
            if WATCH_SYMBOLS:
                for symbol in WATCH_SYMBOLS:
                    if ':USDT' not in symbol:  # 只查询现货
                        try:
                            orders = self.spot_exchange.fetch_open_orders(symbol)
                            all_orders.extend(orders)
                        except Exception as e:
                            print(f"[{self.format_time()}] ⚠️ 查询 {symbol} 现货订单失败: {e}")
            else:
                # 查询所有未成交订单
                all_orders = self.spot_exchange.fetch_open_orders()
            
            # 打印原始数据
            print(f"\n[{self.format_time()}] 🔍 现货订单原始数据 (共 {len(all_orders)} 个):")
            print(json.dumps(all_orders, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"[{self.format_time()}] ❌ 现货订单查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_futures_orders(self):
        """检查合约未成交订单"""

        print(f"检查合约未成交订单")
        try:
            all_orders = []
            
            # 如果指定了监控交易对，只查询这些
            if WATCH_SYMBOLS:
                for symbol in WATCH_SYMBOLS:
                    if ':USDT' in symbol:  # 只查询合约
                        try:
                            orders = self.futures_exchange.fetch_open_orders(symbol)
                            all_orders.extend(orders)
                        except Exception as e:
                            print(f"[{self.format_time()}] ⚠️ 查询 {symbol} 合约订单失败: {e}")
            else:
                # 查询所有未成交订单
                all_orders = self.futures_exchange.fetch_open_orders()
            
            # 打印原始数据
            print(f"\n[{self.format_time()}] 🔍 合约订单原始数据 (共 {len(all_orders)} 个):")
            print(json.dumps(all_orders, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"[{self.format_time()}] ❌ 合约订单查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """运行监控"""
        print("开始监控... (按 Ctrl+C 停止)\n")
        
        try:
            while True:
                # 检查现货余额
                self.check_spot_balance()
                
                # 检查合约余额
                self.check_futures_balance()
                
                # 检查合约持仓
                self.check_positions()
                
                # 检查现货订单
                self.check_spot_orders()
                
                # 检查合约订单
                self.check_futures_orders()
                
                # 等待下次检查
                print(f"\n{'='*70}")
                print(f"等待 {MONITOR_INTERVAL} 秒后继续...")
                print(f"{'='*70}\n")
                time.sleep(MONITOR_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n\n[{self.format_time()}] 监控已停止")
            print("=" * 70)


if __name__ == "__main__":
    # 检查 API 配置
    if API_KEY == "YOUR_API_KEY":
        print("\n❌ 错误: 请先配置你的 API Key 和 Secret!")
        print("请修改文件顶部的 API_KEY 和 SECRET\n")
        exit(1)
    
    # 创建监控器并运行
    monitor = AccountMonitor(API_KEY, SECRET, PROXY)
    monitor.run()
