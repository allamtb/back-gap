import React, { useEffect, useState } from "react";
import { Card, Button, Space, Select, Tag, Input, Row, Col, Divider, AutoComplete } from "antd";
import { PlusOutlined, DeleteOutlined, CloseOutlined } from "@ant-design/icons";

/**
 * ExchangeManager - 管理多个交易所配置的组件
 * 支持从后端获取交易所列表，单独选择币种，支持多个交易所
 * 
 * @param {Array} exchanges - 当前的交易所配置数组 [{exchange, symbol, label, color}]
 * @param {Function} onChange - 配置变化的回调函数
 */
export default function ExchangeManager({ exchanges = [], onChange }) {
  // 从后端获取的交易所列表
  const [availableExchanges, setAvailableExchanges] = useState([]);
  // 当前选择的币种（单个）
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  // 当前选择的交易所（多个）
  const [selectedExchanges, setSelectedExchanges] = useState([]);
  // 从后端获取的币种列表
  const [availableSymbols, setAvailableSymbols] = useState([]);
  // 币种加载状态
  const [symbolsLoading, setSymbolsLoading] = useState(false);
  
  // 默认币种列表（作为后备）
  const defaultSymbols = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
    'BNB/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT'
  ];

  const availableColors = [
    '#ff9800', '#2196f3', '#4caf50', '#f44336', 
    '#9c27b0', '#ff5722', '#00bcd4', '#ffeb3b'
  ];

  // 从后端加载交易所列表（复用 ExchangeSelector 的逻辑）
  const loadExchanges = async () => {
    try {
      const res = await fetch("/api/exchanges", { timeout: 2500 });
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      setAvailableExchanges(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Failed to load exchanges:", e);
      // 降级到默认交易所列表
      setAvailableExchanges(['binance', 'bybit', 'okx', 'htx']);
    }
  };

  // 从后端加载币种列表（基于币安）
  const loadSymbols = async () => {
    setSymbolsLoading(true);
    try {
      // 获取币安的 USDT 交易对（限制200个）
      const res = await fetch("/api/symbols?exchange=binance&quote=USDT&limit=200");
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      
      if (data.success && Array.isArray(data.data?.symbols)) {
        setAvailableSymbols(data.data.symbols);
        console.log(`✅ 加载了 ${data.data.symbols.length} 个币种`);
      } else {
        throw new Error("Invalid response format");
      }
    } catch (e) {
      console.error("Failed to load symbols:", e);
      // 降级到默认币种列表
      setAvailableSymbols(defaultSymbols);
    } finally {
      setSymbolsLoading(false);
    }
  };

  useEffect(() => {
    loadExchanges();
    loadSymbols();
  }, []);

  // 添加币对（当前选择的币种 + 选择的所有交易所）
  const handleAddPairs = () => {
    if (!selectedSymbol || selectedExchanges.length === 0) {
      return;
    }

    const newExchanges = [...exchanges];
    selectedExchanges.forEach((exchange) => {
      // 检查是否已存在相同的币对
      const exists = newExchanges.some(
        (e) => e.exchange === exchange && e.symbol === selectedSymbol
      );
      
      if (!exists) {
        newExchanges.push({
          exchange,
          symbol: selectedSymbol,
          label: `${exchange} ${selectedSymbol}`,
          color: availableColors[newExchanges.length % availableColors.length],
        });
      }
    });

    onChange(newExchanges);
    // 清空选择
    setSelectedExchanges([]);
  };

  // 删除单个币对
  const handleRemove = (index) => {
    // 使用函数式更新，确保基于最新的 exchanges 状态
    onChange(prevExchanges => prevExchanges.filter((_, i) => i !== index));
  };

  return (
    <Card 
      size="small" 
      title="交易所对比配置"
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 币种选择区域 */}
        <Card size="small" title="添加币对" style={{ backgroundColor: '#f5f5f5' }}>
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            <Row gutter={8} align="middle">
              <Col span={6}>
                <span style={{ fontSize: '12px', color: '#666' }}>币种:</span>
              </Col>
              <Col span={18}>
                <AutoComplete
                  size="small"
                  value={selectedSymbol}
                  onChange={setSelectedSymbol}
                  onSelect={(value) => setSelectedSymbol(value)}
                  onBlur={(e) => {
                    const value = e.target.value;
                    if (value) {
                      setSelectedSymbol(value.toUpperCase());
                    }
                  }}
                  options={(availableSymbols.length > 0 ? availableSymbols : defaultSymbols).map(s => ({ 
                    label: s, 
                    value: s 
                  }))}
                  placeholder={symbolsLoading ? "正在加载币种..." : "输入或选择币种 (如: BTC/USDT)"}
                  style={{ width: '100%' }}
                  filterOption={(inputValue, option) =>
                    option.value.toUpperCase().indexOf(inputValue.toUpperCase()) !== -1
                  }
                  allowClear
                  disabled={symbolsLoading}
                  notFoundContent={symbolsLoading ? "加载中..." : "未找到匹配币种"}
                />
              </Col>
            </Row>

            <Row gutter={8} align="middle">
              <Col span={6}>
                <span style={{ fontSize: '12px', color: '#666' }}>交易所:</span>
              </Col>
              <Col span={18}>
                <Select
                  mode="multiple"
                  size="small"
                  value={selectedExchanges}
                  onChange={setSelectedExchanges}
                  placeholder="选择一个或多个交易所"
                  style={{ width: '100%' }}
                  options={availableExchanges.map(ex => ({ label: ex, value: ex }))}
                  maxTagCount="responsive"
                />
              </Col>
            </Row>

            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={handleAddPairs}
              disabled={!selectedSymbol || selectedExchanges.length === 0}
              block
            >
              添加 {selectedExchanges.length > 0 ? `${selectedExchanges.length} 个币对` : '币对'}
            </Button>
          </Space>
        </Card>

        {/* 已添加的币对列表 */}
        <Card 
          size="small" 
          title={`已添加的币对 (${exchanges.length})`}
          style={{ backgroundColor: '#fafafa' }}
        >
          {exchanges.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#999', padding: '20px 0' }}>
              暂无币对，请先添加
            </div>
          ) : (
            <Space wrap size="small">
              {exchanges.map((config, index) => (
                <Tag
                  key={`${config.exchange}-${config.symbol}-${index}`}
                  color={config.color}
                  closable
                  onClose={() => handleRemove(index)}
                  style={{ 
                    fontSize: '13px', 
                    padding: '4px 8px',
                    marginBottom: '4px'
                  }}
                >
                  {config.label}
                </Tag>
              ))}
            </Space>
          )}
        </Card>
      </Space>
    </Card>
  );
}

