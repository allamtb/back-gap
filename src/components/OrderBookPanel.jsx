import React, { useState, useEffect } from "react";
import { Card, Table, Space, Tag, Empty, Row, Col, Divider } from "antd";
import { ArrowUpOutlined, ArrowDownOutlined, SwapOutlined } from "@ant-design/icons";
import { formatPrice, formatAmount, preciseSubtract, preciseSum } from "../utils/formatters";

/**
 * OrderBookPanel - 订单薄5档明细横向对比展示
 * 
 * @param {Array} exchanges - 交易所配置数组（最多显示前2个）
 * @param {Object} depthData - 订单薄数据对象 {exchange_symbol_marketType: {bids: [[price, amount], ...], asks: [...]}}
 * @param {Function} onPriceClick - 双击价格时的回调函数 (exchange, symbol, marketType, price, side)
 */
export default function OrderBookPanel({ exchanges = [], depthData = {}, onPriceClick }) {
  // 取前两个交易所进行对比
  const displayExchanges = exchanges.slice(0, 2);

  // 渲染单个交易所的订单薄
  const renderOrderBook = (exchangeConfig) => {
    const key = `${exchangeConfig.exchange}_${exchangeConfig.symbol}_${exchangeConfig.market_type || 'spot'}`;
    const depth = depthData[key] || { bids: [], asks: [] };

    // 买盘表格列（紧凑版）
    const bidColumns = [
      {
        title: '价格',
        dataIndex: 'price',
        key: 'price',
        width: '50%',
        onCell: (record) => ({
          onDoubleClick: () => {
            if (onPriceClick) {
              onPriceClick(
                exchangeConfig.exchange, 
                exchangeConfig.symbol, 
                exchangeConfig.market_type || 'spot', 
                parseFloat(record.price), 
                'buy'
              );
            }
          },
          onMouseEnter: (e) => {
            if (onPriceClick) {
              e.currentTarget.style.backgroundColor = '#f6ffed';
              e.currentTarget.style.cursor = 'pointer';
            }
          },
          onMouseLeave: (e) => {
            if (onPriceClick) {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.cursor = 'default';
            }
          },
          title: onPriceClick ? '双击填入限价单' : '',
          style: {
            transition: 'background-color 0.2s',
          }
        }),
        render: (price) => (
          <span 
            style={{ 
              color: '#52c41a', 
              fontWeight: 'bold', 
              fontSize: '11px',
            }}
          >
            {formatPrice(price)}
          </span>
        ),
      },
      {
        title: '数量',
        dataIndex: 'amount',
        key: 'amount',
        width: '50%',
        render: (amount) => (
          <span style={{ fontSize: '10px', color: '#666' }}>
            {formatAmount(amount)}
          </span>
        ),
      },
    ];

    // 卖盘表格列（紧凑版）
    const askColumns = [
      {
        title: '价格',
        dataIndex: 'price',
        key: 'price',
        width: '50%',
        onCell: (record) => ({
          onDoubleClick: () => {
            if (onPriceClick) {
              onPriceClick(
                exchangeConfig.exchange, 
                exchangeConfig.symbol, 
                exchangeConfig.market_type || 'spot', 
                parseFloat(record.price), 
                'sell'
              );
            }
          },
          onMouseEnter: (e) => {
            if (onPriceClick) {
              e.currentTarget.style.backgroundColor = '#fff1f0';
              e.currentTarget.style.cursor = 'pointer';
            }
          },
          onMouseLeave: (e) => {
            if (onPriceClick) {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.cursor = 'default';
            }
          },
          title: onPriceClick ? '双击填入限价单' : '',
          style: {
            transition: 'background-color 0.2s',
          }
        }),
        render: (price) => (
          <span 
            style={{ 
              color: '#ff4d4f', 
              fontWeight: 'bold', 
              fontSize: '11px',
            }}
          >
            {formatPrice(price)}
          </span>
        ),
      },
      {
        title: '数量',
        dataIndex: 'amount',
        key: 'amount',
        width: '50%',
        render: (amount) => (
          <span style={{ fontSize: '10px', color: '#666' }}>
            {formatAmount(amount)}
          </span>
        ),
      },
    ];

    // 转换订单薄数据为表格数据（取前5档）
    const bidsData = (depth.bids || [])
      .slice(0, 5)
      .map((item, index) => ({
        key: `bid-${index}`,
        price: item[0],
        amount: item[1],
      }));

    const asksData = (depth.asks || [])
      .slice(0, 5)
      .reverse() // 卖盘倒序显示（价格从低到高）
      .map((item, index) => ({
        key: `ask-${index}`,
        price: item[0],
        amount: item[1],
      }));

    // 计算买卖盘总量（使用精确求和避免浮点数精度问题）
    const totalBids = preciseSum(bidsData.map(item => item.amount));
    const totalAsks = preciseSum(asksData.map(item => item.amount));

    // 计算价差（使用精确计算避免浮点数精度问题）
    const spread = bidsData.length > 0 && asksData.length > 0
      ? preciseSubtract(asksData[asksData.length - 1].price, bidsData[0].price)
      : '- - -';

    return (
      <div style={{ height: '100%' }}>
        {/* 交易所标题 */}
        <div style={{ 
          padding: '6px 8px', 
          backgroundColor: exchangeConfig.color || '#1890ff',
          color: 'white',
          borderRadius: '4px 4px 0 0',
          fontWeight: 'bold',
          fontSize: '12px',
          textAlign: 'center'
        }}>
          {exchangeConfig.exchange} {exchangeConfig.symbol}
          <Tag 
            style={{ 
              marginLeft: 6, 
              fontSize: '10px',
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              border: 'none'
            }}
          >
            {exchangeConfig.market_type === 'spot' ? '现货' : '合约'}
          </Tag>
        </div>

        {/* 订单薄数据 */}
        {bidsData.length === 0 && asksData.length === 0 ? (
          <Empty
            description="暂无数据"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ padding: '20px 0' }}
          />
        ) : (
          <div style={{ backgroundColor: '#fafafa', padding: '8px' }}>
            {/* 卖盘（上方，红色） */}
            <div style={{ marginBottom: 6 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '3px 6px',
                  backgroundColor: '#fff1f0',
                  borderRadius: 3,
                  marginBottom: 3,
                }}
              >
                <Space size={4}>
                  <ArrowUpOutlined style={{ color: '#ff4d4f', fontSize: '11px' }} />
                  <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#ff4d4f' }}>
                    卖盘
                  </span>
                </Space>
                <span style={{ fontSize: '9px', color: '#999' }}>
                  总量: {formatAmount(totalAsks)}
                </span>
              </div>
              <Table
                size="small"
                columns={askColumns}
                dataSource={asksData}
                pagination={false}
                showHeader={false}
                bordered
                style={{ marginBottom: 3 }}
              />
            </div>

            {/* 价差分隔 */}
            <div
              style={{
                textAlign: 'center',
                padding: '6px 0',
                backgroundColor: '#fff',
                borderRadius: 3,
                marginBottom: 6,
                fontSize: '10px',
                color: '#999',
                fontWeight: 'bold',
              }}
            >
              价差: <span style={{ color: '#1890ff' }}>{spread}</span>
            </div>

            {/* 买盘（下方，绿色） */}
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '3px 6px',
                  backgroundColor: '#f6ffed',
                  borderRadius: 3,
                  marginBottom: 3,
                }}
              >
                <Space size={4}>
                  <ArrowDownOutlined style={{ color: '#52c41a', fontSize: '11px' }} />
                  <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#52c41a' }}>
                    买盘
                  </span>
                </Space>
                <span style={{ fontSize: '9px', color: '#999' }}>
                  总量: {formatAmount(totalBids)}
                </span>
              </div>
              <Table
                size="small"
                columns={bidColumns}
                dataSource={bidsData}
                pagination={false}
                showHeader={false}
                bordered
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  // 计算套利机会（如果有两个交易所）
  const calculateArbitrage = () => {
    if (displayExchanges.length < 2) return null;

    const key1 = `${displayExchanges[0].exchange}_${displayExchanges[0].symbol}_${displayExchanges[0].market_type || 'spot'}`;
    const key2 = `${displayExchanges[1].exchange}_${displayExchanges[1].symbol}_${displayExchanges[1].market_type || 'spot'}`;
    
    const depth1 = depthData[key1];
    const depth2 = depthData[key2];

    if (!depth1 || !depth2 || !depth1.bids?.length || !depth2.asks?.length) return null;

    // 交易所1买入，交易所2卖出的套利空间（使用精确计算）
    const arb1to2 = preciseSubtract(depth1.bids[0][0], depth2.asks[0][0]);
    // 交易所2买入，交易所1卖出的套利空间（使用精确计算）
    const arb2to1 = preciseSubtract(depth2.bids[0][0], depth1.asks[0][0]);

    const maxArb = Math.max(arb1to2, arb2to1);
    const direction = arb1to2 > arb2to1 ? `${displayExchanges[1].exchange}→${displayExchanges[0].exchange}` : `${displayExchanges[0].exchange}→${displayExchanges[1].exchange}`;

    return { maxArb, direction };
  };

  const arbitrage = calculateArbitrage();

  return (
    <Card
      size="small"
      title={
        <Space size={8}>
          <span>📊 订单薄对比</span>
          <Tag color="blue" style={{ fontSize: '10px', margin: 0 }}>
            5档明细
          </Tag>
        </Space>
      }
      extra={
        arbitrage && Math.abs(arbitrage.maxArb) > 0.01 ? (
          <Tag 
            color={arbitrage.maxArb > 0 ? 'green' : 'red'} 
            style={{ fontSize: '10px' }}
          >
            <SwapOutlined /> 套利: {arbitrage.maxArb} ({arbitrage.direction})
          </Tag>
        ) : null
      }
      bodyStyle={{ padding: '8px' }}
      style={{ height: '100%' }}
    >
      {displayExchanges.length === 0 ? (
        <Empty
          description="请先配置交易所"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          style={{ marginTop: 40 }}
        />
      ) : (
        <Row gutter={8}>
          {displayExchanges.map((exchange, index) => (
            <Col 
              key={`${exchange.exchange}_${exchange.symbol}`}
              span={displayExchanges.length === 1 ? 24 : 12}
            >
              {renderOrderBook(exchange)}
            </Col>
          ))}
        </Row>
      )}
    </Card>
  );
}


