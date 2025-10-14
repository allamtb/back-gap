using System;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 交易数据模型
    /// </summary>
    public class TradeData
    {
        /// <summary>
        /// 交易时间
        /// </summary>
        public DateTime Time { get; set; }

        /// <summary>
        /// 交易价格
        /// </summary>
        public decimal Price { get; set; }

        /// <summary>
        /// 交易数量
        /// </summary>
        public decimal Quantity { get; set; }

        /// <summary>
        /// 是否是买方挂单成交 (Maker)
        /// true = 买方是Maker（挂单成交，被动）, false = 卖方是Maker（市价成交，主动）
        /// 在 Binance 的 trade stream 中，"m" 字段表示买方是否是挂单方（Maker）
        /// </summary>
        public bool IsBuyerMaker { get; set; }

        /// <summary>
        /// 交易方向描述
        /// IsBuyerMaker=true: 买方挂单，卖方主动吃单 → 卖出↓
        /// IsBuyerMaker=false: 卖方挂单，买方主动吃单 → 买入↑
        /// </summary>
        public string Direction => IsBuyerMaker ? "卖出↓" : "买入↑";

        /// <summary>
        /// 订单类型文本描述（主动吃单/被动挂单）
        /// IsBuyerMaker=true: 挂单成交（买方是Maker，即被动方）
        /// IsBuyerMaker=false: 市价成交（买方是Taker，即主动方）
        /// </summary>
        public string OrderTypeText => IsBuyerMaker ? "挂单成交" : "市价成交";
    }
}


