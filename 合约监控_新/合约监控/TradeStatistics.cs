using System;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 时间窗口交易统计数据模型
    /// 用于按时间维度统计交易数据
    /// </summary>
    public class TimeWindowStatistics
    {
        /// <summary>
        /// 统计周期开始时间
        /// </summary>
        public DateTime StartTime { get; set; }

        /// <summary>
        /// 统计周期结束时间
        /// </summary>
        public DateTime EndTime { get; set; }

        /// <summary>
        /// 委托成交量（挂单成交，BTC数量）
        /// </summary>
        public decimal LimitOrderVolume { get; set; }

        /// <summary>
        /// 市价成交量（主动吃单，BTC数量）
        /// </summary>
        public decimal MarketOrderVolume { get; set; }

        /// <summary>
        /// 总成交量
        /// </summary>
        public decimal TotalVolume => LimitOrderVolume + MarketOrderVolume;

        /// <summary>
        /// 市价比（市价成交量占比）
        /// </summary>
        public decimal MarketOrderRatio => TotalVolume > 0 ? (MarketOrderVolume / TotalVolume) * 100 : 0;

        /// <summary>
        /// 转换为CSV行格式
        /// </summary>
        public string ToCsvLine()
        {
            return $"{StartTime:yyyy-MM-dd HH:mm},{LimitOrderVolume:F4},{MarketOrderVolume:F4},{TotalVolume:F4},{MarketOrderRatio:F2}%";
        }

        /// <summary>
        /// CSV文件头
        /// </summary>
        public static string CsvHeader => "时间,委托成交(BTC),市价成交(BTC),总量(BTC),市价比";
    }

    /// <summary>
    /// 统计时间窗口类型
    /// </summary>
    public enum StatisticsWindowType
    {
        OneMinute,      // 1分钟
        FiveMinutes,    // 5分钟
        FifteenMinutes, // 15分钟
        OneHour,        // 1小时
        OneDay          // 1天
    }
}

