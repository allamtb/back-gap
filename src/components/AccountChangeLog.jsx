import React from "react";
import { Card, Timeline, Tag, Empty } from "antd";
import { WalletOutlined, ArrowUpOutlined, ArrowDownOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

/**
 * AccountChangeLog - 账户实时变化日志
 * 
 * 功能：
 * 1. 展示资产变化记录（时间轴）
 * 2. WebSocket实时接收账户变化
 * 3. 显示变化类型（充值、提现、交易、手续费等）
 */
export default function AccountChangeLog({ changes = [] }) {
  // 模拟数据（待后端接口）
  const mockChanges = [
    {
      id: '1',
      time: dayjs().subtract(2, 'minute').format('HH:mm:ss'),
      exchange: 'binance',
      type: 'trade',
      currency: 'USDT',
      amount: -100.5,
      description: 'BTC/USDT 买入成交',
    },
    {
      id: '2',
      time: dayjs().subtract(5, 'minute').format('HH:mm:ss'),
      exchange: 'bybit',
      type: 'trade',
      currency: 'USDT',
      amount: +99.8,
      description: 'BTC/USDT 卖出成交',
    },
    {
      id: '3',
      time: dayjs().subtract(10, 'minute').format('HH:mm:ss'),
      exchange: 'binance',
      type: 'fee',
      currency: 'USDT',
      amount: -0.05,
      description: '交易手续费',
    },
  ];

  const displayChanges = changes.length > 0 ? changes : mockChanges;

  const getTypeColor = (type) => {
    switch (type) {
      case 'trade': return 'blue';
      case 'fee': return 'orange';
      case 'deposit': return 'green';
      case 'withdraw': return 'red';
      default: return 'default';
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'trade': return '交易';
      case 'fee': return '手续费';
      case 'deposit': return '充值';
      case 'withdraw': return '提现';
      default: return '其他';
    }
  };

  return (
    <Card 
      title={<span><WalletOutlined /> 账户实时变化</span>}
      size="small"
      bodyStyle={{ padding: '16px', maxHeight: '300px', overflowY: 'auto' }}
    >
      {displayChanges.length === 0 ? (
        <Empty 
          description="暂无账户变化记录" 
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Timeline
          items={displayChanges.map(change => ({
            color: change.amount > 0 ? 'green' : 'red',
            children: (
              <div key={change.id}>
                <div style={{ fontSize: '11px', color: '#999' }}>{change.time}</div>
                <div style={{ marginTop: 4 }}>
                  <Tag color="blue">{change.exchange.toUpperCase()}</Tag>
                  <Tag color={getTypeColor(change.type)}>{getTypeLabel(change.type)}</Tag>
                </div>
                <div style={{ marginTop: 4, fontSize: '13px' }}>
                  {change.description}
                </div>
                <div style={{ 
                  marginTop: 4, 
                  fontSize: '14px', 
                  fontWeight: 'bold',
                  color: change.amount > 0 ? '#52c41a' : '#ff4d4f'
                }}>
                  {change.amount > 0 ? (
                    <><ArrowUpOutlined /> +{change.amount.toFixed(2)}</>
                  ) : (
                    <><ArrowDownOutlined /> {change.amount.toFixed(2)}</>
                  )} {change.currency}
                </div>
              </div>
            )
          }))}
        />
      )}
    </Card>
  );
}


