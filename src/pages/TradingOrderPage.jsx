import React, { useState, useCallback, useRef } from "react";
import { Row, Col, Card, Space, Tabs, Input, message } from "antd";
import RealtimePriceTable from "../components/RealtimePriceTable";
import OpenPositionPanel from "../components/OpenPositionPanel";
import PositionStatusTable from "../components/PositionStatusTable";
import OrderMessageLog from "../components/OrderMessageLog";
import OperationLog from "../components/OperationLog";
import ExchangeManager from "../components/ExchangeManager";
import TradingConfig, { getTradingConfig } from "../components/TradingConfig";
import DrawerResizeHandle from "../components/DrawerResizeHandle";
import { useWebSocketTicker } from "../hooks/useWebSocketTicker";
import { useTabManager } from "../hooks/useTabManager";
import { useDrawerResize } from "../hooks/useDrawerResize";
import { useOrderMonitoring } from "../hooks/useOrderMonitoring";
import { usePositionMonitoring } from "../hooks/usePositionMonitoring";
import { getExchangeCredentials } from "../utils/configManager";
import { generateSymbol } from "../utils/exchangeRules";

// 默认交易所配置
const DEFAULT_EXCHANGES = [
  { exchange: 'binance', symbol: 'BTC/USDT', market_type: 'spot', label: 'Binance BTC/USDT', color: '#ff9800' },
  { exchange: 'bybit', symbol: 'BTC/USDT', market_type: 'spot', label: 'Bybit BTC/USDT', color: '#2196f3' },
];

// 生成默认 Tab 名称（根据主要币对）
const generateTabLabel = (exchanges) => {
  if (!exchanges || exchanges.length === 0) {
    return '交易面板';
  }
  // 提取第一个交易所的币对基础币种
  const firstSymbol = exchanges[0].symbol;
  const baseCurrency = firstSymbol.split('/')[0];
  return `${baseCurrency} 交易`;
};

