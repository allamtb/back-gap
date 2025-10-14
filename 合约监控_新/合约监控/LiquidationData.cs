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
        /// 注意：这个数量是包含杠杆的合约数量，不是保证金数量
        /// 例如：用户用1000 USDT保证金开10倍杠杆，这里显示的是10000 USDT的合约数量
        /// 实际爆仓损失的是保证金（1000 USDT），而不是这个合约数量（10000 USDT）
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
        /// 注意：这是合约的名义价值（包含杠杆），不是实际损失的保证金
        /// 实际损失的保证金 = 爆仓金额 / 杠杆倍数
        /// 由于币安API不直接返回杠杆倍数，所以这里只显示合约名义价值
        /// </summary>
        public decimal LiquidationValue
        {
            get => Price * Quantity;
        }
    }
}

