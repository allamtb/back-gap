import React, { useState } from "react";
import { Card, Timeline, Tag, Empty, Radio, Space } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, LinkOutlined, DisconnectOutlined, DatabaseOutlined, ShoppingCartOutlined, FileSearchOutlined, UserOutlined, RobotOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

/**
 * OperationLog - 操作日志
 * 
 * 功能：
 * 1. 展示后端操作日志（WebSocket连接、持仓、交易、订单等）
 * 2. 显示操作时间、类型、成功/失败状态
 * 3. 支持滚动查看历史记录
 * 4. 区分人工操作和系统操作
 */
export default function OperationLog({ logs = [], maxLogs = 100 }) {
  const [filterSource, setFilterSource] = useState('all'); // 'all', 'manual', 'system'
  
  // 根据过滤条件筛选日志
  const filteredLogs = filterSource === 'all' 
    ? logs 
    : logs.filter(log => log.source === filterSource);
  
  // 限制日志数量
  const displayLogs = filteredLogs.slice(0, maxLogs);

  // 获取操作类型配置
  const getTypeConfig = (type) => {
    switch (type) {
      case 'websocket_connect':
        return { color: 'blue', icon: <LinkOutlined />, label: 'WebSocket连接' };
      case 'websocket_disconnect':
        return { color: 'orange', icon: <DisconnectOutlined />, label: 'WebSocket断开' };
      case 'websocket_error':
        return { color: 'red', icon: <CloseCircleOutlined />, label: 'WebSocket错误' };
      case 'position_fetch':
        return { color: 'cyan', icon: <DatabaseOutlined />, label: '获取持仓' };
      case 'position_close':
        return { color: 'purple', icon: <DatabaseOutlined />, label: '平仓操作' };
      case 'order_fetch':
        return { color: 'geekblue', icon: <FileSearchOutlined />, label: '获取订单' };
      case 'order_create':
        return { color: 'green', icon: <ShoppingCartOutlined />, label: '创建订单' };
      default:
        return { color: 'default', icon: null, label: type };
    }
  };

  // 格式化时间
  const formatTime = (timestamp) => {
    return dayjs(timestamp).format('HH:mm:ss');
  };

  // 统计各类型日志数量
  const manualCount = logs.filter(log => log.source === 'manual').length;
  const systemCount = logs.filter(log => log.source === 'system').length;

  return (
    <Card 
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>📋 操作日志</span>
          <Radio.Group 
            size="small" 
            value={filterSource} 
            onChange={(e) => setFilterSource(e.target.value)}
            style={{ fontSize: '11px' }}
          >
            <Radio.Button value="all">全部 ({logs.length})</Radio.Button>
            <Radio.Button value="manual">
              <UserOutlined /> 交易 ({manualCount})
            </Radio.Button>
            <Radio.Button value="system">
              <RobotOutlined /> 系统 ({systemCount})
            </Radio.Button>
          </Radio.Group>
        </div>
      }
      size="small"
      bodyStyle={{ padding: '16px', maxHeight: '300px', overflowY: 'auto' }}
    >
      {displayLogs.length === 0 ? (
        <Empty 
          description={filterSource === 'all' ? "暂无操作日志" : `暂无${filterSource === 'manual' ? '交易' : '系统'}操作日志`}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Timeline
          items={displayLogs.map(log => {
            const typeConfig = getTypeConfig(log.type);
            const isSuccess = log.status === 'success';
            const isManual = log.source === 'manual';
            
            return {
              color: isSuccess ? 'green' : 'red',
              dot: isSuccess ? <CheckCircleOutlined /> : <CloseCircleOutlined />,
              children: (
                <div key={log.id}>
                  <div style={{ fontSize: '11px', color: '#999', marginBottom: 4 }}>
                    {formatTime(log.time)}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <Tag color={isManual ? 'blue' : 'default'} icon={isManual ? <UserOutlined /> : <RobotOutlined />}>
                      {isManual ? '交易操作' : '系统'}
                    </Tag>
                    <Tag color={typeConfig.color} icon={typeConfig.icon}>
                      {typeConfig.label}
                    </Tag>
                    <Tag color={isSuccess ? 'success' : 'error'}>
                      {isSuccess ? '成功' : '失败'}
                    </Tag>
                  </div>
                  <div style={{ marginTop: 4, fontSize: '13px', color: isSuccess ? '#52c41a' : '#ff4d4f' }}>
                    {log.message}
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

