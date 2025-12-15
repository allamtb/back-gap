"""
币安 PEOPLE 币交易测试工具（GUI版本）

功能：
1. 查看 PEOPLE 币的持仓情况（现货和合约）
2. 查看已关闭订单和未关闭订单
3. 下单买入 PEOPLE（现货和合约）
4. 平仓操作
5. 实时显示账户变化和订单变化

使用方法：
python backend/examples/binance_people_test.py
"""

import ccxt
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, Optional, List
from datetime import datetime
import threading
import time
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BinancePeopleTrading:
    """币安 PEOPLE 币交易客户端"""
    
    def __init__(
        self,
        api_key: str,
        secret: str,
        proxy: Optional[str] = None
    ):
        """
        初始化币安交易客户端
        
        Args:
            api_key: API Key
            secret: API Secret
            proxy: 代理地址，如 "http://127.0.0.1:1080"
        """
        self.api_key = api_key
        self.secret = secret
        self.proxy = proxy
        self.symbol = 'PEOPLE/USDT'  # PEOPLE 交易对
        
        # 初始化现货和合约交易所实例
        self._init_exchanges()
        
        logger.info("✅ 币安客户端初始化成功")
    
    def _init_exchanges(self):
        """初始化现货和合约交易所实例"""
        base_config = {
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'timeout': 30000,
            'options': {
                'warnOnFetchOpenOrdersWithoutSymbol': False,
            }
        }
        
        # 配置代理
        if self.proxy:
            base_config['proxies'] = {
                'http': self.proxy,
                'https': self.proxy
            }
            logger.info(f"🌐 使用代理: {self.proxy}")
        
        # 现货交易所
        spot_config = base_config.copy()
        spot_config['options']['defaultType'] = 'spot'
        self.spot_exchange = ccxt.binance(spot_config)
        
        # 合约交易所
        futures_config = base_config.copy()
        futures_config['options']['defaultType'] = 'future'
        self.futures_exchange = ccxt.binance(futures_config)
        
        # 加载市场数据
        try:
            self.spot_exchange.load_markets()
            self.futures_exchange.load_markets()
            logger.info(f"✅ 市场数据加载成功")
        except Exception as e:
            logger.error(f"❌ 市场数据加载失败: {e}")
    
    # ==================== 查询功能 ====================
    
    def get_spot_balance(self) -> Dict:
        """获取现货余额"""
        # 优先使用直接方法，避免调用可能有权限问题的端点
        try:
            # 方法1: 直接调用账户信息接口（最可靠）
            account = self.spot_exchange.private_get_account()
            if 'balances' in account:
                balance = {'info': account}
                for item in account.get('balances', []):
                    asset = item.get('asset', '')
                    free = float(item.get('free', 0))
                    locked = float(item.get('locked', 0))
                    total = free + locked
                    if total > 0 or asset in ['USDT', 'PEOPLE']:  # 只显示有余额或关注的币种
                        balance[asset] = {
                            'free': free,
                            'used': locked,
                            'total': total
                        }
                return balance
        except Exception as e1:
            error_msg1 = str(e1)
            logger.warning(f"⚠️ 直接方法获取余额失败，尝试标准方法: {error_msg1}")
            
            # 方法2: 使用 ccxt 的标准方法
            try:
                balance = self.spot_exchange.fetch_balance({'type': 'spot'})
                return balance
            except Exception as e2:
                error_msg2 = str(e2)
                error_type = type(e2).__name__
                logger.error(f"❌ 获取现货余额失败 [{error_type}]: {error_msg2}")
                logger.error(f"   方法1错误: {error_msg1}")
                logger.error(f"   方法2错误: {error_msg2}")
                # 返回错误信息
                return {'error': error_msg2, 'error_type': error_type, 'method1_error': error_msg1}
    
    def get_futures_balance(self) -> Dict:
        """获取合约余额"""
        # 优先使用直接方法，避免调用可能有权限问题的端点
        try:
            # 方法1: 直接调用合约账户信息接口（最可靠）
            account = self.futures_exchange.fapiPrivate_get_account()
            if 'assets' in account:
                balance = {'info': account}
                for item in account.get('assets', []):
                    asset = item.get('asset', '')
                    wallet_balance = float(item.get('walletBalance', 0))
                    if wallet_balance > 0 or asset in ['USDT']:  # 只显示有余额或关注的币种
                        balance[asset] = {
                            'free': wallet_balance,
                            'used': 0,
                            'total': wallet_balance
                        }
                return balance
        except Exception as e1:
            error_msg1 = str(e1)
            logger.warning(f"⚠️ 直接方法获取合约余额失败，尝试标准方法: {error_msg1}")
            
            # 方法2: 使用 ccxt 的标准方法
            try:
                balance = self.futures_exchange.fetch_balance({'type': 'future'})
                return balance
            except Exception as e2:
                error_msg2 = str(e2)
                error_type = type(e2).__name__
                logger.error(f"❌ 获取合约余额失败 [{error_type}]: {error_msg2}")
                logger.error(f"   方法1错误: {error_msg1}")
                logger.error(f"   方法2错误: {error_msg2}")
                # 返回错误信息
                return {'error': error_msg2, 'error_type': error_type, 'method1_error': error_msg1}
    
    def get_futures_positions(self) -> List[Dict]:
        """获取合约持仓"""
        try:
            positions = self.futures_exchange.fetch_positions([self.symbol])
            # 只返回有持仓的
            active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            return active_positions
        except Exception as e:
            logger.error(f"❌ 获取合约持仓失败: {e}")
            return []
    
    def get_spot_orders(self, status: str = 'all') -> List[Dict]:
        """
        获取现货订单
        
        Args:
            status: 'open' 未关闭订单, 'closed' 已关闭订单, 'all' 所有订单
        """
        try:
            if status == 'open':
                orders = self.spot_exchange.fetch_open_orders(self.symbol)
            elif status == 'closed':
                orders = self.spot_exchange.fetch_closed_orders(self.symbol, limit=100)
            else:
                open_orders = self.spot_exchange.fetch_open_orders(self.symbol)
                closed_orders = self.spot_exchange.fetch_closed_orders(self.symbol, limit=100)
                orders = open_orders + closed_orders
            
            return orders
        except Exception as e:
            logger.error(f"❌ 获取现货订单失败: {e}")
            return []
    
    def get_futures_orders(self, status: str = 'all') -> List[Dict]:
        """
        获取合约订单
        
        Args:
            status: 'open' 未关闭订单, 'closed' 已关闭订单, 'all' 所有订单
        """
        try:
            if status == 'open':
                orders = self.futures_exchange.fetch_open_orders(self.symbol)
            elif status == 'closed':
                orders = self.futures_exchange.fetch_closed_orders(self.symbol, limit=100)
            else:
                open_orders = self.futures_exchange.fetch_open_orders(self.symbol)
                closed_orders = self.futures_exchange.fetch_closed_orders(self.symbol, limit=100)
                orders = open_orders + closed_orders
            
            return orders
        except Exception as e:
            logger.error(f"❌ 获取合约订单失败: {e}")
            return []
    
    def get_ledger_entries(self, code: str = 'PEOPLE', since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        获取账本条目（使用交易历史模拟账本）
        
        注意：币安的 fetch_ledger 只支持合约账户，不支持现货账户。
        因此使用 fetch_my_trades 获取交易历史，并转换为账本条目格式。
        
        Args:
            code: 币种代码，如 'PEOPLE'
            since: 起始时间戳（毫秒），用于增量查询
            limit: 返回条目数量限制
        
        Returns:
            账本条目列表，按时间倒序排列（最新的在前）
        """
        try:
            # 构造交易对（尝试常见的交易对）
            symbol = None
            possible_symbols = [f'{code}/USDT', f'{code}/BUSD', f'{code}/FDUSD']
            
            for sym in possible_symbols:
                if sym in self.spot_exchange.markets:
                    symbol = sym
                    break
            
            if not symbol:
                logger.warning(f"⚠️ 未找到 {code} 的交易对")
                return []
            
            # 使用 fetch_my_trades 获取交易历史
            trades = self.spot_exchange.fetch_my_trades(symbol, since=since, limit=limit)
            
            # 将交易记录转换为账本条目格式
            ledger_entries = []
            for trade in trades:
                timestamp = trade.get('timestamp', 0)
                side = trade.get('side', '')  # 'buy' 或 'sell'
                amount = trade.get('amount', 0)
                price = trade.get('price', 0)
                cost = trade.get('cost', 0)
                fee = trade.get('fee', {})
                order_id = trade.get('order', '')
                
                # 创建交易条目
                trade_entry = {
                    'id': trade.get('id', ''),
                    'timestamp': timestamp,
                    'datetime': trade.get('datetime', ''),
                    'type': 'trade',
                    'direction': 'in' if side == 'buy' else 'out',
                    'currency': code,
                    'amount': amount if side == 'buy' else -amount,  # 买入为正，卖出为负
                    'fee': fee,
                    'info': trade,
                    'referenceId': order_id,
                    'symbol': symbol,
                    'side': side,
                    'price': price,
                    'cost': cost
                }
                ledger_entries.append(trade_entry)
                
                # 如果有手续费，创建手续费条目
                if fee and fee.get('cost', 0) > 0:
                    fee_entry = {
                        'id': f"{trade.get('id', '')}_fee",
                        'timestamp': timestamp,  # 手续费时间与交易时间相同
                        'datetime': trade.get('datetime', ''),
                        'type': 'fee',
                        'direction': 'out',
                        'currency': fee.get('currency', 'USDT'),
                        'amount': -abs(fee.get('cost', 0)),  # 手续费总是负数
                        'fee': None,
                        'info': trade,
                        'referenceId': order_id,
                        'symbol': symbol
                    }
                    ledger_entries.append(fee_entry)
            
            # 按时间戳倒序排列（最新的在前）
            ledger_entries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            return ledger_entries
            
        except Exception as e:
            error_msg = str(e)
            # 如果是权限错误，给出更友好的提示
            if 'permission' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                logger.error(f"❌ 获取交易历史失败: API Key 可能没有读取交易历史的权限")
            else:
                logger.error(f"❌ 获取账本条目失败: {e}")
            return []
    
    # ==================== 交易功能 ====================
    
    def spot_buy(self, amount: float, price: Optional[float] = None) -> Dict:
        """
        现货买入 PEOPLE
        
        注意：此方法按 PEOPLE 数量（基础货币数量）买入，而不是按 USDT 金额买入。
        例如：amount=1000 表示买入 1000 个 PEOPLE，实际花费的 USDT 金额 = 1000 * 当前市价。
        
        如果需要按 USDT 金额买入，需要使用 quoteOrderQty 参数，但本方法不支持此功能。
        
        Args:
            amount: PEOPLE 数量（基础货币数量），不是 USDT 金额
            price: 价格（不指定则市价买入）
        
        Returns:
            订单信息
        """
        try:
            if price is None:
                # 市价买入：按 PEOPLE 数量买入
                # 注意：create_market_buy_order 的 amount 参数是基础货币（PEOPLE）的数量
                # 不使用 quoteOrderQty 参数，确保按数量买入而不是按 USDT 金额买入
                logger.info(f"📝 现货市价买入: {self.symbol} 数量={amount} PEOPLE（按数量买入，非按 USDT 金额）")
                order = self.spot_exchange.create_market_buy_order(self.symbol, amount)
            else:
                # 限价买入：按 PEOPLE 数量买入
                logger.info(f"📝 现货限价买入: {self.symbol} 数量={amount} PEOPLE 价格={price} USDT（按数量买入，非按 USDT 金额）")
                order = self.spot_exchange.create_limit_buy_order(self.symbol, amount, price)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 现货买入失败: {e}")
            raise
    
    def spot_close(self, amount: Optional[float] = None, price: Optional[float] = None) -> Dict:
        """
        现货平仓（卖出 PEOPLE）
        
        注意：此方法按 PEOPLE 数量（基础货币数量）卖出。
        例如：amount=1000 表示卖出 1000 个 PEOPLE，实际获得的 USDT 金额 = 1000 * 当前市价。
        
        Args:
            amount: PEOPLE 数量（基础货币数量），不指定则查询余额后全部卖出
            price: 价格（不指定则市价卖出）
        
        Returns:
            订单信息
        """
        try:
            # 如果没有指定数量，查询余额
            if amount is None:
                balance = self.get_spot_balance()
                if 'error' in balance:
                    raise ValueError(f"无法获取余额: {balance.get('error')}")
                
                people_balance = balance.get('PEOPLE', {})
                amount = float(people_balance.get('free', 0))
                
                if amount == 0:
                    raise ValueError("PEOPLE 余额为 0，无法平仓")
                
                logger.info(f"📊 查询到可用 PEOPLE 余额: {amount}")
            
            if amount <= 0:
                raise ValueError(f"卖出数量必须大于 0，当前: {amount}")
            
            if price is None:
                # 市价卖出：按 PEOPLE 数量卖出
                logger.info(f"📝 现货市价卖出: {self.symbol} 数量={amount} PEOPLE（按数量卖出）")
                order = self.spot_exchange.create_market_sell_order(self.symbol, amount)
            else:
                # 限价卖出：按 PEOPLE 数量卖出
                logger.info(f"📝 现货限价卖出: {self.symbol} 数量={amount} PEOPLE 价格={price} USDT（按数量卖出）")
                order = self.spot_exchange.create_limit_sell_order(self.symbol, amount, price)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 现货平仓失败: {e}")
            raise
    
    def futures_long(self, amount: float, price: Optional[float] = None) -> Dict:
        """
        合约做多（开多仓）
        
        Args:
            amount: 合约数量（张数）
            price: 价格（不指定则市价开仓）
        
        Returns:
            订单信息
        
        Note:
            - 币安合约最小名义价值为 5 USDT
            - 名义价值 = 合约数量 × 价格
            - 如果名义价值 < 5 USDT，订单将被拒绝
        """
        try:
            # 获取用于计算名义价值的价格
            notional_price = price
            if notional_price is None:
                # 市价单：获取当前价格来计算名义价值
                try:
                    ticker = self.futures_exchange.fetch_ticker(self.symbol)
                    notional_price = ticker.get('last') or ticker.get('ask')  # 使用最新价或卖一价
                    logger.info(f"📊 当前价格: {notional_price} USDT（用于计算名义价值）")
                except Exception as e:
                    logger.warning(f"⚠️ 无法获取当前价格，跳过名义价值检查: {e}")
                    notional_price = None
            
            # 检查名义价值（如果能够获取价格）
            if notional_price is not None:
                notional_value = amount * notional_price
                min_notional = 5.0  # 币安最小名义价值
                
                if notional_value < min_notional:
                    error_msg = (
                        f"订单名义价值不足！\n"
                        f"当前名义价值: {notional_value:.4f} USDT\n"
                        f"最小要求: {min_notional} USDT\n"
                        f"建议: 至少需要 {min_notional / notional_price:.2f} 张合约"
                    )
                    logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)
                
                logger.info(f"✅ 名义价值检查通过: {notional_value:.4f} USDT (数量={amount} × 价格={notional_price})")
            
            # 执行下单
            # 注意：如果账户是双向持仓模式（Hedge Mode），需要指定 positionSide
            # 如果账户是单向持仓模式（One-way Mode），指定 positionSide 会被忽略，不会报错
            params = {'positionSide': 'LONG'}  # 做多时使用 LONG
            
            if price is None:
                logger.info(f"📝 合约市价做多: {self.symbol} 数量={amount} 张")
                order = self.futures_exchange.create_market_buy_order(self.symbol, amount, params)
            else:
                logger.info(f"📝 合约限价做多: {self.symbol} 数量={amount} 张 价格={price}")
                order = self.futures_exchange.create_limit_buy_order(self.symbol, amount, price, params)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except ValueError:
            # 重新抛出 ValueError（名义价值不足）
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 合约做多失败: {e}")
            
            # 检查是否是保证金不足错误
            if "-2019" in error_msg or "Margin is insufficient" in error_msg or "margin" in error_msg.lower():
                # 尝试获取账户余额信息
                try:
                    balance = self.get_futures_balance()
                    if balance and 'USDT' in balance.get('total', {}):
                        available = balance.get('USDT', {}).get('free', 0)
                        total = balance.get('USDT', {}).get('total', 0)
                        used = balance.get('USDT', {}).get('used', 0)
                        
                        # 计算所需保证金（估算）
                        required_margin = amount * (notional_price or 0) if notional_price else None
                        
                        error_detail = (
                            f"保证金不足！\n\n"
                            f"错误码: -2019\n"
                            f"可用保证金: {available:.4f} USDT\n"
                            f"已用保证金: {used:.4f} USDT\n"
                            f"总保证金: {total:.4f} USDT"
                        )
                        if required_margin:
                            error_detail += f"\n\n所需保证金（估算）: {required_margin:.4f} USDT"
                        error_detail += "\n\n请减少合约数量或增加账户保证金后再试。"
                        
                        raise ValueError(error_detail)
                except Exception as balance_error:
                    logger.warning(f"⚠️ 获取账户余额失败: {balance_error}")
                
                # 如果获取余额失败，仍然抛出友好的错误信息
                raise ValueError(
                    f"保证金不足！\n\n"
                    f"错误码: -2019\n"
                    f"账户可用保证金不足以支持此次开仓。\n\n"
                    f"请减少合约数量或增加账户保证金后再试。"
                )
            
            raise
    
    def futures_close(self, side: str, amount: Optional[float] = None) -> Dict:
        """
        合约平仓
        
        Args:
            side: 平仓方向 ('long' 平多仓, 'short' 平空仓)
            amount: 平仓数量（不指定则查询持仓后全部平仓）
        
        Returns:
            订单信息
        """
        try:
            # 如果没有指定数量，查询持仓
            if amount is None:
                positions = self.get_futures_positions()
                position = None
                for pos in positions:
                    if pos.get('side') == side:
                        position = pos
                        break
                
                if not position:
                    raise ValueError(f"未找到 {side} 持仓")
                
                amount = abs(float(position.get('contracts', 0)))
                if amount == 0:
                    raise ValueError(f"持仓数量为0")
            
            # 平仓方向相反：平多仓用卖，平空仓用买
            # 注意：如果账户是双向持仓模式（Hedge Mode），需要指定 positionSide
            if side == 'long':
                logger.info(f"📝 合约平多仓: {self.symbol} 数量={amount}")
                params = {'positionSide': 'LONG'}  # 平多仓时使用 LONG
                order = self.futures_exchange.create_market_sell_order(self.symbol, amount, params)
            elif side == 'short':
                logger.info(f"📝 合约平空仓: {self.symbol} 数量={amount}")
                params = {'positionSide': 'SHORT'}  # 平空仓时使用 SHORT
                order = self.futures_exchange.create_market_buy_order(self.symbol, amount, params)
            else:
                raise ValueError(f"无效的平仓方向: {side}，应为 'long' 或 'short'")
            
            logger.info(f"✅ 平仓订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 合约平仓失败: {e}")
            raise


class BinancePeopleGUI:
    """币安 PEOPLE 交易 GUI"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("币安 PEOPLE 币交易测试工具")
        self.root.geometry("1400x900")
        
        # API 配置
        self.api_key = "ZXoTmFIgKcBCxeMCGDW0Fyth1OgEKBaVZ1o8IxdvNHYQ2iI2y4FxVyHW0WfhpZjw"
        self.secret = "WaFESAtZzJfDBYzR6In2bHXySOpDkXqLkHuAnLaursjDzcp0cz3poSEWBWfWpCcP"
        # 代理将在GUI中配置
        
        # 交易客户端
        self.client = None
        self.refresh_thread = None
        self.is_refreshing = False
        self.is_connecting = False  # 添加连接状态标志
        
        # 余额和订单监控
        self.last_balance = None  # 上次余额记录
        self.monitored_orders = {}  # 监控的订单 {order_id: order_info}
        self.order_monitor_thread = None  # 订单监控线程
        self.is_monitoring_orders = False  # 是否正在监控订单
        
        # 账本监控
        self.last_ledger_timestamp = None  # 最后查询的账本时间戳（毫秒）
        self.ledger_monitor_thread = None  # 账本监控线程
        self.is_monitoring_ledger = False  # 是否正在监控账本
        
        # 创建界面
        self._create_widgets()
        
        # 延迟连接客户端（让GUI先显示）
        self.root.after(100, self._connect)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding="10")
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="刷新数据", command=self._refresh_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="开始自动刷新", command=self._start_auto_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="停止自动刷新", command=self._stop_auto_refresh).pack(side=tk.LEFT, padx=5)
        
        # ========== API配置区域 ==========
        config_frame = ttk.LabelFrame(self.root, text="API配置", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 代理配置
        proxy_frame = ttk.Frame(config_frame)
        proxy_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(proxy_frame, text="代理地址:").pack(side=tk.LEFT, padx=5)
        self.proxy_entry = ttk.Entry(proxy_frame, width=40)
        self.proxy_entry.pack(side=tk.LEFT, padx=5)
        self.proxy_entry.insert(0, "http://127.0.0.1:1080")  # 默认使用本地代理
        ttk.Label(proxy_frame, text="(留空=不使用代理，格式: http://127.0.0.1:1080)").pack(side=tk.LEFT, padx=5)
        
        self.reconnect_btn = ttk.Button(proxy_frame, text="重新连接", command=self._reconnect)
        self.reconnect_btn.pack(side=tk.LEFT, padx=10)
        
        # 主容器（左右分栏）
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：持仓和订单信息
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 右侧：交易操作和日志
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # ========== 左侧内容 ==========
        
        # 现货持仓
        spot_balance_frame = ttk.LabelFrame(left_frame, text="现货持仓 (PEOPLE)", padding="10")
        spot_balance_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.spot_balance_text = scrolledtext.ScrolledText(spot_balance_frame, height=5, wrap=tk.WORD)
        self.spot_balance_text.pack(fill=tk.BOTH, expand=True)
        
        # 合约持仓
        futures_positions_frame = ttk.LabelFrame(left_frame, text="合约持仓 (PEOPLE)", padding="10")
        futures_positions_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.futures_positions_text = scrolledtext.ScrolledText(futures_positions_frame, height=5, wrap=tk.WORD)
        self.futures_positions_text.pack(fill=tk.BOTH, expand=True)
        
        # 未关闭订单
        open_orders_frame = ttk.LabelFrame(left_frame, text="未关闭订单", padding="10")
        open_orders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.open_orders_text = scrolledtext.ScrolledText(open_orders_frame, height=10, wrap=tk.WORD)
        self.open_orders_text.pack(fill=tk.BOTH, expand=True)
        
        # 已关闭订单
        closed_orders_frame = ttk.LabelFrame(left_frame, text="已关闭订单 (最近20条)", padding="10")
        closed_orders_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        self.closed_orders_text = scrolledtext.ScrolledText(closed_orders_frame, height=10, wrap=tk.WORD)
        self.closed_orders_text.pack(fill=tk.BOTH, expand=True)
        
        # 账本变化日志（PEOPLE交易）
        balance_change_frame = ttk.LabelFrame(left_frame, text="账本变化（PEOPLE交易）", padding="10")
        balance_change_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        self.balance_change_text = scrolledtext.ScrolledText(balance_change_frame, height=8, wrap=tk.WORD)
        self.balance_change_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置账本变化文本颜色
        self.balance_change_text.tag_config("increase", foreground="green")
        self.balance_change_text.tag_config("decrease", foreground="red")
        self.balance_change_text.tag_config("info", foreground="blue")
        self.balance_change_text.tag_config("trade", foreground="green")
        self.balance_change_text.tag_config("fee", foreground="orange")
        self.balance_change_text.tag_config("error", foreground="red")
        
        # ========== 右侧内容 ==========
        
        # 交易操作
        trading_frame = ttk.LabelFrame(right_frame, text="交易操作", padding="10")
        trading_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 现货买入
        spot_buy_frame = ttk.Frame(trading_frame)
        spot_buy_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(spot_buy_frame, text="现货买入:").pack(side=tk.LEFT, padx=5)
        self.spot_amount_entry = ttk.Entry(spot_buy_frame, width=15)
        self.spot_amount_entry.pack(side=tk.LEFT, padx=5)
        self.spot_amount_entry.insert(0, "100")
        ttk.Label(spot_buy_frame, text="PEOPLE").pack(side=tk.LEFT, padx=5)
        
        self.spot_price_entry = ttk.Entry(spot_buy_frame, width=15)
        self.spot_price_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(spot_buy_frame, text="价格(留空=市价)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(spot_buy_frame, text="买入", command=self._spot_buy).pack(side=tk.LEFT, padx=5)
        
        # 现货平仓（卖出）
        spot_close_frame = ttk.Frame(trading_frame)
        spot_close_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(spot_close_frame, text="现货平仓:").pack(side=tk.LEFT, padx=5)
        self.spot_close_amount_entry = ttk.Entry(spot_close_frame, width=15)
        self.spot_close_amount_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(spot_close_frame, text="PEOPLE(留空=全部)").pack(side=tk.LEFT, padx=5)
        
        self.spot_close_price_entry = ttk.Entry(spot_close_frame, width=15)
        self.spot_close_price_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(spot_close_frame, text="价格(留空=市价)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(spot_close_frame, text="卖出", command=self._spot_close).pack(side=tk.LEFT, padx=5)
        
        # 合约做多
        futures_long_frame = ttk.Frame(trading_frame)
        futures_long_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(futures_long_frame, text="合约做多:").pack(side=tk.LEFT, padx=5)
        self.futures_amount_entry = ttk.Entry(futures_long_frame, width=15)
        self.futures_amount_entry.pack(side=tk.LEFT, padx=5)
        self.futures_amount_entry.insert(0, "10")
        ttk.Label(futures_long_frame, text="张").pack(side=tk.LEFT, padx=5)
        
        self.futures_price_entry = ttk.Entry(futures_long_frame, width=15)
        self.futures_price_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(futures_long_frame, text="价格(留空=市价)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(futures_long_frame, text="做多", command=self._futures_long).pack(side=tk.LEFT, padx=5)
        
        # 添加最小名义价值提示
        hint_label = ttk.Label(futures_long_frame, text="⚠️ 最小名义价值: 5 USDT", foreground="gray")
        hint_label.pack(side=tk.LEFT, padx=10)
        
        # 平仓操作
        close_frame = ttk.Frame(trading_frame)
        close_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(close_frame, text="平仓:").pack(side=tk.LEFT, padx=5)
        self.close_side_var = tk.StringVar(value="long")
        ttk.Radiobutton(close_frame, text="平多仓", variable=self.close_side_var, value="long").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(close_frame, text="平空仓", variable=self.close_side_var, value="short").pack(side=tk.LEFT, padx=5)
        
        self.close_amount_entry = ttk.Entry(close_frame, width=15)
        self.close_amount_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(close_frame, text="数量(留空=全部)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(close_frame, text="平仓", command=self._futures_close).pack(side=tk.LEFT, padx=5)
        
        # 订单实时变化消息
        order_monitor_frame = ttk.LabelFrame(right_frame, text="PEOPLE 订单实时变化", padding="10")
        order_monitor_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.order_monitor_text = scrolledtext.ScrolledText(order_monitor_frame, height=8, wrap=tk.WORD)
        self.order_monitor_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置订单监控文本颜色
        self.order_monitor_text.tag_config("new", foreground="blue")
        self.order_monitor_text.tag_config("filled", foreground="green")
        self.order_monitor_text.tag_config("partial", foreground="orange")
        self.order_monitor_text.tag_config("canceled", foreground="red")
        self.order_monitor_text.tag_config("error", foreground="red")
        self.order_monitor_text.tag_config("info", foreground="black")
        
        # 日志区域
        log_frame = ttk.LabelFrame(right_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志文本颜色
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
    
    def _connect(self):
        """连接币安API（在后台线程中执行，避免阻塞GUI）"""
        if self.is_connecting:
            self._log("⚠️ 正在连接中，请稍候...", "warning")
            return
        
        self.is_connecting = True
        self.reconnect_btn.config(state='disabled')  # 禁用按钮
        
        def connect_thread():
            try:
                # 从输入框获取代理地址
                proxy_str = self.proxy_entry.get().strip()
                proxy = proxy_str if proxy_str else None
                
                # 在主线程更新日志
                if proxy:
                    self.root.after(0, lambda: self._log(f"🌐 使用代理: {proxy}", "info"))
                else:
                    self.root.after(0, lambda: self._log("🌐 不使用代理", "info"))
                
                self.root.after(0, lambda: self._log("正在连接币安API...", "info"))
                
                # 在后台线程中创建客户端（这里会阻塞，但不影响GUI）
                client = BinancePeopleTrading(self.api_key, self.secret, proxy)
                
                # 连接成功后，在主线程更新
                self.root.after(0, lambda: self._log("✅ 连接成功！", "success"))
                self.root.after(0, lambda: setattr(self, 'client', client))
                self.root.after(0, self._refresh_all)
                # 启动订单监控
                self.root.after(0, self._start_order_monitoring)
                # 启动账本监控
                self.root.after(0, self._start_ledger_monitoring)
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"❌ 连接失败: {error_msg}", "error"))
                logger.error(f"连接失败: {error_msg}", exc_info=True)
                self.root.after(0, lambda: messagebox.showerror(
                    "连接失败", 
                    f"无法连接到币安API:\n{error_msg}\n\n请检查:\n1. API Key 和 Secret 是否正确\n2. 网络连接是否正常\n3. 是否需要配置代理"
                ))
            finally:
                self.is_connecting = False
                self.root.after(0, lambda: self.reconnect_btn.config(state='normal'))
        
        # 在后台线程中执行连接
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _reconnect(self):
        """重新连接（使用新的代理配置）"""
        if self.client:
            # 停止自动刷新
            if self.is_refreshing:
                self._stop_auto_refresh()
            
            # 停止订单监控
            self.is_monitoring_orders = False
            self.monitored_orders.clear()
            
            # 停止账本监控
            self.is_monitoring_ledger = False
            self.last_ledger_timestamp = None
            
            self._log("🔄 正在重新连接...", "info")
            self.client = None  # 清除旧连接
        
        # 延迟连接，确保界面更新
        self.root.after(100, self._connect)
    
    def _log(self, message: str, tag: str = "info"):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
    
    def _refresh_all(self):
        """刷新所有数据（在后台线程中执行，避免阻塞GUI）"""
        if not self.client:
            self._log("❌ 客户端未连接", "error")
            return
        
        def refresh_thread():
            try:
                self.root.after(0, lambda: self._log("🔄 正在刷新数据...", "info"))
                
                # 在后台线程中获取数据
                spot_balance = self.client.get_spot_balance()
                positions = self.client.get_futures_positions()
                spot_open = self.client.get_spot_orders('open')
                futures_open = self.client.get_futures_orders('open')
                spot_closed = self.client.get_spot_orders('closed')
                futures_closed = self.client.get_futures_orders('closed')
                
                # 处理数据
                if 'error' in spot_balance:
                    spot_text = f"❌ 获取失败: {spot_balance.get('error', '未知错误')}\n"
                    spot_text += f"错误类型: {spot_balance.get('error_type', 'Unknown')}\n"
                    spot_text += "提示: 请检查API权限，确保有读取账户信息的权限"
                else:
                    people_spot = spot_balance.get('PEOPLE', {})
                    usdt_spot = spot_balance.get('USDT', {})
                    if people_spot or usdt_spot:
                        spot_text = f"PEOPLE: {people_spot.get('total', 0):.8f} (可用: {people_spot.get('free', 0):.8f}, 冻结: {people_spot.get('used', 0):.8f})\n"
                        spot_text += f"USDT: {usdt_spot.get('total', 0):.2f} (可用: {usdt_spot.get('free', 0):.2f})"
                    else:
                        spot_text = "无持仓数据"
                
                positions_text = ""
                if positions:
                    for pos in positions:
                        side = pos.get('side', 'unknown')
                        contracts = pos.get('contracts', 0)
                        entry_price = pos.get('entryPrice', 0)
                        mark_price = pos.get('markPrice', 0)
                        unrealized_pnl = pos.get('unrealizedPnl', 0)
                        positions_text += f"{side.upper()}: {contracts} 张, 开仓价: {entry_price}, 标记价: {mark_price}, 未实现盈亏: {unrealized_pnl:.2f} USDT\n"
                else:
                    positions_text = "无持仓"
                
                all_open = spot_open + futures_open
                open_text = ""
                if all_open:
                    for order in all_open[:20]:
                        symbol = order.get('symbol', '')
                        side = order.get('side', '')
                        type_str = order.get('type', '')
                        amount = order.get('amount', 0)
                        price = order.get('price', 'market')
                        status = order.get('status', '')
                        order_id = order.get('id', '')
                        open_text += f"[{symbol}] {side} {type_str} {amount} @ {price} - {status} (ID: {order_id})\n"
                else:
                    open_text = "无未关闭订单"
                
                all_closed = spot_closed + futures_closed
                all_closed.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                
                closed_text = ""
                if all_closed:
                    for order in all_closed[:20]:
                        symbol = order.get('symbol', '')
                        side = order.get('side', '')
                        type_str = order.get('type', '')
                        amount = order.get('amount', 0)
                        filled = order.get('filled', 0)
                        price = order.get('price', 'market')
                        status = order.get('status', '')
                        order_id = order.get('id', '')
                        timestamp = order.get('timestamp', 0)
                        if timestamp:
                            dt = datetime.fromtimestamp(timestamp / 1000)
                            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            time_str = "未知"
                        closed_text += f"[{time_str}] [{symbol}] {side} {type_str} {filled}/{amount} @ {price} - {status} (ID: {order_id})\n"
                else:
                    closed_text = "无已关闭订单"
                
                # 在主线程中更新GUI
                def update_gui():
                    self.spot_balance_text.delete(1.0, tk.END)
                    self.spot_balance_text.insert(1.0, spot_text)
                    self.futures_positions_text.delete(1.0, tk.END)
                    self.futures_positions_text.insert(1.0, positions_text)
                    self.open_orders_text.delete(1.0, tk.END)
                    self.open_orders_text.insert(1.0, open_text)
                    self.closed_orders_text.delete(1.0, tk.END)
                    self.closed_orders_text.insert(1.0, closed_text)
                    self._log("✅ 数据刷新完成", "success")
                
                self.root.after(0, update_gui)
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"❌ 刷新数据失败: {error_msg}", "error"))
                logger.error(f"刷新数据失败: {error_msg}", exc_info=True)
        
        # 在后台线程中执行刷新
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def _start_auto_refresh(self):
        """开始自动刷新"""
        if self.is_refreshing:
            self._log("⚠️ 自动刷新已在运行", "warning")
            return
        
        self.is_refreshing = True
        self._log("🔄 开始自动刷新（每5秒）", "info")
        
        def refresh_loop():
            while self.is_refreshing:
                try:
                    self.root.after(0, self._refresh_all)
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"自动刷新错误: {e}")
        
        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
    
    def _stop_auto_refresh(self):
        """停止自动刷新"""
        if not self.is_refreshing:
            self._log("⚠️ 自动刷新未运行", "warning")
            return
        
        self.is_refreshing = False
        self._log("⏹️ 停止自动刷新", "info")
    
    def _log_balance_change(self, message: str, tag: str = "info"):
        """记录余额变化日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.balance_change_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.balance_change_text.see(tk.END)
    
    def _log_order_change(self, message: str, tag: str = "info"):
        """记录订单变化日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.order_monitor_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.order_monitor_text.see(tk.END)
    
    def _compare_and_show_balance_change(self, balance_before: Dict, balance_after: Dict, order_id: str):
        """对比并显示余额变化"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 检查是否有错误
            if 'error' in balance_before or 'error' in balance_after:
                error_msg = "余额查询失败，无法对比变化"
                if 'error' in balance_before:
                    error_msg += f" (买入前: {balance_before.get('error', '')})"
                if 'error' in balance_after:
                    error_msg += f" (买入后: {balance_after.get('error', '')})"
                self._log_balance_change(f"❌ {error_msg}", "error")
                return
            
            # 对比 PEOPLE 余额
            people_before = balance_before.get('PEOPLE', {})
            people_after = balance_after.get('PEOPLE', {})
            
            people_before_total = people_before.get('total', 0)
            people_after_total = people_after.get('total', 0)
            people_change = people_after_total - people_before_total
            
            # 对比 USDT 余额
            usdt_before = balance_before.get('USDT', {})
            usdt_after = balance_after.get('USDT', {})
            
            usdt_before_total = usdt_before.get('total', 0)
            usdt_after_total = usdt_after.get('total', 0)
            usdt_change = usdt_after_total - usdt_before_total
            
            # 显示余额变化
            self._log_balance_change(f"\n{'='*50}", "info")
            self._log_balance_change(f"📊 订单 {order_id} 余额变化对比", "info")
            self._log_balance_change(f"{'='*50}", "info")
            
            # PEOPLE 余额变化
            if abs(people_change) > 0.00000001:  # 避免浮点数精度问题
                tag = "increase" if people_change > 0 else "decrease"
                self._log_balance_change(
                    f"PEOPLE: {people_before_total:.8f} → {people_after_total:.8f} "
                    f"({'+' if people_change > 0 else ''}{people_change:.8f})",
                    tag
                )
            else:
                self._log_balance_change(
                    f"PEOPLE: {people_before_total:.8f} → {people_after_total:.8f} (无变化)",
                    "info"
                )
            
            # USDT 余额变化
            if abs(usdt_change) > 0.01:  # 避免浮点数精度问题
                tag = "increase" if usdt_change > 0 else "decrease"
                self._log_balance_change(
                    f"USDT: {usdt_before_total:.2f} → {usdt_after_total:.2f} "
                    f"({'+' if usdt_change > 0 else ''}{usdt_change:.2f})",
                    tag
                )
            else:
                self._log_balance_change(
                    f"USDT: {usdt_before_total:.2f} → {usdt_after_total:.2f} (无变化)",
                    "info"
                )
            
            self._log_balance_change(f"{'='*50}\n", "info")
            
        except Exception as e:
            logger.error(f"对比余额变化失败: {e}", exc_info=True)
            self._log_balance_change(f"❌ 对比余额变化失败: {e}", "error")
    
    def _start_order_monitoring(self):
        """启动订单监控"""
        if self.is_monitoring_orders:
            return
        
        if not self.client:
            return
        
        self.is_monitoring_orders = True
        self._log_order_change("🔄 开始监控 PEOPLE 订单状态变化...", "info")
        
        def monitor_loop():
            while self.is_monitoring_orders and self.client:
                try:
                    # 检查每个监控的订单
                    orders_to_remove = []
                    
                    for order_id, order_info in list(self.monitored_orders.items()):
                        try:
                            # 查询订单最新状态
                            symbol = order_info.get('symbol', 'PEOPLE/USDT')
                            
                            # 尝试获取订单详情
                            try:
                                # 先尝试从现货订单中查找
                                spot_orders = self.client.get_spot_orders('all')
                                current_order = None
                                
                                for o in spot_orders:
                                    if str(o.get('id')) == str(order_id):
                                        current_order = o
                                        break
                                
                                if not current_order:
                                    # 如果找不到，可能订单已关闭，从已关闭订单中查找
                                    continue
                                
                                # 检查状态变化
                                last_status = order_info.get('last_status')
                                current_status = current_order.get('status', 'unknown')
                                last_filled = order_info.get('last_filled', 0)
                                current_filled = current_order.get('filled', 0)
                                
                                # 状态变化
                                if current_status != last_status:
                                    status_map = {
                                        'open': '待成交',
                                        'closed': '已成交',
                                        'canceled': '已取消',
                                        'expired': '已过期',
                                        'rejected': '已拒绝'
                                    }
                                    status_text = status_map.get(current_status, current_status)
                                    
                                    tag = "filled" if current_status == 'closed' else "canceled" if current_status == 'canceled' else "info"
                                    # 使用默认参数捕获变量值，避免闭包问题
                                    oid_str = str(order_id)
                                    self.root.after(0, lambda oid=oid_str, st=status_text, t=tag: 
                                        self._log_order_change(f"📋 订单 {oid} 状态变化: {st}", t))
                                    
                                    order_info['last_status'] = current_status
                                
                                # 成交数量变化
                                if abs(current_filled - last_filled) > 0.00000001:
                                    filled_change = current_filled - last_filled
                                    order_amount = current_order.get('amount', 0)
                                    tag = "filled" if current_filled >= order_amount * 0.99 else "partial"
                                    # 使用默认参数捕获变量值，避免闭包问题
                                    oid_str = str(order_id)
                                    self.root.after(0, lambda oid=oid_str, fc=filled_change, cf=current_filled, amt=order_amount, t=tag:
                                        self._log_order_change(
                                            f"📈 订单 {oid} 成交更新: +{fc:.8f} PEOPLE (已成交: {cf:.8f}/{amt:.8f})",
                                            t
                                        ))
                                    
                                    order_info['last_filled'] = current_filled
                                
                                # 如果订单已关闭，从监控列表中移除
                                if current_status in ['closed', 'canceled', 'expired', 'rejected']:
                                    orders_to_remove.append(order_id)
                                
                            except Exception as e:
                                logger.debug(f"查询订单 {order_id} 状态失败: {e}")
                                
                        except Exception as e:
                            logger.error(f"监控订单 {order_id} 时出错: {e}")
                    
                    # 移除已关闭的订单
                    for order_id in orders_to_remove:
                        if order_id in self.monitored_orders:
                            del self.monitored_orders[order_id]
                    
                    # 每3秒检查一次
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"订单监控循环错误: {e}")
                    time.sleep(3)
        
        self.order_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.order_monitor_thread.start()
    
    def _log_ledger_entry(self, entry: Dict):
        """
        格式化并显示账本条目
        
        Args:
            entry: 账本条目字典
        """
        try:
            timestamp = entry.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "未知时间"
            
            entry_type = entry.get('type', '').lower()
            direction = entry.get('direction', '')
            amount = entry.get('amount', 0)
            currency = entry.get('currency', '')
            before = entry.get('before', None)
            after = entry.get('after', None)
            reference_id = entry.get('referenceId', '')
            fee = entry.get('fee', {})
            
            # 构建显示文本
            if entry_type == 'trade':
                # 交易类型
                side = entry.get('side', '')  # 'buy' 或 'sell'
                direction_text = "买入" if side == 'buy' else "卖出"
                direction_emoji = "📈" if side == 'buy' else "📉"
                tag = "trade"
                
                # 获取价格和成本信息
                price = entry.get('price', 0)
                cost = entry.get('cost', 0)
                symbol = entry.get('symbol', '')
                
                text = f"[{time_str}] {direction_emoji} 交易 | {direction_text} | "
                if amount > 0:
                    text += f"+{abs(amount):.8f}" if side == 'buy' else f"-{abs(amount):.8f}"
                else:
                    text += f"{amount:.8f}"
                text += f" {currency}"
                
                # 显示价格和成本
                if price > 0:
                    text += f" @ {price:.8f}"
                if cost > 0:
                    # 确定成本币种（通常是交易对的报价币种）
                    if symbol:
                        quote_currency = symbol.split('/')[-1] if '/' in symbol else 'USDT'
                        text += f" | 成本: {cost:.8f} {quote_currency}"
                
                # 显示余额变化
                if before is not None and after is not None:
                    text += f" | 余额: {before:.8f} → {after:.8f}"
                
                # 显示关联订单ID
                if reference_id:
                    text += f" | 订单ID: {reference_id}"
                
                # 显示手续费（如果有，但手续费会单独显示为一条记录）
                if fee and fee.get('cost', 0) != 0:
                    fee_cost = fee.get('cost', 0)
                    fee_currency = fee.get('currency', '')
                    text += f" | 手续费: {fee_cost:.8f} {fee_currency}"
                
            elif entry_type == 'fee':
                # 手续费类型
                tag = "fee"
                fee_cost = fee.get('cost', 0) if fee else amount
                fee_currency = fee.get('currency', '') if fee else currency
                
                text = f"[{time_str}] 💰 手续费 | 支出 | -{abs(fee_cost):.8f} {fee_currency}"
                
                # 显示余额变化
                if before is not None and after is not None:
                    text += f" | 余额: {before:.8f} → {after:.8f}"
                
                # 显示关联订单ID
                if reference_id:
                    text += f" | 订单ID: {reference_id}"
            else:
                # 其他类型
                tag = "info"
                text = f"[{time_str}] 📊 {entry_type} | {direction} | {amount:.8f} {currency}"
            
            # 在主线程中更新GUI（使用默认参数避免闭包问题）
            self.root.after(0, lambda t=text, g=tag: self._log_balance_change(t, g))
            
        except Exception as e:
            logger.error(f"格式化账本条目失败: {e}", exc_info=True)
            error_text = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ 账本条目解析失败: {e}"
            self.root.after(0, lambda et=error_text: self._log_balance_change(et, "error"))
    
    def _start_ledger_monitoring(self):
        """启动账本监控"""
        if self.is_monitoring_ledger:
            return
        
        if not self.client:
            return
        
        self.is_monitoring_ledger = True
        self._log_balance_change("🔄 开始监控 PEOPLE 账本变化...", "info")
        
        def monitor_loop():
            while self.is_monitoring_ledger and self.client:
                try:
                    # 首次查询：获取最近100条交易记录
                    if self.last_ledger_timestamp is None:
                        entries = self.client.get_ledger_entries('PEOPLE', since=None, limit=100)
                        if entries:
                            # 记录最新时间戳（第一条是最新的）
                            self.last_ledger_timestamp = entries[0].get('timestamp', 0)
                            # 显示最近的条目（最多显示10条）
                            for entry in entries[:10]:
                                self._log_ledger_entry(entry)
                            self.root.after(0, lambda: self._log_balance_change(
                                f"✅ 已加载 {len(entries)} 条历史交易记录", "info"
                            ))
                        else:
                            # 没有找到交易记录
                            self.root.after(0, lambda: self._log_balance_change(
                                f"ℹ️ 未找到 PEOPLE 交易历史记录", "info"
                            ))
                            # 设置一个初始时间戳，避免重复查询
                            self.last_ledger_timestamp = int(time.time() * 1000)
                    else:
                        # 增量查询：只获取新条目
                        entries = self.client.get_ledger_entries(
                            'PEOPLE', 
                            since=self.last_ledger_timestamp + 1,  # +1 避免重复
                            limit=50
                        )
                        
                        if entries:
                            # 按时间正序排列（旧的在前），确保按顺序显示
                            entries.sort(key=lambda x: x.get('timestamp', 0))
                            
                            # 显示新条目
                            for entry in entries:
                                self._log_ledger_entry(entry)
                            
                            # 更新最新时间戳
                            if entries:
                                self.last_ledger_timestamp = entries[-1].get('timestamp', 0)
                    
                    # 每5秒查询一次
                    time.sleep(5)
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"账本监控错误: {error_msg}", exc_info=True)
                    # 如果是API权限错误或交易历史查询失败，停止监控
                    if ("permission" in error_msg.lower() or 
                        "not allowed" in error_msg.lower() or
                        "unauthorized" in error_msg.lower() or
                        "fetch_my_trades" in error_msg.lower()):
                        self.root.after(0, lambda: self._log_balance_change(
                            f"❌ 交易历史查询失败，停止监控。请检查API Key是否有读取交易历史的权限。", 
                            "error"
                        ))
                        self.is_monitoring_ledger = False
                        break
                    else:
                        # 其他错误，继续尝试
                        self.root.after(0, lambda: self._log_balance_change(
                            f"⚠️ 交易历史查询错误: {error_msg[:100]}，5秒后重试...", 
                            "error"
                        ))
                    time.sleep(5)
        
        self.ledger_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.ledger_monitor_thread.start()
    
    def _spot_buy(self):
        """现货买入"""
        if not self.client:
            messagebox.showerror("错误", "客户端未连接")
            return
        
        def buy_thread():
            try:
                amount = float(self.spot_amount_entry.get())
                price_str = self.spot_price_entry.get().strip()
                price = float(price_str) if price_str else None
                
                # 买入前记录余额
                self.root.after(0, lambda: self._log(f"📝 正在下单：现货买入 {amount} PEOPLE @ {price or '市价'}", "info"))
                self.root.after(0, lambda: self._log_balance_change("📊 买入前余额查询中...", "info"))
                
                balance_before = self.client.get_spot_balance()
                
                # 下单
                order = self.client.spot_buy(amount, price)
                order_id = order.get('id')
                
                self.root.after(0, lambda: self._log(f"✅ 订单创建成功！订单ID: {order_id}", "success"))
                self.root.after(0, lambda: self._log_order_change(f"🆕 新订单创建: 订单ID={order_id}, 数量={amount} PEOPLE, 价格={price or '市价'}", "new"))
                
                # 将订单加入监控列表
                self.monitored_orders[order_id] = {
                    'order': order,
                    'last_status': order.get('status', 'unknown'),
                    'last_filled': order.get('filled', 0),
                    'symbol': order.get('symbol', 'PEOPLE/USDT'),
                    'side': order.get('side', 'buy'),
                    'amount': order.get('amount', amount),
                    'price': order.get('price', price)
                }
                
                # 等待2秒后查询余额变化（给订单一些时间成交）
                time.sleep(2)
                
                # 买入后查询余额
                balance_after = self.client.get_spot_balance()
                
                # 对比并显示余额变化
                self.root.after(0, lambda: self._compare_and_show_balance_change(balance_before, balance_after, order_id))
                
                # 刷新数据
                self.root.after(0, self._refresh_all)
                
                # 显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("成功", f"订单创建成功！\n订单ID: {order_id}\n\n余额变化已显示在左侧"))
                
            except ValueError as e:
                self.root.after(0, lambda: self._log(f"❌ 输入错误: {e}", "error"))
                self.root.after(0, lambda: messagebox.showerror("输入错误", f"请输入有效的数字:\n{e}"))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"❌ 下单失败: {error_msg}", "error"))
                self.root.after(0, lambda: self._log_order_change(f"❌ 订单创建失败: {error_msg}", "error"))
                self.root.after(0, lambda: messagebox.showerror("下单失败", f"下单失败:\n{error_msg}"))
        
        # 在后台线程中执行买入操作
        threading.Thread(target=buy_thread, daemon=True).start()
    
    def _spot_close(self):
        """现货平仓（卖出）"""
        if not self.client:
            messagebox.showerror("错误", "客户端未连接")
            return
        
        def close_thread():
            try:
                amount_str = self.spot_close_amount_entry.get().strip()
                amount = float(amount_str) if amount_str else None
                price_str = self.spot_close_price_entry.get().strip()
                price = float(price_str) if price_str else None
                
                # 卖出前记录余额
                self.root.after(0, lambda: self._log(f"📝 正在下单：现货卖出 {amount or '全部'} PEOPLE @ {price or '市价'}", "info"))
                self.root.after(0, lambda: self._log_balance_change("📊 卖出前余额查询中...", "info"))
                
                balance_before = self.client.get_spot_balance()
                
                # 下单
                order = self.client.spot_close(amount, price)
                order_id = order.get('id')
                
                # 如果数量为空，获取实际卖出的数量
                if amount is None:
                    people_balance = balance_before.get('PEOPLE', {})
                    amount = float(people_balance.get('free', 0))
                
                self.root.after(0, lambda: self._log(f"✅ 订单创建成功！订单ID: {order_id}", "success"))
                self.root.after(0, lambda: self._log_order_change(f"🆕 新订单创建: 订单ID={order_id}, 数量={amount} PEOPLE, 价格={price or '市价'}", "new"))
                
                # 将订单加入监控列表
                self.monitored_orders[order_id] = {
                    'order': order,
                    'last_status': order.get('status', 'unknown'),
                    'last_filled': order.get('filled', 0),
                    'symbol': order.get('symbol', 'PEOPLE/USDT'),
                    'side': order.get('side', 'sell'),
                    'amount': order.get('amount', amount),
                    'price': order.get('price', price)
                }
                
                # 等待2秒后查询余额变化（给订单一些时间成交）
                time.sleep(2)
                
                # 卖出后查询余额
                balance_after = self.client.get_spot_balance()
                
                # 对比并显示余额变化
                self.root.after(0, lambda: self._compare_and_show_balance_change(balance_before, balance_after, order_id))
                
                # 刷新数据
                self.root.after(0, self._refresh_all)
                
                # 显示成功消息
                self.root.after(0, lambda: messagebox.showinfo("成功", f"订单创建成功！\n订单ID: {order_id}\n\n余额变化已显示在左侧"))
                
            except ValueError as e:
                self.root.after(0, lambda: self._log(f"❌ 输入错误: {e}", "error"))
                self.root.after(0, lambda: messagebox.showerror("输入错误", f"请输入有效的数字:\n{e}"))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"❌ 下单失败: {error_msg}", "error"))
                self.root.after(0, lambda: self._log_order_change(f"❌ 订单创建失败: {error_msg}", "error"))
                self.root.after(0, lambda: messagebox.showerror("下单失败", f"下单失败:\n{error_msg}"))
        
        # 在后台线程中执行卖出操作
        threading.Thread(target=close_thread, daemon=True).start()
    
    def _futures_long(self):
        """合约做多"""
        if not self.client:
            messagebox.showerror("错误", "客户端未连接")
            return
        
        def long_thread():
            try:
                amount = float(self.futures_amount_entry.get())
                price_str = self.futures_price_entry.get().strip()
                price = float(price_str) if price_str else None
                
                self.root.after(0, lambda: self._log(f"📝 正在下单：合约做多 {amount} 张 @ {price or '市价'}", "info"))
                order = self.client.futures_long(amount, price)
                
                self.root.after(0, lambda: self._log(f"✅ 订单创建成功！订单ID: {order.get('id')}", "success"))
                self.root.after(0, lambda: messagebox.showinfo("成功", f"订单创建成功！\n订单ID: {order.get('id')}"))
                
                # 刷新数据
                self.root.after(0, self._refresh_all)
                
            except ValueError as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"❌ {error_msg}", "error"))
                # 检查是否是名义价值不足的错误
                if "名义价值" in error_msg:
                    self.root.after(0, lambda: messagebox.showerror("订单名义价值不足", error_msg))
                else:
                    self.root.after(0, lambda: messagebox.showerror("输入错误", f"请输入有效的数字:\n{error_msg}"))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"❌ 下单失败: {error_msg}", "error"))
                # 检查是否是币安的名义价值错误
                if "notional" in error_msg.lower() or "4164" in error_msg:
                    detailed_msg = (
                        f"订单名义价值不足！\n\n"
                        f"币安要求订单名义价值至少为 5 USDT\n"
                        f"名义价值 = 合约数量 × 价格\n\n"
                        f"请增加合约数量或价格后再试。"
                    )
                    self.root.after(0, lambda: messagebox.showerror("下单失败", detailed_msg))
                # 检查是否是持仓方向错误（双向持仓模式相关）
                elif "position side" in error_msg.lower() or "4061" in error_msg:
                    detailed_msg = (
                        f"持仓方向设置错误！\n\n"
                        f"错误码: -4061\n"
                        f"这通常发生在账户设置为双向持仓模式（Hedge Mode）时。\n\n"
                        f"代码已自动添加 positionSide 参数，\n"
                        f"如果仍然报错，请检查币安账户的持仓模式设置。"
                    )
                    self.root.after(0, lambda: messagebox.showerror("下单失败", detailed_msg))
                else:
                    self.root.after(0, lambda: messagebox.showerror("下单失败", f"下单失败:\n{error_msg}"))
        
        # 在后台线程中执行下单操作
        threading.Thread(target=long_thread, daemon=True).start()
    
    def _futures_close(self):
        """合约平仓"""
        if not self.client:
            messagebox.showerror("错误", "客户端未连接")
            return
        
        try:
            side = self.close_side_var.get()
            amount_str = self.close_amount_entry.get().strip()
            amount = float(amount_str) if amount_str else None
            
            self._log(f"📝 正在平仓：{side} {amount or '全部'}", "info")
            order = self.client.futures_close(side, amount)
            self._log(f"✅ 平仓订单创建成功！订单ID: {order.get('id')}", "success")
            messagebox.showinfo("成功", f"平仓订单创建成功！\n订单ID: {order.get('id')}")
            
            # 刷新数据
            self._refresh_all()
            
        except ValueError as e:
            self._log(f"❌ 输入错误: {e}", "error")
            messagebox.showerror("输入错误", f"请输入有效的数字:\n{e}")
        except Exception as e:
            error_msg = str(e)
            self._log(f"❌ 平仓失败: {error_msg}", "error")
            # 检查是否是持仓方向错误（双向持仓模式相关）
            if "position side" in error_msg.lower() or "4061" in error_msg:
                detailed_msg = (
                    f"持仓方向设置错误！\n\n"
                    f"错误码: -4061\n"
                    f"这通常发生在账户设置为双向持仓模式（Hedge Mode）时。\n\n"
                    f"代码已自动添加 positionSide 参数，\n"
                    f"如果仍然报错，请检查币安账户的持仓模式设置。"
                )
                messagebox.showerror("平仓失败", detailed_msg)
            else:
                messagebox.showerror("平仓失败", f"平仓失败:\n{error_msg}")


def main():
    """主函数"""
    try:
        root = tk.Tk()
        app = BinancePeopleGUI(root)
        # 确保窗口显示在最前面
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        root.mainloop()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    print("=" * 60)
    print("币安 PEOPLE 币交易测试工具")
    print("=" * 60)
    print("正在启动GUI界面...")
    print("如果窗口没有显示，请检查:")
    print("1. 是否安装了 tkinter (通常Python自带)")
    print("2. 是否有错误信息输出")
    print("3. 窗口可能被其他窗口遮挡")
    print("=" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序异常退出: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