export default function TradingOrderPage() {
  // ==================== Tab 管理 ====================
  const tabManager = useTabManager({
    storageKey: 'trading_order_tabs_config',
    generateTabLabel,
    defaultExchanges: DEFAULT_EXCHANGES,
    maxTabs: 10
  });

  const {
    tabs,
    activeKey,
    setActiveKey,
    editingKey,
    editingLabel,
    setEditingLabel,
    inputRef,
    onEdit,
    startEdit,
    finishEdit,
    cancelEdit,
    updateCurrentTabExchanges,
    currentExchanges
  } = tabManager;

  // ==================== 可拖动抽屉 ====================
  const {
    drawerWidth,
    isResizing,
    resizeRef,
    startResizing
  } = useDrawerResize({
    storageKey: 'trading_order_drawer_width',
    defaultWidth: 300,
    minWidth: 80,
    maxWidth: 300,
    siderWidth: 200
  });

  // ==================== Tab 内状态（每个 Tab 独立） ====================
  // 使用 Map 存储每个 Tab 的状态
  const [tabStates, setTabStates] = useState(() => {
    const states = new Map();
    tabs.forEach(tab => {
      states.set(tab.key, {
        selectedExchanges: [],
        selectedPositions: [],
        positions: [],
        orderMessages: [],
        operationLogs: []
      });
    });
    return states;
  });

  // 获取当前 Tab 的状态
  const getCurrentTabState = () => {
    return tabStates.get(activeKey) || {
      selectedExchanges: [],
      selectedPositions: [],
      positions: [],
      orderMessages: [],
      operationLogs: []
    };
  };

  // 更新当前 Tab 的状态
  const updateCurrentTabState = (updates) => {
    setTabStates(prev => {
      const newStates = new Map(prev);
      const currentState = newStates.get(activeKey) || {};
      newStates.set(activeKey, { ...currentState, ...updates });
      return newStates;
    });
  };

  // 添加操作日志
  const addOperationLog = useCallback((log) => {
    const logEntry = {
      id: Date.now(),
      time: Date.now(),
      type: log.type,
      status: log.status,
      message: log.message,
      source: log.source || 'system' // 'manual' 或 'system'，默认为 'system'
    };
    
    setTabStates(prev => {
      const newStates = new Map(prev);
      const currentState = newStates.get(activeKey) || { operationLogs: [] };
      const currentLogs = currentState.operationLogs || [];
      
      // 添加新日志到数组开头（最新的在上方）
      const newLogs = [logEntry, ...currentLogs].slice(0, 100); // 限制最多100条
      
      newStates.set(activeKey, { ...currentState, operationLogs: newLogs });
      return newStates;
    });
  }, [activeKey]);

  const currentTabState = getCurrentTabState();

  // ==================== WebSocket 订阅（Ticker） ====================
  // Ticker 数据回调
  const handleTickerUpdate = useCallback((exchange, symbol, marketType, ticker) => {
    // console.log('📈 Ticker 更新:', exchange, symbol, ticker);
  }, []);

  // 订阅 Ticker 数据（只在当前激活 Tab 时启用）
  const { tickerData } = useWebSocketTicker(
    currentExchanges,
    handleTickerUpdate,
    currentExchanges.length > 0
  );

  // ==================== 订单监控 ====================
  // 获取交易配置中的监控间隔（使用 state 以便响应配置变化）
  // 注意：配置中存储的是秒数，但传给 hook 时需要转换为毫秒
  const [orderMonitoringInterval, setOrderMonitoringInterval] = useState(() => {
    const config = getTradingConfig();
    const intervalSeconds = config.orderMonitoringInterval || 60; // 默认60秒
    return intervalSeconds * 1000; // 转换为毫秒传给 hook
  });

  // 监听配置更新事件（当用户点击"应用"按钮时触发）
  React.useEffect(() => {
    const handleConfigUpdate = (event) => {
      if (event.detail && event.detail.type === 'orderMonitoringInterval') {
        const newIntervalSeconds = event.detail.value;
        const newInterval = newIntervalSeconds * 1000; // 转换为毫秒
        console.log('🔄 [TradingOrderPage] 订单监控间隔配置已应用:', newIntervalSeconds, '秒');
        setOrderMonitoringInterval(newInterval);
      }
    };

    window.addEventListener('tradingConfigUpdated', handleConfigUpdate);
    return () => {
      window.removeEventListener('tradingConfigUpdated', handleConfigUpdate);
    };
  }, []);

  // ==================== 持仓监控 ====================
  // 获取交易配置中的持仓监控间隔（使用 state 以便响应配置变化）
  // 注意：配置中存储的是秒数，但传给 hook 时需要转换为毫秒
  const [positionMonitoringInterval, setPositionMonitoringInterval] = useState(() => {
    const config = getTradingConfig();
    const intervalSeconds = config.positionMonitoringInterval || 300; // 默认300秒（5分钟）
    return intervalSeconds * 1000; // 转换为毫秒传给 hook
  });

  // 监听配置更新事件（当用户点击"应用"按钮时触发）
  React.useEffect(() => {
    const handleConfigUpdate = (event) => {
      if (event.detail && event.detail.type === 'positionMonitoringInterval') {
        const newIntervalSeconds = event.detail.value;
        const newInterval = newIntervalSeconds * 1000; // 转换为毫秒
        console.log('🔄 [TradingOrderPage] 持仓监控间隔配置已应用:', newIntervalSeconds, '秒');
        setPositionMonitoringInterval(newInterval);
      }
    };

    window.addEventListener('tradingConfigUpdated', handleConfigUpdate);
    return () => {
      window.removeEventListener('tradingConfigUpdated', handleConfigUpdate);
    };
  }, []);

  // 从当前 Tab 的交易所配置中提取币种列表（基础货币）
  const getCurrentTabSymbols = useCallback(() => {
    if (!currentExchanges || currentExchanges.length === 0) {
      return new Set();
    }
    
    const symbols = new Set();
    currentExchanges.forEach(ex => {
      // 从交易对中提取基础货币（如 "BTC/USDT" -> "BTC"）
      const symbol = ex.symbol || '';
      if (symbol.includes('/')) {
        const baseCurrency = symbol.split('/')[0];
        symbols.add(baseCurrency.toUpperCase());
      } else {
        // 如果没有分隔符，直接使用
        symbols.add(symbol.toUpperCase());
      }
    });
    
    return symbols;
  }, [currentExchanges]);

  // 过滤持仓数据：只显示当前 Tab 选择的币种
  const filterPositionsByTabSymbols = useCallback((positions) => {
    const tabSymbols = getCurrentTabSymbols();
    
    // 如果没有配置币种，返回空数组
    if (tabSymbols.size === 0) {
      return [];
    }
    
    return positions.filter(pos => {
      // 提取持仓的基础货币
      let positionBaseCurrency = '';
      
      if (pos.symbol) {
        // 如果是交易对格式（如 "BTC/USDT"），提取基础货币
        if (pos.symbol.includes('/')) {
          positionBaseCurrency = pos.symbol.split('/')[0].toUpperCase();
        } else {
          // 如果是币种代码（如 "BTC"），直接使用
          positionBaseCurrency = pos.symbol.toUpperCase();
        }
      }
      
      // 检查是否匹配当前 Tab 的币种
      return tabSymbols.has(positionBaseCurrency);
    });
  }, [getCurrentTabSymbols]);

  // 持仓更新回调
  // isDataRefresh: true 表示是数据刷新（可能有新行），false 表示是价格更新
  const handlePositionsUpdate = useCallback((positions, isDataRefresh = false) => {
    // 先过滤持仓：只显示当前 Tab 选择的币种
    const filteredPositions = filterPositionsByTabSymbols(positions);
    
    if (isDataRefresh) {
      // 数据刷新：直接更新，显示loading
      setTabStates(prev => {
        const newStates = new Map(prev);
        const currentState = newStates.get(activeKey) || {};
        newStates.set(activeKey, { ...currentState, positions: filteredPositions });
        return newStates;
      });
    } else {
      // 价格更新：只更新价格相关的字段，不触发整体刷新
      // 注意：价格更新时，只更新已存在的持仓，不添加新持仓
      setTabStates(prev => {
        const newStates = new Map(prev);
        const currentState = newStates.get(activeKey) || {};
        const currentPositions = currentState.positions || [];
        
        // 创建价格更新映射（只包含已存在的持仓）
        const priceUpdateMap = new Map();
        filteredPositions.forEach(pos => {
          // 检查这个持仓是否已经存在
          const existingPos = currentPositions.find(p => p.key === pos.key);
          if (existingPos) {
            priceUpdateMap.set(pos.key, {
              currentPrice: pos.currentPrice,
              unrealizedPnl: pos.unrealizedPnl,
              pnlPercent: pos.pnlPercent
            });
          }
        });
        
        // 只更新价格相关字段，保持其他字段不变，不添加新持仓
        const updatedPositions = currentPositions.map(pos => {
          const priceUpdate = priceUpdateMap.get(pos.key);
          if (priceUpdate) {
            return {
              ...pos,
              currentPrice: priceUpdate.currentPrice,
              unrealizedPnl: priceUpdate.unrealizedPnl,
              pnlPercent: priceUpdate.pnlPercent
            };
          }
          return pos;
        });
        
        newStates.set(activeKey, { ...currentState, positions: updatedPositions });
        return newStates;
      });
    }
  }, [activeKey, filterPositionsByTabSymbols]);

  // 启动持仓监控（只在当前激活 Tab 时启用）
  const { 
    isMonitoring: isPositionMonitoring, 
    positions: realtimePositions,
    loading: positionsLoading,
    error: positionsError,
    refresh: refreshPositions,
    refreshCountdown: positionRefreshCountdown
  } = usePositionMonitoring(
    currentExchanges,
    handlePositionsUpdate,
    currentExchanges.length > 0 && activeKey, // 只在有交易所配置且 Tab 激活时启用
    positionMonitoringInterval,
    tickerData, // 传递 tickerData，用于获取现货持仓的当前价格
    addOperationLog // 传递日志回调
  );

  // 订单消息回调
  const handleOrderMessage = useCallback((message) => {
    // 检查消息是否匹配当前 Tab 的币对
    const tabSymbols = getCurrentTabSymbols();
    
    // 从订单消息中提取币种
    let orderSymbol = '';
    if (message.symbol) {
      if (message.symbol.includes('/')) {
        orderSymbol = message.symbol.split('/')[0].toUpperCase();
      } else {
        orderSymbol = message.symbol.toUpperCase();
      }
    }
    
    // 调试日志：显示所有订单消息和过滤情况
    console.log('🔍 [订单监控] 收到订单消息:', {
      orderId: message.orderId,
      symbol: message.symbol,
      extractedSymbol: orderSymbol,
      tabSymbols: Array.from(tabSymbols),
      exchange: message.exchange,
      type: message.type,
      currentExchanges: currentExchanges.map(ex => ({
        exchange: ex.exchange,
        symbol: ex.symbol,
        market_type: ex.market_type
      }))
    });
    
    // 如果消息的币种不在当前 Tab 的币种列表中，不添加
    // 注意：如果 tabSymbols 为空，允许所有消息通过（兼容性处理）
    if (tabSymbols.size > 0) {
      if (!orderSymbol) {
        console.warn('⚠️ [订单监控] 订单消息缺少 symbol 字段，已跳过:', {
          orderId: message.orderId,
          message: message
        });
        return;
      }
      
      if (!tabSymbols.has(orderSymbol)) {
        console.log('⚠️ [订单监控] 订单消息币种不匹配，已跳过:', {
          orderId: message.orderId,
          orderSymbol: orderSymbol,
          messageSymbol: message.symbol,
          tabSymbols: Array.from(tabSymbols),
          currentExchanges: currentExchanges.map(ex => ({
            exchange: ex.exchange,
            symbol: ex.symbol,
            market_type: ex.market_type
          }))
        });
        return;
      }
      
      console.log('✅ [订单监控] 订单消息币种匹配，将添加:', {
        orderId: message.orderId,
        orderSymbol: orderSymbol,
        tabSymbols: Array.from(tabSymbols)
      });
    } else {
      console.warn('⚠️ [订单监控] Tab 币种列表为空，允许所有消息通过:', {
        orderId: message.orderId,
        symbol: message.symbol
      });
    }
    
    // 将新消息添加到当前 Tab 的 orderMessages 列表
    setTabStates(prev => {
      const newStates = new Map(prev);
      const currentState = newStates.get(activeKey) || {};
      const currentMessages = currentState.orderMessages || [];
      
      // 去重逻辑：检查是否已存在相同的订单消息
      // 基于 orderId + type + description 来判断是否重复
      const isDuplicate = currentMessages.some(existingMsg => {
        // 如果是同一个订单的相同类型消息
        if (existingMsg.orderId === message.orderId && 
            existingMsg.type === message.type) {
          // 如果描述相同，认为是重复（比如都是"订单状态: 已成交"）
          if (existingMsg.description === message.description) {
            return true;
          }
          // 对于已关闭的订单，如果类型和订单ID相同，也认为是重复
          // 因为已关闭订单的状态不会改变
          if (['filled', 'cancelled', 'other'].includes(message.type) &&
              existingMsg.type === message.type) {
            return true;
          }
        }
        return false;
      });
      
      // 如果是重复消息，不添加
      if (isDuplicate) {
        console.log('⚠️ [订单监控] 检测到重复消息，已跳过:', {
          orderId: message.orderId,
          type: message.type,
          time: message.time,
          description: message.description
        });
        return newStates;
      }
      
      newStates.set(activeKey, {
        ...currentState,
        orderMessages: [message, ...currentMessages].slice(0, 100) // 最多保留 100 条消息
      });
      return newStates;
    });
    // 不再自动触发持仓刷新，只保留定时刷新和手动刷新
  }, [activeKey, getCurrentTabSymbols]);

  // 启动订单监控（只在当前激活 Tab 时启用）
  const { 
    isMonitoring: isOrderMonitoring,
    refreshCountdown: orderRefreshCountdown,
    manualRefresh: manualRefreshOrders,
    clearMonitoredOrders
  } = useOrderMonitoring(
    currentExchanges,
    handleOrderMessage,
    currentExchanges.length > 0 && activeKey, // 只在有交易所配置且 Tab 激活时启用
    orderMonitoringInterval,
    addOperationLog // 传递日志回调
  );

  // 注意：不再需要这个 useEffect，因为 handlePositionsUpdate 已经处理了过滤和更新

  // 当交易所配置改变时，自动触发持仓刷新
  // 使用 ref 存储上一次的交易所配置，以便准确检测变化
  const prevExchangesRef = React.useRef(JSON.stringify(currentExchanges));
  
  React.useEffect(() => {
    const currentExchangesStr = JSON.stringify(currentExchanges);
    
    // 检测交易所配置是否真的改变了（排除首次渲染）
    if (prevExchangesRef.current !== currentExchangesStr && currentExchanges.length > 0 && activeKey) {
      console.log('🔄 [TradingOrderPage] 交易所配置已更新，触发持仓刷新和订单消息清空');
      
      // 清空当前 Tab 的订单消息（因为币对已切换）
      setTabStates(prev => {
        const newStates = new Map(prev);
        const currentState = newStates.get(activeKey) || {};
        newStates.set(activeKey, {
          ...currentState,
          orderMessages: [] // 清空订单消息
        });
        return newStates;
      });
      
      // 清空订单监控列表（确保旧币对的订单不再被监控）
      if (clearMonitoredOrders) {
        clearMonitoredOrders();
        console.log('🔄 [TradingOrderPage] 已清空订单监控列表');
      }
      
      // 延迟一下，确保交易所配置已完全更新
      const timer = setTimeout(() => {
        refreshPositions();
        // 触发订单监控刷新，获取新币对的订单
        if (manualRefreshOrders) {
          manualRefreshOrders();
        }
      }, 300);
      
      // 更新 ref
      prevExchangesRef.current = currentExchangesStr;
      
      return () => clearTimeout(timer);
    } else {
      // 首次渲染或未改变时，也更新 ref
      prevExchangesRef.current = currentExchangesStr;
    }
  }, [currentExchanges, activeKey, refreshPositions, manualRefreshOrders]);

  // ==================== 选中交易所（用于开仓） ====================
  const handleExchangeSelection = (selected) => {
    if (selected.length > 2) {
      message.warning('最多只能选择2个交易所进行开仓');
      return;
    }
    updateCurrentTabState({ selectedExchanges: selected });
  };

  // ==================== 选中持仓（用于平仓） ====================
  const handlePositionSelection = (selected) => {
    updateCurrentTabState({ selectedPositions: selected });
  };

  // ==================== 快速平仓 ====================
  const handleQuickClose = async (position) => {
    if (!position || !position.amount || position.amount <= 0) {
      message.warning('持仓数量无效，无法平仓');
      return;
    }

    try {
      // 获取交易所凭证
      const credentials = getExchangeCredentials();
      const exchangeCred = credentials.find(c => c.exchange === position.exchange);

      if (!exchangeCred) {
        message.error(`未找到 ${position.exchange} 的凭证配置`);
        return;
      }

      const { exchange, symbol, marketType, side, amount } = position;

      // 处理 symbol：如果是现货持仓，symbol 可能是币种代码（如 'PEOPLE'），需要转换为完整交易对（如 'PEOPLE/USDT'）
      let orderSymbol = symbol;
      if (marketType === 'spot') {
        // 检查是否是完整交易对格式（包含 '/'）
        if (!symbol.includes('/')) {
          // 不是完整交易对，需要转换为完整交易对
          orderSymbol = generateSymbol(symbol, exchange, 'spot');
          console.log(`🔄 现货持仓 symbol 转换: ${symbol} → ${orderSymbol}`);
        }
      }

      // 构建订单参数
      let orderParams = {
        exchange: exchange,
        marketType: marketType,
        symbol: orderSymbol, // 使用转换后的 symbol
        type: 'market', // 平仓使用市价单
        side: '', // 根据市场类型和方向确定
        amount: amount,
        credentials: exchangeCred,
      };

      // 根据市场类型和方向确定平仓逻辑
      if (marketType === 'spot') {
        // 现货平仓：卖出持有的币种
        orderParams.side = 'sell';
        console.log(`📤 现货平仓: ${exchange} ${orderSymbol} 数量=${amount}`);
      } else if (marketType === 'futures' || marketType === 'future') {
        // 合约平仓：根据方向判断
        // 平多仓：卖出 + closePosition: 'long' (后端会设置 positionSide: 'LONG')
        // 平空仓：买入 + closePosition: 'short' (后端会设置 positionSide: 'SHORT')
        if (side === 'long') {
          // 平多仓：卖出
          orderParams.side = 'sell';
          orderParams.closePosition = 'long'; // 告诉后端这是平多仓
          console.log(`📤 合约平多仓: ${exchange} ${symbol} 数量=${amount} (卖出)`);
        } else if (side === 'short') {
          // 平空仓：买入
          orderParams.side = 'buy';
          orderParams.closePosition = 'short'; // 告诉后端这是平空仓
          console.log(`📤 合约平空仓: ${exchange} ${symbol} 数量=${amount} (买入)`);
        } else {
          message.error(`未知的持仓方向: ${side}`);
          return;
        }
      } else {
        message.error(`未知的市场类型: ${marketType}`);
        return;
      }

      // 调用后端API进行平仓
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

      if (!result.success) {
        throw new Error(result.message || '平仓失败');
      }

      const orderId = result.data?.orderId || result.data?.id;
      message.success(`✅ 平仓成功！订单ID: ${orderId}`, 3);
      
      // 记录成功日志（人工操作）
      const positionType = marketType === 'spot' ? '现货' : '合约';
      const sideText = marketType === 'spot' ? '卖出' : (side === 'long' ? '平多仓(卖出)' : '平空仓(买入)');
      addOperationLog({
        type: 'position_close',
        status: 'success',
        message: `平仓成功: ${exchange} ${symbol} ${positionType} ${sideText} 数量=${amount}`,
        source: 'manual'
      });

      // 平仓成功后，延迟刷新持仓和订单
      setTimeout(() => {
        refreshPositions();
        if (manualRefreshOrders) {
          manualRefreshOrders();
        }
      }, 1000);

    } catch (error) {
      console.error('平仓失败:', error);
      const errorMsg = error.message || String(error);
      
      // 记录失败日志（人工操作）
      const positionType = marketType === 'spot' ? '现货' : '合约';
      const sideText = marketType === 'spot' ? '卖出' : (side === 'long' ? '平多仓(卖出)' : '平空仓(买入)');
      addOperationLog({
        type: 'position_close',
        status: 'error',
        message: `平仓失败: ${exchange} ${symbol} ${positionType} ${sideText} 数量=${amount} - ${errorMsg}`,
        source: 'manual'
      });
      
      // 检查是否是名义价值错误
      if (errorMsg.includes('notional') || errorMsg.includes('4164')) {
        message.error(`平仓失败：订单名义价值不足（最小5 USDT）`, 5);
      } else if (errorMsg.includes('position side') || errorMsg.includes('4061')) {
        message.error(`平仓失败：持仓方向设置错误，请检查账户持仓模式`, 5);
      } else {
        message.error(`平仓失败: ${errorMsg}`, 5);
      }
    }
  };

  // 当 Tab 切换时，确保新 Tab 有状态，并默认选中前两个交易所
  React.useEffect(() => {
    setTabStates(prev => {
      const newStates = new Map(prev);
      tabs.forEach(tab => {
        if (!newStates.has(tab.key)) {
          // 默认选中前两个交易所（如果有至少2个）
          const defaultSelectedExchanges = tab.exchanges && tab.exchanges.length >= 2
            ? tab.exchanges.slice(0, 2).map(ex => ({
              exchange: ex.exchange,
              symbol: ex.symbol,
              marketType: ex.market_type || 'spot',
              color: ex.color
            }))
            : [];
          
          newStates.set(tab.key, {
            selectedExchanges: defaultSelectedExchanges,
            selectedPositions: [],
            positions: [],
            orderMessages: [],
            operationLogs: []
          });
        } else {
          // 如果已有状态但 selectedExchanges 为空，且交易所数量>=2，则默认选中前两个
          const currentState = newStates.get(tab.key);
          if (currentState && 
              (!currentState.selectedExchanges || currentState.selectedExchanges.length === 0) &&
              tab.exchanges && tab.exchanges.length >= 2) {
            const defaultSelectedExchanges = tab.exchanges.slice(0, 2).map(ex => ({
              exchange: ex.exchange,
              symbol: ex.symbol,
              marketType: ex.market_type || 'spot',
              color: ex.color
            }));
            newStates.set(tab.key, {
              ...currentState,
              selectedExchanges: defaultSelectedExchanges
            });
          } else if (currentState && currentState.selectedExchanges && currentState.selectedExchanges.length > 0) {
            // 当交易所配置改变时，更新 selectedExchanges 中的 symbol
            // 保持相同的 exchange 和 marketType，但更新 symbol
            const updatedSelectedExchanges = currentState.selectedExchanges.map(selected => {
              // 在 tab.exchanges 中查找匹配的交易所配置（相同的 exchange 和 marketType）
              const matchingConfig = tab.exchanges.find(ex => 
                ex.exchange === selected.exchange && 
                (ex.market_type || 'spot') === selected.marketType
              );
              
              if (matchingConfig) {
                // 如果找到匹配的配置，更新 symbol
                return {
                  ...selected,
                  symbol: matchingConfig.symbol,
                  color: matchingConfig.color
                };
              }
              
              // 如果没有找到匹配的配置，保持原样
              return selected;
            });
            
            // 检查是否有变化
            const hasChanged = updatedSelectedExchanges.some((updated, index) => {
              const original = currentState.selectedExchanges[index];
              return !original || updated.symbol !== original.symbol;
            });
            
            if (hasChanged) {
              newStates.set(tab.key, {
                ...currentState,
                selectedExchanges: updatedSelectedExchanges
              });
            }
          }
        }
      });
      return newStates;
    });
  }, [tabs]);

  // 渲染 Tab 标签（支持双击编辑）
  const renderTabLabel = (tab) => {
    if (editingKey === tab.key) {
      return (
        <Input
          ref={inputRef}
          size="small"
          value={editingLabel}
          onChange={(e) => setEditingLabel(e.target.value)}
          onBlur={finishEdit}
          onPressEnter={finishEdit}
          onKeyDown={(e) => {
            // 阻止 Backspace 和其他编辑键的默认行为（防止触发 Tab 删除）
            if (e.key === 'Escape') {
              e.stopPropagation();
              cancelEdit();
            } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key.length === 1) {
              // 阻止事件冒泡到 Tabs 组件
              e.stopPropagation();
            }
          }}
          style={{ width: 120 }}
          onClick={(e) => e.stopPropagation()}
          placeholder="输入标签名称"
          title="编辑标签名称"
          aria-label="编辑标签名称"
        />
      );
    }

    return (
      <span
        onDoubleClick={(e) => {
          e.stopPropagation();
          startEdit(tab.key, tab.label);
        }}
        style={{ cursor: 'text', userSelect: 'none' }}
        title="双击编辑名称"
      >
        {tab.label}
      </span>
    );
  };

  // 构建 Tabs items
  const tabItems = tabs.map(tab => {
    const tabState = tabStates.get(tab.key) || {
      selectedExchanges: [],
      selectedPositions: [],
      positions: [],
      orderMessages: []
    };

    return {
      key: tab.key,
      label: renderTabLabel(tab),
      children: (
        <div style={{ position: 'relative' }}>
          {/* 主内容区 */}
          <div style={{ 
            marginLeft: `${drawerWidth}px`,
            transition: isResizing ? 'none' : 'margin-left 0.3s ease',
            padding: '0 12px'
          }}>
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              {/* 第一行：实时价格监控表格 */}
              <Card 
                title="💹 实时价格监控 & 选择开仓"
                size="small"
                bodyStyle={{ padding: '12px' }}
              >
                <RealtimePriceTable
                  exchanges={tab.exchanges}
                  tickerData={tab.key === activeKey ? tickerData : {}}
                  onSelectionChange={handleExchangeSelection}
                  selectedKeys={tabState.selectedExchanges.map(ex => {
                    // 根据 exchange、symbol、marketType 找到对应的 index
                    const index = tab.exchanges.findIndex(
                      config => 
                        config.exchange === ex.exchange &&
                        config.symbol === ex.symbol &&
                        (config.market_type || 'spot') === ex.marketType
                    );
                    // 生成与 record.key 格式一致的 key: `${exchange}-${symbol}-${market_type}-${index}`
                    return index >= 0 
                      ? `${ex.exchange}-${ex.symbol}-${ex.marketType}-${index}`
                      : null;
                  }).filter(Boolean)}
                  onLog={addOperationLog}
                />
              </Card>

              {/* 第二行：左侧（开仓+持仓状态） + 右侧（订单消息） */}
              <Row gutter={12}>
                {/* 左侧：开仓、持仓状态 */}
                <Col span={18}>
                  <Space direction="vertical" style={{ width: '100%' }} size={12}>
                    {/* 开仓控件 */}
                    <OpenPositionPanel
                      selectedExchanges={tabState.selectedExchanges}
                      tickerData={tab.key === activeKey ? tickerData : {}}
                      positions={tabState.positions}
                      onPositionOpened={() => {
                        // 开仓成功后，立即触发订单监控刷新，以便立即检测到新订单
                        if (tab.key === activeKey) {
                          console.log('🔄 [TradingOrderPage] 开仓成功，立即刷新订单监控');
                          manualRefreshOrders();
                        }
                      }}
                      onLog={addOperationLog}
                    />

                    {/* 实时持仓状态（包含汇总行） */}
                    <Card 
                      title={
                        <span>
                          📊 实时持仓状态
                          {(() => {
                            const tabSymbols = Array.from(getCurrentTabSymbols());
                            if (tabSymbols.length > 0) {
                              return (
                                <span style={{ marginLeft: 8, fontSize: '11px', color: '#666' }}>
                                  (仅显示: {tabSymbols.join(', ')})
                                </span>
                              );
                            }
                            return null;
                          })()}
                          {isPositionMonitoring && (
                            <span style={{ marginLeft: 8, fontSize: '12px', color: '#52c41a' }}>
                              ● 监控中
                            </span>
                          )}
                        </span>
                      }
                      size="small"
                      bodyStyle={{ padding: '12px' }}
                    >
                      <PositionStatusTable
                        positions={tabState.positions}
                        onSelectionChange={handlePositionSelection}
                        onClosePosition={handleQuickClose}
                        loading={positionsLoading}
                        error={positionsError}
                        onRefresh={refreshPositions}
                        refreshCountdown={positionRefreshCountdown}
                        monitoringInterval={positionMonitoringInterval / 1000} // 转换为秒显示
                      />
                    </Card>
                  </Space>
                </Col>

                {/* 右侧：订单实时变化消息 + 操作日志 */}
                <Col span={6}>
                  <Space direction="vertical" style={{ width: '100%' }} size={12}>
                    <OrderMessageLog 
                      messages={tabState.orderMessages}
                      onManualRefresh={manualRefreshOrders}
                      refreshCountdown={orderRefreshCountdown}
                      monitoringInterval={orderMonitoringInterval / 1000} // 转换为秒显示
                    />
                    <OperationLog logs={tabState.operationLogs} />
                  </Space>
                </Col>
              </Row>
            </Space>
          </div>

          {/* 可拖动的配置抽屉（从内容区左侧滑出，不覆盖 Sider） */}
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              bottom: 0,
              width: `${drawerWidth}px`,
              transition: isResizing ? 'none' : 'width 0.3s ease',
              backgroundColor: '#fff',
              boxShadow: drawerWidth > 0 ? '2px 0 8px rgba(0,0,0,0.15)' : 'none',
              zIndex: 100,
              display: 'flex',
              overflow: 'hidden'
            }}
          >
            {/* 抽屉内容区 */}
            <div style={{ 
              flex: 1, 
              overflowY: 'auto', 
              overflowX: 'hidden',
              padding: '12px'
            }}>
              <Space direction="vertical" style={{ width: '100%' }} size={12}>
                <div style={{ 
                  fontSize: '16px', 
                  fontWeight: 600, 
                  color: '#1890ff',
                  marginBottom: 8,
                  paddingBottom: 8,
                  borderBottom: '2px solid #1890ff'
                }}>
                  配置面板
                </div>
                
                {/* 添加币对（交易所配置） */}
                <ExchangeManager
                  exchanges={tab.exchanges}
                  onChange={updateCurrentTabExchanges}
                />
                
                {/* 交易配置 */}
                <TradingConfig />
              </Space>
            </div>

            {/* 拖动手柄 */}
            <DrawerResizeHandle
              resizeRef={resizeRef}
              onMouseDown={startResizing}
              isResizing={isResizing}
              drawerWidth={drawerWidth}
            />
          </div>
        </div>
      )
    };
  });

  return (
    <div>
      <Tabs
        type="editable-card"
        activeKey={activeKey}
        onChange={setActiveKey}
        onEdit={onEdit}
        items={tabItems}
        style={{ marginBottom: -12 }}
        aria-label="交易面板标签页"
      />
    </div>
  );
}

