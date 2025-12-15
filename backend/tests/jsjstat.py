import sys
import json
import time
import threading
import os
from datetime import datetime, timedelta
from collections import defaultdict

import ccxt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton, 
                             QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSpinBox, QComboBox, QMessageBox, QScrollArea)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette


class ExchangeWorker(QThread):
    """交易所工作线程，防止界面锁死"""
    connection_result = pyqtSignal(str, str, object)  # 交易所名称, 结果消息, 交易所对象
    asset_result = pyqtSignal(str, dict)  # 交易所名称, 资产数据
    order_result = pyqtSignal(str, list)  # 交易所名称, 订单数据
    error_signal = pyqtSignal(str, str)  # 操作类型, 错误消息
    
    def __init__(self):
        super().__init__()
        self.operations = []
        self.running = True
    
    def add_connection_test(self, exchange_name, config):
        """添加连接测试任务"""
        self.operations.append(('connection', exchange_name, config))
    
    def add_asset_fetch(self, exchange_name, exchange_obj):
        """添加资产获取任务"""
        self.operations.append(('asset', exchange_name, exchange_obj))
    
    def add_order_fetch(self, exchange_name, exchange_obj, status_filters, time_range):
        """添加订单获取任务"""
        self.operations.append(('order', exchange_name, exchange_obj, status_filters, time_range))
    
    def run(self):
        """执行任务队列"""
        while self.running and self.operations:
            operation = self.operations.pop(0)
            op_type = operation[0]
            
            try:
                if op_type == 'connection':
                    self.test_connection(operation[1], operation[2])
                elif op_type == 'asset':
                    self.fetch_assets(operation[1], operation[2])
                elif op_type == 'order':
                    self.fetch_orders(operation[1], operation[2], operation[3], operation[4])
            except Exception as e:
                self.error_signal.emit(op_type, str(e))
    
    def test_connection(self, exchange_name, config):
        """测试交易所连接"""
        try:
            if exchange_name == 'binance':
                exchange = ccxt.binance(config)
            elif exchange_name == 'okx':
                exchange = ccxt.okx(config)
            elif exchange_name == 'bybit':
                exchange = ccxt.bybit(config)
            else:
                raise ValueError(f"不支持的交易所: {exchange_name}")
            
            # 测试连接
            exchange.fetch_balance()
            self.connection_result.emit(exchange_name, "success", exchange)
            
        except Exception as e:
            self.connection_result.emit(exchange_name, f"failed: {str(e)}", None)
    
    def fetch_assets(self, exchange_name, exchange_obj):
        """获取资产数据"""
        try:
            assets = self._fetch_exchange_assets(exchange_name, exchange_obj)
            self.asset_result.emit(exchange_name, assets)
        except Exception as e:
            self.error_signal.emit('asset', f"{exchange_name}资产获取失败: {str(e)}")
    
    def fetch_orders(self, exchange_name, exchange_obj, status_filters, time_range):
        """获取订单数据"""
        try:
            orders = self._fetch_exchange_orders(exchange_name, exchange_obj, status_filters, time_range)
            self.order_result.emit(exchange_name, orders)
        except Exception as e:
            self.error_signal.emit('order', f"{exchange_name}订单获取失败: {str(e)}")
    
    def _fetch_exchange_assets(self, exchange_name, exchange):
        """获取交易所资产的具体实现"""
        try:
            balance = exchange.fetch_balance()
            assets = {}
            
            # 处理现货资产
            for currency, amount in balance['total'].items():
                if amount > 1e-8:  # 只显示有余额的资产
                    assets[currency] = {
                        'spot': amount,
                        'contract': 0,
                        'total': amount
                    }
            
            # 处理合约持仓
            try:
                positions = exchange.fetch_positions()
                for position in positions:
                    if position.get('contracts', 0) and abs(position['contracts']) > 1e-8:
                        symbol = position['symbol'].split('/')[0] if '/' in position['symbol'] else position['symbol']
                        contracts = position['contracts']
                        if position.get('side') == 'short':
                            contracts = -contracts
                        
                        if symbol in assets:
                            assets[symbol]['contract'] += contracts
                            assets[symbol]['total'] += contracts
                        else:
                            assets[symbol] = {
                                'spot': 0,
                                'contract': contracts,
                                'total': contracts
                            }
            except Exception as e:
                print(f"获取{exchange_name}合约持仓失败: {e}")
            
            return assets
            
        except Exception as e:
            raise Exception(f"获取资产失败: {str(e)}")
    
    def _fetch_exchange_orders(self, exchange_name, exchange, status_filters, time_range):
        """获取交易所订单的具体实现"""
        try:
            # 计算时间范围
            since = None
            if time_range != 'all':
                now = datetime.now()
                if time_range == '10min':
                    start_time = now - timedelta(minutes=10)
                elif time_range == '1hour':
                    start_time = now - timedelta(hours=1)
                elif time_range == '1day':
                    start_time = now - timedelta(days=1)
                elif time_range == '7days':
                    start_time = now - timedelta(days=7)
                else:
                    start_time = now - timedelta(days=1)  # 默认1天
                
                since = int(start_time.timestamp() * 1000)
            
            all_orders = []
            
            # 分别获取现货和合约订单
            print(f"正在获取{exchange_name}订单...")
            
            # 获取现货订单
            try:
                print(f"获取{exchange_name}现货订单...")
                spot_orders = exchange.fetch_orders(symbol=None, since=since, limit=50, params={})
                print(f"获取到{exchange_name}现货订单数量: {len(spot_orders)}")
                for order in spot_orders:
                    order['order_type'] = '现货'
                all_orders.extend(spot_orders)
            except Exception as e:
                print(f"获取{exchange_name}现货订单失败: {e}")
            
            # 获取合约订单（对于支持合约的交易所）
            if exchange_name in ['binance', 'okx', 'bybit']:
                try:
                    print(f"获取{exchange_name}合约订单...")
                    # 不同交易所的合约订单查询方式
                    if exchange_name == 'binance':
                        # 币安合约订单
                        futures_orders = exchange.fapiPrivateGetAllOrders({'timestamp': since} if since else {})
                        if isinstance(futures_orders, list):
                            for order in futures_orders:
                                order['order_type'] = '合约'
                            all_orders.extend(futures_orders)
                    elif exchange_name == 'okx':
                        # OKX合约订单
                        futures_orders = exchange.privateGetTradeOrdersHistoryArchive({'ordType': 'futures'})
                        if isinstance(futures_orders, list):
                            for order in futures_orders:
                                order['order_type'] = '合约'
                            all_orders.extend(futures_orders)
                    elif exchange_name == 'bybit':
                        # Bybit合约订单
                        futures_orders = exchange.privateGetLinearOrderList({})
                        if isinstance(futures_orders, list):
                            for order in futures_orders:
                                order['order_type'] = '合约'
                            all_orders.extend(futures_orders)
                    
                    print(f"获取到{exchange_name}合约订单数量: {len([o for o in all_orders if o.get('order_type') == '合约'])}")
                except Exception as e:
                    print(f"获取{exchange_name}合约订单失败: {e}")
            
            # 如果上面的方法都失败了，尝试通过symbol名称识别
            if len(all_orders) == 0:
                print("尝试通过交易对名称识别订单类型...")
                try:
                    all_orders_raw = exchange.fetch_orders(symbol=None, since=since, limit=100, params={})
                    for order in all_orders_raw:
                        # 通过symbol名称识别合约订单
                        symbol = order.get('symbol', '').upper()
                        if any(marker in symbol for marker in ['USDT', 'BUSD', 'PERP', 'SWAP', 'FUTURES']):
                            # 包含这些标记的很可能是合约订单
                            order['order_type'] = '合约'
                        else:
                            order['order_type'] = '现货'
                    all_orders.extend(all_orders_raw)
                    print(f"通过symbol识别获取到订单数量: {len(all_orders)}")
                except Exception as e:
                    print(f"通过symbol识别获取订单失败: {e}")
            
            # 去重处理
            seen_order_ids = set()
            unique_orders = []
            for order in all_orders:
                order_id = order.get('id')
                if order_id and order_id not in seen_order_ids:
                    seen_order_ids.add(order_id)
                    unique_orders.append(order)
            
            print(f"{exchange_name}总订单数量（去重后）: {len(unique_orders)}")
            print(f"现货订单: {len([o for o in unique_orders if o.get('order_type') == '现货'])}")
            print(f"合约订单: {len([o for o in unique_orders if o.get('order_type') == '合约'])}")
            
            filtered_orders = []
            for order in unique_orders:
                # 状态过滤 - 支持多选
                if status_filters and order['status'] not in status_filters:
                    continue
                
                # 格式化时间
                if 'timestamp' in order and order['timestamp']:
                    order['datetime'] = datetime.fromtimestamp(order['timestamp'] / 1000)
                    order['datetime_str'] = order['datetime'].strftime("%m-%d %H:%M:%S")
                else:
                    order['datetime'] = None
                    order['datetime_str'] = "未知时间"
                
                # 处理成交时间
                if 'lastTradeTimestamp' in order and order['lastTradeTimestamp']:
                    order['trade_datetime'] = datetime.fromtimestamp(order['lastTradeTimestamp'] / 1000)
                    order['trade_datetime_str'] = order['trade_datetime'].strftime("%m-%d %H:%M:%S")
                else:
                    order['trade_datetime'] = None
                    order['trade_datetime_str'] = "未成交"
                
                # 处理数量显示（卖/short方向为负数）
                order['display_amount'] = order.get('amount', 0)
                if order.get('side') in ['sell', 'short']:
                    order['display_amount'] = -order['display_amount']
                
                # 计算交易金额和手续费
                price = order.get('price', 0)
                order['cost'] = order.get('amount', 0) * price if price else 0
                
                # 处理手续费 - 确保是数字类型
                order['fee_cost'] = 0
                order['fee_currency'] = ''
                if 'fee' in order and order['fee']:
                    fee_cost = order['fee'].get('cost', 0)
                    # 确保手续费是数字类型
                    try:
                        order['fee_cost'] = float(fee_cost) if fee_cost else 0
                    except (ValueError, TypeError):
                        order['fee_cost'] = 0
                    order['fee_currency'] = order['fee'].get('currency', '')
                
                # 确保订单类型字段存在
                if 'order_type' not in order:
                    # 通过其他方式识别订单类型
                    symbol = order.get('symbol', '').upper()
                    order_type = order.get('type', '').upper()
                    
                    # 合约订单的识别规则
                    contract_indicators = [
                        'USDT', 'BUSD', 'PERP', 'SWAP', 'FUTURES', 'FUTURE',
                        '合约', 'CONTRACT', '线性', 'INVERSE'
                    ]
                    
                    if any(indicator in symbol for indicator in contract_indicators) or \
                       any(indicator in order_type for indicator in contract_indicators):
                        order['order_type'] = '合约'
                    else:
                        order['order_type'] = '现货'
                
                filtered_orders.append(order)
            
            print(f"{exchange_name}过滤后订单数量: {len(filtered_orders)}")
            return filtered_orders
            
        except Exception as e:
            raise Exception(f"获取订单失败: {str(e)}")
    
    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()


