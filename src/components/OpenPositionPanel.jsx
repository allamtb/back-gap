import React from "react";
import { Card, Space, Button, InputNumber, Checkbox, Statistic, Row, Col, Tag, Alert, message } from "antd";
import { RiseOutlined, ExclamationCircleOutlined } from "@ant-design/icons";
import { getTradingConfig } from "./TradingConfig";
import { getExchangeCredentials } from "../utils/configManager";
import { formatPrice, preciseSubtract } from "../utils/formatters";

/**
 * OpenPositionPanel - 一键开仓
 * 
 * 功能：
 * 1. 显示选中的2个交易所币对
 * 2. 自动判断高价（卖出）和低价（买入）
 * 3. 输入数量（两边一致）
 * 4. 计算预期价差收益
 * 5. 开仓按钮（市价/限价）
 * 6. 检查单笔最大金额和持仓最大USDT限制
 */
export default function OpenPositionPanel({ 
  selectedExchanges = [], 
  tickerData = {}, 
  positions = [],
  onPositionOpened,
  onLog = null
}) {
  const [amount, setAmount] = React.useState(1);
  const [isMarketOrder, setIsMarketOrder] = React.useState(true);
  const [buyPrice, setBuyPrice] = React.useState(null);
  const [sellPrice, setSellPrice] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  // 判断是否可以开仓（必须选中2个交易所）
  const canOpen = selectedExchanges.length === 2;

  // 使用 ref 存储上一次的币对标识
  const prevSymbolKeyRef = React.useRef(null);

  // 当币对改变时，清空数量输入和价格显示
  React.useEffect(() => {
    // 生成当前币对的唯一标识（排序后确保顺序一致）
    const currentSymbolKey = selectedExchanges.length === 2
      ? [selectedExchanges[0].symbol, selectedExchanges[1].symbol].sort().join('_')
      : null;
    
    // 如果币对改变，重置数量为默认值 1，并清空价格显示
    if (prevSymbolKeyRef.current !== null && prevSymbolKeyRef.current !== currentSymbolKey) {
      // 币对已改变，重置数量为默认值，清空价格
      setAmount(1);
      setBuyPrice(null);
      setSellPrice(null);
      console.log('🔄 [OpenPositionPanel] 币对已改变，已清空价格显示');
    }
    
    // 更新上一次的币对标识
    prevSymbolKeyRef.current = currentSymbolKey;
    
    // 如果没有选中2个交易所，重置数量为默认值 1，并清空价格
    if (selectedExchanges.length !== 2) {
      setAmount(1);
      setBuyPrice(null);
      setSellPrice(null);
    } else if (prevSymbolKeyRef.current === null) {
      // 首次选中2个交易所时，设置默认值为 1
      setAmount(1);
    }
  }, [selectedExchanges]);

  // 获取两个交易所的价格
  const getPrices = () => {
    if (!canOpen) return { high: null, low: null, highEx: null, lowEx: null };

    const prices = selectedExchanges.map(ex => {
      const key = `${ex.exchange}_${ex.symbol}_${ex.marketType}`;
      const ticker = tickerData[key] || {};
      return {
        exchange: ex,
        price: ticker.price ? parseFloat(ticker.price) : null
      };
    });

    // 如果价格数据不完整，返回 null（不显示价格）
    if (!prices[0].price || !prices[1].price) {
      return { high: null, low: null, highEx: null, lowEx: null };
    }

    // 比较价格，找出高价和低价
    if (prices[0].price > prices[1].price) {
      return {
        high: prices[0].price,
        low: prices[1].price,
        highEx: prices[0].exchange,
        lowEx: prices[1].exchange
      };
    } else {
      return {
        high: prices[1].price,
        low: prices[0].price,
        highEx: prices[1].exchange,
        lowEx: prices[0].exchange
      };
    }
  };

  const { high, low, highEx, lowEx } = getPrices();

  // 判断市场类型的辅助函数
  const isFutures = (exchange) => {
    const marketType = exchange?.marketType || exchange?.market_type || 'spot';
    return marketType === 'futures' || marketType === 'future';
  };

  // 获取交易配置
  const tradingConfig = getTradingConfig();
  const maxOrderAmount = tradingConfig.maxOrderAmount;
  const maxPosition = tradingConfig.maxPosition;

  // 计算价差和预期收益（使用精确计算避免浮点数精度问题）
  const priceDiffRaw = high && low ? preciseSubtract(high, low) : 0;
  const priceDiff = (priceDiffRaw !== '-' && typeof priceDiffRaw === 'number') ? priceDiffRaw : 0;
  const priceDiffPercent = high && low && priceDiff !== 0 ? ((priceDiff / low) * 100).toFixed(3) : '0.000';
  const expectedProfit = amount && priceDiff && priceDiff !== 0 ? (amount * priceDiff).toFixed(2) : '0.00';

  // 计算订单金额（使用较低价格，因为买入时用低价）
  const orderAmount = amount && low ? amount * low : 0;
  
  // 检查是否超过单笔最大金额
  const exceedsMaxOrderAmount = orderAmount > maxOrderAmount;

  // 计算当前持仓总USDT价值
  const calculateCurrentPositionValue = () => {
    if (!positions || positions.length === 0) return 0;
    return positions.reduce((total, pos) => {
      // 使用开仓均价 * 数量计算持仓价值
      const positionValue = (pos.openPrice || 0) * (pos.amount || 0);
      return total + positionValue;
    }, 0);
  };

  const currentPositionValue = calculateCurrentPositionValue();
  const newTotalPositionValue = currentPositionValue + orderAmount;
  
  // 检查是否超过持仓最大USDT
  const exceedsMaxPosition = newTotalPositionValue > maxPosition;

  // 创建单个订单
  const createSingleOrder = async (exchange, symbol, marketType, side, orderAmount, orderPrice) => {
    // 获取交易所凭证
    const credentials = getExchangeCredentials();
    const exchangeCred = credentials.find(c => c.exchange === exchange);

    if (!exchangeCred) {
      throw new Error(`未找到 ${exchange} 的凭证配置`);
    }

    // 构建订单参数
    const orderParams = {
      exchange: exchange,
      marketType: marketType,
      symbol: symbol,
      type: isMarketOrder ? 'market' : 'limit',
      side: side,
      amount: orderAmount,
      ...(isMarketOrder ? {} : { price: orderPrice }),
      credentials: exchangeCred,
    };

    console.log(`📤 提交${side === 'buy' ? '买入' : '卖出'}订单:`, orderParams);

    const response = await fetch('/api/create-order', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(orderParams),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message || '下单失败');
    }

    return result.data;
  };

  // 检查合约订单的最小名义价值（5 USDT）
  const checkMinNotional = (exchange, marketType, price, orderAmount) => {
    // 只检查合约订单
    if (marketType !== 'futures' && marketType !== 'future') {
      return { valid: true };
    }

    // 合约订单的最小名义价值通常是 5 USDT
    const minNotional = 5.0;
    const notional = orderAmount * price;

    if (notional < minNotional) {
      const minAmount = minNotional / price;
      return {
        valid: false,
        message: `合约订单名义价值不足！\n当前名义价值: ${notional.toFixed(4)} USDT\n最小要求: ${minNotional} USDT\n建议数量: 至少 ${minAmount.toFixed(4)}`
      };
    }

    return { valid: true };
  };

  // 开仓处理
  const handleOpenPosition = async () => {
    if (!amount || amount <= 0) {
      message.warning('请输入有效的数量');
      return;
    }

    if (!canOpen) {
      message.warning('请选择2个交易所');
      return;
    }

    // 检查价格数据
    if (!low || !high) {
      message.error('价格数据不完整，无法开仓');
      return;
    }

    // 检查合约订单的最小名义价值
    const buyMarketType = lowEx.marketType || lowEx.market_type || 'spot';
    const sellMarketType = highEx.marketType || highEx.market_type || 'spot';
    
    // 检查买入订单（低价交易所）
    const buyNotionalCheck = checkMinNotional(lowEx.exchange, buyMarketType, low, amount);
    if (!buyNotionalCheck.valid) {
      message.error(`买入订单${buyNotionalCheck.message}`);
      return;
    }

    // 检查卖出订单（高价交易所）
    const sellNotionalCheck = checkMinNotional(highEx.exchange, sellMarketType, high, amount);
    if (!sellNotionalCheck.valid) {
      message.error(`卖出订单${sellNotionalCheck.message}`);
      return;
    }

    // 检查单笔最大金额限制
    if (exceedsMaxOrderAmount) {
      message.error(`单笔最大金额限制：${maxOrderAmount} USDT，当前订单金额：${orderAmount.toFixed(2)} USDT`);
      return;
    }

    // 检查持仓最大USDT限制
    if (exceedsMaxPosition) {
      message.error(`持仓最大USDT限制：${maxPosition} USDT，当前持仓：${currentPositionValue.toFixed(2)} USDT，开仓后总持仓：${newTotalPositionValue.toFixed(2)} USDT`);
      return;
    }

    setLoading(true);
    
    let buyOrderResult = null;
    let sellOrderResult = null;
    let buyError = null;
    let sellError = null;

    try {
      // 同时提交买入和卖出订单
      // 使用市价单以确保快速成交
      const [buyResult, sellResult] = await Promise.allSettled([
        // 在低价交易所买入
        createSingleOrder(
          lowEx.exchange,
          lowEx.symbol,
          lowEx.marketType || lowEx.market_type || 'spot',
          'buy',
          amount,
          null // 市价单不需要价格
        ),
        // 在高价交易所卖出
        createSingleOrder(
          highEx.exchange,
          highEx.symbol,
          highEx.marketType || highEx.market_type || 'spot',
          'sell',
          amount,
          null // 市价单不需要价格
        )
      ]);

      // 处理买入订单结果
      if (buyResult.status === 'fulfilled') {
        buyOrderResult = buyResult.value;
        console.log('✅ 买入订单创建成功:', buyOrderResult);
        
        // 记录成功日志（人工操作）
        if (onLog) {
          const marketTypeText = (lowEx.marketType || lowEx.market_type || 'spot') === 'spot' ? '现货' : '合约';
          onLog({
            type: 'order_create',
            status: 'success',
            message: `下单成功: ${lowEx.exchange} ${lowEx.symbol} ${marketTypeText} 买入 ${amount} (市价)`,
            source: 'manual'
          });
        }
      } else {
        buyError = buyResult.reason;
        console.error('❌ 买入订单失败:', buyError);
        
        // 记录失败日志（人工操作）
        if (onLog) {
          const marketTypeText = (lowEx.marketType || lowEx.market_type || 'spot') === 'spot' ? '现货' : '合约';
          onLog({
            type: 'order_create',
            status: 'error',
            message: `下单失败: ${lowEx.exchange} ${lowEx.symbol} ${marketTypeText} 买入 ${amount} (市价) - ${buyError.message || '未知错误'}`,
            source: 'manual'
          });
        }
        
        // 检查是否是名义价值错误
        const errorMsg = buyError?.message || String(buyError);
        if (errorMsg.includes('notional') || errorMsg.includes('4164')) {
          const notional = amount * low;
          const minAmount = 5 / low;
          buyError = new Error(
            `买入订单名义价值不足！\n当前名义价值: ${notional.toFixed(4)} USDT\n最小要求: 5 USDT\n建议数量: 至少 ${minAmount.toFixed(4)}`
          );
        } else if (errorMsg.includes('position side') || errorMsg.includes('positionSide')) {
          // 持仓方向错误（通常发生在合约订单，但用户说是现货，可能是交易所配置问题）
          buyError = new Error(
            `买入订单失败：持仓方向设置错误\n这可能是交易所账户配置问题。\n如果是现货订单，请检查交易所账户设置。\n如果是合约订单，请检查账户的持仓模式（单向/双向）。`
          );
        }
      }

      // 处理卖出订单结果
      if (sellResult.status === 'fulfilled') {
        sellOrderResult = sellResult.value;
        console.log('✅ 卖出订单创建成功:', sellOrderResult);
        
        // 记录成功日志（人工操作）
        if (onLog) {
          const marketTypeText = (highEx.marketType || highEx.market_type || 'spot') === 'spot' ? '现货' : '合约';
          onLog({
            type: 'order_create',
            status: 'success',
            message: `下单成功: ${highEx.exchange} ${highEx.symbol} ${marketTypeText} 卖出 ${amount} (市价)`,
            source: 'manual'
          });
        }
      } else {
        sellError = sellResult.reason;
        console.error('❌ 卖出订单失败:', sellError);
        
        // 记录失败日志（人工操作）
        if (onLog) {
          const marketTypeText = (highEx.marketType || highEx.market_type || 'spot') === 'spot' ? '现货' : '合约';
          onLog({
            type: 'order_create',
            status: 'error',
            message: `下单失败: ${highEx.exchange} ${highEx.symbol} ${marketTypeText} 卖出 ${amount} (市价) - ${sellError.message || '未知错误'}`,
            source: 'manual'
          });
        }
        
        // 检查是否是名义价值错误
        const errorMsg = sellError?.message || String(sellError);
        if (errorMsg.includes('notional') || errorMsg.includes('4164')) {
          const notional = amount * high;
          const minAmount = 5 / high;
          sellError = new Error(
            `卖出订单名义价值不足！\n当前名义价值: ${notional.toFixed(4)} USDT\n最小要求: 5 USDT\n建议数量: 至少 ${minAmount.toFixed(4)}`
          );
        } else if (errorMsg.includes('position side') || errorMsg.includes('positionSide')) {
          // 持仓方向错误（通常发生在合约订单，但用户说是现货，可能是交易所配置问题）
          sellError = new Error(
            `卖出订单失败：持仓方向设置错误\n这可能是交易所账户配置问题。\n如果是现货订单，请检查交易所账户设置。\n如果是合约订单，请检查账户的持仓模式（单向/双向）。`
          );
        }
      }

      // 根据结果显示消息
      if (buyOrderResult && sellOrderResult) {
        // 两个订单都成功
        message.success(
          `✅ 开仓成功！买入订单ID: ${buyOrderResult.orderId || buyOrderResult.id}，卖出订单ID: ${sellOrderResult.orderId || sellOrderResult.id}`,
          5
        );
        
        // 开仓成功后，触发持仓刷新
        if (onPositionOpened) {
          setTimeout(() => {
            onPositionOpened();
          }, 1000);
        }
      } else if (buyOrderResult) {
        // 只有买入成功
        message.warning(
          `⚠️ 买入成功（订单ID: ${buyOrderResult.orderId || buyOrderResult.id}），但卖出失败: ${sellError?.message || '未知错误'}`,
          5
        );
      } else if (sellOrderResult) {
        // 只有卖出成功
        message.warning(
          `⚠️ 卖出成功（订单ID: ${sellOrderResult.orderId || sellOrderResult.id}），但买入失败: ${buyError?.message || '未知错误'}`,
          5
        );
      } else {
        // 两个订单都失败
        const errorMsg = `开仓失败！买入错误: ${buyError?.message || '未知错误'}，卖出错误: ${sellError?.message || '未知错误'}`;
        message.error(errorMsg, 5);
        throw new Error(errorMsg);
      }

    } catch (error) {
      console.error('开仓失败:', error);
      message.error(`开仓失败: ${error.message}`, 5);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card 
      title={<span><RiseOutlined /> 一键开仓</span>}
      size="small"
      bodyStyle={{ padding: '8px 12px' }}
    >
      {!canOpen ? (
        <Alert
          message="请在上方价格表格中勾选2个交易所"
          type="warning"
          showIcon
          style={{ marginBottom: 0 }}
        />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size={6}>
          {/* 第一行：交易所价格 + 价差信息（紧凑布局） */}
          <Row gutter={8} align="middle">
            <Col span={8}>
              <div style={{ fontSize: '10px', color: '#666', marginBottom: 2 }}>高价卖出</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
                <Tag color="red" style={{ margin: 0, fontSize: '10px', padding: '2px 6px' }}>
                  {highEx?.exchange.toUpperCase()}
                </Tag>
                <Tag 
                  color={isFutures(highEx) ? 'orange' : 'green'} 
                  style={{ margin: 0, fontSize: '9px', padding: '1px 4px' }}
                >
                  {isFutures(highEx) ? '合约' : '现货'}
                </Tag>
              </div>
              <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#ff4d4f', marginTop: 2 }}>
                {high ? formatPrice(high) : '-'}
              </div>
            </Col>
            <Col span={8}>
              <div style={{ fontSize: '10px', color: '#666', marginBottom: 2 }}>低价买入</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
                <Tag color="green" style={{ margin: 0, fontSize: '10px', padding: '2px 6px' }}>
                  {lowEx?.exchange.toUpperCase()}
                </Tag>
                <Tag 
                  color={isFutures(lowEx) ? 'orange' : 'green'} 
                  style={{ margin: 0, fontSize: '9px', padding: '1px 4px' }}
                >
                  {isFutures(lowEx) ? '合约' : '现货'}
                </Tag>
              </div>
              <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#52c41a', marginTop: 2 }}>
                {low ? formatPrice(low) : '-'}
              </div>
            </Col>
            <Col span={8}>
              {high && low && (
                <>
                  <div style={{ fontSize: '10px', color: '#666', marginBottom: 2 }}>价差</div>
                  <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#1890ff' }}>
                    {formatPrice(priceDiff)} ({priceDiffPercent}%)
                  </div>
                  {amount > 0 && (
                    <div style={{ fontSize: '11px', color: '#1890ff', marginTop: 2 }}>
                      预期收益: {expectedProfit} USDT
                    </div>
                  )}
                </>
              )}
            </Col>
          </Row>

          {/* 第二行：数量输入 + 市价切换（横向排列，数量在前，市价在后，居右对齐） */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: '#666', whiteSpace: 'nowrap' }}>数量:</span>
              <div style={{ width: '120px' }}>
                <InputNumber
                  value={amount}
                  onChange={setAmount}
                  placeholder="数量"
                  min={0}
                  step={0.001}
                  style={{ width: '100%' }}
                  size="small"
                  disabled={!canOpen}
                />
              </div>
              {amount && amount > 0 && low && (
                <span style={{ 
                  fontSize: '12px', 
                  color: '#1890ff', 
                  fontWeight: 500,
                  whiteSpace: 'nowrap'
                }}>
                  ≈ {orderAmount.toFixed(2)} USDT
                </span>
              )}
            </div>
            <div>
              <Checkbox 
                checked={isMarketOrder}
                disabled={true}
                style={{ fontSize: '12px' }}
              >
                市价
              </Checkbox>
            </div>
          </div>

          {/* 限制提示信息 */}
          {amount && amount > 0 && low && (
            <div style={{ marginTop: 4 }}>
              {/* 单笔最大金额限制提示 */}
              {exceedsMaxOrderAmount && (
                <Alert
                  message={
                    <span>
                      <ExclamationCircleOutlined style={{ marginRight: 4, color: '#ff4d4f' }} />
                      超过单笔最大金额限制
                    </span>
                  }
                  description={
                    <span>
                      单笔最大金额：<strong>{maxOrderAmount} USDT</strong>，
                      当前订单金额：<strong style={{ color: '#ff4d4f' }}>{orderAmount.toFixed(2)} USDT</strong>
                    </span>
                  }
                  type="error"
                  showIcon={false}
                  style={{ marginBottom: 4, fontSize: '11px' }}
                  size="small"
                />
              )}
              
              {/* 持仓最大USDT限制提示 */}
              {exceedsMaxPosition && (
                <Alert
                  message={
                    <span>
                      <ExclamationCircleOutlined style={{ marginRight: 4, color: '#ff4d4f' }} />
                      超过持仓最大USDT限制
                    </span>
                  }
                  description={
                    <span>
                      持仓最大USDT：<strong>{maxPosition} USDT</strong>，
                      当前持仓：<strong>{currentPositionValue.toFixed(2)} USDT</strong>，
                      开仓后总持仓：<strong style={{ color: '#ff4d4f' }}>{newTotalPositionValue.toFixed(2)} USDT</strong>
                    </span>
                  }
                  type="error"
                  showIcon={false}
                  style={{ marginBottom: 4, fontSize: '11px' }}
                  size="small"
                />
              )}

              {/* 正常提示：显示订单金额和当前持仓 */}
              {!exceedsMaxOrderAmount && !exceedsMaxPosition && (
                <div style={{ fontSize: '11px', color: '#666', marginTop: 4 }}>
                  <div>订单金额: <strong>{orderAmount.toFixed(2)} USDT</strong> / 单笔最大: {maxOrderAmount} USDT</div>
                  {currentPositionValue > 0 && (
                    <div>当前持仓: <strong>{currentPositionValue.toFixed(2)} USDT</strong> / 持仓最大: {maxPosition} USDT</div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 第三行：开仓按钮（放在数量输入框下方，居右对齐） */}
          <Row>
            <Col span={3} offset={21}>
              <Button
                type="primary"
                size="small"
                block
                loading={loading}
                onClick={handleOpenPosition}
                disabled={!canOpen || !amount || amount <= 0 || exceedsMaxOrderAmount || exceedsMaxPosition}
              >
                {loading ? '...' : '开仓'}
              </Button>
            </Col>
          </Row>
        </Space>
      )}
    </Card>
  );
}

