import React from "react";
import { Card, Row, Col, Statistic, Tag, Space } from "antd";
import { RiseOutlined, FallOutlined, DollarOutlined } from "@ant-design/icons";

/**
 * ProfitSummary - 实时盈利状态汇总
 * 
 * 功能：
 * 1. 总持仓价值
 * 2. 总浮动盈亏
 * 3. 盈亏率
 * 4. 持仓公式展示
 * 5. 盈利公式展示
 */
export default function ProfitSummary({ positions = [] }) {
  // 计算总持仓价值
  const totalPositionValue = positions.reduce((sum, pos) => {
    return sum + (pos.amount * pos.currentPrice);
  }, 0);

  // 计算总浮动盈亏
  const totalUnrealizedPnl = positions.reduce((sum, pos) => {
    return sum + (pos.unrealizedPnl || 0);
  }, 0);

  // 计算盈亏率
  const totalOpenValue = positions.reduce((sum, pos) => {
    return sum + (pos.amount * pos.openPrice);
  }, 0);
  const pnlPercent = totalOpenValue > 0 ? (totalUnrealizedPnl / totalOpenValue) * 100 : 0;

  // 计算持仓公式（做多 - 做空）
  const longPositions = positions.filter(p => p.side === 'long');
  const shortPositions = positions.filter(p => p.side === 'short');
  
  const totalLong = longPositions.reduce((sum, pos) => sum + pos.amount, 0);
  const totalShort = shortPositions.reduce((sum, pos) => sum + pos.amount, 0);
  const netPosition = totalLong - totalShort;

  // 模拟数据（当没有真实数据时）
  const displayData = positions.length > 0 ? {
    totalPositionValue,
    totalUnrealizedPnl,
    pnlPercent,
    totalLong,
    totalShort,
    netPosition
  } : {
    totalPositionValue: 6600,
    totalUnrealizedPnl: 25,
    pnlPercent: 0.38,
    totalLong: 1000,
    totalShort: 1000,
    netPosition: 0
  };

  return (
    <Card 
      title="💰 实时盈利状态"
      size="small"
      bodyStyle={{ padding: '16px' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={16}>
        {/* 核心指标 */}
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="总持仓价值"
              value={displayData.totalPositionValue}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USDT"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="浮动盈亏"
              value={displayData.totalUnrealizedPnl}
              precision={2}
              prefix={displayData.totalUnrealizedPnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
              suffix="USDT"
              valueStyle={{ 
                color: displayData.totalUnrealizedPnl >= 0 ? '#52c41a' : '#ff4d4f',
                fontWeight: 'bold'
              }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="盈亏率"
              value={displayData.pnlPercent}
              precision={2}
              suffix="%"
              valueStyle={{ 
                color: displayData.pnlPercent >= 0 ? '#52c41a' : '#ff4d4f',
                fontWeight: 'bold'
              }}
            />
          </Col>
        </Row>

        {/* 持仓公式展示 */}
        <Card size="small" style={{ backgroundColor: '#f0f5ff', borderColor: '#adc6ff' }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: 8 }}>持仓计算公式：</div>
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#1890ff' }}>
            做多 +{displayData.totalLong.toFixed(2)} - 做空 {displayData.totalShort.toFixed(2)} = {displayData.netPosition.toFixed(2)}
          </div>
          <div style={{ fontSize: '11px', color: '#999', marginTop: 4 }}>
            {displayData.netPosition === 0 ? (
              <Tag color="green">✅ 完全对冲（无方向性风险）</Tag>
            ) : displayData.netPosition > 0 ? (
              <Tag color="orange">⚠️ 净多仓 {displayData.netPosition.toFixed(2)}</Tag>
            ) : (
              <Tag color="orange">⚠️ 净空仓 {Math.abs(displayData.netPosition).toFixed(2)}</Tag>
            )}
          </div>
        </Card>

        {/* 盈利公式展示（示例） */}
        <Card size="small" style={{ backgroundColor: '#f6ffed', borderColor: '#b7eb8f' }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: 8 }}>盈利计算公式示例：</div>
          <div style={{ fontSize: '14px', color: '#52c41a' }}>
            做多盈亏 <span style={{ fontWeight: 'bold' }}>-10</span> + 
            做空盈亏 <span style={{ fontWeight: 'bold' }}>+20</span> - 
            手续费 <span style={{ fontWeight: 'bold' }}>4</span> = 
            <span style={{ fontWeight: 'bold', fontSize: '16px' }}> +6 USDT</span>
          </div>
          <div style={{ fontSize: '11px', color: '#999', marginTop: 4 }}>
            注：当前手续费计算功能待配置页面完成后启用
          </div>
        </Card>

        {/* 持仓明细汇总 */}
        <div style={{ fontSize: '11px', color: '#999' }}>
          <div>持仓交易所数量：{new Set(positions.map(p => p.exchange)).size}</div>
          <div>持仓品种数量：{new Set(positions.map(p => p.symbol)).size}</div>
          <div>总持仓笔数：{positions.length}</div>
        </div>
      </Space>
    </Card>
  );
}


