using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 币安 WebSocket 管理器
    /// 负责管理交易流和订单簿流的连接和数据接收
    /// </summary>
    public class BinanceWebSocketManager : IDisposable
    {
        private ClientWebSocket? wsTradeStream;
        private ClientWebSocket? wsOrderBookStream;
        private ClientWebSocket? wsLiquidationStream; // 爆仓流
        private CancellationTokenSource? cancellationTokenSource;
        private readonly string? proxyUrl;
        private string? currentSymbol; // 保存当前交易对，用于重连
        private int reconnectCount = 0; // 重连次数
        private DateTime? lastReconnectTime; // 最后重连时间
        private bool isManualDisconnect = false; // 是否手动断开
        private DateTime lastTradeStreamDataTime = DateTime.Now; // 最后收到交易流数据的时间
        private DateTime lastOrderBookDataTime = DateTime.Now; // 最后收到订单簿数据的时间
        private DateTime lastLiquidationDataTime = DateTime.Now; // 最后收到爆仓数据的时间
        private TradeStatisticsManager? statisticsManager; // 市价比统计管理器
        private LargeOrderStatisticsManager? largeOrderStatisticsManager; // 大单统计管理器
        private LiquidationMonitor? liquidationMonitor; // 爆仓监控器
        private decimal largeOrderThreshold = 0.05M; // 大单阈值（默认0.05 BTC）

        /// <summary>
        /// 交易数据接收事件
        /// </summary>
        public event Action<TradeStreamData>? OnTradeReceived;

        /// <summary>
        /// 订单簿数据接收事件
        /// </summary>
        public event Action<OrderBookData>? OnOrderBookReceived;

        /// <summary>
        /// 错误事件
        /// </summary>
        public event Action<string>? OnError;

        /// <summary>
        /// 重连中事件（参数：重连次数，重连时间）
        /// </summary>
        public event Action<int, DateTime>? OnReconnecting;

        /// <summary>
        /// 重连成功事件（参数：重连次数）
        /// </summary>
        public event Action<int>? OnReconnected;

        /// <summary>
        /// 爆仓数据接收事件
        /// </summary>
        public event Action<LiquidationData>? OnLiquidationReceived;

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="proxyUrl">代理地址（可选）</param>
        /// <param name="largeOrderThreshold">大单阈值（默认0.05 BTC）</param>
        public BinanceWebSocketManager(string? proxyUrl = null, decimal largeOrderThreshold = 0.05M)
        {
            this.proxyUrl = proxyUrl;
            this.largeOrderThreshold = largeOrderThreshold;
            cancellationTokenSource = new CancellationTokenSource();
        }

        /// <summary>
        /// 连接交易流
        /// </summary>
        /// <param name="symbol">交易对（小写，例如：btcusdt）</param>
        public async Task ConnectTradeStreamAsync(string symbol)
        {
            try
            {
                currentSymbol = symbol; // 保存交易对
                isManualDisconnect = false; // 重置手动断开标志
                reconnectCount = 0; // 重置重连计数
                lastTradeStreamDataTime = DateTime.Now; // 重置心跳时间
                lastOrderBookDataTime = DateTime.Now; // 重置心跳时间

                // 初始化市价比统计管理器
                if (statisticsManager == null)
                {
                    statisticsManager = new TradeStatisticsManager(symbol.ToUpper(), Constants.StatisticsDirectory);
                    // 统计日志和错误不显示在界面上，避免干扰连接状态显示
                    // 如果需要调试，可以输出到独立的日志文件
                    statisticsManager.OnLog += (msg) => System.Diagnostics.Debug.WriteLine($"[市价比统计] {msg}");
                    statisticsManager.OnError += (msg) => System.Diagnostics.Debug.WriteLine($"[市价比统计错误] {msg}");
                }

                // 初始化大单统计管理器
                if (largeOrderStatisticsManager == null)
                {
                    largeOrderStatisticsManager = new LargeOrderStatisticsManager(symbol.ToUpper(), largeOrderThreshold, "large_order_statistics");
                    largeOrderStatisticsManager.OnLog += (msg) => System.Diagnostics.Debug.WriteLine($"[大单统计] {msg}");
                    largeOrderStatisticsManager.OnError += (msg) => System.Diagnostics.Debug.WriteLine($"[大单统计错误] {msg}");
                }

                wsTradeStream = new ClientWebSocket();
                ConfigureWebSocket(wsTradeStream);

                string url = $"{Constants.BinanceWebSocketBaseUrl}/{symbol}@trade";
                await wsTradeStream.ConnectAsync(new Uri(url), cancellationTokenSource.Token);

                // 启动接收任务
                _ = Task.Run(() => ReceiveTradeStreamAsync(cancellationTokenSource.Token));
                
                // 启动心跳检测
                StartHeartbeatMonitor();
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"连接交易流失败: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 连接订单簿流
        /// </summary>
        /// <param name="symbol">交易对（小写，例如：btcusdt）</param>
        public async Task ConnectOrderBookStreamAsync(string symbol)
        {
            try
            {
                wsOrderBookStream = new ClientWebSocket();
                ConfigureWebSocket(wsOrderBookStream);

                string url = $"{Constants.BinanceWebSocketBaseUrl}/{symbol}@depth20@100ms";
                await wsOrderBookStream.ConnectAsync(new Uri(url), cancellationTokenSource.Token);

                // 启动接收任务
                _ = Task.Run(() => ReceiveOrderBookStreamAsync(cancellationTokenSource.Token));
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"连接订单簿流失败: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 连接爆仓订单流
        /// </summary>
        /// <param name="symbol">交易对（小写，例如：btcusdt）</param>
        public async Task ConnectLiquidationStreamAsync(string symbol)
        {
            try
            {
                // 初始化爆仓监控器
                if (liquidationMonitor == null)
                {
                    liquidationMonitor = new LiquidationMonitor();
                }

                wsLiquidationStream = new ClientWebSocket();
                ConfigureWebSocket(wsLiquidationStream);

                // 订阅指定交易对的爆仓流
                string url = $"{Constants.BinanceWebSocketBaseUrl}/{symbol}@forceOrder";
                await wsLiquidationStream.ConnectAsync(new Uri(url), cancellationTokenSource.Token);

                // 启动接收任务
                _ = Task.Run(() => ReceiveLiquidationStreamAsync(cancellationTokenSource.Token));
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"连接爆仓流失败: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// 启动心跳检测任务
        /// </summary>
        private void StartHeartbeatMonitor()
        {
            _ = Task.Run(async () =>
            {
                while (!cancellationTokenSource?.Token.IsCancellationRequested ?? false)
                {
                    try
                    {
                        await Task.Delay(Constants.HeartbeatCheckInterval, cancellationTokenSource.Token);

                        if (isManualDisconnect || cancellationTokenSource?.Token.IsCancellationRequested == true)
                        {
                            break;
                        }

                        var now = DateTime.Now;

                        // 检查交易流
                        if ((now - lastTradeStreamDataTime).TotalSeconds > Constants.HeartbeatTimeoutSeconds)
                        {
                            if (wsTradeStream?.State == WebSocketState.Open)
                            {
                                OnError?.Invoke($"交易流心跳超时({(now - lastTradeStreamDataTime).TotalSeconds:F1}秒)，触发重连");
                                await wsTradeStream.CloseAsync(WebSocketCloseStatus.NormalClosure, "Heartbeat timeout", CancellationToken.None);
                            }
                        }

                        // 检查订单簿流
                        if ((now - lastOrderBookDataTime).TotalSeconds > Constants.HeartbeatTimeoutSeconds)
                        {
                            if (wsOrderBookStream?.State == WebSocketState.Open)
                            {
                                OnError?.Invoke($"订单簿流心跳超时({(now - lastOrderBookDataTime).TotalSeconds:F1}秒)，触发重连");
                                await wsOrderBookStream.CloseAsync(WebSocketCloseStatus.NormalClosure, "Heartbeat timeout", CancellationToken.None);
                            }
                        }
                    }
                    catch (OperationCanceledException)
                    {
                        break;
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"心跳检测异常: {ex.Message}");
                    }
                }
            });
        }

        /// <summary>
        /// 配置 WebSocket 代理
        /// </summary>
        private void ConfigureWebSocket(ClientWebSocket ws)
        {
            if (!string.IsNullOrEmpty(proxyUrl))
            {
                ws.Options.Proxy = new WebProxy(proxyUrl);
            }
            else
            {
                ws.Options.Proxy = null;
            }
        }

        /// <summary>
        /// 接收交易流数据
        /// </summary>
        private async Task ReceiveTradeStreamAsync(CancellationToken cancellationToken)
        {
            var buffer = new byte[Constants.TradeStreamBufferSize];
            var messageBuilder = new StringBuilder();

            try
            {
                while (wsTradeStream != null && wsTradeStream.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
                {
                    var result = await wsTradeStream.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await wsTradeStream.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancellationToken);
                        break;
                    }

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        messageBuilder.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));

                        if (result.EndOfMessage)
                        {
                            // 更新心跳时间
                            lastTradeStreamDataTime = DateTime.Now;
                            
                            string msg = messageBuilder.ToString();
                            messageBuilder.Clear();

                            // 解析并触发事件
                            var tradeData = ParseTradeMessage(msg);
                            if (tradeData != null)
                            {
                                OnTradeReceived?.Invoke(tradeData);
                                
                                // 统计交易数据（市价比统计）
                                if (statisticsManager != null && decimal.TryParse(tradeData.Quantity, out decimal qty))
                                {
                                    statisticsManager.ProcessTrade(tradeData.Time, qty, tradeData.IsBuyerMaker);
                                }

                                // 统计大单数据
                                if (largeOrderStatisticsManager != null && decimal.TryParse(tradeData.Quantity, out decimal qty2))
                                {
                                    largeOrderStatisticsManager.ProcessTrade(tradeData.Time, qty2, tradeData.IsBuyerMaker);
                                }
                            }
                        }
                    }
                }

                // 如果不是手动断开且不是取消，则尝试重连
                if (!isManualDisconnect && !cancellationToken.IsCancellationRequested)
                {
                    await AttemptReconnectTradeStreamAsync(cancellationToken);
                }
            }
            catch (OperationCanceledException)
            {
                // 正常取消，不处理
            }
            catch (WebSocketException ex)
            {
                if (!cancellationToken.IsCancellationRequested && !isManualDisconnect)
                {
                    OnError?.Invoke($"WebSocket连接错误: {ex.Message}");
                    await AttemptReconnectTradeStreamAsync(cancellationToken);
                }
            }
            catch (Exception ex)
            {
                if (!cancellationToken.IsCancellationRequested && !isManualDisconnect)
                {
                    OnError?.Invoke($"交易流接收错误: {ex.Message}");
                    await AttemptReconnectTradeStreamAsync(cancellationToken);
                }
            }
        }

        /// <summary>
        /// 尝试重连交易流
        /// </summary>
        private async Task AttemptReconnectTradeStreamAsync(CancellationToken cancellationToken)
        {
            if (string.IsNullOrEmpty(currentSymbol) || isManualDisconnect || cancellationToken.IsCancellationRequested)
            {
                return;
            }

            try
            {
                // 等待5秒后重连
                await Task.Delay(5000, cancellationToken);

                if (cancellationToken.IsCancellationRequested || isManualDisconnect)
                {
                    return;
                }

                reconnectCount++;
                lastReconnectTime = DateTime.Now;
                OnReconnecting?.Invoke(reconnectCount, lastReconnectTime.Value);

                // 清理旧连接
                wsTradeStream?.Dispose();

                // 重新连接
                wsTradeStream = new ClientWebSocket();
                ConfigureWebSocket(wsTradeStream);

                string url = $"{Constants.BinanceWebSocketBaseUrl}/{currentSymbol}@trade";
                await wsTradeStream.ConnectAsync(new Uri(url), cancellationToken);

                // 检查连接状态
                if (wsTradeStream.State == WebSocketState.Open)
                {
                    OnError?.Invoke($"交易流重连成功（第 {reconnectCount} 次）");
                    OnReconnected?.Invoke(reconnectCount); // 触发重连成功事件
                    
                    // 继续接收数据
                    _ = Task.Run(() => ReceiveTradeStreamAsync(cancellationToken));
                }
                else
                {
                    throw new Exception($"连接状态异常: {wsTradeStream.State}");
                }
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"重连失败: {ex.Message}，5秒后再次尝试...");
                // 继续尝试重连
                await AttemptReconnectTradeStreamAsync(cancellationToken);
            }
        }

        /// <summary>
        /// 尝试重连订单簿流
        /// </summary>
        private async Task AttemptReconnectOrderBookStreamAsync(CancellationToken cancellationToken)
        {
            if (string.IsNullOrEmpty(currentSymbol) || isManualDisconnect || cancellationToken.IsCancellationRequested)
            {
                return;
            }

            try
            {
                // 等待5秒后重连
                await Task.Delay(5000, cancellationToken);

                if (cancellationToken.IsCancellationRequested || isManualDisconnect)
                {
                    return;
                }

                reconnectCount++;
                lastReconnectTime = DateTime.Now;
                OnReconnecting?.Invoke(reconnectCount, lastReconnectTime.Value);

                // 清理旧连接
                wsOrderBookStream?.Dispose();

                // 重新连接
                wsOrderBookStream = new ClientWebSocket();
                ConfigureWebSocket(wsOrderBookStream);

                string url = $"{Constants.BinanceWebSocketBaseUrl}/{currentSymbol}@depth20@100ms";
                await wsOrderBookStream.ConnectAsync(new Uri(url), cancellationToken);

                // 检查连接状态
                if (wsOrderBookStream.State == WebSocketState.Open)
                {
                    OnError?.Invoke($"订单簿流重连成功（第 {reconnectCount} 次）");
                    OnReconnected?.Invoke(reconnectCount); // 触发重连成功事件
                    
                    // 继续接收数据
                    _ = Task.Run(() => ReceiveOrderBookStreamAsync(cancellationToken));
                }
                else
                {
                    throw new Exception($"连接状态异常: {wsOrderBookStream.State}");
                }
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"订单簿流重连失败: {ex.Message}，5秒后再次尝试...");
                // 继续尝试重连
                await AttemptReconnectOrderBookStreamAsync(cancellationToken);
            }
        }

        /// <summary>
        /// 接收订单簿流数据
        /// </summary>
        private async Task ReceiveOrderBookStreamAsync(CancellationToken cancellationToken)
        {
            var buffer = new byte[Constants.OrderBookStreamBufferSize];
            var messageBuilder = new StringBuilder();

            try
            {
                while (wsOrderBookStream != null && wsOrderBookStream.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
                {
                    var result = await wsOrderBookStream.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await wsOrderBookStream.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancellationToken);
                        break;
                    }

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        messageBuilder.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));

                        if (result.EndOfMessage)
                        {
                            // 更新心跳时间
                            lastOrderBookDataTime = DateTime.Now;
                            
                            string msg = messageBuilder.ToString();
                            messageBuilder.Clear();

                            // 解析并触发事件
                            var orderBookData = ParseOrderBookMessage(msg);
                            if (orderBookData != null)
                            {
                                OnOrderBookReceived?.Invoke(orderBookData);
                            }
                        }
                    }
                }
            }
            catch (OperationCanceledException)
            {
                // 正常取消，不处理
            }
            catch (Exception ex)
            {
                if (!cancellationToken.IsCancellationRequested)
                {
                    OnError?.Invoke($"订单簿流接收错误: {ex.Message}");
                    await AttemptReconnectOrderBookStreamAsync(cancellationToken);
                }
            }
        }

        /// <summary>
        /// 接收爆仓流数据
        /// </summary>
        private async Task ReceiveLiquidationStreamAsync(CancellationToken cancellationToken)
        {
            var buffer = new byte[8192];
            var messageBuilder = new StringBuilder();

            try
            {
                while (wsLiquidationStream != null && wsLiquidationStream.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
                {
                    var result = await wsLiquidationStream.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await wsLiquidationStream.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancellationToken);
                        break;
                    }

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        messageBuilder.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));

                        if (result.EndOfMessage)
                        {
                            // 更新心跳时间
                            lastLiquidationDataTime = DateTime.Now;
                            
                            string msg = messageBuilder.ToString();
                            messageBuilder.Clear();

                            // 解析并触发事件
                            var liquidationData = ParseLiquidationMessage(msg);
                            if (liquidationData != null)
                            {
                                // 添加到监控器（会自动过滤）
                                var filtered = liquidationMonitor?.AddLiquidation(liquidationData);
                                if (filtered != null)
                                {
                                    OnLiquidationReceived?.Invoke(filtered);
                                }
                            }
                        }
                    }
                }
            }
            catch (OperationCanceledException)
            {
                // 正常取消，不处理
            }
            catch (Exception ex)
            {
                if (!cancellationToken.IsCancellationRequested)
                {
                    OnError?.Invoke($"爆仓流接收错误: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// 解析爆仓消息
        /// </summary>
        private LiquidationData? ParseLiquidationMessage(string message)
        {
            try
            {
                using var doc = JsonDocument.Parse(message);
                var root = doc.RootElement;
                
                // 爆仓流返回的数据格式：{"o": {...}}
                if (!root.TryGetProperty("o", out var orderData))
                    return null;

                // 使用事件时间 E（毫秒时间戳）
                var timestamp = root.GetProperty("E").GetInt64();
                var time = DateTimeOffset.FromUnixTimeMilliseconds(timestamp).ToLocalTime().DateTime;

                // 解析价格和数量
                // 优先使用平均价格 ap，如果不存在则使用订单价格 p
                string priceStr;
                if (orderData.TryGetProperty("ap", out var apElement) && !string.IsNullOrEmpty(apElement.GetString()))
                {
                    priceStr = apElement.GetString() ?? "0";
                }
                else
                {
                    priceStr = orderData.GetProperty("p").GetString() ?? "0";
                }
                
                var quantityStr = orderData.GetProperty("q").GetString() ?? "0";
                var symbol = orderData.GetProperty("s").GetString() ?? "";
                var side = orderData.GetProperty("S").GetString() ?? "";
                var orderType = orderData.GetProperty("o").GetString() ?? "";
                var orderStatus = orderData.GetProperty("X").GetString() ?? "";
                var lastFilledQtyStr = orderData.GetProperty("z").GetString() ?? "0";

                return new LiquidationData
                {
                    Time = time,
                    Symbol = symbol,
                    Side = side,
                    OrderType = orderType,
                    Price = decimal.Parse(priceStr),
                    Quantity = decimal.Parse(quantityStr),
                    LastFilledQty = decimal.Parse(lastFilledQtyStr),
                    OrderStatus = orderStatus
                };
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"解析爆仓消息失败: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 解析交易消息
        /// </summary>
        private TradeStreamData? ParseTradeMessage(string message)
        {
            try
            {
                using var doc = JsonDocument.Parse(message);
                var data = doc.RootElement;

                var price = data.GetProperty("p").GetString() ?? "0";
                var qty = data.GetProperty("q").GetString() ?? "0";
                var isMaker = data.GetProperty("m").GetBoolean();
                var timestamp = data.GetProperty("T").GetInt64();
                var time = DateTimeOffset.FromUnixTimeMilliseconds(timestamp).ToLocalTime().DateTime;

                return new TradeStreamData
                {
                    Time = time,
                    Price = price,
                    Quantity = qty,
                    IsBuyerMaker = isMaker,
                    Side = isMaker ? "挂单成交 (被动)" : "市价成交 (主动)"
                };
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"解析交易消息失败: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 解析订单簿消息
        /// </summary>
        private OrderBookData? ParseOrderBookMessage(string message)
        {
            try
            {
                using var doc = JsonDocument.Parse(message);
                var root = doc.RootElement;

                // 立即复制数据到独立的结构
                var asks = root.GetProperty("a").EnumerateArray()
                    .Select(item => (item[0].GetString() ?? "0", item[1].GetString() ?? "0"))
                    .ToList();

                var bids = root.GetProperty("b").EnumerateArray()
                    .Select(item => (item[0].GetString() ?? "0", item[1].GetString() ?? "0"))
                    .ToList();

                return new OrderBookData
                {
                    Asks = asks,
                    Bids = bids,
                    Timestamp = DateTime.Now
                };
            }
            catch (Exception ex)
            {
                OnError?.Invoke($"解析订单簿消息失败: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 断开连接
        /// </summary>
        public async Task DisconnectAsync()
        {
            try
            {
                isManualDisconnect = true; // 标记为手动断开，阻止自动重连
                cancellationTokenSource?.Cancel();

                if (wsTradeStream != null && wsTradeStream.State == WebSocketState.Open)
                {
                    await wsTradeStream.CloseAsync(WebSocketCloseStatus.NormalClosure, "关闭连接", CancellationToken.None);
                }

                if (wsOrderBookStream != null && wsOrderBookStream.State == WebSocketState.Open)
                {
                    await wsOrderBookStream.CloseAsync(WebSocketCloseStatus.NormalClosure, "关闭连接", CancellationToken.None);
                }

                if (wsLiquidationStream != null && wsLiquidationStream.State == WebSocketState.Open)
                {
                    await wsLiquidationStream.CloseAsync(WebSocketCloseStatus.NormalClosure, "关闭连接", CancellationToken.None);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"断开连接错误: {ex.Message}");
            }
        }

        /// <summary>
        /// 获取市价比统计文件目录
        /// </summary>
        public string GetStatisticsDirectory()
        {
            return statisticsManager?.GetStatisticsDirectory() ?? "";
        }

        /// <summary>
        /// 获取大单统计文件目录
        /// </summary>
        public string GetLargeOrderStatisticsDirectory()
        {
            return largeOrderStatisticsManager?.GetStatisticsDirectory() ?? "";
        }

        /// <summary>
        /// 更新大单阈值
        /// </summary>
        public void UpdateLargeOrderThreshold(decimal threshold)
        {
            largeOrderThreshold = threshold;
            largeOrderStatisticsManager?.UpdateLargeOrderThreshold(threshold);
        }

        /// <summary>
        /// 获取爆仓监控器
        /// </summary>
        public LiquidationMonitor? GetLiquidationMonitor()
        {
            return liquidationMonitor;
        }

        /// <summary>
        /// 获取爆仓统计
        /// </summary>
        public LiquidationStatistics? GetLiquidationStatistics()
        {
            return liquidationMonitor?.GetStatistics();
        }

        /// <summary>
        /// 更新爆仓监控参数
        /// </summary>
        public void UpdateLiquidationMonitorParams(int timeWindowMinutes, decimal minThreshold)
        {
            if (liquidationMonitor != null)
            {
                liquidationMonitor.TimeWindowMinutes = timeWindowMinutes;
                liquidationMonitor.MinLiquidationThreshold = minThreshold;
            }
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            try
            {
                // 保存统计数据
                statisticsManager?.FlushAll();
                statisticsManager?.Dispose();
                
                // 保存大单统计数据
                largeOrderStatisticsManager?.FlushAll();
                largeOrderStatisticsManager?.Dispose();
                
                cancellationTokenSource?.Cancel();
                cancellationTokenSource?.Dispose();
                wsTradeStream?.Dispose();
                wsOrderBookStream?.Dispose();
                wsLiquidationStream?.Dispose();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"释放资源错误: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// 交易流数据模型
    /// </summary>
    public class TradeStreamData
    {
        public DateTime Time { get; set; }
        public string Price { get; set; } = "";
        public string Quantity { get; set; } = "";
        public bool IsBuyerMaker { get; set; }
        public string Side { get; set; } = "";
    }

    /// <summary>
    /// 订单簿数据模型
    /// </summary>
    public class OrderBookData
    {
        public List<(string price, string qty)> Asks { get; set; } = new List<(string, string)>();
        public List<(string price, string qty)> Bids { get; set; } = new List<(string, string)>();
        public DateTime Timestamp { get; set; }
    }
}

