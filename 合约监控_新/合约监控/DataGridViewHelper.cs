using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace FuturesTradeViewer
{
    /// <summary>
    /// DataGridView 操作辅助类
    /// </summary>
    public static class DataGridViewHelper
    {
        /// <summary>
        /// 列配置信息
        /// </summary>
        public class ColumnConfig
        {
            public string Name { get; set; } = "";
            public string HeaderText { get; set; } = "";
            public int Width { get; set; } = 100;
        }

        /// <summary>
        /// 初始化 DataGridView（通用方法）
        /// </summary>
        /// <param name="grid">目标表格</param>
        /// <param name="columns">列配置</param>
        /// <param name="hideRowHeader">是否隐藏行头</param>
        public static void InitializeGrid(DataGridView grid, List<ColumnConfig> columns, bool hideRowHeader = true)
        {
            grid.Rows.Clear();
            grid.Columns.Clear();

            foreach (var col in columns)
            {
                grid.Columns.Add(col.Name, col.HeaderText);
                grid.Columns[col.Name].Width = col.Width;
            }

            grid.RowHeadersVisible = !hideRowHeader;
        }

        /// <summary>
        /// 初始化实时交易表格
        /// </summary>
        public static void InitializeTradeGrid(DataGridView grid)
        {
            var columns = new List<ColumnConfig>
            {
                new ColumnConfig { Name = Constants.TradeTimeColumn, HeaderText = "时间", Width = 100 },
                new ColumnConfig { Name = Constants.TradePriceColumn, HeaderText = "价格", Width = 100 },
                new ColumnConfig { Name = Constants.TradeQtyColumn, HeaderText = "数量", Width = 100 },
                new ColumnConfig { Name = Constants.TradeSideColumn, HeaderText = "方向", Width = 150 }
            };

            InitializeGrid(grid, columns);
        }

        /// <summary>
        /// 初始化异常大单表格
        /// </summary>
        public static void InitializeAbnormalGrid(DataGridView grid)
        {
            var columns = new List<ColumnConfig>
            {
                new ColumnConfig { Name = Constants.AbnormalTimeColumn, HeaderText = "时间", Width = 150 },
                new ColumnConfig { Name = Constants.AbnormalPriceColumn, HeaderText = "价格", Width = 120 },
                new ColumnConfig { Name = Constants.AbnormalQuantityColumn, HeaderText = "数量", Width = 120 },
                new ColumnConfig { Name = Constants.AbnormalDirectionColumn, HeaderText = "方向", Width = 100 },
                new ColumnConfig { Name = Constants.AbnormalOrderTypeColumn, HeaderText = "吃单/挂单", Width = 100 },
                new ColumnConfig { Name = Constants.AbnormalShortRatioColumn, HeaderText = "短期倍数", Width = 120 }
            };

            InitializeGrid(grid, columns);
        }

        /// <summary>
        /// 初始化订单簿表格
        /// </summary>
        public static void InitializeOrderBookGrid(DataGridView grid, bool isBuyOrder)
        {
            var columns = new List<ColumnConfig>
            {
                new ColumnConfig { Name = Constants.OrderPriceColumn, HeaderText = "价格", Width = 100 },
                new ColumnConfig { Name = Constants.OrderQtyColumn, HeaderText = "数量", Width = 100 }
            };

            InitializeGrid(grid, columns);

            // 设置颜色
            if (isBuyOrder)
            {
                grid.DefaultCellStyle.BackColor = Constants.BuyOrderBookBackgroundColor;
                grid.DefaultCellStyle.ForeColor = Constants.BuyForegroundColor;
                grid.ColumnHeadersDefaultCellStyle.BackColor = Constants.BuyHeaderBackgroundColor;
                grid.ColumnHeadersDefaultCellStyle.ForeColor = Constants.HeaderForegroundColor;
            }
            else
            {
                grid.DefaultCellStyle.BackColor = Constants.SellOrderBookBackgroundColor;
                grid.DefaultCellStyle.ForeColor = Constants.SellForegroundColor;
                grid.ColumnHeadersDefaultCellStyle.BackColor = Constants.SellHeaderBackgroundColor;
                grid.ColumnHeadersDefaultCellStyle.ForeColor = Constants.HeaderForegroundColor;
            }
        }

        /// <summary>
        /// 初始化连续大单历史表格
        /// </summary>
        public static void InitializeConsecutiveHistoryGrid(DataGridView grid)
        {
            var columns = new List<ColumnConfig>
            {
                new ColumnConfig { Name = Constants.ConsecutiveTriggerTimeColumn, HeaderText = "触发时间", Width = 90 },
                new ColumnConfig { Name = Constants.ConsecutiveWindowStartColumn, HeaderText = "窗口开始", Width = 90 },
                new ColumnConfig { Name = Constants.ConsecutiveWindowEndColumn, HeaderText = "窗口结束", Width = 90 },
                new ColumnConfig { Name = Constants.ConsecutiveDirectionColumn, HeaderText = "方向", Width = 70 },
                new ColumnConfig { Name = Constants.ConsecutiveCountColumn, HeaderText = "笔数", Width = 60 },
                new ColumnConfig { Name = Constants.ConsecutiveTotalVolumeColumn, HeaderText = "总量(BTC)", Width = 90 },
                new ColumnConfig { Name = Constants.ConsecutiveAvgVolumeColumn, HeaderText = "均量(BTC)", Width = 90 },
                new ColumnConfig { Name = Constants.ConsecutiveMaxVolumeColumn, HeaderText = "最大(BTC)", Width = 90 },
                new ColumnConfig { Name = Constants.ConsecutiveMaxRatioColumn, HeaderText = "最大倍数", Width = 80 },
                new ColumnConfig { Name = Constants.ConsecutiveWindowDurationColumn, HeaderText = "窗口时长", Width = 80 }
            };

            InitializeGrid(grid, columns);
        }

        /// <summary>
        /// 更新订单簿表格（增量更新）
        /// </summary>
        public static void UpdateOrderGrid(DataGridView grid, List<(string price, string qty)> orders)
        {
            // 确保行数匹配
            int targetCount = Math.Min(orders.Count, Constants.MaxOrderBookDepth);

            // 调整行数
            while (grid.Rows.Count < targetCount)
            {
                grid.Rows.Add();
            }
            while (grid.Rows.Count > targetCount)
            {
                grid.Rows.RemoveAt(grid.Rows.Count - 1);
            }

            // 更新每一行的数据
            for (int i = 0; i < targetCount; i++)
            {
                var order = orders[i];
                grid.Rows[i].Cells[0].Value = order.price; // 价格
                grid.Rows[i].Cells[1].Value = order.qty;   // 数量
            }
        }

        /// <summary>
        /// 添加异常交易到表格顶部
        /// </summary>
        public static void AddAbnormalTradeRow(DataGridView grid, AbnormalTrade abnormalTrade, int maxRows)
        {
            try
            {
                // 插入到顶部
                grid.Rows.Insert(0, 1);
                DataGridViewRow row = grid.Rows[0];

                // 设置数据
                row.Cells[Constants.AbnormalTimeColumn].Value = abnormalTrade.Trade.Time.ToString("HH:mm:ss.fff");
                row.Cells[Constants.AbnormalPriceColumn].Value = abnormalTrade.Trade.Price.ToString("F2");
                row.Cells[Constants.AbnormalQuantityColumn].Value = abnormalTrade.Trade.Quantity.ToString("F4");
                row.Cells[Constants.AbnormalDirectionColumn].Value = abnormalTrade.Direction;
                row.Cells[Constants.AbnormalOrderTypeColumn].Value = abnormalTrade.Trade.OrderTypeText;
                row.Cells[Constants.AbnormalShortRatioColumn].Value = $"{abnormalTrade.ShortTermRatio:F2}x";

                // 设置背景色和前景色
                if (abnormalTrade.Direction == "买入↑")
                {
                    row.DefaultCellStyle.BackColor = Constants.BuyBackgroundColor;
                    row.DefaultCellStyle.ForeColor = Constants.BuyForegroundColor;
                }
                else
                {
                    row.DefaultCellStyle.BackColor = Constants.SellBackgroundColor;
                    row.DefaultCellStyle.ForeColor = Constants.SellForegroundColor;
                }

                // 根据倍数调整字体加粗
                if (abnormalTrade.ShortTermRatio >= Constants.BoldFontRatioThreshold)
                {
                    row.DefaultCellStyle.Font = new Font(grid.DefaultCellStyle.Font, FontStyle.Bold);
                }

                // 限制最大行数
                if (grid.Rows.Count > maxRows)
                    grid.Rows.RemoveAt(grid.Rows.Count - 1);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"添加异常交易行错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 添加交易数据行到表格顶部
        /// </summary>
        public static void AddTradeRow(DataGridView grid, DateTime time, string price, string qty, string side, int maxRows)
        {
            try
            {
                // 插入到顶部
                grid.Rows.Insert(0, 1);
                DataGridViewRow row = grid.Rows[0];

                row.Cells[0].Value = time.ToString("HH:mm:ss.fff");
                row.Cells[1].Value = price;
                row.Cells[2].Value = qty;
                row.Cells[3].Value = side;

                // 限制最大行数
                if (grid.Rows.Count > maxRows)
                    grid.Rows.RemoveAt(grid.Rows.Count - 1);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"添加交易行错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 更新连续大单历史表格
        /// </summary>
        public static void UpdateConsecutiveHistoryGrid(DataGridView grid, List<ConsecutiveLargeOrderEvent> events)
        {
            try
            {
                // 清空现有数据
                grid.Rows.Clear();

                // 添加窗口快照数据
                foreach (var evt in events)
                {
                    int rowIndex = grid.Rows.Add();
                    var row = grid.Rows[rowIndex];

                    row.Cells[Constants.ConsecutiveTriggerTimeColumn].Value = evt.TriggerTime.ToString("HH:mm:ss");
                    row.Cells[Constants.ConsecutiveWindowStartColumn].Value = evt.WindowStartTime.ToString("HH:mm:ss");
                    row.Cells[Constants.ConsecutiveWindowEndColumn].Value = evt.WindowEndTime.ToString("HH:mm:ss");
                    row.Cells[Constants.ConsecutiveDirectionColumn].Value = evt.Direction;
                    row.Cells[Constants.ConsecutiveCountColumn].Value = evt.Count;
                    row.Cells[Constants.ConsecutiveTotalVolumeColumn].Value = evt.TotalVolume.ToString("F2");
                    row.Cells[Constants.ConsecutiveAvgVolumeColumn].Value = evt.AverageVolume.ToString("F4");
                    row.Cells[Constants.ConsecutiveMaxVolumeColumn].Value = evt.MaxVolume.ToString("F4");
                    row.Cells[Constants.ConsecutiveMaxRatioColumn].Value = $"{evt.MaxRatio:F2}x";
                    row.Cells[Constants.ConsecutiveWindowDurationColumn].Value = $"{evt.WindowSeconds}秒";

                    // 设置颜色
                    row.DefaultCellStyle.BackColor = Color.White;
                    row.DefaultCellStyle.ForeColor = evt.Direction == "买入" ? Color.DarkGreen : Color.DarkRed;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"更新连续大单历史表格错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 初始化爆仓列表表格
        /// </summary>
        public static void InitializeLiquidationGrid(DataGridView grid)
        {
            var columns = new List<ColumnConfig>
            {
                new ColumnConfig { Name = Constants.LiquidationTimeColumn, HeaderText = "时间", Width = 100 },
                new ColumnConfig { Name = Constants.LiquidationPriceColumn, HeaderText = "价格", Width = 100 },
                new ColumnConfig { Name = Constants.LiquidationQuantityColumn, HeaderText = "数量", Width = 100 },
                new ColumnConfig { Name = Constants.LiquidationValueColumn, HeaderText = "金额(USDT)", Width = 110 },
                new ColumnConfig { Name = Constants.LiquidationDirectionColumn, HeaderText = "方向", Width = 100 }
            };

            InitializeGrid(grid, columns);
        }

        /// <summary>
        /// 添加爆仓数据行到表格顶部
        /// </summary>
        public static void AddLiquidationRow(DataGridView grid, LiquidationData data, int maxRows)
        {
            try
            {
                // 插入到顶部
                grid.Rows.Insert(0, 1);
                DataGridViewRow row = grid.Rows[0];

                // 设置数据
                row.Cells[Constants.LiquidationTimeColumn].Value = data.Time.ToString("HH:mm:ss");
                row.Cells[Constants.LiquidationPriceColumn].Value = data.Price.ToString("F2");
                row.Cells[Constants.LiquidationQuantityColumn].Value = data.Quantity.ToString("F4");
                row.Cells[Constants.LiquidationValueColumn].Value = data.LiquidationValue.ToString("F2");
                row.Cells[Constants.LiquidationDirectionColumn].Value = data.Direction;

                // 设置颜色
                if (data.IsLongLiquidation)
                {
                    // 多头爆仓 - 红色
                    row.DefaultCellStyle.BackColor = Constants.LongLiquidationBackgroundColor;
                    row.DefaultCellStyle.ForeColor = Constants.LongLiquidationForegroundColor;
                }
                else
                {
                    // 空头爆仓 - 绿色
                    row.DefaultCellStyle.BackColor = Constants.ShortLiquidationBackgroundColor;
                    row.DefaultCellStyle.ForeColor = Constants.ShortLiquidationForegroundColor;
                }

                // 大额爆仓加粗显示（> 100,000 USDT）
                if (data.LiquidationValue > 100000)
                {
                    row.DefaultCellStyle.Font = new Font(grid.DefaultCellStyle.Font, FontStyle.Bold);
                }

                // 限制最大行数
                if (grid.Rows.Count > maxRows)
                    grid.Rows.RemoveAt(grid.Rows.Count - 1);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"添加爆仓行错误: {ex.Message}");
            }
        }
    }
}

