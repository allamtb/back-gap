import React, { useRef, useState, useEffect, useCallback } from "react";
import { Spin, Alert, Card, Select, InputNumber, Space, Row, Col, Slider, Switch, Button, Checkbox, Badge } from "antd";
import { ReloadOutlined, ApiOutlined } from "@ant-design/icons";
import { useExchangeData } from "../hooks/useExchangeData";
import { useChartManager } from "../hooks/useChartManager";
import { usePriceMarkers } from "../hooks/usePriceMarkers";
import { useExchangeManager } from "../hooks/useExchangeManager";
import { useWebSocketKline } from "../hooks/useWebSocketKline";

/**
 * MultiExchangeChart - 多交易所价格曲线对比组件（重构版）
 * 
 * @param {Array} exchanges - 交易所配置数组，每个元素格式：
 *   { exchange: 'binance', symbol: 'BTC/USDT', label: 'Binance BTC', color: '#ff9800' }
 * @param {number} height - 图表高度，默认500
 */
export default function MultiExchangeChart({
  exchanges = [],
  height = 500,
}) {
  const chartContainerRef = useRef(null);
  
  // ==================== 状态管理 ====================
  // 图表参数状态
  const [interval, setInterval] = useState("15m");
  const [limit, setLimit] = useState(100);
  
  // 差异标注状态
  const [enableMarkers, setEnableMarkers] = useState(true);
  const [threshold, setThreshold] = useState(50);
  
  // 选中的交易所（用于价差比对）
  const [selectedExchanges, setSelectedExchanges] = useState([]);
  
  // 实时数据开关
  const [enableRealtime, setEnableRealtime] = useState(true);

  // ==================== 数据获取 ====================
  const {
    loading,
    error,
    chartData,
    fetchAllData,
    fetchNewData,
    clearError,
    removeData,
  } = useExchangeData();

  // ==================== 图表管理 ====================
  const {
    addLineSeries,
    removeLineSeries,
    updateSeriesData,
    updateLiveKline,
    getLineSeries,
    clearAllMarkers,
  } = useChartManager(chartContainerRef, height);

  // ==================== 交易所管理 ====================
  useExchangeManager(
    exchanges,
    addLineSeries,
    removeLineSeries,
    fetchNewData,
    fetchAllData,
    removeData,
    interval,
    limit
  );

  // ==================== 实时数据 WebSocket ====================
  // K 线更新回调
  const handleKlineUpdate = useCallback((exchange, symbol, kline) => {
    updateLiveKline(exchange, symbol, kline);
  }, [updateLiveKline]);

  // WebSocket 连接
  const { connected, error: wsError, reconnect } = useWebSocketKline(
    exchanges,
    interval,
    handleKlineUpdate,
    enableRealtime
  );

  // ==================== 交易所选择处理 ====================
  // 当交易所列表变化时，清理已删除交易所的选中状态
  useEffect(() => {
    const validKeys = exchanges.map((_, index) => `exchange-${index}`);
    const filteredSelected = selectedExchanges.filter(key => validKeys.includes(key));
    
    // 只有当选中列表确实发生变化时才更新
    if (filteredSelected.length !== selectedExchanges.length) {
      setSelectedExchanges(filteredSelected);
    }
  }, [exchanges]);

  // 处理交易所勾选
  const handleExchangeSelect = (exchangeKey, checked) => {
    if (checked) {
      // 最多只能选择2个
      if (selectedExchanges.length < 2) {
        setSelectedExchanges([...selectedExchanges, exchangeKey]);
      }
    } else {
      setSelectedExchanges(selectedExchanges.filter(key => key !== exchangeKey));
    }
  };

  // 根据选中的交易所获取对应的交易所配置
  const getSelectedExchangeConfigs = () => {
    return exchanges.filter((_, index) => 
      selectedExchanges.includes(`exchange-${index}`)
    );
  };

  // ==================== 价格差异标注 ====================
  usePriceMarkers(
    enableMarkers,
    threshold,
    exchanges,
    chartData,
    getLineSeries,
    clearAllMarkers,
    selectedExchanges.length === 2 ? getSelectedExchangeConfigs() : []
  );

  // ==================== 数据更新监听 ====================
  // 当图表数据变化时，更新线条数据
  useEffect(() => {
    updateSeriesData(exchanges, chartData);
  }, [chartData, exchanges, updateSeriesData]);

  // 当周期或数据条数变化时，重新获取所有数据
  useEffect(() => {
    if (exchanges.length > 0) {
      fetchAllData(exchanges, interval, limit);
    }
  }, [exchanges.length, interval, limit, fetchAllData]);

  // ==================== UI 渲染 ====================
  return (
    <div className="multi-exchange-chart">
      {/* 控制面板 */}
      <Card 
        size="small" 
        style={{ marginBottom: 16, backgroundColor: '#fafafa' }}
        bodyStyle={{ padding: '12px' }}
      >
        {/* 第一行：周期、数据条数、实时数据 */}
        <Row gutter={16} align="middle" style={{ marginBottom: 12 }}>
          <Col flex="auto">
            <Space size="large">
              <Space>
                <span style={{ color: '#666' }}>周期:</span>
                <Select
                  value={interval}
                  onChange={setInterval}
                  size="small"
                  style={{ width: 100 }}
                  options={[
                    { value: "1m", label: "1分钟" },
                    { value: "5m", label: "5分钟" },
                    { value: "15m", label: "15分钟" },
                    { value: "1h", label: "1小时" },
                    { value: "4h", label: "4小时" },
                    { value: "1d", label: "1天" },
                  ]}
                />
              </Space>

              <Space>
                <span style={{ color: '#666' }}>数据条数:</span>
                <InputNumber
                  value={limit}
                  onChange={setLimit}
                  size="small"
                  min={10}
                  max={1000}
                  step={10}
                  style={{ width: 100 }}
                />
              </Space>

              <Space>
                <span style={{ color: '#666' }}>实时数据:</span>
                <Switch 
                  checked={enableRealtime}
                  onChange={setEnableRealtime}
                  size="small"
                  checkedChildren="开"
                  unCheckedChildren="关"
                />
                <Badge 
                  status={connected ? "success" : "error"} 
                  text={
                    <span style={{ fontSize: '12px', color: connected ? '#52c41a' : '#999' }}>
                      {connected ? "已连接" : "未连接"}
                    </span>
                  }
                />
                {!connected && (
                  <Button 
                    size="small" 
                    type="link" 
                    onClick={reconnect}
                    icon={<ApiOutlined />}
                  >
                    重连
                  </Button>
                )}
                {wsError && (
                  <span style={{ fontSize: '12px', color: '#ff4d4f' }}>
                    {wsError}
                  </span>
                )}
              </Space>
            </Space>
          </Col>
          
          <Col>
            <span style={{ fontSize: '12px', color: '#999' }}>
              {interval} / {limit}条 {enableRealtime && connected ? '/ 实时更新' : ''}
            </span>
          </Col>
        </Row>

        {/* 第二行：交易所选择（用于价差比对） */}
        {exchanges.length > 0 && (
          <Row gutter={16} align="middle" style={{ marginBottom: 12 }}>
            <Col flex="auto">
              <Space size="middle" style={{ width: '100%' }}>
                <span style={{ color: '#666', fontWeight: 500 }}>选择交易所进行价差比对:</span>
                <Space size="small">
                  {exchanges.map((exchange, index) => {
                    const exchangeKey = `exchange-${index}`;
                    const isChecked = selectedExchanges.includes(exchangeKey);
                    const isDisabled = !isChecked && selectedExchanges.length >= 2;
                    
                    return (
                      <Checkbox
                        key={exchangeKey}
                        checked={isChecked}
                        disabled={isDisabled}
                        onChange={(e) => handleExchangeSelect(exchangeKey, e.target.checked)}
                      >
                        <span style={{ color: exchange.color, fontWeight: 500 }}>
                          {exchange.label}
                        </span>
                      </Checkbox>
                    );
                  })}
                </Space>
              </Space>
            </Col>
            <Col>
              <span style={{ 
                fontSize: '12px', 
                color: selectedExchanges.length === 2 ? '#52c41a' : '#ff4d4f',
                fontWeight: 500
              }}>
                {selectedExchanges.length === 2 
                  ? '✓ 已选择2个交易所' 
                  : `请选择2个交易所 (${selectedExchanges.length}/2)`}
              </span>
            </Col>
          </Row>
        )}

        {/* 第三行：差异标注控制 */}
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space size="large" style={{ width: '100%' }}>
              <Space>
                <span style={{ color: '#666' }}>差异标注:</span>
                <Switch 
                  checked={enableMarkers}
                  onChange={setEnableMarkers}
                  size="small"
                />
              </Space>

              {enableMarkers && (
                <Space style={{ flex: 1, maxWidth: 500 }}>
                  <span style={{ color: '#666' }}>阈值:</span>
                  <Slider
                    value={threshold}
                    onChange={setThreshold}
                    min={1}
                    max={500}
                    step={1}
                    style={{ width: 200, minWidth: 150 }}
                    tooltip={{ 
                      formatter: (value) => `≥ ${value}`,
                    }}
                  />
                  <span style={{ 
                    fontSize: '12px', 
                    color: '#1890ff',
                    fontWeight: 500,
                    minWidth: 60
                  }}>
                    ≥ {threshold}
                  </span>
                </Space>
              )}
            </Space>
          </Col>
          
          <Col>
            <span style={{ fontSize: '12px', color: '#999' }}>
              {enableMarkers ? `标注差异 ≥ ${threshold} 的点` : '标注已关闭'}
            </span>
          </Col>
        </Row>
      </Card>

      {/* 图表区域 */}
      <div style={{ position: 'relative' }}>
        {loading && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 10,
          }}>
            <Spin size="large" tip="正在加载数据..." />
          </div>
        )}
        
        {error && (
          <Alert
            message="数据加载失败"
            description={error}
            type="error"
            closable
            onClose={clearError}
            style={{ marginBottom: 16 }}
            action={
              <Button 
                size="small" 
                type="primary" 
                onClick={() => fetchAllData(exchanges, interval, limit)}
                icon={<ReloadOutlined />}
              >
                重试
              </Button>
            }
          />
        )}

        {exchanges.length === 0 && !loading && (
          <Alert
            message="暂无数据"
            description="请添加至少一个交易所进行对比"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

 
        <div 
          ref={chartContainerRef} 
          style={{ 
            width: "100%", 
            height: `${height}px`,
            minHeight: "400px",
            minWidth: "300px",
            opacity: loading ? 0.5 : 1,
          }} 
        />
      </div>
    </div>
  );
}

56