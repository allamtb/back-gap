using System;
using System.Drawing;
using System.Collections.Generic;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 异常交易数据模型（简化版，移除等级）
    /// </summary>
    public class AbnormalTrade
    {
        /// <summary>
        /// 原始交易数据
        /// </summary>
        public TradeData Trade { get; set; }

        /// <summary>
        /// 短期窗口平均值
        /// </summary>
        public decimal ShortTermAverage { get; set; }

        /// <summary>
        /// 相对短期平均的倍数
        /// </summary>
        public double ShortTermRatio { get; set; }

        /// <summary>
        /// 交易方向
        /// </summary>
        public string Direction => Trade.Direction;

        /// <summary>
        /// 获取背景颜色（根据方向）
        /// </summary>
        public Color GetBackgroundColor()
        {
            // 买入方向 - 浅绿色
            if (!Trade.IsBuyerMaker)
            {
                return Color.FromArgb(144, 238, 144);  // 浅绿
            }
            // 卖出方向 - 浅红色
            else
            {
                return Color.FromArgb(255, 182, 193);  // 浅粉红
            }
        }

        /// <summary>
        /// 获取前景文字颜色
        /// </summary>
        public Color GetForegroundColor()
        {
            return Color.Black;
        }
    }

    /// <summary>
    /// 连续大单事件（窗口快照模式）
    /// </summary>
    public class ConsecutiveLargeOrderEvent
    {
        /// <summary>
        /// 检测窗口的开始时间（当前时间 - 窗口秒数）
        /// </summary>
        public DateTime WindowStartTime { get; set; }

        /// <summary>
        /// 检测窗口的结束时间（触发时的当前时间）
        /// </summary>
        public DateTime WindowEndTime { get; set; }

        /// <summary>
        /// 触发时间（记录创建时间）
        /// </summary>
        public DateTime TriggerTime { get; set; }

        /// <summary>
        /// 窗口内第一笔大单的时间
        /// </summary>
        public DateTime FirstTradeTime { get; set; }

        /// <summary>
        /// 窗口内最后一笔大单的时间
        /// </summary>
        public DateTime LastTradeTime { get; set; }

        /// <summary>
        /// 窗口时长（秒）
        /// </summary>
        public int WindowSeconds { get; set; }

        /// <summary>
        /// 窗口时长文本
        /// </summary>
        public string WindowDurationText => $"{WindowSeconds}秒";

        /// <summary>
        /// 方向："买入" 或 "卖出"
        /// </summary>
        public string Direction { get; set; }

        /// <summary>
        /// 大单笔数
        /// </summary>
        public int Count { get; set; }

        /// <summary>
        /// 总成交量
        /// </summary>
        public decimal TotalVolume { get; set; }

        /// <summary>
        /// 平均单笔成交量
        /// </summary>
        public decimal AverageVolume => Count > 0 ? TotalVolume / Count : 0;

        /// <summary>
        /// 最大单笔成交量
        /// </summary>
        public decimal MaxVolume { get; set; }

        /// <summary>
        /// 最大倍数
        /// </summary>
        public double MaxRatio { get; set; }

        /// <summary>
        /// 包含的所有大单
        /// </summary>
        public List<AbnormalTrade> Trades { get; set; } = new List<AbnormalTrade>();

        /// <summary>
        /// 窗口ID（用于去重，相同窗口不重复记录）
        /// 格式：方向_窗口开始时间_窗口结束时间
        /// </summary>
        public string WindowId => $"{Direction}_{WindowStartTime:HHmmss}_{WindowEndTime:HHmmss}";

        /// <summary>
        /// 获取背景颜色
        /// </summary>
        public Color GetBackgroundColor()
        {
            return Direction == "买入" 
                ? Color.FromArgb(144, 238, 144)  // 浅绿
                : Color.FromArgb(255, 182, 193);  // 浅粉红
        }

        /// <summary>
        /// 开始时间（兼容旧代码，映射到窗口开始时间）
        /// </summary>
        public DateTime StartTime => WindowStartTime;

        /// <summary>
        /// 结束时间（兼容旧代码，映射到窗口结束时间）
        /// </summary>
        public DateTime? EndTime => WindowEndTime;

        /// <summary>
        /// 持续时间文本（兼容旧代码，显示窗口时长）
        /// </summary>
        public string DurationText => WindowDurationText;

        /// <summary>
        /// 是否活跃（兼容旧代码，窗口模式下总是false）
        /// </summary>
        public bool IsActive => false;
    }
}



