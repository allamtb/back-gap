using System;
using System.Collections.Generic;
using System.Linq;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 爆仓统计数据
    /// </summary>
    public class LiquidationStatistics
    {
        /// <summary>
        /// 多头爆仓总数量（币的数量）
        /// </summary>
        public decimal TotalLongQuantity { get; set; }

        /// <summary>
        /// 空头爆仓总数量（币的数量）
        /// </summary>
        public decimal TotalShortQuantity { get; set; }

        /// <summary>
        /// 多头爆仓总金额（USDT）
        /// </summary>
        public decimal TotalLongValue { get; set; }

        /// <summary>
        /// 空头爆仓总金额（USDT）
        /// </summary>
        public decimal TotalShortValue { get; set; }

        /// <summary>
        /// 多头爆仓次数
        /// </summary>
        public int LongLiquidationCount { get; set; }

        /// <summary>
        /// 空头爆仓次数
        /// </summary>
        public int ShortLiquidationCount { get; set; }

        /// <summary>
        /// 最大单笔爆仓数量
        /// </summary>
        public decimal LargestLiquidationQuantity { get; set; }

        /// <summary>
        /// 最大单笔爆仓金额
        /// </summary>
        public decimal LargestLiquidationValue { get; set; }

        /// <summary>
        /// 最大爆仓是否为多头爆仓
        /// </summary>
        public bool IsLargestLongLiquidation { get; set; }

        /// <summary>
        /// 统计时间窗口（分钟）
        /// </summary>
        public int TimeWindowMinutes { get; set; }
    }

    /// <summary>
    /// 爆仓监控器
    /// </summary>
    public class LiquidationMonitor
    {
        private readonly List<LiquidationData> liquidations = new List<LiquidationData>();
        private readonly object lockObject = new object();

        /// <summary>
        /// 统计时间窗口（分钟）
        /// </summary>
        public int TimeWindowMinutes { get; set; } = 15;

        /// <summary>
        /// 最小爆仓数量阈值（币的数量，如 0.1 BTC）
        /// </summary>
        public decimal MinLiquidationThreshold { get; set; } = 0.1M;

        /// <summary>
        /// 添加爆仓数据（自动过滤低于阈值的数据）
        /// </summary>
        /// <param name="data">爆仓数据</param>
        /// <returns>如果数据符合阈值返回数据，否则返回 null</returns>
        public LiquidationData? AddLiquidation(LiquidationData data)
        {
            // 过滤：数量低于阈值的不记录
            if (data.Quantity < MinLiquidationThreshold)
            {
                return null;
            }

            lock (lockObject)
            {
                liquidations.Add(data);

                // 清理超出时间窗口的数据
                var cutoffTime = DateTime.Now.AddMinutes(-TimeWindowMinutes);
                liquidations.RemoveAll(l => l.Time < cutoffTime);
            }

            return data;
        }

        /// <summary>
        /// 获取统计数据
        /// </summary>
        public LiquidationStatistics GetStatistics()
        {
            lock (lockObject)
            {
                var cutoffTime = DateTime.Now.AddMinutes(-TimeWindowMinutes);
                var recentLiquidations = liquidations.Where(l => l.Time >= cutoffTime).ToList();

                var longLiquidations = recentLiquidations.Where(l => l.IsLongLiquidation).ToList();
                var shortLiquidations = recentLiquidations.Where(l => l.IsShortLiquidation).ToList();

                // 找出最大爆仓（按金额）
                var largestLiquidation = recentLiquidations
                    .OrderByDescending(l => l.LiquidationValue)
                    .FirstOrDefault();

                var stats = new LiquidationStatistics
                {
                    TimeWindowMinutes = TimeWindowMinutes,
                    
                    // 多头爆仓统计
                    TotalLongQuantity = longLiquidations.Sum(l => l.Quantity),
                    TotalLongValue = longLiquidations.Sum(l => l.LiquidationValue),
                    LongLiquidationCount = longLiquidations.Count,
                    
                    // 空头爆仓统计
                    TotalShortQuantity = shortLiquidations.Sum(l => l.Quantity),
                    TotalShortValue = shortLiquidations.Sum(l => l.LiquidationValue),
                    ShortLiquidationCount = shortLiquidations.Count,
                    
                    // 最大爆仓
                    LargestLiquidationQuantity = largestLiquidation?.Quantity ?? 0,
                    LargestLiquidationValue = largestLiquidation?.LiquidationValue ?? 0,
                    IsLargestLongLiquidation = largestLiquidation?.IsLongLiquidation ?? false
                };

                return stats;
            }
        }

        /// <summary>
        /// 获取最近的爆仓数据（最多返回指定数量）
        /// </summary>
        public List<LiquidationData> GetRecentLiquidations(int maxCount = 100)
        {
            lock (lockObject)
            {
                var cutoffTime = DateTime.Now.AddMinutes(-TimeWindowMinutes);
                return liquidations
                    .Where(l => l.Time >= cutoffTime)
                    .OrderByDescending(l => l.Time)
                    .Take(maxCount)
                    .ToList();
            }
        }

        /// <summary>
        /// 清空所有数据
        /// </summary>
        public void Clear()
        {
            lock (lockObject)
            {
                liquidations.Clear();
            }
        }
    }
}

