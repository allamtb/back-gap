using System;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 时间窗口大单统计数据模型
    /// 用于按时间维度统计大单交易数据
    /// </summary>
    public class LargeOrderWindowStatistics
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
        /// 合约总成交量（BTC数量）
        /// </summary>
        public decimal TotalVolume { get; set; }

        /// <summary>
        /// 大单总成交量（BTC数量）
        /// </summary>
        public decimal LargeOrderVolume { get; set; }

        /// <summary>
        /// 买大单成交量（BTC数量）
        /// </summary>
        public decimal BuyLargeOrderVolume { get; set; }

        /// <summary>
        /// 卖大单成交量（BTC数量）
        /// </summary>
        public decimal SellLargeOrderVolume { get; set; }

        /// <summary>
        /// 大单比例（%）
        /// </summary>
        public decimal LargeOrderRatio => TotalVolume > 0 ? (LargeOrderVolume / TotalVolume) * 100 : 0;

        /// <summary>
        /// 转换为CSV行格式
        /// </summary>
        public string ToCsvLine()
        {
            return $"{StartTime:yyyy-MM-dd HH:mm},{TotalVolume:F4},{LargeOrderVolume:F4},{LargeOrderRatio:F2}%,{BuyLargeOrderVolume:F4},{SellLargeOrderVolume:F4}";
        }

        /// <summary>
        /// CSV文件头
        /// </summary>
        public static string CsvHeader => "时间,合约总成交(BTC),大单成交(BTC),大单比,买大单(BTC),卖大单(BTC)";
    }
}

