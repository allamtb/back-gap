using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Timers;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 交易统计管理器
    /// 负责统计和记录不同时间维度的交易数据
    /// </summary>
    public class TradeStatisticsManager : IDisposable
    {
        private readonly string symbol;
        private readonly string baseDirectory;
        private readonly string logFilePath;
        private readonly object logLock = new object();
        
        // 当前各时间窗口的统计数据
        private TimeWindowStatistics currentMinute1;
        private TimeWindowStatistics currentMinute5;
        private TimeWindowStatistics currentMinute15;
        private TimeWindowStatistics currentHour1;
        private TimeWindowStatistics currentDay1;

        // 定时保存计时器
        private readonly System.Timers.Timer autoSaveTimer;

        // 事件：统计数据更新
        public event Action<string>? OnLog;
        public event Action<string>? OnError;

        public TradeStatisticsManager(string symbol, string baseDirectory = "statistics")
        {
            this.symbol = symbol;
            this.baseDirectory = baseDirectory;
            this.logFilePath = Path.Combine(baseDirectory, "statistics.log");

            // 初始化当前时间窗口
            var now = DateTime.Now;
            currentMinute1 = CreateWindow(StatisticsWindowType.OneMinute, now);
            currentMinute5 = CreateWindow(StatisticsWindowType.FiveMinutes, now);
            currentMinute15 = CreateWindow(StatisticsWindowType.FifteenMinutes, now);
            currentHour1 = CreateWindow(StatisticsWindowType.OneHour, now);
            currentDay1 = CreateWindow(StatisticsWindowType.OneDay, now);

            // 确保目录存在
            EnsureDirectoryExists();

            // 写入启动日志
            WriteLog($"统计管理器已启动 - 交易对: {symbol}");

            // 初始化定时保存计时器（每10秒保存一次）
            autoSaveTimer = new System.Timers.Timer(10000); // 10秒
            autoSaveTimer.Elapsed += OnAutoSaveTimer;
            autoSaveTimer.AutoReset = true;
            autoSaveTimer.Start();
        }

        /// <summary>
        /// 处理新的交易数据
        /// </summary>
        public void ProcessTrade(DateTime tradeTime, decimal quantity, bool isBuyerMaker)
        {
            try
            {
                var now = tradeTime;

                // 检查并更新各时间窗口
                CheckAndUpdateWindow(ref currentMinute1, StatisticsWindowType.OneMinute, now, quantity, isBuyerMaker);
                CheckAndUpdateWindow(ref currentMinute5, StatisticsWindowType.FiveMinutes, now, quantity, isBuyerMaker);
                CheckAndUpdateWindow(ref currentMinute15, StatisticsWindowType.FifteenMinutes, now, quantity, isBuyerMaker);
                CheckAndUpdateWindow(ref currentHour1, StatisticsWindowType.OneHour, now, quantity, isBuyerMaker);
                CheckAndUpdateWindow(ref currentDay1, StatisticsWindowType.OneDay, now, quantity, isBuyerMaker);
            }
            catch (Exception ex)
            {
                var errorMsg = $"处理交易统计失败: {ex.Message}";
                WriteLog(errorMsg, isError: true);
                OnError?.Invoke(errorMsg);
            }
        }

        /// <summary>
        /// 检查时间窗口是否需要切换，并更新统计数据
        /// </summary>
        private void CheckAndUpdateWindow(ref TimeWindowStatistics window, StatisticsWindowType type, DateTime now, decimal quantity, bool isBuyerMaker)
        {
            var expectedStart = GetWindowStart(type, now);

            // 如果时间窗口已经过期，保存旧窗口并创建新窗口
            if (expectedStart > window.StartTime)
            {
                // 保存旧窗口数据（使用更新模式，避免重复记录）
                SaveWindowData(window, type, updateExisting: true);

                // 创建新窗口
                window = CreateWindow(type, now);
            }

            // 累加当前交易数据
            if (isBuyerMaker)
            {
                window.LimitOrderVolume += quantity; // 委托成交（挂单）
            }
            else
            {
                window.MarketOrderVolume += quantity; // 市价成交（主动吃单）
            }
        }

        /// <summary>
        /// 创建新的时间窗口
        /// </summary>
        private TimeWindowStatistics CreateWindow(StatisticsWindowType type, DateTime now)
        {
            var start = GetWindowStart(type, now);
            var end = GetWindowEnd(type, start);

            return new TimeWindowStatistics
            {
                StartTime = start,
                EndTime = end,
                LimitOrderVolume = 0,
                MarketOrderVolume = 0
            };
        }

        /// <summary>
        /// 获取时间窗口的开始时间（对齐到整点）
        /// </summary>
        private DateTime GetWindowStart(StatisticsWindowType type, DateTime now)
        {
            return type switch
            {
                StatisticsWindowType.OneMinute => new DateTime(now.Year, now.Month, now.Day, now.Hour, now.Minute, 0),
                StatisticsWindowType.FiveMinutes => new DateTime(now.Year, now.Month, now.Day, now.Hour, (now.Minute / 5) * 5, 0),
                StatisticsWindowType.FifteenMinutes => new DateTime(now.Year, now.Month, now.Day, now.Hour, (now.Minute / 15) * 15, 0),
                StatisticsWindowType.OneHour => new DateTime(now.Year, now.Month, now.Day, now.Hour, 0, 0),
                StatisticsWindowType.OneDay => new DateTime(now.Year, now.Month, now.Day, 0, 0, 0),
                _ => now
            };
        }

        /// <summary>
        /// 获取时间窗口的结束时间
        /// </summary>
        private DateTime GetWindowEnd(StatisticsWindowType type, DateTime start)
        {
            return type switch
            {
                StatisticsWindowType.OneMinute => start.AddMinutes(1),
                StatisticsWindowType.FiveMinutes => start.AddMinutes(5),
                StatisticsWindowType.FifteenMinutes => start.AddMinutes(15),
                StatisticsWindowType.OneHour => start.AddHours(1),
                StatisticsWindowType.OneDay => start.AddDays(1),
                _ => start
            };
        }

        /// <summary>
        /// 定时保存事件处理
        /// </summary>
        private void OnAutoSaveTimer(object? sender, ElapsedEventArgs e)
        {
            try
            {
                // 保存所有当前窗口数据（不创建新窗口）
                SaveWindowData(currentMinute1, StatisticsWindowType.OneMinute, updateExisting: true);
                SaveWindowData(currentMinute5, StatisticsWindowType.FiveMinutes, updateExisting: true);
                SaveWindowData(currentMinute15, StatisticsWindowType.FifteenMinutes, updateExisting: true);
                SaveWindowData(currentHour1, StatisticsWindowType.OneHour, updateExisting: true);
                SaveWindowData(currentDay1, StatisticsWindowType.OneDay, updateExisting: true);
            }
            catch (Exception ex)
            {
                var errorMsg = $"定时保存失败: {ex.Message}";
                WriteLog(errorMsg, isError: true);
                OnError?.Invoke(errorMsg);
            }
        }

        /// <summary>
        /// 保存时间窗口数据到CSV文件
        /// </summary>
        /// <param name="updateExisting">是否更新已存在的行（用于定时保存）</param>
        private void SaveWindowData(TimeWindowStatistics window, StatisticsWindowType type, bool updateExisting = false)
        {
            try
            {
                var filePath = GetCsvFilePath(window.StartTime, type);
                var directory = Path.GetDirectoryName(filePath);
                
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // 使用UTF-8 BOM编码，这样Excel打开时不会乱码
                var encoding = new UTF8Encoding(true);

                // 如果文件不存在，先写入表头
                bool fileExists = File.Exists(filePath);
                if (!fileExists)
                {
                    File.WriteAllText(filePath, TimeWindowStatistics.CsvHeader + Environment.NewLine, encoding);
                }

                if (updateExisting && fileExists)
                {
                    // 更新模式：读取所有行，更新或添加当前窗口的数据
                    var lines = File.ReadAllLines(filePath, encoding).ToList();
                    var timeKey = window.StartTime.ToString("yyyy-MM-dd HH:mm");
                    bool found = false;

                    for (int i = 1; i < lines.Count; i++) // 跳过表头
                    {
                        if (lines[i].StartsWith(timeKey))
                        {
                            lines[i] = window.ToCsvLine();
                            found = true;
                            break;
                        }
                    }

                    if (!found)
                    {
                        lines.Add(window.ToCsvLine());
                    }

                    File.WriteAllLines(filePath, lines, encoding);
                }
                else
                {
                    // 追加模式：直接追加数据行
                    File.AppendAllText(filePath, window.ToCsvLine() + Environment.NewLine, encoding);
                }

                // 静默保存，不输出日志
            }
            catch (Exception ex)
            {
                var errorMsg = $"保存统计数据失败 ({GetWindowTypeName(type)}): {ex.Message}";
                WriteLog(errorMsg, isError: true);
                OnError?.Invoke(errorMsg);
            }
        }

        /// <summary>
        /// 获取CSV文件路径
        /// </summary>
        private string GetCsvFilePath(DateTime date, StatisticsWindowType type)
        {
            var dateFolder = date.ToString("yyyyMMdd");
            var fileName = type switch
            {
                StatisticsWindowType.OneMinute => $"{symbol}_1分钟市价比_{dateFolder}.csv",
                StatisticsWindowType.FiveMinutes => $"{symbol}_5分钟市价比_{dateFolder}.csv",
                StatisticsWindowType.FifteenMinutes => $"{symbol}_15分钟市价比_{dateFolder}.csv",
                StatisticsWindowType.OneHour => $"{symbol}_1小时市价比_{dateFolder}.csv",
                StatisticsWindowType.OneDay => $"{symbol}_1天市价比_{dateFolder}.csv",
                _ => $"{symbol}_未知_{dateFolder}.csv"
            };

            return Path.Combine(baseDirectory, dateFolder, fileName);
        }

        /// <summary>
        /// 获取时间窗口类型名称
        /// </summary>
        private string GetWindowTypeName(StatisticsWindowType type)
        {
            return type switch
            {
                StatisticsWindowType.OneMinute => "1分钟",
                StatisticsWindowType.FiveMinutes => "5分钟",
                StatisticsWindowType.FifteenMinutes => "15分钟",
                StatisticsWindowType.OneHour => "1小时",
                StatisticsWindowType.OneDay => "1天",
                _ => "未知"
            };
        }

        /// <summary>
        /// 确保基础目录存在
        /// </summary>
        private void EnsureDirectoryExists()
        {
            if (!Directory.Exists(baseDirectory))
            {
                Directory.CreateDirectory(baseDirectory);
            }
        }

        /// <summary>
        /// 写入日志到文件
        /// </summary>
        private void WriteLog(string message, bool isError = false)
        {
            try
            {
                lock (logLock)
                {
                    var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
                    var logLevel = isError ? "ERROR" : "INFO";
                    var logLine = $"[{timestamp}] [{logLevel}] {message}{Environment.NewLine}";
                    
                    File.AppendAllText(logFilePath, logLine, Encoding.UTF8);
                }
            }
            catch
            {
                // 日志写入失败时静默处理，避免影响主功能
            }
        }

        /// <summary>
        /// 获取统计文件目录路径
        /// </summary>
        public string GetStatisticsDirectory()
        {
            return Path.GetFullPath(baseDirectory);
        }

        /// <summary>
        /// 强制保存当前所有窗口数据（程序退出时调用）
        /// </summary>
        public void FlushAll()
        {
            try
            {
                // 使用更新模式，避免重复记录
                SaveWindowData(currentMinute1, StatisticsWindowType.OneMinute, updateExisting: true);
                SaveWindowData(currentMinute5, StatisticsWindowType.FiveMinutes, updateExisting: true);
                SaveWindowData(currentMinute15, StatisticsWindowType.FifteenMinutes, updateExisting: true);
                SaveWindowData(currentHour1, StatisticsWindowType.OneHour, updateExisting: true);
                SaveWindowData(currentDay1, StatisticsWindowType.OneDay, updateExisting: true);
                WriteLog("强制保存所有统计数据完成");
            }
            catch (Exception ex)
            {
                var errorMsg = $"保存统计数据失败: {ex.Message}";
                WriteLog(errorMsg, isError: true);
                OnError?.Invoke(errorMsg);
            }
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            WriteLog("统计管理器正在关闭...");
            autoSaveTimer?.Stop();
            autoSaveTimer?.Dispose();
            FlushAll(); // 保存最后的数据
            WriteLog("统计管理器已关闭");
        }
    }
}

