using System;
using System.Collections.Generic;
using System.Linq;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 异常交易检测器（简化版 + 连续大单检测）
    /// </summary>
    public class AbnormalTradeDetector
    {
        // 交易历史队列（保存30分钟）
        private Queue<TradeData> tradeHistory = new Queue<TradeData>();

        // 异常交易记录列表
        private List<AbnormalTrade> abnormalTrades = new List<AbnormalTrade>();

        // 最大保存的异常交易数量
        private const int MaxAbnormalTrades = 100;

        // 历史基准数据（从API获取）
        private decimal historicalBaseline = 0M;  // 历史平均每笔交易量
        private bool useHistoricalBaseline = false;  // 是否使用历史基准

        // === 连续大单检测相关（窗口模式）===
        private List<ConsecutiveLargeOrderEvent> consecutiveEvents = new List<ConsecutiveLargeOrderEvent>();
        private const int MaxConsecutiveEvents = 100;  // 最多保存100个连续事件
        
        // 窗口去重：记录最近触发的窗口ID，避免重复记录
        private HashSet<string> recentWindowIds = new HashSet<string>();
        private DateTime lastWindowCleanup = DateTime.Now;

        // 配置参数
        public decimal MinThreshold { get; set; } = 0.05M;         // 最小交易量阈值（0.05 BTC）
        public decimal ShortTermMultiple { get; set; } = 2.5M;     // 短期倍数（2.5倍即算异常）
        public int ShortTermMinutes { get; set; } = 5;             // 短期窗口（分钟）
        public bool OnlyActiveTaker { get; set; } = true;          // 只关注主动吃单

        // === 连续大单配置参数 ===
        public bool EnableConsecutiveDetection { get; set; } = true;  // 启用连续大单检测
        public int ConsecutiveWindowSeconds { get; set; } = 60;       // 连续检测窗口（秒）
        public int ConsecutiveMinCount { get; set; } = 3;             // 最小笔数
        public bool ConsecutiveSameDirectionOnly { get; set; } = true; // 只统计同方向
        public decimal ConsecutiveMinThreshold { get; set; } = 0.05M; // 连续大单的最小交易量阈值（独立设置）

        /// <summary>
        /// 添加新交易并检测异常
        /// </summary>
        public AbnormalTrade? AddTrade(TradeData trade)
        {
            if (trade == null) return null;

            // 1. 加入历史队列
            tradeHistory.Enqueue(trade);

            // 2. 清理30分钟外的数据
            CleanOldTrades();

            // 3. 过滤条件：是否只关注市价成交（主动吃单）
            // 注意：WebSocket trade stream 的所有数据都是已成交的交易
            // IsBuyerMaker=true: 买方是Maker（挂单），卖方是Taker（主动吃单）→ 主动卖出
            // IsBuyerMaker=false: 卖方是Maker（挂单），买方是Taker（主动吃单）→ 主动买入
            // 因此，无论 IsBuyerMaker 是 true 还是 false，都有一方是主动吃单
            // 如果要过滤，应该根据具体的业务需求（比如只看买入或只看卖出）
            // 当前逻辑已修正：不过滤任何方向的主动吃单
            // if (OnlyActiveTaker && trade.IsBuyerMaker)
            //     return null;  // 错误逻辑：这会过滤掉所有主动卖出

            // 4. 检查是否达到最小阈值
            if (trade.Quantity < MinThreshold)
                return null;

            // 5. 计算短期平均值
            var shortTermTrades = GetTradesInWindow(ShortTermMinutes);

            // 如果实时数据不足，返回
            if (shortTermTrades.Count == 0)
                return null;

            decimal avgShort = shortTermTrades.Average(t => t.Quantity);

            // 6. 判断是否异常（简化版，只用短期倍数）
            bool isAbnormal = trade.Quantity >= avgShort * ShortTermMultiple;

            if (!isAbnormal)
                return null;

            // 7. 创建异常交易对象
            double shortRatio = (double)(trade.Quantity / avgShort);

            var abnormalTrade = new AbnormalTrade
            {
                Trade = trade,
                ShortTermAverage = avgShort,
                ShortTermRatio = shortRatio
            };

            // 8. 记录异常交易
            abnormalTrades.Insert(0, abnormalTrade);  // 插入到最前面

            // 限制列表长度
            if (abnormalTrades.Count > MaxAbnormalTrades)
                abnormalTrades.RemoveAt(abnormalTrades.Count - 1);

            // 9. 连续大单检测
            if (EnableConsecutiveDetection)
            {
                UpdateConsecutiveDetection(abnormalTrade);
            }

            return abnormalTrade;
        }

        /// <summary>
        /// 更新连续大单检测（窗口快照模式）
        /// </summary>
        private void UpdateConsecutiveDetection(AbnormalTrade abnormalTrade)
        {
            // 过滤：只处理符合连续大单阈值的交易
            if (abnormalTrade.Trade.Quantity < ConsecutiveMinThreshold) return;

            string direction = abnormalTrade.Direction;
            
            // 获取当前窗口内的大单
            var windowTrades = GetAbnormalTradesInWindow(ConsecutiveWindowSeconds, direction)
                .Where(t => t.Trade.Quantity >= ConsecutiveMinThreshold)
                .ToList();
            int windowCount = windowTrades.Count;

            // 判断是否达到触发阈值
            if (windowCount >= ConsecutiveMinCount)
            {
                // 计算窗口时间范围
                DateTime now = DateTime.Now;
                DateTime windowStart = now.AddSeconds(-ConsecutiveWindowSeconds);
                DateTime windowEnd = now;

                // 生成窗口ID（用于去重）
                string directionShort = direction == "买入↑" ? "买入" : "卖出";
                string windowId = $"{directionShort}_{windowStart:HHmmss}_{windowEnd:HHmmss}";

                // 检查是否已记录过相同窗口
                if (!recentWindowIds.Contains(windowId))
                {
                    // 创建窗口快照
                    var newEvent = new ConsecutiveLargeOrderEvent
                    {
                        WindowStartTime = windowStart,
                        WindowEndTime = windowEnd,
                        TriggerTime = now,
                        WindowSeconds = ConsecutiveWindowSeconds,
                        Direction = directionShort,
                        Count = windowCount,
                        Trades = new List<AbnormalTrade>(windowTrades),
                        TotalVolume = windowTrades.Sum(t => t.Trade.Quantity),
                        MaxVolume = windowTrades.Max(t => t.Trade.Quantity),
                        MaxRatio = windowTrades.Max(t => t.ShortTermRatio),
                        FirstTradeTime = windowTrades.First().Trade.Time,
                        LastTradeTime = windowTrades.Last().Trade.Time
                    };

                    // 添加到历史记录
                    consecutiveEvents.Insert(0, newEvent);
                    
                    // 记录窗口ID
                    recentWindowIds.Add(windowId);
                }
            }

            // 定期清理窗口ID缓存（每10秒清理一次）
            if ((DateTime.Now - lastWindowCleanup).TotalSeconds > 10)
            {
                CleanupWindowIds();
                lastWindowCleanup = DateTime.Now;
            }

            // 限制列表长度
            if (consecutiveEvents.Count > MaxConsecutiveEvents)
            {
                consecutiveEvents.RemoveRange(MaxConsecutiveEvents, consecutiveEvents.Count - MaxConsecutiveEvents);
            }
        }

        /// <summary>
        /// 清理过期的窗口ID（保留最近3分钟的）
        /// </summary>
        private void CleanupWindowIds()
        {
            // 清空所有窗口ID，因为3分钟后的窗口不会重复
            if (recentWindowIds.Count > 1000)
            {
                recentWindowIds.Clear();
            }
        }

        /// <summary>
        /// 获取指定时间窗口内的异常大单
        /// </summary>
        private List<AbnormalTrade> GetAbnormalTradesInWindow(int seconds, string? directionFilter = null)
        {
            var cutoffTime = DateTime.Now.AddSeconds(-seconds);
            var trades = abnormalTrades.Where(t => t.Trade.Time >= cutoffTime);

            if (ConsecutiveSameDirectionOnly && !string.IsNullOrEmpty(directionFilter))
            {
                trades = trades.Where(t => t.Direction == directionFilter);
            }

            return trades.ToList();
        }

        /// <summary>
        /// 获取所有异常交易
        /// </summary>
        public List<AbnormalTrade> GetAbnormalTrades()
        {
            return abnormalTrades.ToList();
        }

        /// <summary>
        /// 获取连续大单事件列表
        /// </summary>
        public List<ConsecutiveLargeOrderEvent> GetConsecutiveEvents()
        {
            return consecutiveEvents.ToList();
        }

        /// <summary>
        /// 获取当前窗口的连续大单统计
        /// </summary>
        public ConsecutiveStatistics GetConsecutiveStatistics()
        {
            var buyTrades = GetAbnormalTradesInWindow(ConsecutiveWindowSeconds, "买入↑")
                .Where(t => t.Trade.Quantity >= ConsecutiveMinThreshold)
                .ToList();
            var sellTrades = GetAbnormalTradesInWindow(ConsecutiveWindowSeconds, "卖出↓")
                .Where(t => t.Trade.Quantity >= ConsecutiveMinThreshold)
                .ToList();

            return new ConsecutiveStatistics
            {
                WindowSeconds = ConsecutiveWindowSeconds,
                MinCount = ConsecutiveMinCount,
                BuyCount = buyTrades.Count,
                BuyTotalVolume = buyTrades.Sum(t => t.Trade.Quantity),
                BuyAverageVolume = buyTrades.Count > 0 ? buyTrades.Average(t => t.Trade.Quantity) : 0,
                BuyMaxVolume = buyTrades.Count > 0 ? buyTrades.Max(t => t.Trade.Quantity) : 0,
                BuyMaxRatio = buyTrades.Count > 0 ? buyTrades.Max(t => t.ShortTermRatio) : 0,
                BuyTriggered = buyTrades.Count >= ConsecutiveMinCount,
                SellCount = sellTrades.Count,
                SellTotalVolume = sellTrades.Sum(t => t.Trade.Quantity),
                SellAverageVolume = sellTrades.Count > 0 ? sellTrades.Average(t => t.Trade.Quantity) : 0,
                SellMaxVolume = sellTrades.Count > 0 ? sellTrades.Max(t => t.Trade.Quantity) : 0,
                SellMaxRatio = sellTrades.Count > 0 ? sellTrades.Max(t => t.ShortTermRatio) : 0,
                SellTriggered = sellTrades.Count >= ConsecutiveMinCount
            };
        }

        /// <summary>
        /// 获取指定时间窗口内的交易
        /// </summary>
        private List<TradeData> GetTradesInWindow(int minutes)
        {
            var cutoffTime = DateTime.Now.AddMinutes(-minutes);
            return tradeHistory.Where(t => t.Time >= cutoffTime).ToList();
        }

        /// <summary>
        /// 清理30分钟外的旧数据
        /// </summary>
        private void CleanOldTrades()
        {
            var cutoffTime = DateTime.Now.AddMinutes(-30);
            while (tradeHistory.Count > 0 && tradeHistory.Peek().Time < cutoffTime)
            {
                tradeHistory.Dequeue();
            }
        }

        /// <summary>
        /// 获取统计信息
        /// </summary>
        public TradeStatistics GetStatistics()
        {
            var shortTermTrades = GetTradesInWindow(ShortTermMinutes);
            var longTermTrades = tradeHistory.ToList();

            var recentAbnormal = abnormalTrades.Where(a => 
                a.Trade.Time >= DateTime.Now.AddMinutes(-ShortTermMinutes)).ToList();

            var buyTrades = recentAbnormal.Where(a => !a.Trade.IsBuyerMaker).ToList();
            var sellTrades = recentAbnormal.Where(a => a.Trade.IsBuyerMaker).ToList();

            // 长期平均值的计算逻辑
            decimal longTermAvg;
            if (longTermTrades.Count >= 30)
            {
                longTermAvg = longTermTrades.Average(t => t.Quantity);
            }
            else if (useHistoricalBaseline && historicalBaseline > 0)
            {
                if (longTermTrades.Count > 0)
                {
                    decimal realtimeAvg = longTermTrades.Average(t => t.Quantity);
                    double historicalWeight = 1.0 - (longTermTrades.Count / 30.0);
                    longTermAvg = (decimal)(historicalWeight * (double)historicalBaseline + 
                                           (1 - historicalWeight) * (double)realtimeAvg);
                }
                else
                {
                    longTermAvg = historicalBaseline;
                }
            }
            else
            {
                longTermAvg = longTermTrades.Count > 0 ? longTermTrades.Average(t => t.Quantity) : 0;
            }

            return new TradeStatistics
            {
                ShortTermAverage = shortTermTrades.Count > 0 ? shortTermTrades.Average(t => t.Quantity) : 0,
                ShortTermCount = shortTermTrades.Count,
                LongTermAverage = longTermAvg,
                LongTermCount = longTermTrades.Count,
                BuyAbnormalCount = buyTrades.Count,
                BuyAbnormalVolume = buyTrades.Sum(a => a.Trade.Quantity),
                SellAbnormalCount = sellTrades.Count,
                SellAbnormalVolume = sellTrades.Sum(a => a.Trade.Quantity),
                BaselineInfo = GetBaselineInfo(),
                HistoricalBaseline = useHistoricalBaseline ? historicalBaseline : 0
            };
        }

        /// <summary>
        /// 设置历史基准数据（从API获取的30分钟平均值）
        /// </summary>
        /// <param name="averageVolumePerTrade">历史平均每笔交易量</param>
        public void SetHistoricalBaseline(decimal averageVolumePerTrade)
        {
            if (averageVolumePerTrade > 0)
            {
                historicalBaseline = averageVolumePerTrade;
                useHistoricalBaseline = true;
            }
        }

        /// <summary>
        /// 获取当前使用的基准信息
        /// </summary>
        public string GetBaselineInfo()
        {
            if (useHistoricalBaseline && historicalBaseline > 0)
            {
                var realtimeCount = tradeHistory.Count;
                if (realtimeCount >= 30)
                    return "使用实时数据";
                else if (realtimeCount > 0)
                    return $"混合模式 (历史{(1.0 - realtimeCount/30.0)*100:F0}% + 实时{realtimeCount/30.0*100:F0}%)";
                else
                    return "使用历史基准";
            }
            return "仅实时数据";
        }

        /// <summary>
        /// 清空所有数据
        /// </summary>
        public void Clear()
        {
            tradeHistory.Clear();
            abnormalTrades.Clear();
            consecutiveEvents.Clear();
   
        }
    }

    /// <summary>
    /// 交易统计信息
    /// </summary>
    public class TradeStatistics
    {
        public decimal ShortTermAverage { get; set; }
        public int ShortTermCount { get; set; }
        public decimal LongTermAverage { get; set; }
        public int LongTermCount { get; set; }
        public int BuyAbnormalCount { get; set; }
        public decimal BuyAbnormalVolume { get; set; }
        public int SellAbnormalCount { get; set; }
        public decimal SellAbnormalVolume { get; set; }
        public string BaselineInfo { get; set; } = "";  // 基准数据来源信息
        public decimal HistoricalBaseline { get; set; }  // 历史基准值

        /// <summary>
        /// 市场状态描述
        /// </summary>
        public string MarketStatus
        {
            get
            {
                if (ShortTermAverage == 0 || LongTermAverage == 0)
                    return "数据不足";

                double ratio = (double)(ShortTermAverage / LongTermAverage);
                if (ratio > 1.5)
                    return "活跃度上升 ↑";
                else if (ratio < 0.7)
                    return "活跃度下降 ↓";
                else
                    return "平稳 ─";
            }
        }

        /// <summary>
        /// 大单方向判断
        /// </summary>
        public string DirectionIndicator
        {
            get
            {
                if (BuyAbnormalCount == 0 && SellAbnormalCount == 0)
                    return "多空平衡 ─";

                if (BuyAbnormalCount > SellAbnormalCount * 1.5)
                    return "买盘强势 ↑";
                else if (SellAbnormalCount > BuyAbnormalCount * 1.5)
                    return "卖盘强势 ↓";
                else
                    return "多空平衡 ─";
            }
        }
    }

    /// <summary>
    /// 连续大单统计信息
    /// </summary>
    public class ConsecutiveStatistics
    {
        public int WindowSeconds { get; set; }
        public int MinCount { get; set; }
        
        // 买入统计
        public int BuyCount { get; set; }
        public decimal BuyTotalVolume { get; set; }
        public decimal BuyAverageVolume { get; set; }
        public decimal BuyMaxVolume { get; set; }
        public double BuyMaxRatio { get; set; }
        public bool BuyTriggered { get; set; }
        
        // 卖出统计
        public int SellCount { get; set; }
        public decimal SellTotalVolume { get; set; }
        public decimal SellAverageVolume { get; set; }
        public decimal SellMaxVolume { get; set; }
        public double SellMaxRatio { get; set; }
        public bool SellTriggered { get; set; }

        /// <summary>
        /// 买入状态描述
        /// </summary>
        public string BuyStatusText
        {
            get
            {
                if (BuyTriggered)
                    return $"[✓触发中] 持续{GetDurationText()}";
                else
                    return $"[✗未触发] 还需{MinCount - BuyCount}笔";
            }
        }

        /// <summary>
        /// 卖出状态描述
        /// </summary>
        public string SellStatusText
        {
            get
            {
                if (SellTriggered)
                    return $"[✓触发中] 持续{GetDurationText()}";
                else
                    return $"[✗未触发] 还需{MinCount - SellCount}笔";
            }
        }

        private string GetDurationText()
        {
            // 简化版，实际持续时间需要从事件中获取
            return $"{WindowSeconds}秒内";
        }
    }
}


