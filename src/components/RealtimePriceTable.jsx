import React, { useState, useEffect } from "react";
import { Table, Button, InputNumber, Space, message, Tag, Tooltip } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getTradingConfig } from "./TradingConfig";
import { getExchangeCredentials } from "../utils/configManager";
import { formatPrice } from "../utils/formatters";

/**
 * RealtimePriceTable - 实时价格监控表格（集成下单功能）
 * 
 * @param {Array} exchanges - 交易所配置数组
 * @param {Object} tickerData - ticker数据对象 {exchange_symbol_marketType: {price, time, ...}}
 * @param {Function} onSelectionChange - 选中交易所变化回调（用于开仓）
 * @param {Array} selectedKeys - 外部控制的选中keys
 */
export default function RealtimePriceTable({ 
  exchanges = [], 
  tickerData = {}, 
  onSelectionChange,
  selectedKeys = [],
  onLog = null
}) {
  // 表格数据（每行一个交易所-币对）
  const [tableData, setTableData] = useState([]);
  // 下单状态
  const [orderLoading, setOrderLoading] = useState({});
  // 输入数据（数量和限价）
  const [inputData, setInputData] = useState({});
  // 选中的行（内部状态，如果没有外部控制）
  const [internalSelectedKeys, setInternalSelectedKeys] = useState([]);

  // 监听订单薄价格点击事件
  useEffect(() => {
    const handleOrderBookPriceClick = (event) => {
      const { exchange, symbol, marketType, price, side } = event.detail;
      const key = `${exchange}_${symbol}_${marketType}`;
      
      // 自动填入限价
      updateInput(key, 'limitPrice', price);
      
      // 显示提示信息
      message.info(`已自动填入${side === 'buy' ? '买入' : '卖出'}限价: ${formatPrice(price)}`);
    };

    window.addEventListener('orderbookPriceClick', handleOrderBookPriceClick);
    
    return () => {
      window.removeEventListener('orderbookPriceClick', handleOrderBookPriceClick);
    };
  }, []);

  // 根据exchanges和tickerData生成表格数据
  useEffect(() => {
    console.log('💹 [RealtimePriceTable] tickerData 更新:', tickerData);
    console.log('💹 [RealtimePriceTable] exchanges:', exchanges);
    
    const data = exchanges.map((config, index) => {
      const key = `${config.exchange}_${config.symbol}_${config.market_type || 'spot'}`;
      const ticker = tickerData[key] || {};
      
      console.log(`💹 [RealtimePriceTable] 处理 ${key}:`, ticker);
      
      return {
        key: `${config.exchange}-${config.symbol}-${config.market_type || 'spot'}-${index}`,
        exchange: config.exchange,
        symbol: config.symbol,
        marketType: config.market_type || 'spot',
        currentPrice: (ticker && ticker.price) ? ticker.price : '-',
        normalizedPrice: '', // 稍后计算
        updateTime: ticker.time ? dayjs(ticker.time).format('HH:mm:ss') : '-',
        amount: inputData[key]?.amount || null,
        limitPrice: inputData[key]?.limitPrice || null,
        color: config.color,
      };
    });
    
    // 计算归一价格（相对于第一个交易所的价格差百分比）
    if (data.length > 0 && data[0].currentPrice !== '-') {
      const basePrice = parseFloat(data[0].currentPrice);
      
      data.forEach((item, index) => {
        if (index === 0) {
          // 第一个交易所作为基准，显示为 0%
          item.normalizedPrice = '0%';
          item.normalizedValue = 0;
        } else if (item.currentPrice !== '-') {
          const currentPrice = parseFloat(item.currentPrice);
          const priceDiff = ((currentPrice - basePrice) / basePrice) * 100;
          item.normalizedPrice = `${priceDiff >= 0 ? '+' : ''}${priceDiff.toFixed(3)}%`;
          item.normalizedValue = priceDiff;
        } else {
          item.normalizedPrice = '-';
          item.normalizedValue = null;
        }
      });
    }
    
    setTableData(data);
  }, [exchanges, tickerData, inputData]);

  // 更新输入数据
  const updateInput = (key, field, value) => {
    setInputData(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: value,
      },
    }));
  };

  // 下单函数
  const handleOrder = async (record, orderType, side) => {
    const key = `${record.exchange}_${record.symbol}_${record.marketType}`;
    const amount = inputData[key]?.amount;
    const limitPrice = inputData[key]?.limitPrice;

    // 验证输入
    if (!amount || amount <= 0) {
      message.warning('请输入有效的数量');
      return;
    }

    if (orderType === 'limit' && (!limitPrice || limitPrice <= 0)) {
      message.warning('请输入有效的限价');
      return;
    }

    // 检查最大金额限制
    const config = getTradingConfig();
    const estimatedCost = orderType === 'limit' 
      ? limitPrice * amount 
      : (record.currentPrice !== '-' ? parseFloat(record.currentPrice) * amount : 0);

    if (estimatedCost > config.maxOrderAmount) {
      message.error(`单笔金额超过最大限制 ${config.maxOrderAmount} USDT`);
      return;
    }

    // 获取交易所凭证
    const credentials = getExchangeCredentials();
    const exchangeCred = credentials.find(c => c.exchange === record.exchange);

    if (!exchangeCred) {
      message.error(`未找到 ${record.exchange} 的凭证配置`);
      return;
    }

    // 构建订单参数
    const orderParams = {
      exchange: record.exchange,
      marketType: record.marketType,
      symbol: record.symbol,
      type: orderType,
      side: side,
      amount: amount,
      ...(orderType === 'limit' && { price: limitPrice }),
      credentials: exchangeCred,
    };

    console.log('📤 提交订单:', orderParams);

    // 设置加载状态
    const loadingKey = `${key}_${orderType}_${side}`;
    setOrderLoading(prev => ({ ...prev, [loadingKey]: true }));

    try {
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

      if (result.success) {
        message.success(`✅ 订单创建成功！订单ID: ${result.data.orderId}`);
        
        // 记录成功日志（人工操作）
        if (onLog) {
          const marketTypeText = record.marketType === 'spot' ? '现货' : '合约';
          const priceInfo = orderType === 'limit' ? `限价 ${limitPrice}` : '市价';
          onLog({
            type: 'order_create',
            status: 'success',
            message: `下单成功: ${record.exchange} ${record.symbol} ${marketTypeText} ${side === 'buy' ? '买入' : '卖出'} ${amount} (${priceInfo})`,
            source: 'manual'
          });
        }
        
        // 清空输入
        setInputData(prev => {
          const newData = { ...prev };
          delete newData[key];
          return newData;
        });
      } else {
        throw new Error(result.message || '下单失败');
      }
    } catch (error) {
      console.error('下单失败:', error);
      message.error(`下单失败: ${error.message}`);
      
      // 记录失败日志（人工操作）
      if (onLog) {
        const marketTypeText = record.marketType === 'spot' ? '现货' : '合约';
        const priceInfo = orderType === 'limit' ? `限价 ${limitPrice}` : '市价';
        onLog({
          type: 'order_create',
          status: 'error',
          message: `下单失败: ${record.exchange} ${record.symbol} ${marketTypeText} ${side === 'buy' ? '买入' : '卖出'} ${amount} (${priceInfo}) - ${error.message || '未知错误'}`,
          source: 'manual'
        });
      }
    } finally {
      setOrderLoading(prev => ({ ...prev, [loadingKey]: false }));
    }
  };

  // 处理行选择变化
  const handleRowSelectionChange = (keys, rows) => {
    // 限制最多选择2个
    if (keys.length > 2) {
      message.warning('最多只能选择2个交易所进行开仓');
      return;
    }
    
    setInternalSelectedKeys(keys);
    
    // 通知父组件
    if (onSelectionChange) {
      const selectedExchanges = rows.map(row => ({
        exchange: row.exchange,
        symbol: row.symbol,
        marketType: row.marketType,
        color: row.color,
      }));
      onSelectionChange(selectedExchanges);
    }
  };

  const columns = [
    {
      title: '交易所',
      dataIndex: 'exchange',
      width: 80,
      render: (text, record) => (
        <Tag color={record.color} style={{ fontSize: '11px', margin: 0 }}>
          {text.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      width: 90,
      render: (text) => <span style={{ fontWeight: 500, fontSize: '12px' }}>{text}</span>,
    },
    {
      title: '类型',
      dataIndex: 'marketType',
      width: 60,
      render: (type) => (
        <Tag color={type === 'spot' ? 'blue' : 'orange'} style={{ fontSize: '10px', margin: 0 }}>
          {type === 'spot' ? '现货' : '合约'}
        </Tag>
      ),
    },
    {
      title: '当前价格',
      dataIndex: 'currentPrice',
      width: 100,
      render: (price) => (
        <span style={{ fontSize: '12px', fontWeight: 'bold', color: price === '-' ? '#999' : '#1890ff' }}>
          {price !== '-' ? formatPrice(price) : '-'}
        </span>
      ),
    },
    {
      title: '归一价格',
      dataIndex: 'normalizedPrice',
      width: 90,
      render: (price, record) => {
        if (!price || price === '-') {
          return <span style={{ fontSize: '11px', color: '#999' }}>-</span>;
        }
        
        // 基准交易所显示蓝色
        if (record.normalizedValue === 0) {
          return (
            <Tooltip title="基准交易所">
              <Tag color="blue" style={{ fontSize: '10px', margin: 0 }}>
                {price}
              </Tag>
            </Tooltip>
          );
        }
        
        // 正数（价格高）显示红色，负数（价格低）显示绿色
        const color = record.normalizedValue > 0 ? '#ff4d4f' : '#52c41a';
        const bgColor = record.normalizedValue > 0 ? '#fff1f0' : '#f6ffed';
        
        return (
          <Tooltip title={`相对于第一个交易所价格差 ${price}`}>
            <span style={{ 
              fontSize: '11px', 
              fontWeight: 'bold',
              color: color,
              backgroundColor: bgColor,
              padding: '2px 6px',
              borderRadius: '4px',
              display: 'inline-block'
            }}>
              {price}
            </span>
          </Tooltip>
        );
      },
    },
    {
      title: '刷新时间',
      dataIndex: 'updateTime',
      width: 80,
      render: (time) => <span style={{ fontSize: '11px', color: '#666' }}>{time}</span>,
    },
  ];

  // 交易操作相关列（添加背景色以区分实时价格列）
  const operationColumns = [
    {
      title: '买卖数量',
      dataIndex: 'amount',
      width: 90,
      onCell: () => ({
        style: { backgroundColor: '#f5f7fa' }
      }),
      onHeaderCell: () => ({
        style: { backgroundColor: '#f5f7fa', textAlign: 'center' }
      }),
      render: (_, record) => {
        const key = `${record.exchange}_${record.symbol}_${record.marketType}`;
        const amount = inputData[key]?.amount;
        const limitPrice = inputData[key]?.limitPrice;
        const currentPrice = record.currentPrice !== '-' ? parseFloat(record.currentPrice) : null;
        
        // 计算所需USDT：优先使用限价，如果没有限价则使用当前价格
        let requiredUSDT = null;
        if (amount && amount > 0) {
          const price = limitPrice || currentPrice;
          if (price && price > 0) {
            requiredUSDT = (amount * price).toFixed(2);
          }
        }
        
        return (
          <Space size={2} direction="vertical" style={{ width: '100%' }}>
            <span style={{ 
              fontSize: '11px', 
              fontWeight: requiredUSDT ? 'bold' : 'normal',
              color: requiredUSDT ? '#1890ff' : '#999',
              lineHeight: '16px'
            }}>
              {requiredUSDT ? `${requiredUSDT} USDT` : '-'}
            </span>
            <InputNumber
              size="small"
              value={inputData[key]?.amount}
              onChange={(value) => updateInput(key, 'amount', value)}
              placeholder="数量"
              min={0}
              step={0.001}
              style={{ width: '100%', fontSize: '11px' }}
            />
          </Space>
        );
      },
    },
    {
      title: '市价操作',
      key: 'marketOrder',
      width: 100,
      onCell: () => ({
        style: { backgroundColor: '#f5f7fa' }
      }),
      onHeaderCell: () => ({
        style: { backgroundColor: '#f5f7fa', textAlign: 'center' }
      }),
      render: (_, record) => {
        const key = `${record.exchange}_${record.symbol}_${record.marketType}`;
        return (
          <Space size={2} direction="vertical" style={{ width: '100%' }}>
            <Button
              type="primary"
              size="small"
              block
              style={{ fontSize: '10px', height: '22px', backgroundColor: '#52c41a', borderColor: '#52c41a' }}
              loading={orderLoading[`${key}_market_buy`]}
              onClick={() => handleOrder(record, 'market', 'buy')}
            >
              市买
            </Button>
            <Button
              danger
              size="small"
              block
              style={{ fontSize: '10px', height: '22px' }}
              loading={orderLoading[`${key}_market_sell`]}
              onClick={() => handleOrder(record, 'market', 'sell')}
            >
              市卖
            </Button>
          </Space>
        );
      },
    },
    {
      title: '限价操作',
      key: 'limitOrder',
      width: 85,
      onCell: () => ({
        style: { backgroundColor: '#f5f7fa' }
      }),
      onHeaderCell: () => ({
        style: { backgroundColor: '#f5f7fa', textAlign: 'center' }
      }),
      render: (_, record) => {
        const key = `${record.exchange}_${record.symbol}_${record.marketType}`;
        return (
          <Space size={4} direction="vertical" style={{ width: '100%' }}>
            <InputNumber
              size="small"
              value={inputData[key]?.limitPrice}
              onChange={(value) => updateInput(key, 'limitPrice', value)}
              placeholder="限价"
              min={0}
              step={0.01}
              style={{ width: '100%', fontSize: '11px' }}
            />
            <Space size={2} wrap>
              <Button
                type="default"
                size="small"
                style={{ fontSize: '10px', padding: '0 4px', height: '22px', color: '#52c41a', borderColor: '#52c41a' }}
                loading={orderLoading[`${key}_limit_buy`]}
                onClick={() => handleOrder(record, 'limit', 'buy')}
              >
                限买
              </Button>
              <Button
                danger
                type="default"
                size="small"
                style={{ fontSize: '10px', padding: '0 4px', height: '22px' }}
                loading={orderLoading[`${key}_limit_sell`]}
                onClick={() => handleOrder(record, 'limit', 'sell')}
              >
                限卖
              </Button>
            </Space>
          </Space>
        );
      },
    },
  ];

  // 使用列分组，将实时数据和操作数据分开
  const groupedColumns = [
    {
      title: '实时价格数据',
      children: columns,
    },
    {
      title: '交易操作',
      children: operationColumns,
      onHeaderCell: () => ({
        style: { backgroundColor: '#f5f7fa', textAlign: 'center' }
      }),
    },
  ];

  // 行选择配置
  const rowSelection = {
    selectedRowKeys: selectedKeys.length > 0 ? selectedKeys : internalSelectedKeys,
    onChange: handleRowSelectionChange,
    getCheckboxProps: (record) => ({
      name: record.key,
    }),
  };

  return (
    <div>
      {/* 选中提示 */}
      <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '12px', color: '#666' }}>
          {(selectedKeys.length > 0 ? selectedKeys : internalSelectedKeys).length > 0 ? (
            <span>
              已选中 <strong>{(selectedKeys.length > 0 ? selectedKeys : internalSelectedKeys).length}</strong> 个交易所
              {(selectedKeys.length > 0 ? selectedKeys : internalSelectedKeys).length === 2 && 
                <span style={{ color: '#52c41a', marginLeft: 8 }}>✓ 可以进行开仓操作</span>
              }
            </span>
          ) : (
            <span style={{ color: '#999' }}>请勾选2个交易所进行套利开仓</span>
          )}
        </div>
        <Button
          type="text"
          size="small"
          icon={<ReloadOutlined />}
          style={{ fontSize: '11px' }}
        >
          刷新
        </Button>
      </div>

      {/* 价格表格 */}
      <Table
        size="small"
        columns={groupedColumns}
        dataSource={tableData}
        rowSelection={rowSelection}
        pagination={false}
        scroll={{ y: 200 }}
        bordered
        style={{ fontSize: '11px' }}
      />
    </div>
  );
}


