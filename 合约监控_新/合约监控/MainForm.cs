using System;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;

namespace FuturesTradeViewer
{
    public partial class MainForm : Form
    {
        private BinanceWebSocketManager? webSocketManager;
        private AbnormalTradeDetector abnormalDetector;
        private System.Windows.Forms.Timer statsUpdateTimer;
        private BinanceApiClient? apiClient;
        private OrderBookData? latestOrderBookData = null; // 缓存最新的订单簿数据

        public MainForm()
        {
            InitializeComponent();
            InitializeAbnormalMonitor();
            InitializePriceTickComboBox();
        }

        /// <summary>
        /// 初始化异常监控器
        /// </summary>
        private void InitializeAbnormalMonitor()
        {
            // 创建检测器实例
            abnormalDetector = new AbnormalTradeDetector
            {
                MinThreshold = thresholdNumeric.Value,
                ShortTermMultiple = multipleNumeric.Value,
                ShortTermMinutes = GetSelectedWindowMinutes(),
                OnlyActiveTaker = onlyActiveTakerCheckBox.Checked,
                // 连续大单配置
                EnableConsecutiveDetection = enableConsecutiveCheckBox.Checked,
                ConsecutiveWindowSeconds = GetSelectedConsecutiveWindowSeconds(),
                ConsecutiveMinCount = (int)consecutiveCountNumeric.Value,
                ConsecutiveMinThreshold = consecutiveThresholdNumeric.Value,
                ConsecutiveSameDirectionOnly = consecutiveSameDirectionCheckBox.Checked
            };

            // 初始化表格
            DataGridViewHelper.InitializeAbnormalGrid(abnormalGrid);
            DataGridViewHelper.InitializeConsecutiveHistoryGrid(consecutiveHistoryGrid);
            DataGridViewHelper.InitializeLiquidationGrid(liquidationGrid);

            // 设置参数控件事件
            SetupParameterEventHandlers();

            // 初始化爆仓监控参数
            InitializeLiquidationMonitor();

            // 创建统计更新定时器
            statsUpdateTimer = new System.Windows.Forms.Timer
            {
                Interval = Constants.StatsUpdateInterval
            };
            statsUpdateTimer.Tick += StatsUpdateTimer_Tick;
            statsUpdateTimer.Start();
        }

        /// <summary>
        /// 初始化价格精度选择器
        /// </summary>
        private void InitializePriceTickComboBox()
        {
            // 默认选中 50（索引 5）
            priceTickComboBox.SelectedIndex = 5;
        }

        /// <summary>
        /// 初始化爆仓监控
        /// </summary>
        private void InitializeLiquidationMonitor()
        {
            // 默认选中15分钟窗口
            liquidationWindowComboBox.SelectedIndex = 2;

            // 设置事件处理器
            liquidationThresholdNumeric.ValueChanged += (s, e) =>
            {
                webSocketManager?.UpdateLiquidationMonitorParams(
                    GetLiquidationWindowMinutes(),
                    liquidationThresholdNumeric.Value);
            };

            liquidationWindowComboBox.SelectedIndexChanged += (s, e) =>
            {
                webSocketManager?.UpdateLiquidationMonitorParams(
                    GetLiquidationWindowMinutes(),
                    liquidationThresholdNumeric.Value);
            };
        }

        /// <summary>
        /// 获取爆仓统计时间窗口（分钟）
        /// </summary>
        private int GetLiquidationWindowMinutes()
        {
            return liquidationWindowComboBox.SelectedIndex switch
            {
                0 => 1,
                1 => 5,
                2 => 15,
                3 => 30,
                _ => 15
            };
        }

