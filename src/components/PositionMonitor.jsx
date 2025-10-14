import React, { useState, useEffect, useRef, useMemo } from "react";
import { Table, Card, Statistic, Row, Col, Space, Tag, Button, Select, Switch, message } from "antd";
import { WalletOutlined, RiseOutlined, FallOutlined, ReloadOutlined, PlayCircleOutlined, PauseCircleOutlined } from "@ant-design/icons";
import { getExchangeCredentials, getExchangeConfig } from "../utils/configManager";
import { setAllSymbols } from "../utils/symbolWatchlist";

const { Countdown } = Statistic;

export default function PositionMonitor() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [prices, setPrices] = useState({}); // 存储价格数据 { exchange: { symbol: price } }
  
  // 实时刷新相关状态
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // 刷新间隔（秒）
  const [nextRefreshTime, setNextRefreshTime] = useState(Date.now() + 30000);
  const timerRef = useRef(null);
  const fetchingRef = useRef(false); // 防止重复请求
  
  // 从配置中获取用户配置的交易所列表
  const configuredExchanges = useMemo(() => {
    return getExchangeConfig();
  }, [positions]); // 当持仓更新时重新获取配置

  // 初始加载
  useEffect(() => {
    fetchPositions();
  }, []);
  
  // 自动刷新定时器 - 改用 setTimeout 实现，确保请求完成后才开始下一次倒计时
  useEffect(() => {
    if (!autoRefresh || refreshInterval <= 0) {
      // 关闭自动刷新时清除定时器
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }
    
    // 清除旧定时器
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [autoRefresh, refreshInterval]);
  
  // 页面可见性变化时的处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面不可见时暂停刷新
        if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
        }
      } else {
        // 页面可见时恢复刷新
        if (autoRefresh) {
          fetchPositions();
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [autoRefresh, refreshInterval]);

  const fetchPositions = async () => {
    // 防止重复请求
    if (fetchingRef.current) {
      console.log('⏳ 持仓请求正在进行中，跳过本次请求');
      return;
    }
    
    console.log('🚀 开始获取持仓数据...');
    
    try {
      const credentials = getExchangeCredentials();
      
      if (credentials.length === 0) {
        console.warn('⚠️ 未配置交易所账户');
        setPositions([]);
        message.warning('请先在配置页面添加交易所账户');
        return;
      }
      
      fetchingRef.current = true;
      setLoading(true);

      // 调用后端 API
      const response = await fetch(`/api/positions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        const apiPositions = data.data;
        
        // 按交易所和币种汇总数据
        const positionMap = new Map();
        
        apiPositions.forEach((pos, index) => {
          const key = `${pos.exchange}-${pos.symbol}`;
          
          if (!positionMap.has(key)) {
            positionMap.set(key, {
              key: key,
              exchangeId: pos.exchange.toLowerCase(), // 保存原始小写ID用于API调用
              exchange: formatExchangeName(pos.exchange), // 格式化名称用于显示
              symbol: pos.symbol,
              spotAmount: 0,
              futuresAmount: 0,      // 净合约持仓（多头为正，空头为负）
              futuresLongAmount: 0,  // 合约多头持仓
              futuresShortAmount: 0, // 合约空头持仓
              totalAmount: 0,
              // 合约持仓额外信息
              unrealizedPnl: 0,      // 未实现盈亏
              notional: 0,           // 名义价值
              leverage: 0,           // 杠杆倍数
            });
          }
          
          const position = positionMap.get(key);
          
          if (pos.type === 'spot') {
            position.spotAmount += pos.amount;
          } else if (pos.type === 'futures' || pos.type === 'futures_balance') {
            // futures: 合约持仓（有开仓）
            // futures_balance: 合约账户余额（未开仓的资金）
            position.futuresAmount += pos.amount; // 净持仓（后端已处理多空方向）
            
            // 分别记录多头和空头持仓
            if (pos.side === 'long') {
              position.futuresLongAmount += Math.abs(pos.amount);
            } else if (pos.side === 'short') {
              position.futuresShortAmount += Math.abs(pos.amount);
            }
            
            // 累加未实现盈亏
            if (pos.unrealizedPnl) {
              position.unrealizedPnl += pos.unrealizedPnl;
            }
            
            // 累加名义价值
            if (pos.notional) {
              position.notional += Math.abs(pos.notional);
            }
            
            // 取最大杠杆倍数（如果有多个持仓）
            if (pos.leverage) {
              position.leverage = Math.max(position.leverage, pos.leverage);
            }
          }
          
          // 总持仓 = 现货 + 净合约持仓
          position.totalAmount = position.spotAmount + position.futuresAmount;
        });
        
        const formattedPositions = Array.from(positionMap.values());
        setPositions(formattedPositions);
        
        // 获取价格数据（用于计算 USDT 等值）
        await fetchPrices(formattedPositions);

        // 同步币种列表到本地（不再按交易所分组）
        try {
          const allSymbols = new Set();
          formattedPositions.forEach(item => {
            allSymbols.add(item.symbol);
          });
          setAllSymbols(Array.from(allSymbols));
          console.log('📝 已写入本地关注币种:', Array.from(allSymbols));
        } catch (e) {
          console.warn('⚠️ 写入本地币种列表失败:', e);
        }
        
        // 仅在手动刷新时显示成功提示
        if (!autoRefresh || loading) {
          message.success(`成功获取 ${formattedPositions.length} 个持仓记录`);
        }
      } else {
        throw new Error(data.message || "API 返回失败");
      }
    } catch (error) {
      console.error("获取持仓失败:", error);
      
      if (error.code === "ECONNABORTED") {
        message.error("请求超时，请检查网络连接");
      } else if (error.response) {
        message.error(`获取持仓失败: ${error.response.data.detail || error.message}`);
      } else if (error.request) {
        message.error("无法连接到后端服务，请确保后端已启动");
      } else {
        message.error(`获取持仓失败: ${error.message}`);
      }
      
      // 出错时清空持仓列表
      setPositions([]);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
      console.log('✅ 持仓请求完成，锁已释放');
      
      // 请求完成后，如果开启了自动刷新，设置下一次刷新
      if (autoRefresh && refreshInterval > 0) {
        const nextTime = Date.now() + refreshInterval * 1000;
        setNextRefreshTime(nextTime);
        
        // 清除旧定时器
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
        
        // 设置新定时器
        timerRef.current = setTimeout(() => {
          fetchPositions();
        }, refreshInterval * 1000);
        
        console.log(`⏰ 已设置下次刷新时间: ${new Date(nextTime).toLocaleTimeString()}`);
      }
    }
  };
  
  // 获取价格数据
  // 稳定币识别函数
  const isStableCoin = (symbol) => {
    const stableCoins = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'GUSD', 'USDD'];
    return stableCoins.includes(symbol.toUpperCase());
  };

  const fetchPrices = async (positionsList) => {
    try {
      // 构建需要获取价格的交易对列表
      const symbolsToFetch = [];
      
      positionsList.forEach(pos => {
        const baseCurrency = pos.symbol;
        // 跳过稳定币（价格固定为1）
        if (isStableCoin(baseCurrency)) {
          return;
        }
        
        // 为每个币种获取对 USDT 的价格
        const symbol = `${baseCurrency}/USDT`;
        symbolsToFetch.push({
          exchange: pos.exchangeId, // 使用原始小写ID
          symbol: symbol
        });
      });
      
      if (symbolsToFetch.length === 0) {
        console.log('ℹ️ 没有需要获取价格的币种（都是稳定币）');
        return;
      }
      
      console.log('📡 正在获取价格:', symbolsToFetch);
      
      // 调用后端价格API
      const response = await fetch('/api/prices', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbols: symbolsToFetch }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setPrices(data.data);
          console.log('✅ 价格数据获取成功:', data.data);
          // 调试：显示价格数据结构
          Object.keys(data.data).forEach(exchangeId => {
            console.log(`  📊 ${exchangeId}:`, Object.keys(data.data[exchangeId]).length, '个交易对');
          });
        } else {
          console.error('❌ 价格API返回失败:', data);
        }
      } else {
        console.error('❌ 价格API请求失败:', response.status);
      }
    } catch (error) {
      console.error('❌ 获取价格失败:', error);
      // 价格获取失败不影响持仓显示
    }
  };
  
  // 手动刷新（立即刷新）
  const handleManualRefresh = () => {
    // 清除现有定时器
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    // 重置倒计时显示（设置为当前时间，显示0秒）
    setNextRefreshTime(Date.now());
    // 立即刷新，fetchPositions 完成后会自动设置下一次定时器
    fetchPositions();
  };
  
  // 切换自动刷新
  const handleAutoRefreshToggle = (checked) => {
    setAutoRefresh(checked);
    if (checked) {
      message.success(`已开启自动刷新（每 ${refreshInterval} 秒）`);
      // 立即刷新一次，fetchPositions 完成后会自动设置定时器
      fetchPositions();
    } else {
      message.info('已暂停自动刷新');
      // 清除定时器
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }
  };
  
  // 修改刷新间隔
  const handleRefreshIntervalChange = (value) => {
    setRefreshInterval(value);
    if (autoRefresh) {
      // 清除现有定时器
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      // 立即重置倒计时显示（使用新的间隔）
      const nextTime = Date.now() + value * 1000;
      setNextRefreshTime(nextTime);
      // 立即刷新，使用新的间隔（fetchPositions 会再次设置定时器）
      fetchPositions();
      message.success(`刷新间隔已更新为 ${value} 秒`);
    }
  };

  // 格式化交易所名称
  const formatExchangeName = (exchange) => {
    const nameMap = {
      binance: "币安",
      okx: "OKX",
      bybit: "Bybit",
      gate: "Gate.io",
      huobi: "火币",
      kucoin: "KuCoin",
    };
    return nameMap[exchange.toLowerCase()] || exchange.toUpperCase();
  };
  
  // 获取价格（带缓存查找）
  const getPrice = (exchangeId, symbol) => {
    // 如果是稳定币，价格为 1
    if (isStableCoin(symbol)) {
      return 1;
    }
    
    // 从价格缓存中查找
    // exchangeId 应该已经是小写的原始ID（如 "binance", "okx"）
    const priceSymbol = `${symbol}/USDT`;
    
    if (prices[exchangeId] && prices[exchangeId][priceSymbol]) {
      return prices[exchangeId][priceSymbol];
    }
    
    // 调试：价格未找到时输出信息
    if (Object.keys(prices).length > 0) {
      console.log(`⚠️ 价格未找到: ${exchangeId} - ${priceSymbol}`, {
        availableExchanges: Object.keys(prices),
        hasExchange: !!prices[exchangeId],
        availableSymbols: prices[exchangeId] ? Object.keys(prices[exchangeId]) : []
      });
    }
    
    return 0; // 找不到价格返回 0
  };
  
  // 计算USDT等值
  const calculateUsdtValue = (exchangeId, symbol, amount) => {
    const price = getPrice(exchangeId, symbol);
    return amount * price;
  };

  // 按交易所汇总数据（带USDT等值）
  const exchangeSummary = useMemo(() => {
    return positions.reduce(
      (acc, item) => {
        const existing = acc.find((x) => x.exchange === item.exchange);
        
        // 计算USDT等值（使用 exchangeId）
        const spotValue = calculateUsdtValue(item.exchangeId, item.symbol, item.spotAmount);
        const futuresValue = calculateUsdtValue(item.exchangeId, item.symbol, item.futuresAmount);
        
        if (existing) {
          existing.spotAmount += item.spotAmount;
          existing.futuresAmount += item.futuresAmount;
          existing.futuresLongAmount += (item.futuresLongAmount || 0);
          existing.futuresShortAmount += (item.futuresShortAmount || 0);
          existing.totalAmount += item.totalAmount;
          existing.spotValue += spotValue;
          existing.futuresValue += futuresValue;
          existing.totalValue += spotValue + futuresValue;
          existing.unrealizedPnl += (item.unrealizedPnl || 0);
          existing.notional += (item.notional || 0);
        } else {
          acc.push({
            key: item.exchange,
            exchange: item.exchange,
            exchangeId: item.exchangeId, // 保存 exchangeId
            spotAmount: item.spotAmount,
            futuresAmount: item.futuresAmount,
            futuresLongAmount: item.futuresLongAmount || 0,
            futuresShortAmount: item.futuresShortAmount || 0,
            totalAmount: item.totalAmount,
            spotValue: spotValue,
            futuresValue: futuresValue,
            totalValue: spotValue + futuresValue,
            unrealizedPnl: item.unrealizedPnl || 0,
            notional: item.notional || 0,
            leverage: item.leverage || 0,
          });
        }
        return acc;
      },
      []
    );
  }, [positions, prices]);

  // 按币种汇总数据（带USDT等值）
  const symbolSummary = useMemo(() => {
    return positions.reduce(
      (acc, item) => {
        const existing = acc.find((x) => x.symbol === item.symbol);
        
        // 计算USDT等值（使用 exchangeId）
        const spotValue = calculateUsdtValue(item.exchangeId, item.symbol, item.spotAmount);
        const futuresValue = calculateUsdtValue(item.exchangeId, item.symbol, item.futuresAmount);
        
        if (existing) {
          existing.spotAmount += item.spotAmount;
          existing.futuresAmount += item.futuresAmount;
          existing.futuresLongAmount += (item.futuresLongAmount || 0);
          existing.futuresShortAmount += (item.futuresShortAmount || 0);
          existing.totalAmount += item.totalAmount;
          existing.spotValue += spotValue;
          existing.futuresValue += futuresValue;
          existing.totalValue += spotValue + futuresValue;
          existing.unrealizedPnl += (item.unrealizedPnl || 0);
          existing.notional += (item.notional || 0);
          // 如果当前 exchangeId 没有价格，但新的 item 有价格，则更新 exchangeId
          if (!existing.exchangeId || (getPrice(existing.exchangeId, item.symbol) === 0 && getPrice(item.exchangeId, item.symbol) > 0)) {
            existing.exchangeId = item.exchangeId;
          }
        } else {
          acc.push({
            key: item.symbol,
            symbol: item.symbol,
            exchangeId: item.exchangeId, // 保存 exchangeId 用于获取价格
            spotAmount: item.spotAmount,
            futuresAmount: item.futuresAmount,
            futuresLongAmount: item.futuresLongAmount || 0,
            futuresShortAmount: item.futuresShortAmount || 0,
            totalAmount: item.totalAmount,
            spotValue: spotValue,
            futuresValue: futuresValue,
            totalValue: spotValue + futuresValue,
            unrealizedPnl: item.unrealizedPnl || 0,
            notional: item.notional || 0,
            isStable: isStableCoin(item.symbol),
          });
        }
        return acc;
      },
      []
    );
  }, [positions, prices]);

  // 计算总汇总（区分稳定币和非稳定币）
  const grandTotal = useMemo(() => {
    const stableCoins = symbolSummary.filter(s => s.isStable);
    const nonStableCoins = symbolSummary.filter(s => !s.isStable);
    
    const stableSpot = stableCoins.reduce((sum, s) => sum + s.spotAmount, 0);
    const stableFutures = stableCoins.reduce((sum, s) => sum + s.futuresAmount, 0);
    const stableTotal = stableSpot + stableFutures;
    
    const nonStableSpotValue = nonStableCoins.reduce((sum, s) => sum + s.spotValue, 0);
    const nonStableFuturesValue = nonStableCoins.reduce((sum, s) => sum + s.futuresValue, 0);
    const nonStableTotalValue = nonStableSpotValue + nonStableFuturesValue;
    
    // 计算总未实现盈亏
    const totalUnrealizedPnl = symbolSummary.reduce((sum, s) => sum + (s.unrealizedPnl || 0), 0);
    
    // 总资产 = 稳定币 + 非稳定币价值
    const totalValue = stableTotal + nonStableTotalValue;
    
    // 实际财富 = 总资产 + 未实现盈亏
    const actualWealth = totalValue + totalUnrealizedPnl;
    
    return {
      stableCoins,
      nonStableCoins,
      stableSpot,
      stableFutures,
      stableTotal,
      nonStableSpotValue,
      nonStableFuturesValue,
      nonStableTotalValue,
      totalValue,
      totalUnrealizedPnl,
      actualWealth,
    };
  }, [symbolSummary]);

  const columns = [
    {
      title: "交易所",
      dataIndex: "exchange",
      key: "exchange",
      width: 100,
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: "币种",
      dataIndex: "symbol",
      key: "symbol",
      width: 80,
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: "现货数量",
      dataIndex: "spotAmount",
      key: "spotAmount",
      align: "right",
      width: 110,
      render: (value) => (
        <span style={{ color: value > 0 ? "#52c41a" : "#000" }}>
          {value.toFixed(4)}
        </span>
      ),
    },
    {
      title: "合约净持仓",
      dataIndex: "futuresAmount",
      key: "futuresAmount",
      align: "right",
      width: 110,
      render: (value, record) => (
        <div>
          <div style={{ color: value >= 0 ? "#1890ff" : "#ff4d4f", fontWeight: 'bold' }}>
            {value >= 0 ? '+' : ''}{value.toFixed(4)}
          </div>
          {(record.futuresLongAmount > 0 || record.futuresShortAmount > 0) && (
            <div style={{ fontSize: 11, color: '#999' }}>
              {record.futuresLongAmount > 0 && <span style={{ color: '#52c41a' }}>↑{record.futuresLongAmount.toFixed(4)}</span>}
              {record.futuresLongAmount > 0 && record.futuresShortAmount > 0 && ' / '}
              {record.futuresShortAmount > 0 && <span style={{ color: '#ff4d4f' }}>↓{record.futuresShortAmount.toFixed(4)}</span>}
            </div>
          )}
        </div>
      ),
    },
    {
      title: "未实现盈亏",
      dataIndex: "unrealizedPnl",
      key: "unrealizedPnl",
      align: "right",
      width: 100,
      render: (value) => {
        if (!value || Math.abs(value) < 0.01) return <span style={{ color: '#999' }}>-</span>;
        return (
          <span style={{ 
            color: value > 0 ? "#52c41a" : "#ff4d4f",
            fontWeight: 'bold'
          }}>
            {value > 0 ? '+' : ''}${value.toFixed(2)}
          </span>
        );
      },
    },
    {
      title: "总数量",
      dataIndex: "totalAmount",
      key: "totalAmount",
      align: "right",
      width: 100,
      render: (value) => {
        const color = value > 0 ? "#52c41a" : value < 0 ? "#ff4d4f" : "#000";
        return (
          <strong style={{ color }}>
            {value.toFixed(4)}
          </strong>
        );
      },
    },
  ];

  // 按交易所汇总的列定义
  const exchangeSummaryColumns = [
    {
      title: "交易所",
      dataIndex: "exchange",
      key: "exchange",
      render: (text) => <Tag color="blue" style={{ fontSize: "14px" }}>{text}</Tag>,
    },
    {
      title: "现货总量",
      dataIndex: "spotAmount",
      key: "spotAmount",
      align: "right",
      render: (value) => (
        <span style={{ color: "#52c41a", fontWeight: "bold", fontSize: "14px" }}>
          {value.toFixed(4)}
        </span>
      ),
    },
    {
      title: "合约总量",
      dataIndex: "futuresAmount",
      key: "futuresAmount",
      align: "right",
      render: (value) => (
        <span style={{ color: "#ff4d4f", fontWeight: "bold", fontSize: "14px" }}>
          {value.toFixed(4)}
        </span>
      ),
    },
    {
      title: "USDT等值",
      dataIndex: "totalValue",
      key: "totalValue",
      align: "right",
      render: (value) => (
        <span style={{ color: "#1890ff", fontWeight: "bold", fontSize: "14px" }}>
          {value > 0 ? `≈ ${value.toFixed(2)} USDT` : '-'}
        </span>
      ),
    },
  ];

  // 按币种汇总的列定义
  const symbolSummaryColumns = [
    {
      title: "币种",
      dataIndex: "symbol",
      key: "symbol",
      render: (text, record) => (
        <Space>
          <strong>{text}</strong>
          {record.isStable && <Tag color="green">稳定币</Tag>}
        </Space>
      ),
    },
    {
      title: "现货总量",
      dataIndex: "spotAmount",
      key: "spotAmount",
      align: "right",
      render: (value) => (
        <span style={{ color: "#52c41a", fontWeight: "bold" }}>
          {value.toFixed(4)}
        </span>
      ),
    },
    {
      title: "合约总量",
      dataIndex: "futuresAmount",
      key: "futuresAmount",
      align: "right",
      render: (value) => (
        <span style={{ color: "#ff4d4f", fontWeight: "bold" }}>
          {value.toFixed(4)}
        </span>
      ),
    },
    {
      title: "净持仓",
      dataIndex: "totalAmount",
      key: "totalAmount",
      align: "right",
      render: (value) => {
        const color = value > 0 ? "#52c41a" : value < 0 ? "#ff4d4f" : "#000";
        return (
          <strong style={{ color, fontSize: "16px" }}>
            {value.toFixed(4)}
          </strong>
        );
      },
    },
    {
      title: "USDT等值",
      dataIndex: "totalValue",
      key: "totalValue",
      align: "right",
      render: (value, record) => (
        <span style={{ color: "#1890ff", fontWeight: "bold" }}>
          {record.isStable ? value.toFixed(2) : (value > 0 ? `≈ ${value.toFixed(2)}` : '-')}
        </span>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      {/* 自动刷新控制栏 */}
      <Card 
        size="small" 
        style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none'
        }}
      >
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            <span style={{ color: '#fff', fontWeight: 500 }}>
              {autoRefresh ? (
                <PlayCircleOutlined style={{ marginRight: 8 }} />
              ) : (
                <PauseCircleOutlined style={{ marginRight: 8 }} />
              )}
              自动刷新
            </span>
            <Switch 
              checked={autoRefresh} 
              onChange={handleAutoRefreshToggle}
              checkedChildren="开启"
              unCheckedChildren="关闭"
            />
            
            <Select
              value={refreshInterval}
              onChange={handleRefreshIntervalChange}
              style={{ width: 120 }}
              disabled={!autoRefresh}
            >
              <Select.Option value={5}>每 5 秒</Select.Option>
              <Select.Option value={10}>每 10 秒</Select.Option>
              <Select.Option value={30}>每 30 秒</Select.Option>
              <Select.Option value={60}>每 1 分钟</Select.Option>
            </Select>
            
            {autoRefresh && (
              <div style={{ 
                display: 'inline-block',
                padding: '4px 12px',
                background: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
                color: '#fff',
                fontSize: '13px'
              }}>
                <Countdown 
                  value={nextRefreshTime} 
                  format="s 秒后刷新"
                  valueStyle={{ 
                    color: '#fff', 
                    fontSize: '13px',
                    fontWeight: 500
                  }}
                />
              </div>
            )}
          </Space>
          
          <Space>
            <span style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px' }}>
              共 {positions.length} 个持仓
            </span>
            <Button
              type="primary"
              size="small"
              icon={<ReloadOutlined spin={loading} />}
              onClick={handleManualRefresh}
              loading={loading}
            >
              立即刷新
            </Button>
          </Space>
        </Space>
      </Card>
      
      {/* 汇总卡片 - 多维度显示 */}
      <Row gutter={[16, 16]}>
        {/* 第一行：3个基础卡片 */}
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="稳定币总持仓"
              value={grandTotal.stableTotal}
              precision={2}
              suffix="USDT"
              valueStyle={{ color: "#52c41a", fontSize: "20px" }}
              prefix={<WalletOutlined />}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: "#999" }}>
              现货: {grandTotal.stableSpot.toFixed(2)} | 合约: {grandTotal.stableFutures.toFixed(2)}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="非稳定币价值"
              value={grandTotal.nonStableTotalValue}
              precision={2}
              suffix="USDT"
              valueStyle={{ color: "#1890ff", fontSize: "20px" }}
              prefix={<RiseOutlined />}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: "#999" }}>
              {grandTotal.nonStableCoins.length} 种币
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="交易所数量"
              value={new Set(positions.map((p) => p.exchange)).size}
              valueStyle={{ fontSize: "20px" }}
              prefix={<WalletOutlined />}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: "#999" }}>
              共 {positions.length} 个持仓
            </div>
          </Card>
        </Col>
        
        {/* 第二行：2个重要卡片 */}
        <Col xs={24} lg={12}>
          <Card style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <Statistic
              title={<span style={{ color: '#fff' }}>总持仓价值</span>}
              value={grandTotal.totalValue}
              precision={2}
              suffix="USDT"
              valueStyle={{ color: "#fff", fontSize: "28px", fontWeight: "bold" }}
              prefix={<WalletOutlined />}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>
              持仓市值: ${grandTotal.totalValue.toFixed(2)}
              {grandTotal.totalUnrealizedPnl !== 0 && (
                <span style={{ 
                  marginLeft: 8, 
                  color: grandTotal.totalUnrealizedPnl > 0 ? '#52c41a' : '#ff4d4f',
                  fontWeight: 'bold',
                  fontSize: 13
                }}>
                  {grandTotal.totalUnrealizedPnl > 0 ? '+' : ''}
                  ${grandTotal.totalUnrealizedPnl.toFixed(2)}
                </span>
              )}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card style={{ 
            background: grandTotal.totalUnrealizedPnl >= 0 
              ? 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' 
              : 'linear-gradient(135deg, #eb3349 0%, #f45c43 100%)'
          }}>
            <Statistic
              title={<span style={{ color: '#fff', fontWeight: 'bold' }}>💎 实际财富</span>}
              value={grandTotal.actualWealth}
              precision={2}
              suffix="USDT"
              valueStyle={{ color: "#fff", fontSize: "28px", fontWeight: "bold" }}
              prefix={<RiseOutlined />}
            />
            <div style={{ marginTop: 8, fontSize: 13, color: 'rgba(255,255,255,0.95)', fontWeight: 500 }}>
              未实现盈亏: {grandTotal.totalUnrealizedPnl > 0 ? '+' : ''}
              ${grandTotal.totalUnrealizedPnl.toFixed(2)}
            </div>
          </Card>
        </Col>
      </Row>
      
      {/* 非稳定币明细卡片 */}
      {grandTotal.nonStableCoins.length > 0 && (
        <Card 
          title="非稳定币持仓明细" 
          size="small"
          extra={<span style={{ color: '#999', fontSize: 12 }}>以 USDT 计价</span>}
        >
          <Space wrap>
            {grandTotal.nonStableCoins.map(coin => {
              // 直接使用 coin.exchangeId 获取价格
              const price = getPrice(coin.exchangeId, coin.symbol);
              const hasLong = coin.futuresLongAmount > 0;
              const hasShort = coin.futuresShortAmount > 0;
              const hasUnrealizedPnl = coin.unrealizedPnl && Math.abs(coin.unrealizedPnl) > 0.01;
              
              return (
                <Card key={coin.symbol} size="small" style={{ minWidth: 200 }}>
                  <div style={{ marginBottom: 4 }}>
                    <strong style={{ fontSize: 16 }}>{coin.symbol}</strong>
                    {price > 0 && (
                      <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                        @ ${price.toFixed(2)}
                      </span>
                    )}
                  </div>
                  
                  <div style={{ fontSize: 12, color: '#52c41a' }}>
                    现货: {coin.spotAmount.toFixed(4)} 
                    {coin.spotValue > 0 && ` (≈ $${coin.spotValue.toFixed(2)})`}
                  </div>
                  
                  {/* 显示净合约持仓 */}
                  <div style={{ fontSize: 12, color: coin.futuresAmount >= 0 ? '#1890ff' : '#ff4d4f' }}>
                    合约净: {coin.futuresAmount >= 0 ? '+' : ''}{coin.futuresAmount.toFixed(4)}
                    {Math.abs(coin.futuresValue) > 0 && ` (≈ $${coin.futuresValue.toFixed(2)})`}
                  </div>
                  
                  {/* 显示多空仓位明细 */}
                  {(hasLong || hasShort) && (
                    <div style={{ fontSize: 11, color: '#999', marginLeft: 8 }}>
                      {hasLong && <span style={{ color: '#52c41a' }}>↑{coin.futuresLongAmount.toFixed(4)}</span>}
                      {hasLong && hasShort && ' / '}
                      {hasShort && <span style={{ color: '#ff4d4f' }}>↓{coin.futuresShortAmount.toFixed(4)}</span>}
                    </div>
                  )}
                  
                  {/* 显示未实现盈亏 */}
                  {hasUnrealizedPnl && (
                    <div style={{ 
                      fontSize: 11, 
                      color: coin.unrealizedPnl > 0 ? '#52c41a' : '#ff4d4f',
                      marginTop: 2
                    }}>
                      PNL: {coin.unrealizedPnl > 0 ? '+' : ''}${coin.unrealizedPnl.toFixed(2)}
                    </div>
                  )}
                  
                  <div style={{ fontSize: 12, fontWeight: 'bold', marginTop: 4, borderTop: '1px solid #f0f0f0', paddingTop: 4 }}>
                    总值: ≈ ${coin.totalValue.toFixed(2)}
                  </div>
                </Card>
              );
            })}
          </Space>
        </Card>
      )}

      {/* 各交易所详细持仓 */}
      <Card title="各交易所持仓明细" bordered={false}>
        <Table
          columns={columns}
          dataSource={positions}
          loading={loading}
          pagination={false}
          size="middle"
          bordered
        />
      </Card>

      {/* 按交易所汇总 */}
      <Card title="按交易所汇总" bordered={false}>
        <Table
          columns={exchangeSummaryColumns}
          dataSource={exchangeSummary}
          pagination={false}
          size="middle"
          bordered
          rowClassName={() => "summary-row"}
        />
      </Card>

      {/* 按币种汇总 */}
      <Card title="按币种汇总" bordered={false}>
        <Table
          columns={symbolSummaryColumns}
          dataSource={symbolSummary}
          pagination={false}
          size="middle"
          bordered
          rowClassName={() => "summary-row"}
        />
      </Card>
    </Space>
  );
}

