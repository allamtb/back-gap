import { useEffect, useRef, useCallback, useState } from 'react';
import { getExchangeCredentials } from '../utils/configManager';
import { generateSymbol } from '../utils/exchangeRules';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';

dayjs.extend(utc);

/**
 * 将多种格式的时间字段转换为毫秒时间戳（本地时区）
 * 支持：秒/毫秒数字、ISO 字符串、无时区字符串（按 UTC 解析再转本地）
 */
const toMillis = (value) => {
  if (!value && value !== 0) return null;

  // 数字：判断秒/毫秒/微秒
  if (typeof value === 'number') {
    if (value > 1e14) return Math.floor(value / 1000); // 微秒→毫秒
    if (value > 1e11) return value; // 毫秒
    return value * 1000; // 秒→毫秒
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (/^\d{10}$/.test(trimmed)) return parseInt(trimmed, 10) * 1000; // 秒
    if (/^\d{13}$/.test(trimmed)) return parseInt(trimmed, 10); // 毫秒

    // 尝试按本地解析
    const parsedLocal = dayjs(trimmed);
    if (parsedLocal.isValid()) return parsedLocal.valueOf();

    // 尝试按 UTC 解析再转本地（处理无时区的 UTC 字符串）
    const parsedUtc = dayjs.utc(trimmed);
    if (parsedUtc.isValid()) return parsedUtc.local().valueOf();
  }

  return null;
};

/**
 * 格式化订单时间：优先成交/更新时间，其次下单时间。默认本地时区。
 */
const formatOrderTime = (order) => {
  const fillTimeRaw = order.fillTime || order.updateTime || order.lastUpdateTime || order.timestamp || order.ts;
  const orderTimeRaw = order.orderTime;

  const fillMs = toMillis(fillTimeRaw);
  if (fillMs) {
    return dayjs(fillMs).format('YYYY-MM-DD HH:mm:ss');
  }

  const orderMs = toMillis(orderTimeRaw);
  if (orderMs) {
    return dayjs(orderMs).format('YYYY-MM-DD HH:mm:ss');
  }

  // 如果都没有，返回当前时间（作为后备，标记为本地）
  return dayjs().format('YYYY-MM-DD HH:mm:ss');
};

/**
 * 订单监控 Hook
 * 参考 backend/examples/binance_people_test.py 中的 _start_order_monitoring 方法
 * 
 * @param {Array} exchanges - 当前 Tab 的交易所配置数组
 * @param {Function} onOrderMessage - 订单消息回调函数 (message) => void
 * @param {boolean} enabled - 是否启用监控
 * @param {number} interval - 轮询间隔（毫秒），默认 60000ms (1分钟)
 * @param {Function} onLog - 日志回调 (log) => void
 * @returns {Object} { isMonitoring, monitoredOrdersCount, refreshCountdown, manualRefresh }
 */
