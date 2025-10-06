import tkinter as tk
from tkinter import ttk, messagebox
import ccxt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import pandas as pd
import threading
import time
import datetime
from datetime import datetime, timedelta
import json
import requests
import numpy as np
import os

class TokenPriceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("区块链代币价差监控工具 - 配置保存版")
        self.root.geometry("1600x1000")
        
        # 配置文件路径
        self.config_file = "token_monitor_config.json"
        
        # 支持的交易所
        self.exchanges = {
            'binance': ccxt.binance,
            'bybit': ccxt.bybit
        }
        
        # 交易所实例字典
        self.exchange_instances = {}
        
        # 代币列表
        self.tokens = []
        
        # K线周期选项
        self.timeframes = {
            '1分钟': '1m',
            '5分钟': '5m', 
            '15分钟': '15m',
            '1小时': '1h',
            '4小时': '4h',
            '1天': '1d'
        }
        
        # 历史数据周期
        self.history_periods = {
            '1小时': 1,
            '6小时': 6,
            '1天': 24,
            '1周': 168
        }
        
        # 网络状态
        self.network_status = {}
        
        # 自动刷新控制
        self.auto_refresh = False
        self.refresh_interval = 3  # 默认3秒
        
        # 价差数据
        self.spread_data = {}
        
        # 价差阈值设置
        self.upper_threshold = 0.3  # 默认0.3%
        self.lower_threshold = -0.2  # 默认-0.2%
        
        # 机会点统计
        self.opportunity_stats = {
            'upper_opportunities': 0,
            'lower_opportunities': 0,
            'all_opportunity_points': []
        }
        
        self.setup_gui()
        self.load_config()  # 启动时加载配置
        self.start_network_monitor()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_gui(self):
        """设置GUI界面"""
        # 设置matplotlib样式
        plt.style.use('default')
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 网络状态显示
        network_frame = ttk.LabelFrame(control_frame, text="网络状态", padding=5)
        network_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.network_status_label = ttk.Label(network_frame, text="检测中...")
        self.network_status_label.pack()
        
        # 自动刷新设置
        refresh_frame = ttk.LabelFrame(control_frame, text="自动刷新设置", padding=5)
        refresh_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 刷新开关
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_cb = ttk.Checkbutton(refresh_frame, text="启用自动刷新", 
                                        variable=self.auto_refresh_var,
                                        command=self.toggle_auto_refresh)
        auto_refresh_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 刷新间隔
        ttk.Label(refresh_frame, text="刷新间隔(秒):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.refresh_interval_var = tk.StringVar(value="3")
        interval_spinbox = ttk.Spinbox(refresh_frame, from_=1, to=60, width=8,
                                     textvariable=self.refresh_interval_var)
        interval_spinbox.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5,0))
        
        # 立即刷新按钮
        refresh_btn = ttk.Button(refresh_frame, text="立即刷新", command=self.update_chart)
        refresh_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 价差阈值设置
        threshold_frame = ttk.LabelFrame(control_frame, text="价差阈值设置 (%)", padding=5)
        threshold_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 上阈值
        ttk.Label(threshold_frame, text="上阈值 (>):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.upper_threshold_var = tk.StringVar(value="0.3")
        upper_spinbox = ttk.Spinbox(threshold_frame, from_=0.01, to=10.0, increment=0.01, width=8,
                                  textvariable=self.upper_threshold_var)
        upper_spinbox.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5,0))
        
        # 下阈值
        ttk.Label(threshold_frame, text="下阈值 (<):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lower_threshold_var = tk.StringVar(value="-0.2")
        lower_spinbox = ttk.Spinbox(threshold_frame, from_=-10.0, to=-0.01, increment=0.01, width=8,
                                  textvariable=self.lower_threshold_var)
        lower_spinbox.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5,0))
        
        # 分析历史机会按钮
        analyze_btn = ttk.Button(threshold_frame, text="分析历史机会", command=self.analyze_historical_opportunities)
        analyze_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 代币添加区域
        add_token_frame = ttk.LabelFrame(control_frame, text="添加代币", padding=5)
        add_token_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 交易所选择
        ttk.Label(add_token_frame, text="交易所:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.exchange_var = tk.StringVar(value='binance')
        exchange_combo = ttk.Combobox(add_token_frame, textvariable=self.exchange_var, 
                                    values=list(self.exchanges.keys()), state='readonly')
        exchange_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        
        # 代币名称
        ttk.Label(add_token_frame, text="代币名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(add_token_frame, textvariable=self.token_var)
        token_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        
        # 交易类型
        ttk.Label(add_token_frame, text="交易类型:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.type_var = tk.StringVar(value='spot')
        type_combo = ttk.Combobox(add_token_frame, textvariable=self.type_var, 
                                values=['spot', 'swap'], state='readonly')
        type_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        
        # 添加按钮
        add_btn = ttk.Button(add_token_frame, text="添加代币", command=self.add_token)
        add_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 代币列表显示
        token_list_frame = ttk.LabelFrame(control_frame, text="已添加代币 (最多6个)", padding=5)
        token_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.token_listbox = tk.Listbox(token_list_frame, height=6)
        self.token_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 删除代币按钮
        remove_btn = ttk.Button(token_list_frame, text="删除选中代币", command=self.remove_token)
        remove_btn.pack(pady=5)
        
        # 设置区域
        settings_frame = ttk.LabelFrame(control_frame, text="图表设置", padding=5)
        settings_frame.pack(fill=tk.X)
        
        # K线周期选择
        ttk.Label(settings_frame, text="K线周期:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.timeframe_var = tk.StringVar(value='15分钟')
        timeframe_combo = ttk.Combobox(settings_frame, textvariable=self.timeframe_var, 
                                     values=list(self.timeframes.keys()), state='readonly')
        timeframe_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        
        # 历史数据周期
        ttk.Label(settings_frame, text="历史数据:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.history_var = tk.StringVar(value='6小时')
        history_combo = ttk.Combobox(settings_frame, textvariable=self.history_var, 
                                   values=list(self.history_periods.keys()), state='readonly')
        history_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        
        # 图表样式选择
        ttk.Label(settings_frame, text="图表样式:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.chart_style_var = tk.StringVar(value='line')
        style_combo = ttk.Combobox(settings_frame, textvariable=self.chart_style_var, 
                                 values=['line', 'candle'], state='readonly')
        style_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        
        # 配置管理按钮
        config_frame = ttk.LabelFrame(control_frame, text="配置管理", padding=5)
        config_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        load_btn = ttk.Button(config_frame, text="加载配置", command=self.load_config)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = ttk.Button(config_frame, text="重置配置", command=self.reset_config)
        reset_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 右侧主区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 上部：价差分析面板（水平布局）
        analysis_frame = ttk.LabelFrame(right_frame, text="实时价差分析与统计", padding=10)
        analysis_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建水平布局的框架
        analysis_container = ttk.Frame(analysis_frame)
        analysis_container.pack(fill=tk.X)
        
        # 左侧：实时价差
        realtime_frame = ttk.LabelFrame(analysis_container, text="实时价差", padding=8)
        realtime_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.realtime_text = tk.Text(realtime_frame, height=6, font=('Consolas', 9), 
                                   bg='#f8f9fa', fg='#333333', relief='flat')
        self.realtime_text.pack(fill=tk.BOTH, expand=True)
        
        # 中间：历史机会统计
        stats_frame = ttk.LabelFrame(analysis_container, text="历史机会统计", padding=8)
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.stats_text = tk.Text(stats_frame, height=6, font=('Consolas', 9), 
                                bg='#f8f9fa', fg='#333333', relief='flat')
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # 右侧：套利策略
        strategy_frame = ttk.LabelFrame(analysis_container, text="套利策略", padding=8)
        strategy_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.strategy_text = tk.Text(strategy_frame, height=6, font=('Consolas', 9), 
                                   bg='#f8f9fa', fg='#333333', relief='flat')
        self.strategy_text.pack(fill=tk.BOTH, expand=True)
        
        # 图表区域
        chart_frame = ttk.LabelFrame(right_frame, text="价格图表 & 机会点标记", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建matplotlib图表
        self.fig, self.ax = plt.subplots(figsize=(12, 8), facecolor='white')
        self.ax.set_facecolor('#f8f9fa')
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 最后更新时间
        self.last_update_var = tk.StringVar(value="最后更新: 从未")
        last_update_label = ttk.Label(self.root, textvariable=self.last_update_var, relief=tk.SUNKEN)
        last_update_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'tokens': self.tokens,
                'auto_refresh': self.auto_refresh_var.get(),
                'refresh_interval': self.refresh_interval_var.get(),
                'upper_threshold': self.upper_threshold_var.get(),
                'lower_threshold': self.lower_threshold_var.get(),
                'timeframe': self.timeframe_var.get(),
                'history_period': self.history_var.get(),
                'chart_style': self.chart_style_var.get(),
                'exchange': self.exchange_var.get(),
                'token_type': self.type_var.get(),
                'last_save_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.status_var.set(f"配置已保存到 {self.config_file}")
            print(f"配置已保存: {config}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if not os.path.exists(self.config_file):
                self.status_var.set("未找到配置文件，使用默认配置")
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载代币列表
            if 'tokens' in config:
                self.tokens = config['tokens']
                self.token_listbox.delete(0, tk.END)
                for token in self.tokens:
                    self.token_listbox.insert(tk.END, token['display_name'])
            
            # 加载自动刷新设置
            if 'auto_refresh' in config:
                self.auto_refresh_var.set(config['auto_refresh'])
            
            if 'refresh_interval' in config:
                self.refresh_interval_var.set(config['refresh_interval'])
            
            # 加载阈值设置
            if 'upper_threshold' in config:
                self.upper_threshold_var.set(config['upper_threshold'])
            
            if 'lower_threshold' in config:
                self.lower_threshold_var.set(config['lower_threshold'])
            
            # 加载图表设置
            if 'timeframe' in config:
                self.timeframe_var.set(config['timeframe'])
            
            if 'history_period' in config:
                self.history_var.set(config['history_period'])
            
            if 'chart_style' in config:
                self.chart_style_var.set(config['chart_style'])
            
            # 加载默认交易所和类型
            if 'exchange' in config:
                self.exchange_var.set(config['exchange'])
            
            if 'token_type' in config:
                self.type_var.set(config['token_type'])
            
            # 更新自动刷新状态
            if self.auto_refresh_var.get():
                self.toggle_auto_refresh()
            
            last_save_time = config.get('last_save_time', '未知')
            self.status_var.set(f"配置已加载 (最后保存: {last_save_time})")
            print(f"配置已加载: {config}")
            
            # 如果有代币，自动更新图表
            if self.tokens:
                self.root.after(1000, self.update_chart)  # 延迟1秒后更新图表
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def reset_config(self):
        """重置配置为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有配置吗？"):
            # 清空代币列表
            self.tokens = []
            self.token_listbox.delete(0, tk.END)
            
            # 重置所有变量为默认值
            self.auto_refresh_var.set(False)
            self.refresh_interval_var.set("3")
            self.upper_threshold_var.set("0.3")
            self.lower_threshold_var.set("-0.2")
            self.timeframe_var.set("15分钟")
            self.history_var.set("6小时")
            self.chart_style_var.set("line")
            self.exchange_var.set("binance")
            self.type_var.set("spot")
            
            # 停止自动刷新
            self.auto_refresh = False
            
            # 清空图表
            self.ax.clear()
            self.ax.text(0.5, 0.5, '请添加代币开始监控', transform=self.ax.transAxes, 
                        ha='center', va='center', fontsize=16, color='black')
            self.canvas.draw()
            
            self.status_var.set("配置已重置为默认值")
    
    def on_closing(self):
        """窗口关闭时自动保存配置"""
        self.save_config()
        self.root.destroy()
    
    def toggle_auto_refresh(self):
        """切换自动刷新状态"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            try:
                self.refresh_interval = int(self.refresh_interval_var.get())
                if self.refresh_interval < 1:
                    self.refresh_interval = 1
            except:
                self.refresh_interval = 3
                
            self.start_auto_refresh()
            self.status_var.set(f"自动刷新已启用 - 间隔{self.refresh_interval}秒")
        else:
            self.status_var.set("自动刷新已禁用")
        
        # 自动保存配置
        self.save_config()
    
    def start_auto_refresh(self):
        """启动自动刷新"""
        def auto_refresh_loop():
            while self.auto_refresh:
                if self.tokens:
                    self.update_chart()
                time.sleep(self.refresh_interval)
        
        if self.auto_refresh:
            threading.Thread(target=auto_refresh_loop, daemon=True).start()
    
    def get_exchange_instance(self, exchange_name):
        """获取交易所实例"""
        if exchange_name not in self.exchange_instances:
            try:
                exchange_class = self.exchanges[exchange_name]
                self.exchange_instances[exchange_name] = exchange_class({
                    'timeout': 30000,
                    'enableRateLimit': True,
                    'proxies': {
                        'http': 'http://127.0.0.1:1080',
                        'https': 'http://127.0.0.1:1080',
                    }
                })
                self.exchange_instances[exchange_name].fetch_markets()
                self.network_status[exchange_name] = True
            except Exception as e:
                messagebox.showerror("错误", f"连接{exchange_name}失败: {str(e)}")
                return None
        return self.exchange_instances[exchange_name]
    
    def add_token(self):
        """添加代币到监控列表"""
        if len(self.tokens) >= 6:
            messagebox.showwarning("警告", "最多只能添加6个代币")
            return
            
        exchange = self.exchange_var.get()
        token = self.token_var.get().strip().upper()
        token_type = self.type_var.get()
        
        if not token:
            messagebox.showwarning("警告", "请输入代币名称")
            return
            
        if not self.get_exchange_instance(exchange):
            return
            
        token_info = {
            'exchange': exchange,
            'symbol': token,
            'type': token_type,
            'display_name': f"{exchange}_{token}_{token_type}"
        }
        
        self.tokens.append(token_info)
        self.token_listbox.insert(tk.END, token_info['display_name'])
        self.token_var.set("")
        
        # 自动保存配置
        self.save_config()
        
        if not self.auto_refresh and self.tokens:
            self.auto_refresh_var.set(True)
            self.toggle_auto_refresh()
    
    def remove_token(self):
        """删除选中的代币"""
        selection = self.token_listbox.curselection()
        if selection:
            index = selection[0]
            self.token_listbox.delete(index)
            self.tokens.pop(index)
            
            # 自动保存配置
            self.save_config()
    
    def calculate_spread(self, current_prices):
        """计算价差"""
        if len(current_prices) < 2:
            return {}
        
        prices = list(current_prices.values())
        tokens = list(current_prices.keys())
        
        max_price = max(prices)
        min_price = min(prices)
        max_token = tokens[prices.index(max_price)]
        min_token = tokens[prices.index(min_price)]
        absolute_spread = max_price - min_price
        percentage_spread = (absolute_spread / min_price) * 100
        
        return {
            'max_token': max_token,
            'max_price': max_price,
            'min_token': min_token,
            'min_price': min_price,
            'absolute_spread': absolute_spread,
            'percentage_spread': percentage_spread,
            'all_prices': current_prices
        }
    
    def analyze_historical_opportunities(self):
        """分析历史机会点"""
        if len(self.tokens) != 2:
            messagebox.showwarning("警告", "历史机会分析需要恰好2个代币")
            return
        
        try:
            self.upper_threshold = float(self.upper_threshold_var.get())
            self.lower_threshold = float(self.lower_threshold_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的阈值")
            return
        
        self.status_var.set("正在分析历史机会点...")
        threading.Thread(target=self._analyze_historical_opportunities_thread, daemon=True).start()
    
    def _analyze_historical_opportunities_thread(self):
        """在后台线程中分析历史机会点"""
        try:
            timeframe = self.timeframes[self.timeframe_var.get()]
            history_hours = self.history_periods[self.history_var.get()]
            
            all_data = {}
            for token in self.tokens:
                data = self.fetch_ohlcv_data(token, timeframe, history_hours)
                if data is not None and not data.empty:
                    all_data[token['display_name']] = data
            
            if len(all_data) != 2:
                self.root.after(0, lambda: messagebox.showerror("错误", "无法获取两个代币的完整数据"))
                return
            
            self._calculate_historical_opportunities(all_data)
            self.root.after(0, self.update_chart)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"分析失败: {str(e)}"))
    
    def _calculate_historical_opportunities(self, all_data):
        """计算历史机会点"""
        self.opportunity_stats = {
            'upper_opportunities': 0,
            'lower_opportunities': 0,
            'all_opportunity_points': []
        }
        
        token_names = list(all_data.keys())
        data_a = all_data[token_names[0]]
        data_b = all_data[token_names[1]]
        
        common_index = data_a.index.intersection(data_b.index)
        data_a_aligned = data_a.loc[common_index]
        data_b_aligned = data_b.loc[common_index]
        
        for timestamp in common_index:
            price_a = data_a_aligned.loc[timestamp, 'close']
            price_b = data_b_aligned.loc[timestamp, 'close']
            
            spread_percentage = ((price_a - price_b) / price_b) * 100
            
            opportunity_type = None
            if spread_percentage > self.upper_threshold:
                self.opportunity_stats['upper_opportunities'] += 1
                opportunity_type = 'upper'
            elif spread_percentage < self.lower_threshold:
                self.opportunity_stats['lower_opportunities'] += 1
                opportunity_type = 'lower'
            
            if opportunity_type:
                self.opportunity_stats['all_opportunity_points'].append({
                    'timestamp': timestamp,
                    'type': opportunity_type,
                    'spread': spread_percentage,
                    'price_a': price_a,
                    'price_b': price_b
                })
    
    def update_spread_display(self, spread_info):
        """更新价差显示"""
        self.realtime_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)
        self.strategy_text.delete(1.0, tk.END)
        
        if not spread_info:
            self.realtime_text.insert(tk.END, "需要至少2个代币\n才能计算价差")
            return
        
        # 左侧：实时价差信息
        self.realtime_text.insert(tk.END, "📊 实时价差信息\n", 'subtitle')
        self.realtime_text.insert(tk.END, 
            f"最高价:\n{spread_info['max_token']}\n"
            f"${spread_info['max_price']:.6f}\n\n"
            f"最低价:\n{spread_info['min_token']}\n"
            f"${spread_info['min_price']:.6f}\n\n"
            f"绝对价差:\n${spread_info['absolute_spread']:.6f}\n\n"
            f"百分比价差:\n{spread_info['percentage_spread']:.4f}%", 'highlight')
        
        # 中间：历史机会统计
        self.stats_text.insert(tk.END, "📈 历史机会统计\n", 'subtitle')
        self.stats_text.insert(tk.END, 
            f"上阈值: {self.upper_threshold}%\n"
            f"机会次数: {self.opportunity_stats['upper_opportunities']}\n\n"
            f"下阈值: {self.lower_threshold}%\n"
            f"机会次数: {self.opportunity_stats['lower_opportunities']}\n\n"
            f"总机会点:\n{len(self.opportunity_stats['all_opportunity_points'])} 次\n\n"
            f"代币数量: {len(spread_info['all_prices'])}", 'stats')
        
        # 右侧：套利策略
        self.strategy_text.insert(tk.END, "💡 实时套利策略\n", 'subtitle')
        
        current_spread = spread_info['percentage_spread']
        if current_spread > self.upper_threshold:
            self.strategy_text.insert(tk.END, 
                f"🔴 上阈值机会!\n\n"
                f"买入: {spread_info['min_token']}\n"
                f"卖出: {spread_info['max_token']}\n\n"
                f"预期收益:\n{current_spread:.4f}%", 'opportunity_upper')
        elif current_spread < self.lower_threshold:
            self.strategy_text.insert(tk.END, 
                f"🔵 下阈值机会!\n\n"
                f"买入: {spread_info['max_token']}\n"
                f"卖出: {spread_info['min_token']}\n\n"
                f"预期收益:\n{abs(current_spread):.4f}%", 'opportunity_lower')
        else:
            self.strategy_text.insert(tk.END, 
                f"🟢 价差在阈值内\n\n"
                f"当前: {current_spread:.4f}%\n"
                f"上阈: {self.upper_threshold}%\n"
                f"下阈: {self.lower_threshold}%", 'normal')
        
        # 配置文本样式
        for text_widget in [self.realtime_text, self.stats_text, self.strategy_text]:
            text_widget.tag_configure('subtitle', foreground='#2c3e50', font=('Consolas', 9, 'bold'))
            text_widget.tag_configure('highlight', foreground='#e74c3c', font=('Consolas', 9))
            text_widget.tag_configure('stats', foreground='#3498db', font=('Consolas', 9))
            text_widget.tag_configure('opportunity_upper', foreground='#e74c3c', font=('Consolas', 9, 'bold'))
            text_widget.tag_configure('opportunity_lower', foreground='#2980b9', font=('Consolas', 9, 'bold'))
            text_widget.tag_configure('normal', foreground='#27ae60', font=('Consolas', 9))
    
    def fetch_ohlcv_data(self, token_info, timeframe, hours_back=24):
        """获取K线数据"""
        try:
            exchange = self.get_exchange_instance(token_info['exchange'])
            if not exchange:
                return None
                
            symbol = token_info['symbol']
            if token_info['type'] == 'spot':
                symbol += '/USDT'
            else:
                symbol += '/USDT:USDT'
                
            since = exchange.milliseconds() - (hours_back * 60 * 60 * 1000)
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            
            if not ohlcv:
                return None
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"获取{token_info['display_name']}数据失败: {str(e)}")
            return None
    
    def update_chart(self):
        """更新图表"""
        if not self.tokens:
            return
            
        self.status_var.set("正在更新图表...")
        threading.Thread(target=self._update_chart_thread, daemon=True).start()
    
    def _update_chart_thread(self):
        """在后台线程中更新图表"""
        try:
            timeframe = self.timeframes[self.timeframe_var.get()]
            history_hours = self.history_periods[self.history_var.get()]
            chart_style = self.chart_style_var.get()
            
            all_data = {}
            current_prices = {}
            
            for token in self.tokens:
                data = self.fetch_ohlcv_data(token, timeframe, history_hours)
                if data is not None and not data.empty:
                    all_data[token['display_name']] = data
                    current_prices[token['display_name']] = data['close'].iloc[-1]
            
            spread_info = self.calculate_spread(current_prices)
            
            if len(self.tokens) == 2 and len(all_data) == 2:
                try:
                    self.upper_threshold = float(self.upper_threshold_var.get())
                    self.lower_threshold = float(self.lower_threshold_var.get())
                    self._calculate_historical_opportunities(all_data)
                except:
                    pass
            
            self.root.after(0, lambda: self._update_interface(all_data, current_prices, spread_info, timeframe, chart_style))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"更新失败: {str(e)}"))
    
    def _update_interface(self, all_data, current_prices, spread_info, timeframe, chart_style):
        """更新界面"""
        self.update_spread_display(spread_info)
        self._draw_chart(all_data, current_prices, spread_info, timeframe, chart_style)
    
    def _draw_chart(self, all_data, current_prices, spread_info, timeframe, chart_style):
        """绘制图表"""
        self.ax.clear()
        
        if not all_data:
            self.ax.text(0.5, 0.5, '无法获取数据', transform=self.ax.transAxes, 
                        ha='center', va='center', fontsize=16, color='black')
            self.canvas.draw()
            self.status_var.set("数据获取失败")
            return
        
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        
        if chart_style == 'line':
            for i, (name, data) in enumerate(all_data.items()):
                if i < len(colors):
                    color = colors[i]
                    linewidth = 2.5 if len(all_data) <= 3 else 2.0
                    
                    price_label = f'{name} (${current_prices[name]:.4f})'
                    if spread_info and len(spread_info.get('all_prices', {})) >= 2:
                        if name == spread_info.get('max_token'):
                            price_label += ' ↗最高'
                        elif name == spread_info.get('min_token'):
                            price_label += ' ↘最低'
                    
                    self.ax.plot(data.index, data['close'], label=price_label, 
                               color=color, linewidth=linewidth, alpha=0.9)
                    
                    last_price = data['close'].iloc[-1]
                    last_time = data.index[-1]
                    self.ax.scatter(last_time, last_price, color=color, s=80, 
                                  zorder=5, edgecolors='white', linewidth=1.5)
        
        else:
            for i, (name, data) in enumerate(all_data.items()):
                if i < len(colors):
                    color = colors[i]
                    for idx in range(len(data)):
                        row = data.iloc[idx]
                        self.ax.plot([data.index[idx], data.index[idx]], 
                                   [row['low'], row['high']], 
                                   color=color, linewidth=1.2, alpha=0.8)
                        body_color = color if row['close'] >= row['open'] else '#e74c3c'
                        body_height = abs(row['close'] - row['open'])
                        if body_height > 0:
                            self.ax.bar(data.index[idx], body_height, 
                                      bottom=min(row['open'], row['close']),
                                      color=body_color, alpha=0.7, width=0.0001)
                    
                    price_label = f'{name} (${current_prices[name]:.4f})'
                    if spread_info and len(spread_info.get('all_prices', {})) >= 2:
                        if name == spread_info.get('max_token'):
                            price_label += ' ↗最高'
                        elif name == spread_info.get('min_token'):
                            price_label += ' ↘最低'
                    
                    self.ax.plot([], [], label=price_label, 
                               color=color, linewidth=3)
        
        if len(self.tokens) == 2 and self.opportunity_stats['all_opportunity_points']:
            for opportunity in self.opportunity_stats['all_opportunity_points']:
                timestamp = opportunity['timestamp']
                opportunity_type = opportunity['type']
                spread_value = opportunity['spread']
                
                avg_price = (opportunity['price_a'] + opportunity['price_b']) / 2
                
                if opportunity_type == 'upper':
                    self.ax.scatter(timestamp, avg_price, color='#e74c3c', s=120, 
                                  marker='o', alpha=0.9, edgecolors='white', linewidth=2,
                                  label='上阈值机会' if opportunity == self.opportunity_stats['all_opportunity_points'][0] else "")
                    self.ax.annotate(f'+{spread_value:.2f}%', (timestamp, avg_price),
                                   xytext=(12, 12), textcoords='offset points',
                                   fontsize=9, color='#e74c3c', weight='bold',
                                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
                else:
                    self.ax.scatter(timestamp, avg_price, color='#3498db', s=120, 
                                  marker='s', alpha=0.9, edgecolors='white', linewidth=2,
                                  label='下阈值机会' if opportunity == self.opportunity_stats['all_opportunity_points'][0] else "")
                    self.ax.annotate(f'{spread_value:.2f}%', (timestamp, avg_price),
                                   xytext=(12, -20), textcoords='offset points',
                                   fontsize=9, color='#3498db', weight='bold',
                                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        title = f'代币价格对比 - {timeframe} K线'
        if spread_info and len(spread_info.get('all_prices', {})) >= 2:
            title += f' | 实时价差: {spread_info["percentage_spread"]:.4f}%'
        if len(self.tokens) == 2:
            title += f' | 机会点: ↑{self.opportunity_stats["upper_opportunities"]} ↓{self.opportunity_stats["lower_opportunities"]}'
        
        self.ax.set_title(title, color='#2c3e50', fontsize=16, pad=20, weight='bold')
        self.ax.set_ylabel('价格 (USDT)', color='#2c3e50', fontsize=12, weight='bold')
        self.ax.set_xlabel('时间', color='#2c3e50', fontsize=12, weight='bold')
        
        legend = self.ax.legend(facecolor='white', edgecolor='#bdc3c7', 
                              fontsize=10, loc='upper left', framealpha=0.9)
        for text in legend.get_texts():
            text.set_color('#2c3e50')
        
        self.ax.grid(True, alpha=0.3, color='#bdc3c7', linestyle='--')
        self.ax.tick_params(colors='#2c3e50')
        self.ax.spines['bottom'].set_color('#bdc3c7')
        self.ax.spines['top'].set_color('#bdc3c7')
        self.ax.spines['right'].set_color('#bdc3c7')
        self.ax.spines['left'].set_color('#bdc3c7')
        self.ax.set_facecolor('#f8f9fa')
        
        if len(all_data) > 0:
            first_data = list(all_data.values())[0]
            if len(first_data) > 0:
                if len(first_data) > 100:
                    date_format = mdates.DateFormatter('%m-%d')
                else:
                    date_format = mdates.DateFormatter('%m-%d %H:%M')
                self.ax.xaxis.set_major_formatter(date_format)
                self.fig.autofmt_xdate()
        
        self.fig.tight_layout()
        self.canvas.draw()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_var.set(f"最后更新: {current_time}")
        
        token_count = len(all_data)
        status_text = f"图表更新完成 - 共{token_count}个代币"
        if spread_info and len(spread_info.get('all_prices', {})) >= 2:
            status_text += f" | 实时价差: {spread_info['percentage_spread']:.4f}%"
        if len(self.tokens) == 2:
            status_text += f" | 历史机会: ↑{self.opportunity_stats['upper_opportunities']} ↓{self.opportunity_stats['lower_opportunities']}"
        self.status_var.set(status_text)
    
    def test_exchange_connection(self, exchange_name):
        """测试交易所连接"""
        try:
            exchange = self.get_exchange_instance(exchange_name)
            if exchange:
                markets = exchange.fetch_markets()
                return len(markets) > 0
        except:
            pass
        return False
    
    def start_network_monitor(self):
        """启动网络监控"""
        def monitor():
            while True:
                status_text = "网络状态: "
                for exchange_name in self.exchanges.keys():
                    is_connected = self.test_exchange_connection(exchange_name)
                    status = "✓" if is_connected else "✗"
                    status_text += f"{exchange_name}{status} "
                    self.network_status[exchange_name] = is_connected
                
                self.root.after(0, lambda: self.network_status_label.config(
                    text=status_text, 
                    foreground="green" if all(self.network_status.values()) else "red"
                ))
                time.sleep(30)
        
        threading.Thread(target=monitor, daemon=True).start()

def main():
    root = tk.Tk()
    app = TokenPriceMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()