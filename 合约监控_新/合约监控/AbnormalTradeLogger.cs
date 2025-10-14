using System;
using System.IO;
using System.Text;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 异常大单日志记录器（按天分割）
    /// </summary>
    public class AbnormalTradeLogger
    {
        private readonly string logDirectory;
        private readonly object lockObject = new object();

        public AbnormalTradeLogger(string logDir = "AbnormalTradeLogs")
        {
            // 使用相对路径，在程序运行目录下创建日志文件夹
            logDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, logDir);
            
            // 确保日志目录存在
            if (!Directory.Exists(logDirectory))
            {
                Directory.CreateDirectory(logDirectory);
            }
        }

        /// <summary>
        /// 记录异常大单
        /// </summary>
        public void LogAbnormalTrade(AbnormalTrade abnormalTrade)
        {
            if (abnormalTrade == null || abnormalTrade.Trade == null)
                return;

            try
            {
                lock (lockObject)
                {
                    string logFilePath = GetTodayLogFilePath();
                    bool isNewFile = !File.Exists(logFilePath);
                    
                    using (StreamWriter sw = new StreamWriter(logFilePath, true, Encoding.UTF8))
                    {
                        // 如果是新文件，先写入表头
                        if (isNewFile)
                        {
                            sw.WriteLine("交易时间 | 价格(USDT) | 数量(BTC) | 金额(USDT) | 方向 | 吃单/挂单 | 短期平均(BTC) | 异常倍数");
                            sw.WriteLine("".PadRight(130, '-')); // 分隔线
                        }
                        
                        // 写入日志条目
                        string logEntry = FormatLogEntry(abnormalTrade);
                        sw.WriteLine(logEntry);
                    }
                }
            }
            catch (Exception ex)
            {
                // 静默处理异常，避免影响主程序
                Console.WriteLine($"日志记录失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 获取今天的日志文件路径
        /// </summary>
        public string GetTodayLogFilePath()
        {
            string fileName = $"AbnormalTrades_{DateTime.Now:yyyyMMdd}.log";
            return Path.Combine(logDirectory, fileName);
        }

        /// <summary>
        /// 获取日志目录路径
        /// </summary>
        public string GetLogDirectory()
        {
            return logDirectory;
        }

        /// <summary>
        /// 格式化日志条目（一行格式，便于数据分析）
        /// </summary>
        private string FormatLogEntry(AbnormalTrade abnormalTrade)
        {
            var trade = abnormalTrade.Trade;
            
            // 格式：交易时间 | 价格 | 数量 | 金额 | 方向 | 吃单/挂单 | 短期平均 | 异常倍数
            string direction = trade.IsBuyerMaker ? "卖出" : "买入";
            string orderType = trade.OrderTypeText;  // 使用 TradeData 的 OrderTypeText 属性
            
            return $"{trade.Time:yyyy-MM-dd HH:mm:ss.fff} | " +
                   $"{trade.Price:F2} | " +
                   $"{trade.Quantity:F4} | " +
                   $"{(trade.Price * trade.Quantity):F2} | " +
                   $"{direction} | " +
                   $"{orderType} | " +
                   $"{abnormalTrade.ShortTermAverage:F4} | " +
                   $"{abnormalTrade.ShortTermRatio:F2}x";
        }

        /// <summary>
        /// 获取异常等级描述
        /// </summary>
        private string GetAbnormalLevel(double ratio)
        {
            if (ratio >= 10) return "⚠️ 极度异常 (10x+)";
            if (ratio >= 5) return "🔥 高度异常 (5x-10x)";
            if (ratio >= 3) return "⚡ 中度异常 (3x-5x)";
            if (ratio >= 2) return "📊 轻度异常 (2x-3x)";
            return "正常";
        }

        /// <summary>
        /// 清理旧日志文件（保留最近N天）
        /// </summary>
        public void CleanOldLogs(int keepDays = 30)
        {
            try
            {
                var files = Directory.GetFiles(logDirectory, "AbnormalTrades_*.log");
                var cutoffDate = DateTime.Now.AddDays(-keepDays);

                foreach (var file in files)
                {
                    var fileInfo = new FileInfo(file);
                    if (fileInfo.CreationTime < cutoffDate)
                    {
                        File.Delete(file);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"清理旧日志失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 获取所有日志文件列表（按日期倒序）
        /// </summary>
        public string[] GetAllLogFiles()
        {
            try
            {
                var files = Directory.GetFiles(logDirectory, "AbnormalTrades_*.log");
                Array.Sort(files);
                Array.Reverse(files);
                return files;
            }
            catch
            {
                return Array.Empty<string>();
            }
        }
    }
}

