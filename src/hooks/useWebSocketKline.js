import { useEffect, useRef, useCallback, useState } from 'react';

/**
 * WebSocket 实时 K 线数据 Hook
 * 
 * @param {Array} exchanges - 交易所配置数组
 * @param {string} interval - K 线周期
 * @param {Function} onKlineUpdate - K 线更新回调 (exchange, symbol, kline, marketType) => void
 * @param {boolean} enabled - 是否启用实时数据
 * @returns {Object} { connected, error, reconnect }
 */
export const useWebSocketKline = (exchanges, interval, onKlineUpdate, enabled = true) => {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const subscriptionsRef = useRef(new Set());
  
  // 使用 ref 存储最新的参数，避免依赖导致重新连接
  const exchangesRef = useRef(exchanges);
  const intervalRef = useRef(interval);
  const onKlineUpdateRef = useRef(onKlineUpdate);
  const enabledRef = useRef(enabled);
  
  // 更新 refs
  useEffect(() => {
    console.log('🔄 更新 refs - exchanges 数量:', exchanges.length, exchanges);
    exchangesRef.current = exchanges;
    intervalRef.current = interval;
    onKlineUpdateRef.current = onKlineUpdate;
    enabledRef.current = enabled;
  }, [exchanges, interval, onKlineUpdate, enabled]);
  
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  /**
   * 订阅交易所数据
   */
  const subscribe = useCallback((exchange, symbol, intervalParam, marketType = 'spot') => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法订阅');
      return;
    }

    const subscriptionKey = `${exchange}_${symbol}_${intervalParam}_${marketType}`;
    
    // 避免重复订阅
    if (subscriptionsRef.current.has(subscriptionKey)) {
      console.log(`⚠️ 跳过重复订阅: ${subscriptionKey}`);
      return;
    }

    const message = {
      type: 'subscribe',
      data: {
        exchange_a: exchange,
        exchange_b: null,  // 单独订阅
        symbol: symbol,
        interval: intervalParam,
        market_type: marketType
      }
    };

    console.log(`📊 发送订阅请求: ${subscriptionKey}`, message);
    ws.send(JSON.stringify(message));
    subscriptionsRef.current.add(subscriptionKey);
    console.log(`✅ 订阅成功: ${subscriptionKey}`);
  }, []);

  /**
   * 取消订阅交易所数据
   */
  const unsubscribe = useCallback((exchange, symbol, intervalParam, marketType = 'spot') => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法取消订阅');
      return;
    }

    const subscriptionKey = `${exchange}_${symbol}_${intervalParam}_${marketType}`;
    
    // 检查是否已订阅
    if (!subscriptionsRef.current.has(subscriptionKey)) {
      console.log(`⚠️ 未订阅该数据: ${subscriptionKey}`);
      return;
    }

    const message = {
      type: 'unsubscribe',
      data: {
        exchange_a: exchange,
        symbol: symbol,
        interval: intervalParam,
        market_type: marketType
      }
    };

    console.log(`❌ 发送取消订阅请求: ${subscriptionKey}`, message);
    ws.send(JSON.stringify(message));
    subscriptionsRef.current.delete(subscriptionKey);
    console.log(`✅ 取消订阅成功: ${subscriptionKey}`);
  }, []);

  /**
   * 建立 WebSocket 连接
   * @param {boolean} force - 是否强制连接（忽略 enabled 检查）
   */
  const connect = useCallback((force = false) => {
    // 只有非强制模式才检查 enabled
    if (!force && !enabledRef.current) {
      return;
    }
    
    // 如果已经有打开的连接，不要重复创建
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // 使用相对路径，让 Vite 代理处理 WebSocket 连接
      // 在开发环境中，Vite 会将 ws://localhost:5173/ws 代理到后端的 WebSocket 服务
      const wsUrl = import.meta.env.DEV 
        ? `ws://${window.location.host}/ws`
        : `ws://${window.location.host}/ws`;
      
      console.log('🔌 正在连接 WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket 已连接');
        setConnected(true);
        setError(null);
        
        // 重新订阅所有交易所
        subscriptionsRef.current.clear();
        // 使用 ref 来访问最新的 exchanges 和 interval
        const currentExchanges = exchangesRef.current;
        const currentInterval = intervalRef.current;
        
        console.log('📋 准备订阅的交易所数量:', currentExchanges.length);
        console.log('📋 交易所列表:', currentExchanges);
        
        currentExchanges.forEach((config, index) => {
          console.log(`[${index}] 正在订阅:`, config.exchange, config.symbol, currentInterval, config.market_type || 'spot');
          subscribe(config.exchange, config.symbol, currentInterval, config.market_type || 'spot');
        });
        
        console.log('📋 订阅完成，总计:', subscriptionsRef.current.size);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'kline_update') {
            const { exchange, symbol, interval: msgInterval, market_type, kline } = message.data;
            
            // ✅ 精确匹配：使用消息中的 interval（如果有）或当前 interval
            const actualInterval = msgInterval || intervalRef.current;
            const key = `${exchange}_${symbol}_${actualInterval}_${market_type || 'spot'}`;
            
            // ✅ 过滤：只处理已订阅的数据
            if (!subscriptionsRef.current.has(key)) {
              console.log(`⏭️ [Kline] 跳过未订阅的数据: ${key} (消息 interval: ${msgInterval})`);
              return;
            }
            
            // 使用 ref 来访问最新的回调，传递 market_type
            onKlineUpdateRef.current?.(exchange, symbol, kline, market_type || 'spot');
          } else if (message.type === 'subscription_confirmed') {
            console.log('📡 订阅确认:', message.data);
          } else if (message.type === 'unsubscription_confirmed') {
            console.log('📡 取消订阅确认:', message.data);
          }
        } catch (err) {
          console.error('WebSocket 消息解析失败:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket 错误:', event);
        setError('WebSocket 连接错误');
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket 已断开');
        setConnected(false);
        wsRef.current = null;
        
        // 自动重连（3秒后）- 只在 enabled 时
        if (enabledRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            console.log('🔄 尝试重新连接...');
            connect();
          }, 3000);
        }
      };

    } catch (err) {
      console.error('WebSocket 连接失败:', err);
      setError(err.message);
    }
  }, [subscribe]);

  /**
   * 手动重连 - 强制重连，不检查 enabled 状态
   */
  const reconnect = useCallback(() => {
    console.log('🔄 手动重连...');
    
    // 清除自动重连定时器
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    // 关闭现有连接
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // 强制重连（忽略 enabled 检查）
    connect(true);
  }, [connect]);

  /**
   * 监听交易所列表和周期变化，智能订阅/取消订阅
   */
  useEffect(() => {
    if (!connected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    // 计算当前应该订阅的列表
    const currentSubscriptions = new Set(
      exchanges.map(config => `${config.exchange}_${config.symbol}_${interval}_${config.market_type || 'spot'}`)
    );

    // ✅ 找出需要取消的订阅（旧订阅但不在新列表中）
    const toRemove = Array.from(subscriptionsRef.current).filter(key => !currentSubscriptions.has(key));
    
    // ✅ 找出需要新增的订阅（新列表中但未订阅）
    const toAdd = Array.from(currentSubscriptions).filter(key => !subscriptionsRef.current.has(key));
    
    // ✅ 取消旧订阅（释放后端资源）
    toRemove.forEach(key => {
      const parts = key.split('_');
      // 处理 symbol 可能包含下划线的情况（如 BTC_USDT）
      const exchange = parts[0];
      const marketType = parts[parts.length - 1];
      const intervalParam = parts[parts.length - 2];
      const symbol = parts.slice(1, parts.length - 2).join('_');
      
      console.log(`❌ 取消旧订阅: ${key}`);
      unsubscribe(exchange, symbol, intervalParam, marketType);
    });
    
    // ✅ 添加新订阅
    toAdd.forEach(key => {
      const parts = key.split('_');
      const exchange = parts[0];
      const marketType = parts[parts.length - 1];
      const intervalParam = parts[parts.length - 2];
      const symbol = parts.slice(1, parts.length - 2).join('_');
      
      console.log(`➕ 添加新订阅: ${key}`);
      subscribe(exchange, symbol, intervalParam, marketType);
    });
  }, [exchanges, interval, connected, subscribe, unsubscribe]);

  /**
   * 初始连接 - 只在组件挂载时执行一次
   */
  useEffect(() => {
    if (!enabled) return;
    
    // 如果已经有连接，不要重复创建
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }
    
    connect();

    return () => {
      // 清理定时器
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      
      // 关闭连接
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      setConnected(false);
    };
  }, []); // 空依赖数组，只在挂载时执行
  
  /**
   * 监听 enabled 状态变化
   */
  useEffect(() => {
    if (!enabled && wsRef.current) {
      // 关闭连接
      wsRef.current.close();
      wsRef.current = null;
      setConnected(false);
      
      // 清理定时器
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    } else if (enabled && !wsRef.current) {
      // 重新连接
      connect();
    }
  }, [enabled, connect]);

  return {
    connected,
    error,
    reconnect,
  };
};

