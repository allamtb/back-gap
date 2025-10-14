using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 币安API客户端 - 获取历史数据
    /// </summary>
    public class BinanceApiClient
    {
        private readonly HttpClient httpClient;
        private readonly string baseUrl = "https://fapi.binance.com";

        public BinanceApiClient(string? proxyUrl = null)
        {
            var handler = new HttpClientHandler();
            
            if (!string.IsNullOrEmpty(proxyUrl))
            {
                handler.Proxy = new System.Net.WebProxy(proxyUrl);
                handler.UseProxy = true;
            }

            httpClient = new HttpClient(handler)
            {
                Timeout = TimeSpan.FromSeconds(30)
            };
        }

        /// <summary>
        /// 获取24小时统计数据
        /// </summary>
        public async Task<Ticker24h?> Get24HourTickerAsync(string symbol)
        {
            try
            {
                string url = $"{baseUrl}/fapi/v1/ticker/24hr?symbol={symbol.ToUpper()}";
                var response = await httpClient.GetStringAsync(url);
                
                using var doc = JsonDocument.Parse(response);
                var root = doc.RootElement;

                return new Ticker24h
                {
                    Symbol = root.GetProperty("symbol").GetString() ?? "",
                    Volume = decimal.Parse(root.GetProperty("volume").GetString() ?? "0"),
                    QuoteVolume = decimal.Parse(root.GetProperty("quoteVolume").GetString() ?? "0"),
                    Count = root.GetProperty("count").GetInt64(),
                    WeightedAvgPrice = decimal.Parse(root.GetProperty("weightedAvgPrice").GetString() ?? "0"),
                    LastPrice = decimal.Parse(root.GetProperty("lastPrice").GetString() ?? "0"),
                    PriceChange = decimal.Parse(root.GetProperty("priceChange").GetString() ?? "0"),
                    PriceChangePercent = decimal.Parse(root.GetProperty("priceChangePercent").GetString() ?? "0")
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"获取24小时数据失败: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 获取K线数据
        /// </summary>
        /// <param name="symbol">交易对</param>
        /// <param name="interval">时间间隔 (1m, 5m, 15m, 1h, 4h, 1d)</param>
        /// <param name="limit">返回数量 (最大1500)</param>
        public async Task<List<KlineData>?> GetKlinesAsync(string symbol, string interval = "1m", int limit = 30)
        {
            try
            {
                string url = $"{baseUrl}/fapi/v1/klines?symbol={symbol.ToUpper()}&interval={interval}&limit={limit}";
                var response = await httpClient.GetStringAsync(url);
                
                using var doc = JsonDocument.Parse(response);
                var klines = new List<KlineData>();

                foreach (var item in doc.RootElement.EnumerateArray())
                {
                    var kline = new KlineData
                    {
                        OpenTime = DateTimeOffset.FromUnixTimeMilliseconds(item[0].GetInt64()).LocalDateTime,
                        CloseTime = DateTimeOffset.FromUnixTimeMilliseconds(item[6].GetInt64()).LocalDateTime,
                        Open = decimal.Parse(item[1].GetString() ?? "0"),
                        High = decimal.Parse(item[2].GetString() ?? "0"),
                        Low = decimal.Parse(item[3].GetString() ?? "0"),
                        Close = decimal.Parse(item[4].GetString() ?? "0"),
                        Volume = decimal.Parse(item[5].GetString() ?? "0"),
                        QuoteVolume = decimal.Parse(item[7].GetString() ?? "0"),
                        TradeCount = item[8].GetInt64(),
                        TakerBuyBaseVolume = decimal.Parse(item[9].GetString() ?? "0"),
                        TakerBuyQuoteVolume = decimal.Parse(item[10].GetString() ?? "0")
                    };
                    
                    klines.Add(kline);
                }

                return klines;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"获取K线数据失败: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 计算指定时间段的平均交易量
        /// </summary>
        public async Task<VolumeStatistics?> GetVolumeStatisticsAsync(string symbol, int minutes = 30)
        {
            try
            {
                // 根据时间长度选择合适的K线间隔
                string interval;
                int limit;

                if (minutes <= 30)
                {
                    interval = "1m";
                    limit = minutes;
                }
                else if (minutes <= 300) // 5小时
                {
                    interval = "5m";
                    limit = minutes / 5;
                }
                else if (minutes <= 1440) // 24小时
                {
                    interval = "15m";
                    limit = minutes / 15;
                }
                else
                {
                    interval = "1h";
                    limit = minutes / 60;
                }

                var klines = await GetKlinesAsync(symbol, interval, Math.Min(limit, 1500));
                
                if (klines == null || klines.Count == 0)
                    return null;

                // 计算统计数据
                var avgVolume = klines.Average(k => k.Volume);
                var avgQuoteVolume = klines.Average(k => k.QuoteVolume);
                var totalTrades = klines.Sum(k => k.TradeCount);
                var avgTradesPerInterval = klines.Average(k => k.TradeCount);

                // 计算每笔平均交易量
                var avgVolumePerTrade = totalTrades > 0 ? klines.Sum(k => k.Volume) / totalTrades : 0;

                return new VolumeStatistics
                {
                    Symbol = symbol.ToUpper(),
                    TimeWindowMinutes = minutes,
                    IntervalUsed = interval,
                    DataPointsCount = klines.Count,
                    AverageVolumePerInterval = avgVolume,
                    AverageQuoteVolumePerInterval = avgQuoteVolume,
                    TotalTrades = totalTrades,
                    AverageTradesPerInterval = avgTradesPerInterval,
                    AverageVolumePerTrade = avgVolumePerTrade,
                    StartTime = klines.First().OpenTime,
                    EndTime = klines.Last().CloseTime
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"计算交易量统计失败: {ex.Message}");
                return null;
            }
        }
    }

    /// <summary>
    /// 24小时行情数据
    /// </summary>
    public class Ticker24h
    {
        public string Symbol { get; set; } = "";
        public decimal Volume { get; set; }              // 24小时成交量
        public decimal QuoteVolume { get; set; }         // 24小时成交额
        public long Count { get; set; }                  // 24小时成交笔数
        public decimal WeightedAvgPrice { get; set; }    // 加权平均价
        public decimal LastPrice { get; set; }           // 最新价
        public decimal PriceChange { get; set; }         // 价格变化
        public decimal PriceChangePercent { get; set; }  // 价格变化百分比

        /// <summary>
        /// 24小时每笔平均交易量
        /// </summary>
        public decimal AverageVolumePerTrade => Count > 0 ? Volume / Count : 0;
    }

    /// <summary>
    /// K线数据
    /// </summary>
    public class KlineData
    {
        public DateTime OpenTime { get; set; }
        public DateTime CloseTime { get; set; }
        public decimal Open { get; set; }
        public decimal High { get; set; }
        public decimal Low { get; set; }
        public decimal Close { get; set; }
        public decimal Volume { get; set; }              // 成交量
        public decimal QuoteVolume { get; set; }         // 成交额
        public long TradeCount { get; set; }             // 成交笔数
        public decimal TakerBuyBaseVolume { get; set; }  // 主动买入成交量
        public decimal TakerBuyQuoteVolume { get; set; } // 主动买入成交额

        /// <summary>
        /// 每笔平均交易量
        /// </summary>
        public decimal AverageVolumePerTrade => TradeCount > 0 ? Volume / TradeCount : 0;
    }

    /// <summary>
    /// 交易量统计数据
    /// </summary>
    public class VolumeStatistics
    {
        public string Symbol { get; set; } = "";
        public int TimeWindowMinutes { get; set; }
        public string IntervalUsed { get; set; } = "";
        public int DataPointsCount { get; set; }
        public decimal AverageVolumePerInterval { get; set; }      // 每个时间间隔的平均交易量
        public decimal AverageQuoteVolumePerInterval { get; set; } // 每个时间间隔的平均交易额
        public long TotalTrades { get; set; }                      // 总交易笔数
        public double AverageTradesPerInterval { get; set; }       // 每个时间间隔的平均交易笔数
        public decimal AverageVolumePerTrade { get; set; }         // 每笔平均交易量
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
    }
}