class SortableTableWidgetItem(QTableWidgetItem):
    """可排序的表格项，支持不同类型的数据排序"""
    
    def __init__(self, text, sort_key):
        super().__init__(text)
        self.sort_key = sort_key
    
    def __lt__(self, other):
        try:
            return self.sort_key < other.sort_key
        except:
            return super().__lt__(other)


class ExchangeMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.exchanges = {}
        self.config_file = "exchange_config.json"
        self.asset_data = {}
        self.order_data = {}
        self.last_asset_data = {}
        self.last_order_data = {}
        self.asset_last_refresh = None
        self.order_last_refresh = None
        
        # 订单状态统计
        self.order_status_stats = defaultdict(lambda: defaultdict(int))
        self.last_order_status_stats = defaultdict(lambda: defaultdict(int))
        
        # 日志文件配置
        self.log_dir = "logs"
        self.asset_log_file = None
        self.order_log_file = None
        self.setup_log_files()
        
        # 创建工作线程
        self.worker = ExchangeWorker()
        self.worker.connection_result.connect(self.handle_connection_result)
        self.worker.asset_result.connect(self.handle_asset_result)
        self.worker.order_result.connect(self.handle_order_result)
        self.worker.error_signal.connect(self.handle_worker_error)
        
        self.init_ui()
        self.load_config()
        self.start_monitoring()

    def setup_log_files(self):
        """设置日志文件"""
        try:
            # 创建日志目录
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            
            # 创建带时间戳的日志文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.asset_log_file = os.path.join(self.log_dir, f"asset_changes_{timestamp}.log")
            self.order_log_file = os.path.join(self.log_dir, f"order_changes_{timestamp}.log")
            
            # 写入日志文件头
            with open(self.asset_log_file, 'w', encoding='utf-8') as f:
                f.write(f"# 资产变化记录日志 - 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# 格式: [时间] 变化内容\n\n")
            
            with open(self.order_log_file, 'w', encoding='utf-8') as f:
                f.write(f"# 订单变化记录日志 - 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# 格式: [时间] 变化内容\n\n")
                
            print(f"资产日志文件: {self.asset_log_file}")
            print(f"订单日志文件: {self.order_log_file}")
            
        except Exception as e:
            print(f"创建日志文件失败: {e}")

    def write_asset_log(self, message):
        """写入资产变化日志到文件"""
        try:
            if self.asset_log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.asset_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"写入资产日志失败: {e}")

    def write_order_log(self, message):
        """写入订单变化日志到文件"""
        try:
            if self.order_log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.order_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"写入订单日志失败: {e}")

    def init_ui(self):
        self.setWindowTitle("区块链交易所监控系统 v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置优化的样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #3c3c3c;
            }
            QTabBar::tab {
                background-color: #4c4c4c;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
            QGroupBox {
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
                color: #e0e0e0;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00a8ff;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #404040;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 3px;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #404040;
                color: #e0e0e0;
                gridline-color: #555;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #555;
                color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #e0e0e0;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #555;
                font-family: 'Courier New';
                font-weight: bold;
            }
            QCheckBox {
                color: #e0e0e0;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
            }
        """)

        # 创建主标签页
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 创建各个功能标签页
        self.setup_exchange_tab()
        self.setup_monitoring_tab()

        # 状态栏
        self.statusBar().showMessage("就绪")

    def setup_exchange_tab(self):
        """设置交易所配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 币安配置组
        binance_group = QGroupBox("币安 (Binance)")
        binance_layout = QVBoxLayout(binance_group)
        
        binance_layout.addWidget(QLabel("API Key:"))
        self.binance_api_key = QLineEdit()
        self.binance_api_key.setEchoMode(QLineEdit.Password)
        binance_layout.addWidget(self.binance_api_key)
        
        binance_layout.addWidget(QLabel("Secret Key:"))
        self.binance_secret = QLineEdit()
        self.binance_secret.setEchoMode(QLineEdit.Password)
        binance_layout.addWidget(self.binance_secret)

        # OKX配置组
        okx_group = QGroupBox("OKX")
        okx_layout = QVBoxLayout(okx_group)
        
        okx_layout.addWidget(QLabel("API Key:"))
        self.okx_api_key = QLineEdit()
        self.okx_api_key.setEchoMode(QLineEdit.Password)
        okx_layout.addWidget(self.okx_api_key)
        
        okx_layout.addWidget(QLabel("Secret Key:"))
        self.okx_secret = QLineEdit()
        self.okx_secret.setEchoMode(QLineEdit.Password)
        okx_layout.addWidget(self.okx_secret)
        
        okx_layout.addWidget(QLabel("Passphrase:"))
        self.okx_passphrase = QLineEdit()
        self.okx_passphrase.setEchoMode(QLineEdit.Password)
        okx_layout.addWidget(self.okx_passphrase)

        # Bybit配置组
        bybit_group = QGroupBox("Bybit")
        bybit_layout = QVBoxLayout(bybit_group)
        
        bybit_layout.addWidget(QLabel("API Key:"))
        self.bybit_api_key = QLineEdit()
        self.bybit_api_key.setEchoMode(QLineEdit.Password)
        bybit_layout.addWidget(self.bybit_api_key)
        
        bybit_layout.addWidget(QLabel("Secret Key:"))
        self.bybit_secret = QLineEdit()
        self.bybit_secret.setEchoMode(QLineEdit.Password)
        bybit_layout.addWidget(self.bybit_secret)

        # 按钮组
        button_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试所有连接")
        self.test_btn.clicked.connect(self.test_all_connections)
        button_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)

        # 连接状态显示
        self.connection_log = QTextEdit()
        self.connection_log.setMaximumHeight(150)
        self.connection_log.setReadOnly(True)

        # 布局安排
        exchange_layout = QHBoxLayout()
        exchange_layout.addWidget(binance_group)
        exchange_layout.addWidget(okx_group)
        exchange_layout.addWidget(bybit_group)

        layout.addLayout(exchange_layout)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("连接状态:"))
        layout.addWidget(self.connection_log)

        self.tab_widget.addTab(tab, "交易所配置")

    def setup_monitoring_tab(self):
        """设置监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建子标签页
        sub_tabs = QTabWidget()
        
        # 资产监控标签页
        asset_tab = self.setup_asset_tab()
        # 订单监控标签页
        order_tab = self.setup_order_tab()
        
        sub_tabs.addTab(asset_tab, "资产与持仓监控")
        sub_tabs.addTab(order_tab, "订单监控")
        
        layout.addWidget(sub_tabs)
        self.tab_widget.addTab(tab, "交易监控")

    def setup_asset_tab(self):
        """设置资产监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 控制面板
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("刷新间隔(秒):"))
        self.asset_interval = QSpinBox()
        self.asset_interval.setRange(1, 300)
        self.asset_interval.setValue(5)
        control_layout.addWidget(self.asset_interval)
        
        control_layout.addWidget(QLabel("选择交易所:"))
        self.binance_asset_check = QCheckBox("币安")
        self.okx_asset_check = QCheckBox("OKX")
        self.bybit_asset_check = QCheckBox("Bybit")
        
        control_layout.addWidget(self.binance_asset_check)
        control_layout.addWidget(self.okx_asset_check)
        control_layout.addWidget(self.bybit_asset_check)
        
        self.refresh_assets_btn = QPushButton("立即刷新")
        self.refresh_assets_btn.clicked.connect(self.refresh_assets)
        control_layout.addWidget(self.refresh_assets_btn)
        
        # 最后刷新时间显示
        self.asset_refresh_time = QLabel("最后刷新时间: 从未刷新")
        control_layout.addWidget(self.asset_refresh_time)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)

        # 资产表格
        self.asset_table = QTableWidget()
        self.asset_table.setColumnCount(6)
        self.asset_table.setHorizontalHeaderLabels(["交易所", "币种", "现货数量", "合约持仓", "总数量", "变化"])
        layout.addWidget(self.asset_table)

        # 变化日志
        layout.addWidget(QLabel("资产变化记录:"))
        self.asset_log = QTextEdit()
        self.asset_log.setMaximumHeight(150)
        self.asset_log.setReadOnly(True)
        layout.addWidget(self.asset_log)

        return tab

    def setup_order_tab(self):
        """设置订单监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 控制面板
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("刷新间隔(秒):"))
        self.order_interval = QSpinBox()
        self.order_interval.setRange(1, 300)
        self.order_interval.setValue(5)
        control_layout.addWidget(self.order_interval)
        
        control_layout.addWidget(QLabel("选择交易所:"))
        self.binance_order_check = QCheckBox("币安")
        self.okx_order_check = QCheckBox("OKX")
        self.bybit_order_check = QCheckBox("Bybit")
        
        control_layout.addWidget(self.binance_order_check)
        control_layout.addWidget(self.okx_order_check)
        control_layout.addWidget(self.bybit_order_check)
        
        # 订单状态选择 - 使用Checkbox支持多选
        control_layout.addWidget(QLabel("订单状态:"))
        self.order_status_open = QCheckBox("open")
        self.order_status_closed = QCheckBox("closed")
        self.order_status_canceled = QCheckBox("canceled")
        
        # 默认选中所有状态
        self.order_status_open.setChecked(True)
        self.order_status_closed.setChecked(True)
        self.order_status_canceled.setChecked(True)
        
        control_layout.addWidget(self.order_status_open)
        control_layout.addWidget(self.order_status_closed)
        control_layout.addWidget(self.order_status_canceled)
        
        # 订单类型过滤
        control_layout.addWidget(QLabel("订单类型:"))
        self.order_type_spot = QCheckBox("现货")
        self.order_type_futures = QCheckBox("合约")
        
        self.order_type_spot.setChecked(True)
        self.order_type_futures.setChecked(True)
        
        control_layout.addWidget(self.order_type_spot)
        control_layout.addWidget(self.order_type_futures)
        
        self.refresh_orders_btn = QPushButton("立即刷新")
        self.refresh_orders_btn.clicked.connect(self.refresh_orders)
        control_layout.addWidget(self.refresh_orders_btn)
        
        # 最后刷新时间显示
        self.order_refresh_time = QLabel("最后刷新时间: 从未刷新")
        control_layout.addWidget(self.order_refresh_time)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)

        # 时间过滤条件 - 简化版本
        time_filter_layout = QHBoxLayout()
        time_filter_layout.addWidget(QLabel("时间范围:"))
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["最近10分钟", "最近1小时", "最近1天", "最近7天", "全部"])
        self.time_range_combo.setCurrentText("最近1天")
        time_filter_layout.addWidget(self.time_range_combo)
        
        time_filter_layout.addStretch()
        layout.addLayout(time_filter_layout)

        # 订单状态统计
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("订单状态统计:"))
        self.order_stats_label = QLabel("")
        stats_layout.addWidget(self.order_stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # 订单表格 - 支持排序，增加交易金额和手续费列
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(14)
        self.order_table.setHorizontalHeaderLabels([
            "交易所", "订单ID", "交易对", "订单类型", "类型", "方向", "数量", "价格", 
            "交易金额", "手续费", "状态", "下单时间", "成交时间", "操作"
        ])
        
        # 启用排序功能
        self.order_table.setSortingEnabled(True)
        self.order_table.sortByColumn(11, Qt.DescendingOrder)  # 默认按下单时间降序排列
        
        layout.addWidget(self.order_table)

        # 错误日志
        layout.addWidget(QLabel("网络错误记录:"))
        self.error_log = QTextEdit()
        self.error_log.setMaximumHeight(100)
        self.error_log.setReadOnly(True)
        self.error_log.setStyleSheet("color: #ff6b6b;")
        layout.addWidget(self.error_log)

        # 变化日志
        layout.addWidget(QLabel("订单变化记录:"))
        self.order_log = QTextEdit()
        self.order_log.setMaximumHeight(150)
        self.order_log.setReadOnly(True)
        layout.addWidget(self.order_log)

        return tab

    def get_order_status_filters(self):
        """获取订单状态过滤条件"""
        status_filters = []
        if self.order_status_open.isChecked():
            status_filters.append('open')
        if self.order_status_closed.isChecked():
            status_filters.append('closed')
        if self.order_status_canceled.isChecked():
            status_filters.append('canceled')
        return status_filters if status_filters else None

    def get_order_type_filters(self):
        """获取订单类型过滤条件"""
        type_filters = []
        if self.order_type_spot.isChecked():
            type_filters.append('现货')
        if self.order_type_futures.isChecked():
            type_filters.append('合约')
        return type_filters if type_filters else None

    def get_time_range(self):
        """获取时间范围"""
        time_range_text = self.time_range_combo.currentText()
        if time_range_text == "最近10分钟":
            return '10min'
        elif time_range_text == "最近1小时":
            return '1hour'
        elif time_range_text == "最近1天":
            return '1day'
        elif time_range_text == "最近7天":
            return '7days'
        else:
            return 'all'

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # 加载API配置
            self.binance_api_key.setText(config.get('binance_api_key', ''))
            self.binance_secret.setText(config.get('binance_secret', ''))
            self.okx_api_key.setText(config.get('okx_api_key', ''))
            self.okx_secret.setText(config.get('okx_secret', ''))
            self.okx_passphrase.setText(config.get('okx_passphrase', ''))
            self.bybit_api_key.setText(config.get('bybit_api_key', ''))
            self.bybit_secret.setText(config.get('bybit_secret', ''))
            
            # 加载资产监控配置
            asset_config = config.get('asset_monitor', {})
            self.binance_asset_check.setChecked(asset_config.get('binance', True))
            self.okx_asset_check.setChecked(asset_config.get('okx', True))
            self.bybit_asset_check.setChecked(asset_config.get('bybit', True))
            self.asset_interval.setValue(asset_config.get('interval', 5))
            
            # 加载订单监控配置
            order_config = config.get('order_monitor', {})
            self.binance_order_check.setChecked(order_config.get('binance', True))
            self.okx_order_check.setChecked(order_config.get('okx', True))
            self.bybit_order_check.setChecked(order_config.get('bybit', True))
            self.order_interval.setValue(order_config.get('interval', 5))
            
            # 加载订单状态过滤配置
            status_config = order_config.get('status_filters', {})
            self.order_status_open.setChecked(status_config.get('open', True))
            self.order_status_closed.setChecked(status_config.get('closed', True))
            self.order_status_canceled.setChecked(status_config.get('canceled', True))
            
            # 加载订单类型过滤配置
            type_config = order_config.get('type_filters', {})
            self.order_type_spot.setChecked(type_config.get('spot', True))
            self.order_type_futures.setChecked(type_config.get('futures', True))
            
            # 加载时间范围配置
            time_range = order_config.get('time_range', '最近1天')
            index = self.time_range_combo.findText(time_range)
            if index >= 0:
                self.time_range_combo.setCurrentIndex(index)
            
            self.log_connection("配置加载成功")
        except FileNotFoundError:
            self.log_connection("未找到配置文件，将创建新配置")
        except Exception as e:
            self.log_connection(f"加载配置时出错: {str(e)}")

    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'binance_api_key': self.binance_api_key.text(),
                'binance_secret': self.binance_secret.text(),
                'okx_api_key': self.okx_api_key.text(),
                'okx_secret': self.okx_secret.text(),
                'okx_passphrase': self.okx_passphrase.text(),
                'bybit_api_key': self.bybit_api_key.text(),
                'bybit_secret': self.bybit_secret.text(),
                'asset_monitor': {
                    'binance': self.binance_asset_check.isChecked(),
                    'okx': self.okx_asset_check.isChecked(),
                    'bybit': self.bybit_asset_check.isChecked(),
                    'interval': self.asset_interval.value()
                },
                'order_monitor': {
                    'binance': self.binance_order_check.isChecked(),
                    'okx': self.okx_order_check.isChecked(),
                    'bybit': self.bybit_order_check.isChecked(),
                    'interval': self.order_interval.value(),
                    'status_filters': {
                        'open': self.order_status_open.isChecked(),
                        'closed': self.order_status_closed.isChecked(),
                        'canceled': self.order_status_canceled.isChecked()
                    },
                    'type_filters': {
                        'spot': self.order_type_spot.isChecked(),
                        'futures': self.order_type_futures.isChecked()
                    },
                    'time_range': self.time_range_combo.currentText()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.log_connection("配置保存成功")
        except Exception as e:
            self.log_connection(f"保存配置时出错: {str(e)}")

    def test_all_connections(self):
        """测试所有交易所连接（非阻塞方式）"""
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        self.log_connection("开始测试所有交易所连接...")
        
        # 清空之前的连接
        self.exchanges.clear()
        
        # 测试币安
        if self.binance_api_key.text() and self.binance_secret.text():
            config = {
                'apiKey': self.binance_api_key.text(),
                'secret': self.binance_secret.text(),
                'sandbox': False,
                'enableRateLimit': True
            }
            self.worker.add_connection_test('binance', config)

        # 测试OKX
        if self.okx_api_key.text() and self.okx_secret.text() and self.okx_passphrase.text():
            config = {
                'apiKey': self.okx_api_key.text(),
                'secret': self.okx_secret.text(),
                'password': self.okx_passphrase.text(),
                'sandbox': False,
                'enableRateLimit': True
            }
            self.worker.add_connection_test('okx', config)

        # 测试Bybit
        if self.bybit_api_key.text() and self.bybit_secret.text():
            config = {
                'apiKey': self.bybit_api_key.text(),
                'secret': self.bybit_secret.text(),
                'sandbox': False,
                'enableRateLimit': True
            }
            self.worker.add_connection_test('bybit', config)
        
        # 启动工作线程
        if not self.worker.isRunning():
            self.worker.start()

    def handle_connection_result(self, exchange_name, result, exchange_obj):
        """处理连接测试结果"""
        if "success" in result:
            self.exchanges[exchange_name] = exchange_obj
            self.log_connection(f"✅ {exchange_name.capitalize()}连接成功")
        else:
            self.log_connection(f"❌ {exchange_name.capitalize()}连接失败: {result}")
        
        # 检查是否所有测试完成
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试所有连接")

    def handle_asset_result(self, exchange_name, assets):
        """处理资产数据结果"""
        self.asset_data[exchange_name] = assets
        
        # 检查是否所有选中的交易所都返回了数据
        selected_exchanges = []
        if self.binance_asset_check.isChecked() and 'binance' in self.exchanges:
            selected_exchanges.append('binance')
        if self.okx_asset_check.isChecked() and 'okx' in self.exchanges:
            selected_exchanges.append('okx')
        if self.bybit_asset_check.isChecked() and 'bybit' in self.exchanges:
            selected_exchanges.append('bybit')
        
        if all(exchange in self.asset_data for exchange in selected_exchanges):
            self.update_asset_display()

    def handle_order_result(self, exchange_name, orders):
        """处理订单数据结果"""
        self.order_data[exchange_name] = orders
        
        # 检查是否所有选中的交易所都返回了数据
        selected_exchanges = []
        if self.binance_order_check.isChecked() and 'binance' in self.exchanges:
            selected_exchanges.append('binance')
        if self.okx_order_check.isChecked() and 'okx' in self.exchanges:
            selected_exchanges.append('okx')
        if self.bybit_order_check.isChecked() and 'bybit' in self.exchanges:
            selected_exchanges.append('bybit')
        
        if all(exchange in self.order_data for exchange in selected_exchanges):
            self.update_order_display()

    def handle_worker_error(self, op_type, error_msg):
        """处理工作线程错误"""
        # 网络错误显示在独立的错误日志中
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if op_type == 'connection':
            self.log_error(f"连接错误: {error_msg}")
        elif op_type == 'asset':
            self.log_error(f"资产获取错误: {error_msg}")
        elif op_type == 'order':
            self.log_error(f"订单获取错误: {error_msg}")

    def log_connection(self, message):
        """记录连接日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.connection_log.append(f"[{timestamp}] {message}")

    def log_error(self, message):
        """记录错误日志 - 最新记录显示在最上面"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_text = self.error_log.toPlainText()
        new_text = f"[{timestamp}] {message}\n" + current_text
        self.error_log.setPlainText(new_text)

    def log_asset_change(self, message):
        """记录资产变化 - 最新记录显示在最上面，并保存到文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_text = self.asset_log.toPlainText()
        new_text = f"[{timestamp}] {message}\n" + current_text
        self.asset_log.setPlainText(new_text)
        
        # 自动保存到日志文件
        self.write_asset_log(message)

    def log_order_change(self, message):
        """记录订单变化 - 最新记录显示在最上面，并保存到文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_text = self.order_log.toPlainText()
        new_text = f"[{timestamp}] {message}\n" + current_text
        self.order_log.setPlainText(new_text)
        
        # 自动保存到日志文件
        self.write_order_log(message)

    def start_monitoring(self):
        """开始监控"""
        self.asset_timer = QTimer()
        self.asset_timer.timeout.connect(self.refresh_assets)
        self.asset_timer.start(self.asset_interval.value() * 1000)
        
        self.order_timer = QTimer()
        self.order_timer.timeout.connect(self.refresh_orders)
        self.order_timer.start(self.order_interval.value() * 1000)

    def refresh_assets(self):
        """刷新资产数据（非阻塞方式）"""
        # 检查是否选择了交易所
        if not any([self.binance_asset_check.isChecked(), 
                   self.okx_asset_check.isChecked(), 
                   self.bybit_asset_check.isChecked()]):
            self.log_error("请至少选择一个交易所进行资产查询")
            return

        # 清空当前数据
        self.asset_data = {}
        
        # 币安资产
        if self.binance_asset_check.isChecked() and 'binance' in self.exchanges:
            self.worker.add_asset_fetch('binance', self.exchanges['binance'])
        
        # OKX资产
        if self.okx_asset_check.isChecked() and 'okx' in self.exchanges:
            self.worker.add_asset_fetch('okx', self.exchanges['okx'])
        
        # Bybit资产
        if self.bybit_asset_check.isChecked() and 'bybit' in self.exchanges:
            self.worker.add_asset_fetch('bybit', self.exchanges['bybit'])
        
        # 启动工作线程
        if not self.worker.isRunning():
            self.worker.start()

    def refresh_orders(self):
        """刷新订单数据（非阻塞方式）"""
        # 检查是否选择了交易所
        if not any([self.binance_order_check.isChecked(), 
                   self.okx_order_check.isChecked(), 
                   self.bybit_order_check.isChecked()]):
            self.log_error("请至少选择一个交易所进行订单查询")
            return
        
        # 检查是否选择了订单状态
        status_filters = self.get_order_status_filters()
        if not status_filters:
            self.log_error("请至少选择一种订单状态进行查询")
            return

        # 清空当前数据
        self.order_data = {}
        
        time_range = self.get_time_range()
        
        # 币安订单
        if self.binance_order_check.isChecked() and 'binance' in self.exchanges:
            self.worker.add_order_fetch('binance', self.exchanges['binance'], status_filters, time_range)
        
        # OKX订单
        if self.okx_order_check.isChecked() and 'okx' in self.exchanges:
            self.worker.add_order_fetch('okx', self.exchanges['okx'], status_filters, time_range)
        
        # Bybit订单
        if self.bybit_order_check.isChecked() and 'bybit' in self.exchanges:
            self.worker.add_order_fetch('bybit', self.exchanges['bybit'], status_filters, time_range)
        
        # 启动工作线程
        if not self.worker.isRunning():
            self.worker.start()

    def update_asset_display(self):
        """更新资产显示"""
        if not self.asset_data:
            return
            
        # 更新最后刷新时间
        self.asset_last_refresh = datetime.now()
        self.asset_refresh_time.setText(f"最后刷新时间: {self.asset_last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 计算所有交易所汇总数据
        total_assets = defaultdict(lambda: {'spot': 0, 'contract': 0, 'total': 0})
        
        for exchange, assets in self.asset_data.items():
            for currency, data in assets.items():
                total_assets[currency]['spot'] += data['spot']
                total_assets[currency]['contract'] += data['contract']
                total_assets[currency]['total'] += data['total']
        
        # 更新表格
        self.asset_table.setRowCount(0)
        
        row = 0
        # 先显示各交易所数据
        for exchange, assets in self.asset_data.items():
            for currency, data in assets.items():
                self.asset_table.insertRow(row)
                
                # 计算变化
                change = ""
                if (exchange in self.last_asset_data and 
                    currency in self.last_asset_data[exchange]):
                    last_total = self.last_asset_data[exchange][currency]['total']
                    current_total = data['total']
                    if abs(current_total - last_total) > 1e-8:
                        diff = current_total - last_total
                        change = f"{diff:+.6f}"
                
                self.asset_table.setItem(row, 0, QTableWidgetItem(exchange.capitalize()))
                self.asset_table.setItem(row, 1, QTableWidgetItem(currency))
                self.asset_table.setItem(row, 2, QTableWidgetItem(f"{data['spot']:.6f}"))
                self.asset_table.setItem(row, 3, QTableWidgetItem(f"{data['contract']:.6f}"))
                self.asset_table.setItem(row, 4, QTableWidgetItem(f"{data['total']:.6f}"))
                
                change_item = QTableWidgetItem(change)
                if change:
                    if '-' in change:
                        change_item.setForeground(QColor('#ff6b6b'))
                    else:
                        change_item.setForeground(QColor('#51cf66'))
                self.asset_table.setItem(row, 5, change_item)
                
                row += 1
        
        # 显示汇总数据
        for currency, data in total_assets.items():
            if abs(data['total']) > 1e-8:  # 只显示有余额的币种
                self.asset_table.insertRow(row)
                self.asset_table.setItem(row, 0, QTableWidgetItem("所有交易所"))
                self.asset_table.setItem(row, 1, QTableWidgetItem(currency))
                self.asset_table.setItem(row, 2, QTableWidgetItem(f"{data['spot']:.6f}"))
                self.asset_table.setItem(row, 3, QTableWidgetItem(f"{data['contract']:.6f}"))
                self.asset_table.setItem(row, 4, QTableWidgetItem(f"{data['total']:.6f}"))
                self.asset_table.setItem(row, 5, QTableWidgetItem(""))
                row += 1
        
        self.asset_table.resizeColumnsToContents()
        
        # 检测变化并更新日志
        self.detect_asset_changes()
        self.last_asset_data = self.asset_data.copy()

    def update_order_display(self):
        """更新订单显示"""
        if not self.order_data:
            return
            
        # 更新最后刷新时间
        self.order_last_refresh = datetime.now()
        self.order_refresh_time.setText(f"最后刷新时间: {self.order_last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 计算订单状态统计
        self.order_status_stats.clear()
        for exchange, orders in self.order_data.items():
            for order in orders:
                order_status = order['status']
                self.order_status_stats[exchange][order_status] += 1
        
        # 更新统计显示
        stats_text = ""
        for exchange, stats in self.order_status_stats.items():
            if stats:
                exchange_stats = [f"{k}: {v}" for k, v in stats.items()]
                stats_text += f"{exchange}: {', '.join(exchange_stats)} | "
        if stats_text:
            self.order_stats_label.setText(stats_text[:-3])  # 去掉最后的 " | "
        
        # 更新表格（临时禁用排序以避免数据混乱）
        self.order_table.setSortingEnabled(False)
        self.order_table.setRowCount(0)
        
        row = 0
        type_filters = self.get_order_type_filters()
        
        for exchange, orders in self.order_data.items():
            for order in orders:
                # 订单类型过滤
                order_type = order.get('order_type', '现货')
                if type_filters and order_type not in type_filters:
                    continue
                
                self.order_table.insertRow(row)
                
                # 交易所
                self.order_table.setItem(row, 0, QTableWidgetItem(exchange.capitalize()))
                
                # 订单ID
                self.order_table.setItem(row, 1, QTableWidgetItem(order['id'][:10] + '...'))
                
                # 交易对
                self.order_table.setItem(row, 2, QTableWidgetItem(order['symbol']))
                
                # 订单类型
                type_item = QTableWidgetItem(order_type)
                if order_type == '现货':
                    type_item.setForeground(QColor('#51cf66'))  # 绿色
                else:
                    type_item.setForeground(QColor('#ffd43b'))  # 黄色
                self.order_table.setItem(row, 3, type_item)
                
                # 类型
                self.order_table.setItem(row, 4, QTableWidgetItem(order['type']))
                
                # 方向
                side_item = QTableWidgetItem(order['side'])
                if order['side'] == 'buy':
                    side_item.setForeground(QColor('#51cf66'))  # 绿色
                else:
                    side_item.setForeground(QColor('#ff6b6b'))  # 红色
                self.order_table.setItem(row, 5, side_item)
                
                # 数量（卖/short方向为负数）
                amount_text = f"{order['display_amount']:.6f}"
                amount_item = SortableTableWidgetItem(amount_text, order['display_amount'])
                if order['side'] == 'buy':
                    amount_item.setForeground(QColor('#51cf66'))
                else:
                    amount_item.setForeground(QColor('#ff6b6b'))
                self.order_table.setItem(row, 6, amount_item)
                
                # 价格
                price = order.get('price', 0)
                price_text = f"{price:.6f}" if price else "市价"
                price_item = SortableTableWidgetItem(price_text, price if price else 0)
                self.order_table.setItem(row, 7, price_item)
                
                # 交易金额
                cost_text = f"{order.get('cost', 0):.2f}" if order.get('cost', 0) > 0 else "市价"
                cost_item = SortableTableWidgetItem(cost_text, order.get('cost', 0))
                self.order_table.setItem(row, 8, cost_item)
                
                # 手续费 - 修复格式化问题
                fee_cost = order.get('fee_cost', 0)
                fee_currency = order.get('fee_currency', '')
                try:
                    # 确保是数字类型
                    fee_cost_num = float(fee_cost) if fee_cost else 0
                    fee_text = f"{fee_cost_num:.6f} {fee_currency}".strip()
                except (ValueError, TypeError):
                    fee_text = f"{fee_cost} {fee_currency}".strip()
                fee_item = QTableWidgetItem(fee_text)
                if fee_cost and float(fee_cost) > 0:
                    fee_item.setForeground(QColor('#ffd43b'))  # 黄色
                self.order_table.setItem(row, 9, fee_item)
                
                # 状态
                status_item = QTableWidgetItem(order['status'])
                if order['status'] == 'open':
                    status_item.setForeground(QColor('#ffd43b'))
                elif order['status'] == 'closed':
                    status_item.setForeground(QColor('#51cf66'))
                elif order['status'] == 'canceled':
                    status_item.setForeground(QColor('#ff6b6b'))
                self.order_table.setItem(row, 10, status_item)
                
                # 下单时间（使用可排序的项）
                datetime_item = SortableTableWidgetItem(
                    order['datetime_str'], 
                    order['datetime'] if order['datetime'] else datetime.min
                )
                self.order_table.setItem(row, 11, datetime_item)
                
                # 成交时间（使用可排序的项）
                trade_datetime_item = SortableTableWidgetItem(
                    order['trade_datetime_str'],
                    order['trade_datetime'] if order['trade_datetime'] else datetime.min
                )
                self.order_table.setItem(row, 12, trade_datetime_item)
                
                # 撤销按钮
                if order['status'] == 'open':
                    cancel_btn = QPushButton("撤销")
                    cancel_btn.clicked.connect(lambda checked, ex=exchange, oid=order['id']: self.cancel_order(ex, oid))
                    self.order_table.setCellWidget(row, 13, cancel_btn)
                
                row += 1
        
        # 重新启用排序
        self.order_table.setSortingEnabled(True)
        self.order_table.resizeColumnsToContents()
        
        # 检测变化并更新日志
        self.detect_order_changes()
        self.last_order_data = self.order_data.copy()
        self.last_order_status_stats = self.order_status_stats.copy()

    def detect_asset_changes(self):
        """检测资产变化"""
        if not self.last_asset_data:
            return
        
        for exchange, assets in self.asset_data.items():
            if exchange not in self.last_asset_data:
                continue
                
            for currency, data in assets.items():
                if currency in self.last_asset_data[exchange]:
                    last_total = self.last_asset_data[exchange][currency]['total']
                    current_total = data['total']
                    
                    if abs(current_total - last_total) > 1e-8:
                        change = current_total - last_total
                        if change > 0:
                            self.log_asset_change(f"📈 {exchange} {currency} 增加了 {change:.6f}")
                        else:
                            self.log_asset_change(f"📉 {exchange} {currency} 减少了 {abs(change):.6f}")

    def detect_order_changes(self):
        """检测订单变化"""
        if not self.last_order_data:
            # 第一次运行，记录初始订单
            for exchange, orders in self.order_data.items():
                for order in orders:
                    price_info = f"@{order.get('price', '市价')}" if order.get('price') else "市价"
                    # 卖/short方向数量显示为负数
                    amount = order['display_amount']
                    cost_info = f"金额:{order.get('cost', 0):.2f}" if order.get('cost', 0) > 0 else ""
                    fee_info = f"手续费:{order.get('fee_cost', 0):.6f} {order.get('fee_currency', '')}".strip()
                    order_type = order.get('order_type', '现货')
                    self.log_order_change(f"📋 初始订单: {exchange} {order['symbol']} {order_type} {order['side']} {amount:.6f} {price_info} {cost_info} {fee_info}")
            return
        
        # 检测新订单
        for exchange, orders in self.order_data.items():
            if exchange not in self.last_order_data:
                continue
                
            current_order_ids = {order['id'] for order in orders}
            last_order_ids = {order['id'] for order in self.last_order_data[exchange]}
            
            new_orders = current_order_ids - last_order_ids
            for order_id in new_orders:
                order = next((o for o in orders if o['id'] == order_id), None)
                if order:
                    price_info = f"@{order.get('price', '市价')}" if order.get('price') else "市价"
                    # 卖/short方向数量显示为负数
                    amount = order['display_amount']
                    cost_info = f"金额:{order.get('cost', 0):.2f}" if order.get('cost', 0) > 0 else ""
                    fee_info = f"手续费:{order.get('fee_cost', 0):.6f} {order.get('fee_currency', '')}".strip()
                    order_type = order.get('order_type', '现货')
                    self.log_order_change(f"🆕 新订单: {exchange} {order['symbol']} {order_type} {order['side']} {amount:.6f} {price_info} {cost_info} {fee_info}")
            
            # 检测消失的订单（成交或撤销）
            removed_orders = last_order_ids - current_order_ids
            for order_id in removed_orders:
                last_order = next((o for o in self.last_order_data[exchange] if o['id'] == order_id), None)
                if last_order:
                    # 检查订单是否成交
                    if last_order['status'] == 'open':
                        # 原来是open状态，现在消失了，说明成交了
                        price_info = f"@{last_order.get('price', '市价')}" if last_order.get('price') else "市价"
                        # 卖/short方向数量显示为负数
                        amount = -last_order['amount'] if last_order['side'] in ['sell', 'short'] else last_order['amount']
                        cost_info = f"金额:{last_order.get('cost', 0):.2f}" if last_order.get('cost', 0) > 0 else ""
                        fee_info = f"手续费:{last_order.get('fee_cost', 0):.6f} {last_order.get('fee_currency', '')}".strip()
                        order_type = last_order.get('order_type', '现货')
                        self.log_order_change(f"✅ 订单成交: {exchange} {last_order['symbol']} {order_type} {last_order['side']} {amount:.6f} {price_info} {cost_info} {fee_info}")
        
        # 检测订单状态变化
        for exchange, orders in self.order_data.items():
            if exchange not in self.last_order_data:
                continue
                
            for order in orders:
                last_order = next((o for o in self.last_order_data[exchange] if o['id'] == order['id']), None)
                if last_order and order['status'] != last_order['status']:
                    price_info = f"@{order.get('price', '市价')}" if order.get('price') else "市价"
                    # 卖/short方向数量显示为负数
                    amount = order['display_amount']
                    cost_info = f"金额:{order.get('cost', 0):.2f}" if order.get('cost', 0) > 0 else ""
                    fee_info = f"手续费:{order.get('fee_cost', 0):.6f} {order.get('fee_currency', '')}".strip()
                    order_type = order.get('order_type', '现货')
                    self.log_order_change(f"🔄 订单状态变化: {exchange} {order['symbol']} {order_type} {last_order['status']} -> {order['status']} {order['side']} {amount:.6f} {price_info} {cost_info} {fee_info}")

    def cancel_order(self, exchange_name, order_id):
        """撤销订单"""
        try:
            exchange = self.exchanges[exchange_name]
            result = exchange.cancel_order(order_id)
            self.log_order_change(f"✅ 订单撤销成功: {exchange_name} {order_id}")
            # 立即刷新订单
            self.refresh_orders()
        except Exception as e:
            self.log_error(f"订单撤销失败: {exchange_name} {order_id} - {str(e)}")

    def closeEvent(self, event):
        """关闭应用程序"""
        self.worker.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = ExchangeMonitor()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()