using System.Drawing;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 应用程序常量配置
    /// </summary>
    public static class Constants
    {
        #region WebSocket 配置

        /// <summary>
        /// 币安期货 WebSocket 基础URL
        /// </summary>
        public const string BinanceWebSocketBaseUrl = "wss://fstream.binance.com/ws";

        /// <summary>
        /// 交易流 WebSocket 缓冲区大小
        /// </summary>
        public const int TradeStreamBufferSize = 8192;

        /// <summary>
        /// 订单簿 WebSocket 缓冲区大小
        /// </summary>
        public const int OrderBookStreamBufferSize = 16384;

        /// <summary>
        /// 心跳检测间隔（毫秒）- 每2秒检查一次
        /// </summary>
        public const int HeartbeatCheckInterval = 2000;

        /// <summary>
        /// 心跳超时阈值（秒）- 5秒没收到数据则认为连接断开
        /// </summary>
        public const int HeartbeatTimeoutSeconds = 5;

        #endregion

        #region 统计功能配置

        /// <summary>
        /// 统计数据保存目录
        /// </summary>
        public const string StatisticsDirectory = "statistics";

        #endregion

        #region Grid 配置

        /// <summary>
        /// 实时交易表格最大行数
        /// </summary>
        public const int MaxTradeGridRows = 100;

        /// <summary>
        /// 异常大单表格最大行数
        /// </summary>
        public const int MaxAbnormalGridRows = 50;

        /// <summary>
        /// 订单簿显示最大档位
        /// </summary>
        public const int MaxOrderBookDepth = 20;

        #endregion

        #region 定时器配置

        /// <summary>
        /// 统计更新定时器间隔（毫秒）
        /// </summary>
        public const int StatsUpdateInterval = 1000;

        #endregion

        #region 颜色配置

        /// <summary>
        /// 买单背景色 - 浅绿色
        /// </summary>
        public static readonly Color BuyBackgroundColor = Color.LightGreen;

        /// <summary>
        /// 买单前景色 - 深绿色
        /// </summary>
        public static readonly Color BuyForegroundColor = Color.DarkGreen;

        /// <summary>
        /// 卖单背景色 - 浅粉色
        /// </summary>
        public static readonly Color SellBackgroundColor = Color.LightPink;

        /// <summary>
        /// 卖单前景色 - 深红色
        /// </summary>
        public static readonly Color SellForegroundColor = Color.DarkRed;

        /// <summary>
        /// 买单表格头部背景色
        /// </summary>
        public static readonly Color BuyHeaderBackgroundColor = Color.Green;

        /// <summary>
        /// 卖单表格头部背景色
        /// </summary>
        public static readonly Color SellHeaderBackgroundColor = Color.IndianRed;

        /// <summary>
        /// 表格头部前景色
        /// </summary>
        public static readonly Color HeaderForegroundColor = Color.White;

        /// <summary>
        /// 卖单订单簿背景色
        /// </summary>
        public static readonly Color SellOrderBookBackgroundColor = Color.MistyRose;

        /// <summary>
        /// 买单订单簿背景色
        /// </summary>
        public static readonly Color BuyOrderBookBackgroundColor = Color.White;

        /// <summary>
        /// 连续大单触发状态颜色 - 买入
        /// </summary>
        public static readonly Color ConsecutiveBuyTriggeredColor = Color.Green;

        /// <summary>
        /// 连续大单触发状态颜色 - 卖出
        /// </summary>
        public static readonly Color ConsecutiveSellTriggeredColor = Color.Red;

        /// <summary>
        /// 未触发状态颜色
        /// </summary>
        public static readonly Color NotTriggeredColor = Color.Gray;

        #endregion

        #region 字体配置

        /// <summary>
        /// 异常交易倍数阈值（超过此倍数加粗显示）
        /// </summary>
        public const double BoldFontRatioThreshold = 5.0;

        #endregion

        #region Grid 列名常量

        // 实时交易表格列名
        public const string TradeTimeColumn = "Time";
        public const string TradePriceColumn = "Price";
        public const string TradeQtyColumn = "Qty";
        public const string TradeSideColumn = "Side";

        // 异常大单表格列名
        public const string AbnormalTimeColumn = "Time";
        public const string AbnormalPriceColumn = "Price";
        public const string AbnormalQuantityColumn = "Quantity";
        public const string AbnormalDirectionColumn = "Direction";
        public const string AbnormalOrderTypeColumn = "OrderType";
        public const string AbnormalShortRatioColumn = "ShortRatio";

        // 订单簿表格列名
        public const string OrderPriceColumn = "Price";
        public const string OrderQtyColumn = "Qty";

        // 连续大单历史表格列名
        public const string ConsecutiveTriggerTimeColumn = "TriggerTime";
        public const string ConsecutiveWindowStartColumn = "WindowStart";
        public const string ConsecutiveWindowEndColumn = "WindowEnd";
        public const string ConsecutiveDirectionColumn = "Direction";
        public const string ConsecutiveCountColumn = "Count";
        public const string ConsecutiveTotalVolumeColumn = "TotalVolume";
        public const string ConsecutiveAvgVolumeColumn = "AvgVolume";
        public const string ConsecutiveMaxVolumeColumn = "MaxVolume";
        public const string ConsecutiveMaxRatioColumn = "MaxRatio";
        public const string ConsecutiveWindowDurationColumn = "WindowDuration";

        // 爆仓列表表格列名
        public const string LiquidationTimeColumn = "Time";
        public const string LiquidationPriceColumn = "Price";
        public const string LiquidationQuantityColumn = "Quantity";
        public const string LiquidationValueColumn = "Value";
        public const string LiquidationDirectionColumn = "Direction";

        #endregion

        #region 爆仓颜色配置

        /// <summary>
        /// 多头爆仓背景色（卖单强平）- 浅红色
        /// </summary>
        public static readonly Color LongLiquidationBackgroundColor = Color.LightCoral;

        /// <summary>
        /// 多头爆仓前景色 - 深红色
        /// </summary>
        public static readonly Color LongLiquidationForegroundColor = Color.DarkRed;

        /// <summary>
        /// 空头爆仓背景色（买单强平）- 浅绿色
        /// </summary>
        public static readonly Color ShortLiquidationBackgroundColor = Color.LightGreen;

        /// <summary>
        /// 空头爆仓前景色 - 深绿色
        /// </summary>
        public static readonly Color ShortLiquidationForegroundColor = Color.DarkGreen;

        #endregion

        #region 爆仓监控配置

        /// <summary>
        /// 爆仓列表表格最大行数
        /// </summary>
        public const int MaxLiquidationGridRows = 100;

        #endregion
    }
}