        /// <summary>
        /// 设置参数控件事件处理器
        /// </summary>
        private void SetupParameterEventHandlers()
        {
            windowComboBox.SelectedIndexChanged += (s, e) =>
            {
                abnormalDetector.ShortTermMinutes = GetSelectedWindowMinutes();
            };
            multipleNumeric.ValueChanged += (s, e) =>
            {
                abnormalDetector.ShortTermMultiple = multipleNumeric.Value;
            };
            thresholdNumeric.ValueChanged += (s, e) =>
            {
                abnormalDetector.MinThreshold = thresholdNumeric.Value;
                // 同时更新大单统计管理器的阈值
                webSocketManager?.UpdateLargeOrderThreshold(thresholdNumeric.Value);
            };
            onlyActiveTakerCheckBox.CheckedChanged += (s, e) =>
            {
                abnormalDetector.OnlyActiveTaker = onlyActiveTakerCheckBox.Checked;
            };

            // 连续大单配置事件
            enableConsecutiveCheckBox.CheckedChanged += (s, e) =>
            {
                abnormalDetector.EnableConsecutiveDetection = enableConsecutiveCheckBox.Checked;
            };
            consecutiveWindowComboBox.SelectedIndexChanged += (s, e) =>
            {
                abnormalDetector.ConsecutiveWindowSeconds = GetSelectedConsecutiveWindowSeconds();
            };
            consecutiveCountNumeric.ValueChanged += (s, e) =>
            {
                abnormalDetector.ConsecutiveMinCount = (int)consecutiveCountNumeric.Value;
            };
            consecutiveThresholdNumeric.ValueChanged += (s, e) =>
            {
                abnormalDetector.ConsecutiveMinThreshold = consecutiveThresholdNumeric.Value;
            };
            consecutiveSameDirectionCheckBox.CheckedChanged += (s, e) =>
            {
                abnormalDetector.ConsecutiveSameDirectionOnly = consecutiveSameDirectionCheckBox.Checked;
            };
        }

        /// <summary>
        /// 获取选中的时间窗口（分钟）
        /// </summary>
        private int GetSelectedWindowMinutes()
        {
            return windowComboBox.SelectedIndex switch
            {
                0 => 1,
                1 => 3,
                2 => 5,
                3 => 10,
                _ => 5
            };
        }

        /// <summary>
        /// 获取选中的连续检测窗口（秒）
        /// </summary>
        private int GetSelectedConsecutiveWindowSeconds()
        {
            return consecutiveWindowComboBox.SelectedIndex switch
            {
                0 => 30,
                1 => 60,
                2 => 90,
                3 => 120,
                4 => 180,
                _ => 60
            };
        }

        /// <summary>
        /// 获取当前选中的价格精度
        /// </summary>
        private decimal GetSelectedTickSize()
        {
            return priceTickComboBox.SelectedIndex switch
            {
                0 => 0.01m,
                1 => 0.1m,
                2 => 1m,
                3 => 5m,
                4 => 10m,
                5 => 50m,
                6 => 100m,
                _ => 50m
            };
        }

        /// <summary>
        /// 聚合订单簿数据（按价格精度）
        /// </summary>
        private List<(string price, string qty)> AggregateOrders(List<(string price, string qty)> orders, decimal tickSize)
        {
            if (orders == null || orders.Count == 0)
                return new List<(string, string)>();

            var grouped = new Dictionary<decimal, decimal>();

            foreach (var (priceStr, qtyStr) in orders)
            {
                if (!decimal.TryParse(priceStr, out decimal price) || !decimal.TryParse(qtyStr, out decimal qty))
                    continue;

                // 按精度向下取整（聚合到最接近的档位）
                // 使用 Math.Round 来避免浮点数精度问题
                decimal aggregatedPrice = Math.Round(Math.Floor(price / tickSize) * tickSize, GetDecimalPlaces(tickSize));

                if (grouped.ContainsKey(aggregatedPrice))
                    grouped[aggregatedPrice] += qty;
                else
                    grouped[aggregatedPrice] = qty;
            }

            // 根据tickSize确定价格显示的小数位数
            int priceDecimals = GetDecimalPlaces(tickSize);
            string priceFormat = $"F{priceDecimals}";

            // 保持原始顺序（从低到高）
            return grouped
                .OrderBy(x => x.Key)
                .Select(x => (x.Key.ToString(priceFormat), x.Value.ToString("F4")))
                .ToList();
        }

