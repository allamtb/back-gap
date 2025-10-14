using System;
using System.IO;
using System.Text;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 爆仓日志记录器 - 记录所有爆仓事件到CSV文件
    /// </summary>
    public class LiquidationLogger
    {
        private readonly string logDirectory;
        private readonly object lockObject = new object();

        public LiquidationLogger(string logDir = "LiquidationLogs")
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
        /// 记录爆仓事件
        /// </summary>
        public void LogLiquidation(LiquidationData liquidation)
        {
            try
            {
                lock (lockObject)
                {
                    string logFile = GetTodayLogFile();
                    bool fileExists = File.Exists(logFile);

                    using (StreamWriter writer = new StreamWriter(logFile, append: true, Encoding.UTF8))
                    {
                        // 如果是新文件，先写入表头
                        if (!fileExists)
                        {
                            writer.WriteLine(GetCsvHeader());
                        }

                        // 写入爆仓记录
                        writer.WriteLine(FormatCsvEntry(liquidation));
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"记录爆仓日志时出错: {ex.Message}");
            }
        }

        /// <summary>
        /// 获取今天的日志文件路径
        /// </summary>
        private string GetTodayLogFile()
        {
            string fileName = $"liquidation_{DateTime.Now:yyyyMMdd}.csv";
            return Path.Combine(logDirectory, fileName);
        }

        /// <summary>
        /// 获取CSV表头
        /// </summary>
        private string GetCsvHeader()
        {
            return "爆仓时间,币种,价格(USDT),数量(币),金额(USDT),方向,订单类型";
        }

        /// <summary>
        /// 格式化CSV条目
        /// </summary>
        private string FormatCsvEntry(LiquidationData liquidation)
        {
            StringBuilder sb = new StringBuilder();

            // 爆仓时间
            sb.Append($"{liquidation.Time:yyyy-MM-dd HH:mm:ss.fff},");

            // 币种
            sb.Append($"{liquidation.Symbol},");

            // 价格
            sb.Append($"{liquidation.Price:F2},");

            // 数量
            sb.Append($"{liquidation.Quantity:F4},");

            // 金额
            sb.Append($"{liquidation.LiquidationValue:F2},");

            // 方向 (LONG=多头爆仓, SHORT=空头爆仓)
            string direction = liquidation.Side == "SELL" ? "多头" : "空头";
            sb.Append($"{direction},");

            // 订单类型
            sb.Append(liquidation.OrderType);

            return sb.ToString();
        }

        /// <summary>
        /// 获取日志目录路径
        /// </summary>
        public string GetLogDirectory()
        {
            return logDirectory;
        }

        /// <summary>
        /// 获取今天的日志文件路径（公开方法）
        /// </summary>
        public string GetTodayLogFilePath()
        {
            return GetTodayLogFile();
        }
    }
}

