import React, { useState, useEffect } from "react";
import { Card, InputNumber, Space, Row, Col, Typography, Button, message } from "antd";
import { DollarOutlined, WalletOutlined, ClockCircleOutlined, CheckOutlined } from "@ant-design/icons";

const { Text } = Typography;

/**
 * TradingConfig - 交易配置面板
 * 支持配置单笔最大金额和持仓最大USDT数
 */
export default function TradingConfig() {
  // 配置项（从localStorage加载）
  const [maxOrderAmount, setMaxOrderAmount] = useState(() => {
    const saved = localStorage.getItem('trading_config_max_order_amount');
    return saved ? parseFloat(saved) : 1000;
  });
  
  const [maxPosition, setMaxPosition] = useState(() => {
    const saved = localStorage.getItem('trading_config_max_position');
    return saved ? parseFloat(saved) : 10000;
  });

  // 订单监控间隔：从 localStorage 加载已保存的值
  const [savedOrderMonitoringInterval, setSavedOrderMonitoringInterval] = useState(() => {
    const saved = localStorage.getItem('trading_config_order_monitoring_interval');
    const savedValue = saved ? parseInt(saved, 10) : null;
    // 如果保存的值小于30（可能是旧的配置，单位是毫秒），自动重置为默认值60秒
    if (savedValue && savedValue < 30) {
      localStorage.setItem('trading_config_order_monitoring_interval', '60');
      return 60; // 默认60秒
    }
    // 如果保存的值大于1000（可能是旧的毫秒值），转换为秒
    if (savedValue && savedValue > 1000) {
      const seconds = Math.floor(savedValue / 1000);
      localStorage.setItem('trading_config_order_monitoring_interval', seconds.toString());
      return seconds;
    }
    return savedValue || 60; // 默认60秒
  });

  // 订单监控间隔：临时输入值（未应用）
  const [orderMonitoringInterval, setOrderMonitoringInterval] = useState(savedOrderMonitoringInterval);

  // 持仓监控间隔：从 localStorage 加载已保存的值
  const [savedPositionMonitoringInterval, setSavedPositionMonitoringInterval] = useState(() => {
    const saved = localStorage.getItem('trading_config_position_monitoring_interval');
    const savedValue = saved ? parseInt(saved, 10) : null;
    // 如果保存的值小于30（可能是旧的配置，单位是毫秒），自动重置为默认值300秒（5分钟）
    if (savedValue && savedValue < 30) {
      localStorage.setItem('trading_config_position_monitoring_interval', '300');
      return 300; // 默认300秒（5分钟）
    }
    // 如果保存的值大于1000（可能是旧的毫秒值），转换为秒
    if (savedValue && savedValue > 1000) {
      const seconds = Math.floor(savedValue / 1000);
      localStorage.setItem('trading_config_position_monitoring_interval', seconds.toString());
      return seconds;
    }
    return savedValue || 300; // 默认300秒（5分钟）
  });

  // 持仓监控间隔：临时输入值（未应用）
  const [positionMonitoringInterval, setPositionMonitoringInterval] = useState(savedPositionMonitoringInterval);

  // 保存配置到localStorage
  useEffect(() => {
    localStorage.setItem('trading_config_max_order_amount', maxOrderAmount.toString());
  }, [maxOrderAmount]);

  useEffect(() => {
    localStorage.setItem('trading_config_max_position', maxPosition.toString());
  }, [maxPosition]);

  // 应用订单监控间隔配置
  const handleApplyOrderMonitoringInterval = () => {
    // 验证最小值
    if (orderMonitoringInterval < 1) {
      message.error('订单监控间隔不能小于 1 秒');
      setOrderMonitoringInterval(savedOrderMonitoringInterval);
      return;
    }
    
    // 如果值大于600，给出警告但不阻止
    if (orderMonitoringInterval > 600) {
      message.warning(`订单监控间隔设置为 ${orderMonitoringInterval} 秒（建议不超过 600 秒）`);
    }
    
    // 保存到 localStorage
    try {
      localStorage.setItem('trading_config_order_monitoring_interval', orderMonitoringInterval.toString());
      console.log('✅ [TradingConfig] 订单监控间隔已保存到 localStorage:', orderMonitoringInterval);
    } catch (error) {
      console.error('❌ [TradingConfig] 保存订单监控间隔失败:', error);
      message.error('保存配置失败，请重试');
      return;
    }
    
    setSavedOrderMonitoringInterval(orderMonitoringInterval);
    message.success('订单监控间隔配置已应用');
    // 触发自定义事件，通知 TradingOrderPage 配置已更新
    window.dispatchEvent(new CustomEvent('tradingConfigUpdated', {
      detail: { type: 'orderMonitoringInterval', value: orderMonitoringInterval }
    }));
  };

  // 检查订单监控间隔是否有未应用的更改
  const hasOrderMonitoringIntervalChanges = orderMonitoringInterval !== savedOrderMonitoringInterval;

  // 应用持仓监控间隔配置
  const handleApplyPositionMonitoringInterval = () => {
    // 验证最小值
    if (positionMonitoringInterval < 1) {
      message.error('持仓监控间隔不能小于 1 秒');
      setPositionMonitoringInterval(savedPositionMonitoringInterval);
      return;
    }
    
    // 如果值大于3600，给出警告但不阻止
    if (positionMonitoringInterval > 3600) {
      message.warning(`持仓监控间隔设置为 ${positionMonitoringInterval} 秒（建议不超过 3600 秒）`);
    }
    
    // 保存到 localStorage
    try {
      localStorage.setItem('trading_config_position_monitoring_interval', positionMonitoringInterval.toString());
      console.log('✅ [TradingConfig] 持仓监控间隔已保存到 localStorage:', positionMonitoringInterval);
    } catch (error) {
      console.error('❌ [TradingConfig] 保存持仓监控间隔失败:', error);
      message.error('保存配置失败，请重试');
      return;
    }
    
    setSavedPositionMonitoringInterval(positionMonitoringInterval);
    message.success('持仓监控间隔配置已应用');
    // 触发自定义事件，通知 TradingOrderPage 配置已更新
    window.dispatchEvent(new CustomEvent('tradingConfigUpdated', {
      detail: { type: 'positionMonitoringInterval', value: positionMonitoringInterval }
    }));
  };

  // 检查持仓监控间隔是否有未应用的更改
  const hasPositionMonitoringIntervalChanges = positionMonitoringInterval !== savedPositionMonitoringInterval;

  return (
    <Card 
      size="small" 
      title="⚙️ 交易配置"
      bodyStyle={{ padding: '12px' }}
      style={{ marginTop: 8 }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        {/* 单笔最大金额 */}
        <Row gutter={8} align="middle">
          <Col span={24}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                <DollarOutlined style={{ marginRight: 4 }} />
                单笔最大金额
              </Text>
              <InputNumber
                size="small"
                value={maxOrderAmount}
                onChange={(value) => setMaxOrderAmount(value || 0)}
                style={{ width: '100%' }}
                min={0}
                max={1000000}
                step={100}
                formatter={(value) => `${value} USDT`}
                parser={(value) => value.replace(' USDT', '')}
                placeholder="输入金额"
              />
            </Space>
          </Col>
        </Row>

        {/* 持仓最大USDT数 */}
        <Row gutter={8} align="middle">
          <Col span={24}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                <WalletOutlined style={{ marginRight: 4 }} />
                持仓最大USDT数（暂未实现）
              </Text>
              <InputNumber
                size="small"
                value={maxPosition}
                onChange={(value) => setMaxPosition(value || 0)}
                style={{ width: '100%' }}
                min={0}
                max={10000000}
                step={1000}
                formatter={(value) => `${value} USDT`}
                parser={(value) => value.replace(' USDT', '')}
                placeholder="输入金额"
              />
            </Space>
          </Col>
        </Row>

        {/* 订单监控间隔 */}
        <Row gutter={8} align="middle">
          <Col span={18}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                <ClockCircleOutlined style={{ marginRight: 4 }} />
                订单监控间隔
              </Text>
            </Space>
          </Col>
          <Col span={6}>
            {/* 空白占位，保持布局一致 */}
          </Col>
        </Row>
        <Row gutter={8} align="middle" style={{ marginTop: 4 }}>
          <Col span={18}>
            <InputNumber
              size="small"
              value={orderMonitoringInterval}
              onChange={(value) => {
                // 允许输入任何数值（包括超出范围的值），在应用时再验证
                if (value !== null && value !== undefined) {
                  setOrderMonitoringInterval(value);
                } else if (value === null) {
                  // 允许清空输入
                  setOrderMonitoringInterval(0);
                }
              }}
              style={{ width: '100%' }}
              step={1}
              addonAfter="秒"
              placeholder="输入秒数（1-600）"
              precision={0}
              controls={true}
            />
          </Col>
          <Col span={6}>
            <Button
              type="primary"
              size="small"
              icon={<CheckOutlined />}
              onClick={handleApplyOrderMonitoringInterval}
              disabled={!hasOrderMonitoringIntervalChanges}
              style={{ width: '100%' }}
              title="应用配置（值必须在1-600秒之间）"
            >
              应用
            </Button>
          </Col>
        </Row>

        {/* 持仓监控间隔 */}
        <Row gutter={8} align="middle">
          <Col span={18}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                <ClockCircleOutlined style={{ marginRight: 4 }} />
                持仓监控间隔
              </Text>
            </Space>
          </Col>
          <Col span={6}>
            {/* 空白占位，保持布局一致 */}
          </Col>
        </Row>
        <Row gutter={8} align="middle" style={{ marginTop: 4 }}>
          <Col span={18}>
            <InputNumber
              size="small"
              value={positionMonitoringInterval}
              onChange={(value) => {
                // 允许输入任何数值（包括超出范围的值），在应用时再验证
                if (value !== null && value !== undefined) {
                  setPositionMonitoringInterval(value);
                } else if (value === null) {
                  // 允许清空输入
                  setPositionMonitoringInterval(0);
                }
              }}
              style={{ width: '100%' }}
              step={1}
              addonAfter="秒"
              placeholder="输入秒数（1-3600）"
              precision={0}
              controls={true}
            />
          </Col>
          <Col span={6}>
            <Button
              type="primary"
              size="small"
              icon={<CheckOutlined />}
              onClick={handleApplyPositionMonitoringInterval}
              disabled={!hasPositionMonitoringIntervalChanges}
              style={{ width: '100%' }}
              title="应用配置（值建议在1-3600秒之间）"
            >
              应用
            </Button>
          </Col>
        </Row>
      </Space>
    </Card>
  );
}

// 导出获取配置的工具函数
export const getTradingConfig = () => {
  const orderInterval = localStorage.getItem('trading_config_order_monitoring_interval');
  let orderIntervalSeconds = 60; // 默认60秒
  if (orderInterval) {
    const parsed = parseInt(orderInterval, 10);
    // 如果值大于1000，说明是旧的毫秒值，转换为秒
    if (parsed > 1000) {
      orderIntervalSeconds = Math.floor(parsed / 1000);
    } else if (parsed >= 1) {
      orderIntervalSeconds = parsed;
    }
  }
  
  return {
    maxOrderAmount: parseFloat(localStorage.getItem('trading_config_max_order_amount') || '1000'),
    maxPosition: parseFloat(localStorage.getItem('trading_config_max_position') || '10000'),
    orderMonitoringInterval: orderIntervalSeconds, // 单位：秒
    positionMonitoringInterval: (() => {
      const positionInterval = localStorage.getItem('trading_config_position_monitoring_interval');
      let positionIntervalSeconds = 300; // 默认300秒（5分钟）
      if (positionInterval) {
        const parsed = parseInt(positionInterval, 10);
        // 如果值大于1000，说明是旧的毫秒值，转换为秒
        if (parsed > 1000) {
          positionIntervalSeconds = Math.floor(parsed / 1000);
        } else if (parsed >= 10) {
          positionIntervalSeconds = parsed;
        }
      }
      return positionIntervalSeconds; // 单位：秒
    })(),
  };
};












