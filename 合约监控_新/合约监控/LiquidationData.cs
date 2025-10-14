using System;

namespace FuturesTradeViewer
{
    /// <summary>
    /// 爆仓数据模型
    /// </summary>
    public class LiquidationData
    {
        /// <summary>
        /// 爆仓时间
        /// </summary>
        public DateTime Time { get; set; }

        /// <summary>
        /// 交易对
        /// </summary>
        public string Symbol { get; set; } = string.Empty;

        /// <summary>
        /// 订单方向（BUY/SELL）
        /// SELL = 多头爆仓（卖出平多）
        /// BUY = 空头爆仓（买入平空）
        /// </summary>
        public string Side { get; set; } = string.Empty;

        /// <summary>
        /// 订单类型
        /// </summary>
        public string OrderType { get; set; } = string.Empty;

        /// <summary>
        /// 爆仓价格
        /// </summary>
        public decimal Price { get; set; }

        /// <summary>
        /// 订单原始数量
        /// </summary>
        private decimal originalQuantity;

        /// <summary>
        /// 累计成交数量（实际爆仓数量）
        /// </summary>
        public decimal LastFilledQty { get; set; }

        /// <summary>
        /// 订单状态
        /// </summary>
        public string OrderStatus { get; set; } = string.Empty;

        /// <summary>
        /// 爆仓数量（使用累计成交数量）
        /// </summary>
        public decimal Quantity
        {
            get => LastFilledQty > 0 ? LastFilledQty : originalQuantity;
            set => originalQuantity = value;
        }

        /// <summary>
        /// 爆仓方向描述
        /// </summary>
        public string Direction
        {
            get => Side == "SELL" ? "多头爆仓" : "空头爆仓";
        }

        /// <summary>
        /// 是否为多头爆仓（卖单强平）
        /// </summary>
        public bool IsLongLiquidation
        {
            get => Side == "SELL";
        }

        /// <summary>
        /// 是否为空头爆仓（买单强平）
        /// </summary>
        public bool IsShortLiquidation
        {
            get => Side == "BUY";
        }

        /// <summary>
        /// 爆仓金额（USDT）= 价格 × 数量
        /// </summary>
        public decimal LiquidationValue
        {
            get => Price * Quantity;
        }
    }
}

