import React, { useEffect, useState, useRef } from "react";
import { Card, Button, Space, Select, Tag, Input, Row, Col, Divider, AutoComplete, Radio } from "antd";
import { PlusOutlined, DeleteOutlined, CloseOutlined } from "@ant-design/icons";
import { generateSymbol } from "../utils/exchangeRules";
import ExchangeRulesConfig from "./ExchangeRulesConfig";

/**
 * ExchangeManager - 管理多个交易所配置的组件
 * 支持从后端获取交易所列表，单独选择币种，支持多个交易所
 * 
 * @param {Array} exchanges - 当前的交易所配置数组 [{exchange, symbol, market_type, label, color}]
 * @param {Function} onChange - 配置变化的回调函数
 */
export default function ExchangeManager({ exchanges = [], onChange }) {
  // 从后端获取的交易所列表
  const [availableExchanges, setAvailableExchanges] = useState([]);
  // 当前选择的币种（单个）- 只存储币种代码（如 'BTC'）
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  // 当前选择的交易所（多个）
  const [selectedExchanges, setSelectedExchanges] = useState([]);
  // 当前选择的市场类型（默认现货）
  const [selectedMarketType, setSelectedMarketType] = useState('spot');
  // 从后端获取的币种列表
  const [availableSymbols, setAvailableSymbols] = useState([]);
  // 币种加载状态
  const [symbolsLoading, setSymbolsLoading] = useState(false);
  // 默认币种列表（只存储币种代码）
  const defaultSymbols = [
    'BTC', 'ETH', 'SOL', 'XRP',
    'BNB', 'ADA', 'DOGE', 'AVAX'
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
      
      if (data.success && Array.isArray(data.data?.coins)) {
        // 🎯 后端已经返回币种代码列表
        setAvailableSymbols(data.data.coins);
        console.log(`✅ 加载了 ${data.data.coins.length} 个币种代码:`, data.data.coins.slice(0, 10));
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

  // ✅ 应用币种到所有已添加的币对（手动触发，不自动）
  const handleApplySymbol = () => {
    // 边界情况处理：如果币种为空、无效，或 exchanges 为空，不执行更新
    if (!selectedSymbol || !selectedSymbol.trim() || exchanges.length === 0) {
      return;
    }

    // 更新所有已添加的币对
    const updatedExchanges = exchanges.map((config) => {
      // 提取原有的交易所和市场类型
      const { exchange, market_type } = config;
      
      // 规则中使用 'future'（无s），但传递给后端使用 'futures'
      const ruleMarketType = market_type === 'futures' ? 'future' : market_type;
      
      // 使用新币种和原有交易所、市场类型生成新交易对
      const newSymbol = generateSymbol(selectedSymbol.trim().toUpperCase(), exchange, ruleMarketType);
      
      // 生成新的 label
      const marketTypeLabel = market_type === 'spot' ? '现货' : '合约';
      const newLabel = `${exchange} ${newSymbol} (${marketTypeLabel})`;
      
      return {
        ...config,
        symbol: newSymbol,
        label: newLabel,
        // 保持原有的 color 和其他属性不变
      };
    });

    // 通知父组件更新
    onChange(updatedExchanges);
    console.log(`✅ 已应用币种 ${selectedSymbol.trim().toUpperCase()} 到 ${updatedExchanges.length} 个币对`);
  };

  // 获取未使用的颜色
  const getNextAvailableColor = (existingExchanges) => {
    const usedColors = existingExchanges.map(e => e.color);
    // 找到第一个未使用的颜色
    const unusedColor = availableColors.find(color => !usedColors.includes(color));
    // 如果所有颜色都被使用了，就循环使用
    return unusedColor || availableColors[existingExchanges.length % availableColors.length];
  };

  // 添加币对（当前选择的币种 + 选择的所有交易所 + 市场类型）
  const handleAddPairs = () => {
    if (!selectedSymbol || selectedExchanges.length === 0) {
      return;
    }

    const newExchanges = [...exchanges];
    const marketTypeLabel = selectedMarketType === 'spot' ? '现货' : '合约';
    
    selectedExchanges.forEach((exchange) => {
      // 🎯 规则中使用 'future'（无s），但传递给后端使用 'futures'
      const ruleMarketType = selectedMarketType === 'futures' ? 'future' : selectedMarketType;
      
      // 🎯 根据规则生成完整交易对
      const fullSymbol = generateSymbol(selectedSymbol, exchange, ruleMarketType);
      
      console.log(`🔄 生成交易对: ${selectedSymbol} + ${exchange} (${selectedMarketType}) → ${fullSymbol}`);
      
      // 检查是否已存在相同的币对（包括市场类型）
      const exists = newExchanges.some(
        (e) => e.exchange === exchange && e.symbol === fullSymbol && e.market_type === selectedMarketType
      );
      
      if (!exists) {
        newExchanges.push({
          exchange,
          symbol: fullSymbol,  // 传递完整交易对（如 'BTC/USDC'）
          market_type: selectedMarketType,
          label: `${exchange} ${fullSymbol} (${marketTypeLabel})`,
          color: getNextAvailableColor(newExchanges),
        });
      }
    });

    onChange(newExchanges);
    // 清空选择
    setSelectedExchanges([]);
  };

  // 删除单个币对
  const handleRemove = (index) => {
    const newExchanges = exchanges.filter((_, i) => i !== index);
    onChange(newExchanges);
  };

  return (
    <Card 
      size="small" 
      title="交易所对比配置"
      extra={<ExchangeRulesConfig />}
      bodyStyle={{ padding: '12px' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* 币种选择区域 */}
        <Card size="small" title="添加币对" style={{ backgroundColor: '#f5f5f5' }} bodyStyle={{ padding: '8px' }}>
          <Space direction="vertical" style={{ width: '100%' }} size={4}>
            <Row gutter={8} align="middle">
              <Col span={6}>
                <span style={{ fontSize: '12px', color: '#666' }}>币种:</span>
              </Col>
              <Col span={14}>
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
                  placeholder={symbolsLoading ? "正在加载币种..." : "输入或选择币种代码 (如: BTC, ETH)"}
                  style={{ width: '100%' }}
                  filterOption={(inputValue, option) =>
                    option.value.toUpperCase().indexOf(inputValue.toUpperCase()) !== -1
                  }
                  allowClear
                  disabled={symbolsLoading}
                  notFoundContent={symbolsLoading ? "加载中..." : "未找到匹配币种"}
                />
              </Col>
              <Col span={4}>
                <Button
                  type="default"
                  size="small"
                  onClick={handleApplySymbol}
                  disabled={!selectedSymbol || !selectedSymbol.trim() || exchanges.length === 0}
                  style={{ width: '100%' }}
                  title="应用币种到所有已添加的币对"
                >
                  应用
                </Button>
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

            <Row gutter={8} align="middle">
              <Col span={6}>
                <span style={{ fontSize: '12px', color: '#666' }}>市场类型:</span>
              </Col>
              <Col span={18}>
                <Radio.Group 
                  size="small"
                  value={selectedMarketType} 
                  onChange={(e) => setSelectedMarketType(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <Radio.Button value="spot" style={{ width: '50%', textAlign: 'center' }}>
                    现货
                  </Radio.Button>
                  <Radio.Button value="futures" style={{ width: '50%', textAlign: 'center' }}>
                    合约
                  </Radio.Button>
                </Radio.Group>
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
          bodyStyle={{ padding: '8px' }}
        >
          {exchanges.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#999', padding: '12px 0', fontSize: 12 }}>
              暂无币对，请先添加
            </div>
          ) : (
            <Space wrap size={4}>
              {exchanges.map((config, index) => (
                <Tag
                  key={`${config.exchange}-${config.symbol}-${index}`}
                  color={config.color}
                  closable
                  onClose={() => handleRemove(index)}
                  style={{ 
                    fontSize: '12px', 
                    padding: '2px 6px',
                    marginBottom: '2px'
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

