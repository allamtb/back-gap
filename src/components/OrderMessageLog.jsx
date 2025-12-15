import React from "react";
import { Card, Timeline, Tag, Badge, Empty, Button, Space } from "antd";
import { BellOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

/**
 * OrderMessageLog - 订单实时变化消息
 * 
 * 功能：
 * 1. 订单创建通知
 * 2. 订单成交通知
 * 3. 订单取消通知
 * 4. WebSocket实时推送
 * 5. 手动刷新按钮
 * 6. 刷新间隔显示
 */
export default function OrderMessageLog({ 
  messages = [], 
  onManualRefresh,
  refreshCountdown = 0,
  monitoringInterval = 60 // 单位：秒
}) {
  // 直接使用传入的消息，不再使用假数据
  const displayMessages = messages;

  // 格式化刷新间隔显示（countdown 是毫秒，interval 是秒）
  const formatRefreshCountdown = (countdown, interval) => {
    if (!countdown && countdown !== 0) return '';
    // countdown 是毫秒，转换为秒
    const countdownSeconds = Math.floor(countdown / 1000);
    const remaining = Math.max(0, interval - countdownSeconds);
    const minutes = Math.floor(remaining / 60);
    const secs = remaining % 60;
    
    if (minutes > 0) {
      return `${minutes}分${secs}秒`;
    }
    return `${secs}秒`;
  };

  const getTypeConfig = (type) => {
    switch (type) {
      case 'created':
        return { color: 'blue', icon: <SyncOutlined />, label: '已创建' };
      case 'filled':
        return { color: 'green', icon: <CheckCircleOutlined />, label: '已成交' };
      case 'cancelled':
        return { color: 'red', icon: <CloseCircleOutlined />, label: '已取消' };
      case 'partial_filled':
        return { color: 'orange', icon: <SyncOutlined />, label: '部分成交' };
      default:
        return { color: 'default', icon: <BellOutlined />, label: '其他' };
    }
  };

  // 判断市场类型的辅助函数
  const isFutures = (marketType) => {
    if (!marketType) return false;
    const mt = String(marketType).toLowerCase().trim();
    // 后端返回的值是 'spot' 或 'futures'
    return mt === 'futures' || mt === 'future';
  };

  const countdownText = formatRefreshCountdown(refreshCountdown, monitoringInterval);

  return (
    <Card 
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            <BellOutlined /> 订单实时变化消息 
            {displayMessages.length > 0 && (
              <Badge 
                count={displayMessages.length} 
                style={{ marginLeft: 8 }} 
              />
            )}
          </span>
          <Space size="small">
            {countdownText && (
              <span style={{ fontSize: '11px', color: '#999' }}>
                下次刷新: {countdownText}
              </span>
            )}
            {onManualRefresh && (
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined />}
                onClick={onManualRefresh}
                title="手动刷新订单"
              >
                刷新
              </Button>
            )}
          </Space>
        </div>
      }
      size="small"
      bodyStyle={{ padding: '16px', maxHeight: '300px', overflowY: 'auto' }}
    >
      {displayMessages.length === 0 ? (
        <Empty 
          description="暂无订单消息" 
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Timeline
          items={displayMessages.map(msg => {
            const typeConfig = getTypeConfig(msg.type);
            return {
              color: typeConfig.color,
              dot: typeConfig.icon,
              children: (
                <div key={msg.id}>
                  <div style={{ 
                    fontSize: '13px', 
                    fontWeight: 600, 
                    color: '#1890ff',
                    marginBottom: 4
                  }}>
                    {msg.time}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <Tag color="blue">{msg.exchange.toUpperCase()}</Tag>
                    <Tag 
                      color={isFutures(msg.marketType) ? 'orange' : 'green'} 
                      style={{ fontSize: '11px', padding: '1px 6px' }}
                    >
                      {isFutures(msg.marketType) ? '合约' : '现货'}
                    </Tag>
                    <Tag color={typeConfig.color}>{typeConfig.label}</Tag>
                    <Tag color={msg.side === 'buy' ? 'green' : 'red'}>
                      {msg.side === 'buy' ? '买入' : '卖出'}
                    </Tag>
                  </div>
                  <div style={{ marginTop: 4, fontSize: '13px', fontWeight: 500 }}>
                    {msg.symbol}  数量: {msg.amount} @ 价格: {msg.price}
                  </div>
                  <div style={{ marginTop: 4, fontSize: '11px', color: '#bfbfbf' }}>
                    订单ID: {msg.orderId}
                  </div>
                </div>
              )
            };
          })}
        />
      )}
    </Card>
  );
}