        /// <summary>
        /// 根据 tickSize 获取小数位数
        /// </summary>
        private int GetDecimalPlaces(decimal tickSize)
        {
            return tickSize switch
            {
                0.01m => 2,
                0.1m => 1,
                _ => 0  // 1, 5, 10, 50, 100 都不需要小数位
            };
        }

        /// <summary>
        /// 刷新订单簿显示（使用缓存数据重新聚合）
        /// </summary>
        private void RefreshOrderBookDisplay()
        {
            if (latestOrderBookData == null) return;

            // 🔑 整个方法在UI线程执行，避免跨线程访问UI控件
            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                decimal tickSize = GetSelectedTickSize();
                var aggregatedAsks = AggregateOrders(latestOrderBookData.Asks, tickSize);
                var aggregatedBids = AggregateOrders(latestOrderBookData.Bids, tickSize);

                DataGridViewHelper.UpdateOrderGrid(sellGrid, aggregatedAsks);
                DataGridViewHelper.UpdateOrderGrid(buyGrid, aggregatedBids);
            });
        }

        /// <summary>
        /// 统计更新定时器事件
        /// </summary>
        private void StatsUpdateTimer_Tick(object? sender, EventArgs e)
        {
            if (abnormalDetector == null) return;

            try
            {
                var stats = abnormalDetector.GetStatistics();
                UpdateStatisticsPanel(stats);

                // 更新连续大单统计
                if (abnormalDetector.EnableConsecutiveDetection)
                {
                    var consecutiveStats = abnormalDetector.GetConsecutiveStatistics();
                    UpdateConsecutiveStatistics(consecutiveStats);

                    // 更新连续大单历史列表
                    UpdateConsecutiveHistoryGrid();
                }

                // 更新爆仓统计
                UpdateLiquidationStatistics();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"统计更新错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 更新统计面板
        /// </summary>
        private void UpdateStatisticsPanel(TradeStatistics stats)
        {
            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                int windowMinutes = GetSelectedWindowMinutes();
                statsShortTermLabel.Text = $"短期({windowMinutes}分钟)：平均 {stats.ShortTermAverage:F4} BTC/笔 | 总笔数：{stats.ShortTermCount}笔";

                // 显示长期统计和基准信息
                string longTermText = $"长期(30分钟)：平均 {stats.LongTermAverage:F4} BTC/笔 | 总笔数：{stats.LongTermCount}笔";
                if (!string.IsNullOrEmpty(stats.BaselineInfo))
                {
                    longTermText += $" [{stats.BaselineInfo}]";
                    if (stats.HistoricalBaseline > 0)
                    {
                        longTermText += $" (历史基准: {stats.HistoricalBaseline:F4})";
                    }
                }
                statsLongTermLabel.Text = longTermText;

                // statsMarketStatusLabel.Text = $"市场状态：【{stats.MarketStatus}】";  // 已取消市场状态显示
                statsBuyAbnormalLabel.Text = $"买入大单：{stats.BuyAbnormalCount}笔({stats.BuyAbnormalVolume:F2} BTC) 🟢";
                statsSellAbnormalLabel.Text = $"卖出大单：{stats.SellAbnormalCount}笔({stats.SellAbnormalVolume:F2} BTC) 🔴";
                statsDirectionLabel.Text = $"大单方向：【{stats.DirectionIndicator}】";
            });
        }

        /// <summary>
        /// 更新连续大单统计
        /// </summary>
        private void UpdateConsecutiveStatistics(ConsecutiveStatistics stats)
        {
            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                // 买入统计
                consecutiveBuyCountLabel.Text = $"买入: {stats.BuyCount}/{stats.MinCount}笔";
                consecutiveBuyVolumeLabel.Text = $"总量: {stats.BuyTotalVolume:F2} BTC";
                consecutiveBuyStatusLabel.Text = stats.BuyStatusText;
                consecutiveBuyStatusLabel.ForeColor = stats.BuyTriggered
                    ? Constants.ConsecutiveBuyTriggeredColor
                    : Constants.NotTriggeredColor;

                // 卖出统计
                consecutiveSellCountLabel.Text = $"卖出: {stats.SellCount}/{stats.MinCount}笔";
                consecutiveSellVolumeLabel.Text = $"总量: {stats.SellTotalVolume:F2} BTC";
                consecutiveSellStatusLabel.Text = stats.SellStatusText;
                consecutiveSellStatusLabel.ForeColor = stats.SellTriggered
                    ? Constants.ConsecutiveSellTriggeredColor
                    : Constants.NotTriggeredColor;
            });
        }

        /// <summary>
        /// 更新连续大单历史表格
        /// </summary>
        private void UpdateConsecutiveHistoryGrid()
        {
            var events = abnormalDetector.GetConsecutiveEvents();
            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                DataGridViewHelper.UpdateConsecutiveHistoryGrid(consecutiveHistoryGrid, events);
            });
        }

        /// <summary>
        /// 更新爆仓统计
        /// </summary>
        private void UpdateLiquidationStatistics()
        {
            var stats = webSocketManager?.GetLiquidationStatistics();
            if (stats == null) return;

            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                liquidationLongCountLabel.Text = $"多头爆仓: {stats.LongLiquidationCount} 笔 / {stats.TotalLongQuantity:F4} 币";
                liquidationLongVolumeLabel.Text = $"多头金额: ${stats.TotalLongValue:F2}";
                liquidationShortCountLabel.Text = $"空头爆仓: {stats.ShortLiquidationCount} 笔 / {stats.TotalShortQuantity:F4} 币";
                liquidationShortVolumeLabel.Text = $"空头金额: ${stats.TotalShortValue:F2}";
                
                // 显示最大爆仓，带方向标识和颜色
                if (stats.LargestLiquidationValue > 0)
                {
                    string direction = stats.IsLargestLongLiquidation ? "多头 🔴" : "空头 🟢";
                    liquidationLargestLabel.Text = $"最大爆仓: {stats.LargestLiquidationQuantity:F4} / ${stats.LargestLiquidationValue:F2} ({direction})";
                    liquidationLargestLabel.ForeColor = stats.IsLargestLongLiquidation ? Color.DarkRed : Color.DarkGreen;
                }
                else
                {
                    liquidationLargestLabel.Text = "最大爆仓: 0.0000 / $0.00";
                    liquidationLargestLabel.ForeColor = Color.Black;
                }
            });
        }

        /// <summary>
        /// 连接按钮点击事件
        /// </summary>
        private async void ConnectButton_Click(object sender, EventArgs e)
        {
            string symbol = symbolBox.Text.Trim().ToLower();

            // 清空异常检测器数据
            abnormalDetector?.Clear();

            // 清空订单簿缓存
            latestOrderBookData = null;

            // 初始化表格
            DataGridViewHelper.InitializeTradeGrid(tradeGrid);
            DataGridViewHelper.InitializeAbnormalGrid(abnormalGrid);
            DataGridViewHelper.InitializeOrderBookGrid(sellGrid, isBuyOrder: false);
            DataGridViewHelper.InitializeOrderBookGrid(buyGrid, isBuyOrder: true);
            DataGridViewHelper.InitializeLiquidationGrid(liquidationGrid);

            connectButton.Enabled = false;
            connectButton.Text = "连接中...";

            try
            {
                // 释放旧的 WebSocket 连接
                webSocketManager?.Dispose();

                // 创建新的 WebSocket 管理器
                string? proxyUrl = useProxyCheckBox.Checked ? proxyTextBox.Text.Trim() : null;
                decimal largeOrderThreshold = thresholdNumeric.Value; // 使用异常大单监控的最小量阈值
                webSocketManager = new BinanceWebSocketManager(proxyUrl, largeOrderThreshold);

                // 订阅事件
                webSocketManager.OnTradeReceived += OnTradeReceived;
                webSocketManager.OnOrderBookReceived += OnOrderBookReceived;
                webSocketManager.OnLiquidationReceived += OnLiquidationReceived;
                webSocketManager.OnError += OnWebSocketError;
                webSocketManager.OnReconnecting += OnWebSocketReconnecting;
                webSocketManager.OnReconnected += OnWebSocketReconnected;

                // 连接 WebSocket 流
                await webSocketManager.ConnectTradeStreamAsync(symbol);
                await webSocketManager.ConnectOrderBookStreamAsync(symbol);
                await webSocketManager.ConnectLiquidationStreamAsync(symbol);

                connectButton.Text = "已连接";
                UpdateConnectionStatus("已连接", Color.DarkGreen);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"连接失败: {ex.Message}", "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
                connectButton.Enabled = true;
                connectButton.Text = "连接";
            }
        }

        /// <summary>
        /// 处理交易数据
        /// </summary>
        private void OnTradeReceived(TradeStreamData tradeData)
        {
            // 创建交易数据对象
            var trade = new TradeData
            {
                Time = tradeData.Time,
                Price = decimal.Parse(tradeData.Price),
                Quantity = decimal.Parse(tradeData.Quantity),
                IsBuyerMaker = tradeData.IsBuyerMaker
            };

            // 检测异常交易
            var abnormalTrade = abnormalDetector?.AddTrade(trade);

            // 更新 UI
            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                // 添加到实时交易表格
                DataGridViewHelper.AddTradeRow(
                    tradeGrid,
                    tradeData.Time,
                    tradeData.Price,
                    tradeData.Quantity,
                    tradeData.Side,
                    Constants.MaxTradeGridRows
                );

                // 如果检测到异常交易，更新异常大单列表
                if (abnormalTrade != null)
                {
                    DataGridViewHelper.AddAbnormalTradeRow(
                        abnormalGrid,
                        abnormalTrade,
                        Constants.MaxAbnormalGridRows
                    );
                }
            });
        }

        /// <summary>
        /// 处理订单簿数据
        /// </summary>
        private void OnOrderBookReceived(OrderBookData orderBookData)
        {
            // 缓存原始数据
            latestOrderBookData = orderBookData;

            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                // 计算价差
                if (orderBookData.Asks.Count > 0 && orderBookData.Bids.Count > 0)
                {
                    var lowestAsk = double.Parse(orderBookData.Asks[0].price);
                    var highestBid = double.Parse(orderBookData.Bids[0].price);
                    var spread = lowestAsk - highestBid;
                    var spreadPercent = (spread / highestBid) * 100;

                    orderTitleLabel.Text = $"委托订单 - 价差: {spread:F2} ({spreadPercent:F4}%) - {DateTime.Now:HH:mm:ss}";
                }
            });

            // 使用聚合后的数据更新订单簿显示
            RefreshOrderBookDisplay();
        }

        /// <summary>
        /// 处理爆仓数据
        /// </summary>
        private void OnLiquidationReceived(LiquidationData liquidationData)
        {
            UIThreadHelper.SafeBeginInvoke(this, () =>
            {
                // 添加到爆仓列表
                DataGridViewHelper.AddLiquidationRow(
                    liquidationGrid,
                    liquidationData,
                    Constants.MaxLiquidationGridRows);
            });
        }

        /// <summary>
        /// 处理 WebSocket 错误
        /// </summary>
        private void OnWebSocketError(string errorMessage)
        {
            UIThreadHelper.SafeInvoke(this, () =>
            {
                // 在状态栏显示错误信息
                UpdateConnectionStatus($"错误: {errorMessage}", Color.DarkRed);
                System.Diagnostics.Debug.WriteLine($"WebSocket 错误: {errorMessage}");
            });
        }

        /// <summary>
        /// 处理 WebSocket 重连中事件
        /// </summary>
        private void OnWebSocketReconnecting(int reconnectCount, DateTime reconnectTime)
        {
            UIThreadHelper.SafeInvoke(this, () =>
            {
                string statusText = $"重连中... (第 {reconnectCount} 次，{reconnectTime:HH:mm:ss})";
                UpdateConnectionStatus(statusText, Color.DarkOrange);
            });
        }

        /// <summary>
        /// 处理 WebSocket 重连成功事件
        /// </summary>
        private void OnWebSocketReconnected(int reconnectCount)
        {
            UIThreadHelper.SafeInvoke(this, () =>
            {
                string statusText = $"已连接 (重连 {reconnectCount} 次后恢复)";
                UpdateConnectionStatus(statusText, Color.DarkGreen);

                // 更新按钮状态
                connectButton.Text = "已连接";
            });
        }

        /// <summary>
        /// 更新连接状态显示
        /// </summary>
        private void UpdateConnectionStatus(string status, Color color)
        {
            UIThreadHelper.SafeInvoke(this, () =>
            {
                connectionStatusLabel.Text = $"连接状态：{status}";
                connectionStatusLabel.ForeColor = color;
            });
        }

        #region Designer 事件处理器（保持为空）

        private void label1_Click(object sender, EventArgs e)
        {
        }

        private void MainForm_Load(object sender, EventArgs e)
        {
        }

        private void consecutiveThresholdLabel_Click(object sender, EventArgs e)
        {
        }

        private void windowComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
        }

        /// <summary>
        /// 价格精度选择器变更事件
        /// </summary>
        private void PriceTickComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            // 立即使用缓存数据重新聚合并刷新显示
            RefreshOrderBookDisplay();
        }

        /// <summary>
        /// 查看市价比统计文件按钮点击事件
        /// </summary>
        private void ViewStatisticsButton_Click(object sender, EventArgs e)
        {
            try
            {
                if (webSocketManager != null)
                {
                    string statisticsDir = webSocketManager.GetStatisticsDirectory();

                    if (!string.IsNullOrEmpty(statisticsDir) && System.IO.Directory.Exists(statisticsDir))
                    {
                        // 打开统计文件目录
                        System.Diagnostics.Process.Start("explorer.exe", statisticsDir);
                    }
                    else
                    {
                        MessageBox.Show("市价比统计目录不存在，请先连接交易对开始统计。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                }
                else
                {
                    MessageBox.Show("请先连接交易对。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开市价比统计目录失败: {ex.Message}", "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// 查看大单统计文件按钮点击事件
        /// </summary>
        private void ViewLargeOrderStatisticsButton_Click(object sender, EventArgs e)
        {
            try
            {
                if (webSocketManager != null)
                {
                    string statisticsDir = webSocketManager.GetLargeOrderStatisticsDirectory();

                    if (!string.IsNullOrEmpty(statisticsDir) && System.IO.Directory.Exists(statisticsDir))
                    {
                        // 打开大单统计文件目录
                        System.Diagnostics.Process.Start("explorer.exe", statisticsDir);
                    }
                    else
                    {
                        MessageBox.Show("大单统计目录不存在，请先连接交易对开始统计。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                }
                else
                {
                    MessageBox.Show("请先连接交易对。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开大单统计目录失败: {ex.Message}", "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// 查看异常大单监控明细
        /// </summary>
        private void ViewAbnormalDetailButton_Click(object sender, EventArgs e)
        {
            try
            {
                string logDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "AbnormalTradeLogs");
                string todayLogFile = Path.Combine(logDirectory, $"abnormal_trades_{DateTime.Now:yyyyMMdd}.csv");

                // 如果今天的日志文件存在，直接打开
                if (File.Exists(todayLogFile))
                {
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = todayLogFile,
                        UseShellExecute = true
                    });
                }
                // 如果今天没有日志，打开日志目录
                else if (Directory.Exists(logDirectory))
                {
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = logDirectory,
                        UseShellExecute = true
                    });
                }
                else
                {
                    MessageBox.Show("还没有异常大单记录。\n\n异常大单会在检测到时自动记录到日志文件中。",
                        "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开异常大单日志失败: {ex.Message}", "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        #endregion

        private void label2_Click(object sender, EventArgs e)
        {

        }

        private void statsDirectionLabel_Click(object sender, EventArgs e)
        {

        }
    }
}