export const useOrderMonitoring = (
  exchanges = [],
  onOrderMessage,
  enabled = true,
  interval = 60000,
  onLog = null
) => {
  // 监控的订单列表 { orderId: { last_status, last_filled, symbol, exchange, ... } }
  const monitoredOrdersRef = useRef(new Map());
  
  // 已生成消息的订单记录（用于去重）
  // key: `${orderId}_${type}_${description}`，确保同一个订单的相同消息只生成一次
  const sentMessagesRef = useRef(new Set());
  
  // 轮询定时器
  const pollingTimerRef = useRef(null);
  
  // 是否正在监控
  const [isMonitoring, setIsMonitoring] = useState(false);
  
  // 刷新间隔计数（从上次刷新开始经过的时间，毫秒）
  const [refreshCountdown, setRefreshCountdown] = useState(0);
  
  // 刷新间隔计数定时器
  const countdownTimerRef = useRef(null);
  
  // 上次刷新时间
  const lastRefreshTimeRef = useRef(null);
  
  // 使用 ref 存储最新的参数，避免依赖导致重新连接
  const exchangesRef = useRef(exchanges);
  const onOrderMessageRef = useRef(onOrderMessage);
  const enabledRef = useRef(enabled);
  const intervalRef = useRef(interval);
  const onLogRef = useRef(onLog);
  
  // 更新 refs
  useEffect(() => {
    exchangesRef.current = exchanges;
    onOrderMessageRef.current = onOrderMessage;
    enabledRef.current = enabled;
    intervalRef.current = interval;
    onLogRef.current = onLog;
  }, [exchanges, onOrderMessage, enabled, interval, onLog]);
  
  /**
   * 检查并发送消息（带去重）
   * @param {Object} message - 消息对象
   * @returns {boolean} - 是否成功发送（false表示重复，已跳过）
   */
  const sendMessageIfNotDuplicate = useCallback((message) => {
    // 生成唯一标识：orderId + type + description
    const messageKey = `${message.orderId}_${message.type}_${message.description}`;
    
    // 检查是否已发送过
    if (sentMessagesRef.current.has(messageKey)) {
      console.log('⚠️ [订单监控] 消息已发送过，跳过:', {
        orderId: message.orderId,
        type: message.type,
        description: message.description
      });
      return false;
    }
    
    // 记录已发送的消息
    sentMessagesRef.current.add(messageKey);
    
    // 发送消息
    if (onOrderMessageRef.current) {
      onOrderMessageRef.current(message);
    }
    
    return true;
  }, []);
  
  /**
   * 获取当前 Tab 相关的订单
   */
  const fetchOrders = useCallback(async () => {
    if (!enabledRef.current || exchangesRef.current.length === 0) {
      return [];
    }
    
    try {
      // 获取交易所凭证
      const credentials = getExchangeCredentials(true);
      
      if (credentials.length === 0) {
        console.warn('⚠️ [订单监控] 未配置交易所账户');
        return [];
      }
      
      // 🔍 调试日志：检查凭证中的 unifiedAccount 字段
      console.log('🔍 [订单监控] 获取到的凭证:', credentials.map(c => ({
        exchange: c.exchange,
        unifiedAccount: c.unifiedAccount,
        hasApiKey: !!c.apiKey
      })));
      
      // 统一账户去重
      const deduplicatedCredentials = credentials.reduce((acc, cred) => {
        if (cred.unifiedAccount) {
          const exists = acc.some(c => c.exchange === cred.exchange);
          if (!exists) {
            acc.push(cred);
          }
        } else {
          acc.push(cred);
        }
        return acc;
      }, []);
      
      console.log('🔍 [订单监控] 去重后的凭证:', deduplicatedCredentials.map(c => ({
        exchange: c.exchange,
        unifiedAccount: c.unifiedAccount
      })));
      
      // 从当前 Tab 的交易所配置中提取币种列表和生成交易对映射
      const baseCurrencies = [];
      const exchangeMap = new Map(); // 用于快速查找交易所配置
      const symbolPairs = {}; // {exchange: {marketType: [symbols]}}
      
      exchangesRef.current.forEach(ex => {
        const symbol = ex.symbol || '';
        let baseCurrency = '';
        
        if (symbol.includes('/')) {
          baseCurrency = symbol.split('/')[0];
        } else if (symbol) {
          baseCurrency = symbol;
        }
        
        if (baseCurrency && !baseCurrencies.includes(baseCurrency.toUpperCase())) {
          baseCurrencies.push(baseCurrency.toUpperCase());
        }
        
        // 记录交易所和币对的映射关系
        const key = `${ex.exchange}_${ex.symbol}_${ex.market_type || 'spot'}`;
        exchangeMap.set(key, ex);
      });
      
      // 根据每个交易所的配置，生成对应的交易对列表（类似持仓监控的逻辑）
      if (baseCurrencies.length > 0) {
        deduplicatedCredentials.forEach(cred => {
          const exchange = cred.exchange.toLowerCase();
          
          if (!symbolPairs[exchange]) {
            symbolPairs[exchange] = {};
          }
          
          if (cred.unifiedAccount) {
            // 统一账户：需要为现货和合约分别生成交易对
            baseCurrencies.forEach(base => {
              const spotSymbol = generateSymbol(base, exchange, 'spot');
              const futuresSymbol = generateSymbol(base, exchange, 'future');
              
              if (!symbolPairs[exchange]['spot']) {
                symbolPairs[exchange]['spot'] = [];
              }
              if (!symbolPairs[exchange]['futures']) {
                symbolPairs[exchange]['futures'] = [];
              }
              
              if (!symbolPairs[exchange]['spot'].includes(spotSymbol)) {
                symbolPairs[exchange]['spot'].push(spotSymbol);
              }
              if (!symbolPairs[exchange]['futures'].includes(futuresSymbol)) {
                symbolPairs[exchange]['futures'].push(futuresSymbol);
              }
            });
          } else {
            // 分离账户：需要为现货和合约分别生成交易对
            baseCurrencies.forEach(base => {
              const spotSymbol = generateSymbol(base, exchange, 'spot');
              const futuresSymbol = generateSymbol(base, exchange, 'future');
              
              if (!symbolPairs[exchange]['spot']) {
                symbolPairs[exchange]['spot'] = [];
              }
              if (!symbolPairs[exchange]['futures']) {
                symbolPairs[exchange]['futures'] = [];
              }
              
              if (!symbolPairs[exchange]['spot'].includes(spotSymbol)) {
                symbolPairs[exchange]['spot'].push(spotSymbol);
              }
              if (!symbolPairs[exchange]['futures'].includes(futuresSymbol)) {
                symbolPairs[exchange]['futures'].push(futuresSymbol);
              }
            });
          }
        });
      }
      
      console.log(`📊 [订单监控] 生成的交易对映射:`, symbolPairs);
      
      // 调用后端 API 获取订单（传递交易对映射，而不是基础货币列表）
      const response = await fetch('/api/orders/by-symbols', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbols: baseCurrencies, // 保留向后兼容
          symbolPairs: Object.keys(symbolPairs).length > 0 ? symbolPairs : undefined, // 传递交易对映射
          credentials: deduplicatedCredentials
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 🔍 详细调试日志
      console.log('🔍 [订单监控] API 响应:', {
        success: data.success,
        total: data.total,
        ordersCount: data.data?.length || 0,
        baseCurrencies: baseCurrencies,
        symbolPairs: symbolPairs,
        exchangeMapKeys: Array.from(exchangeMap.keys()),
        firstOrder: data.data?.[0]
      });
      
      // 🔍 统计订单的市场类型分布
      if (data.data && data.data.length > 0) {
        const spotOrders = data.data.filter(o => (o.order_type || o.marketType || 'spot') === 'spot');
        const futuresOrders = data.data.filter(o => (o.order_type || o.marketType || 'spot') === 'futures' || (o.order_type || o.marketType || 'spot') === 'future');
        console.log('📊 [订单监控] 订单市场类型分布:', {
          现货: spotOrders.length,
          合约: futuresOrders.length,
          总计: data.data.length
        });
        
        // 如果有合约订单，显示示例
        if (futuresOrders.length > 0) {
          console.log('📋 [订单监控] 合约订单示例:', futuresOrders.slice(0, 3));
        }
      }
      
      if (data.success && data.data) {
        // 🔧 标准化 symbol 的辅助函数：去掉合约的 :USDT 后缀
        const normalizeSymbol = (symbol) => {
          if (!symbol) return symbol;
          // 去掉合约的 :USDT 或 :USD 后缀（如 PEOPLE/USDT:USDT -> PEOPLE/USDT）
          return symbol.replace(/:(USDT|USD|USDC|BUSD|FDUSD)$/, '');
        };
        
        // 构建交易所和币种的集合，用于宽松匹配（标准化后的 symbol）
        const exchangeSymbolSet = new Set();
        exchangesRef.current.forEach(ex => {
          const normalizedSymbol = normalizeSymbol(ex.symbol);
          exchangeSymbolSet.add(`${ex.exchange}_${normalizedSymbol}`);
        });
        
        // 同时构建一个包含原始 symbol 和标准化 symbol 的 exchangeMap（用于严格匹配）
        const normalizedExchangeMap = new Map();
        exchangeMap.forEach((value, key) => {
          // key 格式：exchange_symbol_marketType（symbol 可能包含 /，但不会包含 _）
          // 例如：binance_PEOPLE/USDT_futures
          const lastUnderscoreIndex = key.lastIndexOf('_');
          if (lastUnderscoreIndex > 0) {
            const prefix = key.substring(0, lastUnderscoreIndex); // exchange_symbol
            const marketType = key.substring(lastUnderscoreIndex + 1); // marketType
            
            // 从 prefix 中分离 exchange 和 symbol
            const firstUnderscoreIndex = prefix.indexOf('_');
            if (firstUnderscoreIndex > 0) {
              const exchange = prefix.substring(0, firstUnderscoreIndex);
              const originalSymbol = prefix.substring(firstUnderscoreIndex + 1);
              const normalizedSymbol = normalizeSymbol(originalSymbol);
              const normalizedKey = `${exchange}_${normalizedSymbol}_${marketType}`;
              normalizedExchangeMap.set(normalizedKey, value);
            }
          }
          // 同时保留原始 key（以防万一）
          normalizedExchangeMap.set(key, value);
        });
        
        // 🔍 调试：打印所有可用的匹配键
        console.log('🔍 [订单监控] 可用的严格匹配键:', Array.from(normalizedExchangeMap.keys()));
        console.log('🔍 [订单监控] 可用的宽松匹配键:', Array.from(exchangeSymbolSet));
        
        // 过滤出当前 Tab 相关的订单（匹配交易所和币对）
        const relevantOrders = data.data.filter(order => {
          // 订单中的字段可能是 order_type 或 marketType
          const orderMarketType = order.order_type || order.marketType || 'spot';
          
          // 🔧 标准化订单的 symbol（去掉 :USDT 后缀）
          const normalizedOrderSymbol = normalizeSymbol(order.symbol);
          
          // 严格匹配：交易所 + 币对（标准化后）+ 市场类型
          const strictKey = `${order.exchange}_${normalizedOrderSymbol}_${orderMarketType}`;
          const strictMatch = normalizedExchangeMap.has(strictKey);
          
          if (strictMatch) {
            console.log('✅ [订单监控] 订单通过严格匹配:', {
              orderId: order.orderId,
              exchange: order.exchange,
              symbol: order.symbol,
              normalizedSymbol: normalizedOrderSymbol,
              marketType: orderMarketType,
              strictKey: strictKey
            });
            return true;
          }
          
          // 宽松匹配：只匹配交易所和币对（标准化后，忽略市场类型）
          // 这可以处理 unified 账户的情况，以及只配置了现货但后端返回了合约订单的情况
          const looseKey = `${order.exchange}_${normalizedOrderSymbol}`;
          const looseMatch = exchangeSymbolSet.has(looseKey);
          
          if (looseMatch) {
            // 如果宽松匹配成功，记录日志以便调试
            console.log('✅ [订单监控] 订单通过宽松匹配:', {
              orderId: order.orderId,
              exchange: order.exchange,
              symbol: order.symbol,
              normalizedSymbol: normalizedOrderSymbol,
              marketType: orderMarketType,
              looseKey: looseKey
            });
            return true;
          }
          
          // 如果没匹配上，打印详细信息用于调试
          console.log('❌ [订单监控] 订单未匹配:', {
            orderId: order.orderId,
            strictKey: strictKey,
            looseKey: looseKey,
            orderExchange: order.exchange,
            orderSymbol: order.symbol,
            normalizedOrderSymbol: normalizedOrderSymbol,
            orderMarketType: orderMarketType,
            orderOrderType: order.order_type,
            orderMarketTypeField: order.marketType,
            availableStrictKeys: Array.from(normalizedExchangeMap.keys()),
            availableLooseKeys: Array.from(exchangeSymbolSet)
          });
          
          return false;
        });
        
        console.log(`📊 [订单监控] 获取到 ${data.data.length} 个订单，过滤后 ${relevantOrders.length} 个相关订单`);
        
        // 如果过滤后没有订单，但 API 返回了订单，打印更多调试信息
        if (relevantOrders.length === 0 && data.data.length > 0) {
          console.warn('⚠️ [订单监控] 过滤后没有订单，可能的原因：', {
            api返回订单数: data.data.length,
            配置的交易所: exchangesRef.current.map(ex => ({
              exchange: ex.exchange,
              symbol: ex.symbol,
              market_type: ex.market_type || 'spot'
            })),
            实际订单示例: data.data.slice(0, 3).map(order => ({
              exchange: order.exchange,
              symbol: order.symbol,
              order_type: order.order_type,
              marketType: order.marketType
            }))
          });
        }
        
        // 记录成功日志（系统操作）
        if (onLogRef.current) {
          onLogRef.current({
            type: 'order_fetch',
            status: 'success',
            message: `获取订单成功: ${relevantOrders.length} 个订单`,
            source: 'system'
          });
        }
        
        return relevantOrders;
      }
      
      if (!data.success) {
        console.error('❌ [订单监控] API 返回失败:', data);
        // 记录失败日志（系统操作）
        if (onLogRef.current) {
          onLogRef.current({
            type: 'order_fetch',
            status: 'error',
            message: `获取订单失败: ${data.message || 'API 返回失败'}`,
            source: 'system'
          });
        }
      }
      
      return [];
    } catch (error) {
      console.error('❌ [订单监控] 获取订单失败:', {
        error: error.message,
        stack: error.stack,
        exchanges: exchangesRef.current.map(ex => ({
          exchange: ex.exchange,
          symbol: ex.symbol,
          market_type: ex.market_type
        }))
      });
      
      // 记录失败日志（系统操作）
      if (onLogRef.current) {
        onLogRef.current({
          type: 'order_fetch',
          status: 'error',
          message: `获取订单失败: ${error.message || '未知错误'}`,
          source: 'system'
        });
      }
      
      return [];
    }
  }, []);
  
  /**
   * 更新刷新时间并重置计数
   */
  const updateRefreshTime = useCallback(() => {
    lastRefreshTimeRef.current = Date.now();
    setRefreshCountdown(0);
  }, []);

  /**
   * 检查订单状态变化并生成消息
   */
  const checkOrderChanges = useCallback(async () => {
    if (!enabledRef.current) {
      return;
    }
    
    try {
      // 更新刷新时间
      updateRefreshTime();
      // 获取当前订单列表
      const currentOrders = await fetchOrders();
      
      // 如果没有监控的订单，初始化监控列表
      if (monitoredOrdersRef.current.size === 0) {
        let monitoredCount = 0;
        let closedOrdersCount = 0;
        
        // 用于记录已处理的已关闭订单，避免重复生成消息
        const processedClosedOrders = new Set();
        
        currentOrders.forEach(order => {
          const status = order.status?.toLowerCase() || 'unknown';
          const isClosed = ['closed', 'canceled', 'expired', 'rejected'].includes(status);
          
          if (isClosed) {
            // 对于已关闭的订单，只生成一次消息（初始化时）
            const orderKey = `${order.orderId}_${status}`;
            if (!processedClosedOrders.has(orderKey)) {
              processedClosedOrders.add(orderKey);
              closedOrdersCount++;
              const statusMap = {
                'closed': '已成交',
                'canceled': '已取消',
                'expired': '已过期',
                'rejected': '已拒绝'
              };
              const statusText = statusMap[status] || status;
              
              // 获取市场类型：优先使用 order_type，然后是 marketType，最后默认为 'spot'
              const marketType = order.order_type || order.marketType || 'spot';
              
              const message = {
                id: `init_closed_${order.orderId}_${Date.now()}`,
                time: formatOrderTime(order),
                exchange: order.exchange,
                symbol: order.symbol,
                type: status === 'closed' ? 'filled' : 
                      status === 'canceled' ? 'cancelled' : 'other',
                side: order.side,
                amount: order.amount,
                price: order.price,
                orderId: String(order.orderId),
                description: `订单状态: ${statusText}`,
                marketType: marketType
              };
              
              // 调试日志：检查市场类型
              if (order.orderId && (!order.order_type && !order.marketType)) {
                console.warn('⚠️ [订单监控] 订单缺少市场类型字段:', {
                  orderId: order.orderId,
                  exchange: order.exchange,
                  symbol: order.symbol,
                  orderKeys: Object.keys(order)
                });
              }
              
              sendMessageIfNotDuplicate(message);
            }
          } else {
            // 只监控未关闭的订单
            monitoredOrdersRef.current.set(order.orderId, {
              last_status: status,
              last_filled: order.filled || 0,
              symbol: order.symbol,
              exchange: order.exchange,
              order_type: order.order_type || order.marketType,
              side: order.side,
              amount: order.amount,
              price: order.price
            });
            monitoredCount++;

            // 初始化阶段也生成一条“已创建”消息，避免页面空白
            const marketType = order.order_type || order.marketType || 'spot';
            const initMessage = {
              id: `init_open_${order.orderId}_${Date.now()}`,
              time: formatOrderTime(order),
              exchange: order.exchange,
              symbol: order.symbol,
              type: 'created',
              side: order.side,
              amount: order.amount,
              price: order.price,
              orderId: String(order.orderId),
              description: '订单初始化: 待成交',
              marketType
            };
            sendMessageIfNotDuplicate(initMessage);
          }
        });
        
        console.log(`📋 [订单监控] 初始化监控列表: ${monitoredCount} 个未关闭订单，${closedOrdersCount} 个已关闭订单`);
        
        // 初始化完成后直接返回，避免重复处理已关闭的订单
        return;
      }
      
      // 检查每个监控的订单
      const ordersToRemove = [];
      
      monitoredOrdersRef.current.forEach((orderInfo, orderId) => {
        // 在当前订单列表中查找该订单
        const currentOrder = currentOrders.find(o => String(o.orderId) === String(orderId));
        
        if (!currentOrder) {
          // 订单不存在，可能已关闭，从监控列表中移除
          ordersToRemove.push(orderId);
          return;
        }
        
        const lastStatus = orderInfo.last_status;
        const currentStatus = (currentOrder.status?.toLowerCase() || 'unknown');
        const lastFilled = orderInfo.last_filled || 0;
        const currentFilled = currentOrder.filled || 0;
        
        // 检查状态变化
        if (currentStatus !== lastStatus) {
          const statusMap = {
            'open': '待成交',
            'closed': '已成交',
            'canceled': '已取消',
            'expired': '已过期',
            'rejected': '已拒绝'
          };
          
          const statusText = statusMap[currentStatus] || currentStatus;
          
          // 获取市场类型：优先使用当前订单的字段，然后是监控信息中的字段，最后默认为 'spot'
          const marketType = currentOrder.order_type || currentOrder.marketType || orderInfo.order_type || 'spot';
          
          // 生成消息
          const message = {
            id: `status_${orderId}_${Date.now()}`,
            time: formatOrderTime(currentOrder),
            exchange: currentOrder.exchange,
            symbol: currentOrder.symbol,
            type: currentStatus === 'closed' ? 'filled' : 
                  currentStatus === 'canceled' ? 'cancelled' : 
                  currentStatus === 'open' ? 'created' : 'partial_filled',
            side: currentOrder.side || orderInfo.side,
            amount: currentOrder.amount || orderInfo.amount,
            price: currentOrder.price || orderInfo.price,
            orderId: String(orderId),
            description: `订单状态变化: ${statusText}`,
            marketType: marketType
          };
          
          // 发送消息（带去重）
          sendMessageIfNotDuplicate(message);
          
          // 更新监控信息
          orderInfo.last_status = currentStatus;
          
          // 如果订单已关闭，标记为待移除
          if (['closed', 'canceled', 'expired', 'rejected'].includes(currentStatus)) {
            ordersToRemove.push(orderId);
          }
        }
        
        // 检查成交数量变化
        if (Math.abs(currentFilled - lastFilled) > 0.00000001) {
          const filledChange = currentFilled - lastFilled;
          const orderAmount = currentOrder.amount || orderInfo.amount;
          const isAlmostFilled = currentFilled >= orderAmount * 0.99;
          
          // 获取市场类型：优先使用当前订单的字段，然后是监控信息中的字段，最后默认为 'spot'
          const marketType = currentOrder.order_type || currentOrder.marketType || orderInfo.order_type || 'spot';
          
          // 生成消息
          const message = {
            id: `filled_${orderId}_${Date.now()}`,
            time: formatOrderTime(currentOrder),
            exchange: currentOrder.exchange,
            symbol: currentOrder.symbol,
            type: isAlmostFilled ? 'filled' : 'partial_filled',
            side: currentOrder.side || orderInfo.side,
            amount: filledChange,
            price: currentOrder.price || orderInfo.price,
            orderId: String(orderId),
            description: `成交更新: +${filledChange.toFixed(8)} (已成交: ${currentFilled.toFixed(8)}/${orderAmount.toFixed(8)})`,
            marketType: marketType
          };
          
          // 发送消息（带去重）
          sendMessageIfNotDuplicate(message);
          
          // 更新监控信息
          orderInfo.last_filled = currentFilled;
        }
      });
      
      // 移除已关闭的订单
      ordersToRemove.forEach(orderId => {
        monitoredOrdersRef.current.delete(orderId);
      });
      
      // 检查是否有新订单需要监控
      currentOrders.forEach(order => {
        const orderId = order.orderId;
        const status = (order.status?.toLowerCase() || 'unknown');
        const isClosed = ['closed', 'canceled', 'expired', 'rejected'].includes(status);
        
        // 如果是新订单（不在监控列表中）
        if (!monitoredOrdersRef.current.has(orderId)) {
          if (isClosed) {
            // 对于已关闭的新订单，生成一条消息通知用户
            const statusMap = {
              'closed': '已成交',
              'canceled': '已取消',
              'expired': '已过期',
              'rejected': '已拒绝'
            };
            const statusText = statusMap[status] || status;
            
            // 获取市场类型：优先使用 order_type，然后是 marketType，最后默认为 'spot'
            const marketType = order.order_type || order.marketType || 'spot';
            
            const message = {
              id: `new_closed_${orderId}_${Date.now()}`,
              time: formatOrderTime(order),
              exchange: order.exchange,
              symbol: order.symbol,
              type: status === 'closed' ? 'filled' : 
                    status === 'canceled' ? 'cancelled' : 'other',
              side: order.side,
              amount: order.amount,
              price: order.price,
              orderId: String(orderId),
              description: `新订单: ${statusText}`,
              marketType: marketType
            };
            
            console.log('📨 [订单监控] 生成已关闭新订单消息:', {
              orderId: message.orderId,
              symbol: message.symbol,
              exchange: message.exchange,
              marketType: message.marketType
            });
            
            sendMessageIfNotDuplicate(message);
          } else {
            // 未关闭的订单，添加到监控列表
            monitoredOrdersRef.current.set(orderId, {
              last_status: status,
              last_filled: order.filled || 0,
              symbol: order.symbol,
              exchange: order.exchange,
              order_type: order.order_type,
              side: order.side,
              amount: order.amount,
              price: order.price
            });
            
            // 生成新订单消息
            // 获取市场类型：优先使用 order_type，然后是 marketType，最后默认为 'spot'
            const marketType = order.order_type || order.marketType || 'spot';
            
            const message = {
              id: `new_${orderId}_${Date.now()}`,
              time: formatOrderTime(order),
              exchange: order.exchange,
              symbol: order.symbol,
              type: 'created',
              side: order.side,
              amount: order.amount,
              price: order.price,
              orderId: String(orderId),
              description: '新订单已创建',
              marketType: marketType
            };
            
            console.log('📨 [订单监控] 生成新订单消息:', {
              orderId: message.orderId,
              symbol: message.symbol,
              exchange: message.exchange,
              marketType: message.marketType
            });
            
            sendMessageIfNotDuplicate(message);
          }
        }
      });
      
    } catch (error) {
      console.error('❌ [订单监控] 检查订单变化失败:', error);
    }
  }, [fetchOrders, updateRefreshTime]);
  
  /**
   * 启动监控
   */
  const startMonitoring = useCallback(() => {
    if (!enabledRef.current || exchangesRef.current.length === 0) {
      console.log('⚠️ [订单监控] 未启用或没有交易所配置');
      return;
    }
    
    if (pollingTimerRef.current) {
      console.log('⚠️ [订单监控] 已经在监控中');
      return; // 已经在监控中
    }
    
    setIsMonitoring(true);
    console.log(`🔄 [订单监控] 开始监控订单状态变化... (间隔: ${intervalRef.current}ms, 交易所: ${exchangesRef.current.length}个)`);
    
    // 立即执行一次检查
    checkOrderChanges();
    
    // 设置定时轮询
    pollingTimerRef.current = setInterval(() => {
      checkOrderChanges();
    }, intervalRef.current);
  }, [checkOrderChanges]);
  
  /**
   * 停止监控
   */
  const stopMonitoring = useCallback(() => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
      setIsMonitoring(false);
      console.log('⏹️ [订单监控] 停止监控');
    }
  }, []);
  
  /**
   * 清空监控列表
   */
  const clearMonitoredOrders = useCallback(() => {
    monitoredOrdersRef.current.clear();
  }, []);

  /**
   * 手动刷新订单
   */
  const manualRefresh = useCallback(() => {
    if (!enabledRef.current) {
      console.log('⚠️ [订单监控] 未启用，无法刷新');
      return;
    }
    console.log('🔄 [订单监控] 手动刷新订单');
    checkOrderChanges();
  }, [checkOrderChanges]);

  // 刷新间隔计数定时器（每秒更新一次）
  useEffect(() => {
    if (!isMonitoring || !lastRefreshTimeRef.current) {
      return;
    }

    countdownTimerRef.current = setInterval(() => {
      if (lastRefreshTimeRef.current) {
        const elapsed = Date.now() - lastRefreshTimeRef.current;
        setRefreshCountdown(elapsed);
      }
    }, 1000); // 每秒更新一次

    return () => {
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
    };
  }, [isMonitoring]);
  
  // 当 enabled、exchanges 或 interval 变化时，重新启动监控
  useEffect(() => {
    // 先停止旧的监控
    stopMonitoring();
    
    // 清空监控列表（因为币对可能已切换）
    clearMonitoredOrders();
    
    // 清空已发送消息记录（避免去重问题）
    sentMessagesRef.current.clear();
    
    console.log('🔄 [订单监控] 交易所配置已变化，清空监控列表和消息记录');
    
    // 如果启用且有交易所配置，重新启动监控
    if (enabled && exchanges.length > 0) {
      // 延迟启动，确保旧的定时器已清理
      const timer = setTimeout(() => {
        startMonitoring();
      }, 100);
      
      return () => {
        clearTimeout(timer);
        stopMonitoring();
      };
    }
    
    return () => {
      stopMonitoring();
    };
  }, [enabled, JSON.stringify(exchanges), interval, startMonitoring, stopMonitoring, clearMonitoredOrders]);
  
  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopMonitoring();
      clearMonitoredOrders();
    };
  }, [stopMonitoring, clearMonitoredOrders]);
  
  return {
    isMonitoring,
    monitoredOrdersCount: monitoredOrdersRef.current.size,
    refreshCountdown, // 刷新间隔计数（毫秒）
    startMonitoring,
    stopMonitoring,
    clearMonitoredOrders,
    manualRefresh // 手动刷新函数
  };
};

