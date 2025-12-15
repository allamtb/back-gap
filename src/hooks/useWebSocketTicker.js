import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket 实时 Ticker 数据 Hook
 * 
 * @param {Array} exchanges - 交易所配置数组
 * @param {Function} onTickerUpdate - ticker更新回调 (exchange, symbol, marketType, ticker) => void
 * @param {boolean} enabled - 是否启用实时数据
 * @param {Function} onLog - 日志回调 (log) => void
 * @returns {Object} { connected, error, reconnect, tickerData }
 */
export const useWebSocketTicker = (exchanges, onTickerUpdate, enabled = true, onLog = null) => {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const subscriptionsRef = useRef(new Set());
  
  // 使用 ref 存储最新的参数
  const exchangesRef = useRef(exchanges);
  const onTickerUpdateRef = useRef(onTickerUpdate);
  const enabledRef = useRef(enabled);
  const onLogRef = useRef(onLog);
  
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [tickerData, setTickerData] = useState({});

  // 更新 refs
  useEffect(() => {
    exchangesRef.current = exchanges;
    onTickerUpdateRef.current = onTickerUpdate;
    enabledRef.current = enabled;
    onLogRef.current = onLog;
  }, [exchanges, onTickerUpdate, enabled, onLog]);

  /**
   * 订阅 ticker 数据
   */
  const subscribe = useCallback((exchange, symbol, marketType = 'spot') => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法订阅 ticker');
      return;
    }

    const subscriptionKey = `${exchange}_${symbol}_${marketType}`;
    
    if (subscriptionsRef.current.has(subscriptionKey)) {
      console.log(`⚠️ 跳过重复订阅 ticker: ${subscriptionKey}`);
      return;
    }

    const message = {
      type: 'subscribe_ticker',
      data: {
        exchange: exchange,
        symbol: symbol,
        market_type: marketType,
      }
    };

    console.log(`📈 发送 ticker 订阅请求: ${subscriptionKey}`, message);
    ws.send(JSON.stringify(message));
    subscriptionsRef.current.add(subscriptionKey);
    console.log(`✅ Ticker 订阅成功: ${subscriptionKey}`);
  }, []);

  /**
   * 取消订阅 ticker 数据
   */
  const unsubscribe = useCallback((exchange, symbol, marketType = 'spot') => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法取消订阅 ticker');
      return;
    }

    const subscriptionKey = `${exchange}_${symbol}_${marketType}`;
    
    if (!subscriptionsRef.current.has(subscriptionKey)) {
      console.log(`⚠️ 未订阅该 ticker: ${subscriptionKey}`);
      return;
    }

    const message = {
      type: 'unsubscribe_ticker',
      data: {
        exchange: exchange,
        symbol: symbol,
        market_type: marketType
      }
    };

    console.log(`❌ 发送取消 ticker 订阅请求: ${subscriptionKey}`, message);
    ws.send(JSON.stringify(message));
    subscriptionsRef.current.delete(subscriptionKey);
    console.log(`✅ 取消 ticker 订阅成功: ${subscriptionKey}`);
  }, []);

  /**
   * 建立 WebSocket 连接
   */
  const connect = useCallback((force = false) => {
    if (!force && !enabledRef.current) {
      return;
    }
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = import.meta.env.DEV 
        ? `ws://${window.location.host}/ws`
        : `ws://${window.location.host}/ws`;
      
      console.log('🔌 正在连接 WebSocket (Ticker):', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket (Ticker) 已连接');
        setConnected(true);
        setError(null);
        
        // 记录连接成功日志（系统操作）
        if (onLogRef.current) {
          onLogRef.current({
            type: 'websocket_connect',
            status: 'success',
            message: 'WebSocket (Ticker) 已连接',
            source: 'system'
          });
        }
        
        subscriptionsRef.current.clear();
        const currentExchanges = exchangesRef.current;
        
        console.log('📋 准备订阅 ticker 的交易所数量:', currentExchanges.length);
        
        currentExchanges.forEach((config) => {
          subscribe(config.exchange, config.symbol, config.market_type || 'spot');
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('🔍 [Ticker] 收到 WebSocket 消息:', message.type, message);
          
          if (message.type === 'ticker_update') {
            const { exchange, symbol, market_type, ticker } = message.data;
            const key = `${exchange}_${symbol}_${market_type}`;
            
            // ✅ 过滤：只处理已订阅的数据
            if (!subscriptionsRef.current.has(key)) {
              console.log(`⏭️ [Ticker] 跳过未订阅的数据: ${key}`);
              return;
            }
            
            console.log('📊 [Ticker] 收到数据:', { exchange, symbol, market_type, ticker, key });
            
            // 更新本地 ticker 数据
            setTickerData(prev => {
              const newData = {
                ...prev,
                [key]: {
                  price: ticker.last || ticker.price,
                  time: ticker.timestamp || Date.now(),
                  volume: ticker.volume,
                  change: ticker.change,
                  changePercent: ticker.percentage,
                },
              };
              console.log('📊 [Ticker] 更新后的 tickerData:', newData);
              return newData;
            });
            
            // 回调
            onTickerUpdateRef.current?.(exchange, symbol, market_type, ticker);
          } else if (message.type === 'ticker_subscription_confirmed') {
            console.log('📡 Ticker 订阅确认:', message.data);
          }
        } catch (err) {
          console.error('WebSocket ticker 消息解析失败:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket (Ticker) 错误:', event);
        setError('WebSocket Ticker 连接错误');
        
        // 记录错误日志（系统操作）
        if (onLogRef.current) {
          onLogRef.current({
            type: 'websocket_error',
            status: 'error',
            message: 'WebSocket (Ticker) 连接错误',
            source: 'system'
          });
        }
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket (Ticker) 已断开');
        setConnected(false);
        wsRef.current = null;
        
        // 记录断开日志（系统操作）
        if (onLogRef.current) {
          onLogRef.current({
            type: 'websocket_disconnect',
            status: 'error',
            message: 'WebSocket (Ticker) 已断开',
            source: 'system'
          });
        }
        
        if (enabledRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            console.log('🔄 尝试重新连接 ticker...');
            connect();
          }, 3000);
        }
      };

    } catch (err) {
      console.error('WebSocket ticker 连接失败:', err);
      setError(err.message);
    }
  }, [subscribe]);

  /**
   * 手动重连
   */
  const reconnect = useCallback(() => {
    console.log('🔄 手动重连 ticker...');
    
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    connect(true);
  }, [connect]);

  /**
   * 监听交易所列表变化，智能订阅/取消订阅
   */
  useEffect(() => {
    if (!connected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const currentSubscriptions = new Set(
      exchanges.map(config => `${config.exchange}_${config.symbol}_${config.market_type || 'spot'}`)
    );

    // ✅ 找出需要取消的订阅
    const toRemove = Array.from(subscriptionsRef.current).filter(key => !currentSubscriptions.has(key));
    
    // ✅ 找出需要新增的订阅
    const toAdd = Array.from(currentSubscriptions).filter(key => !subscriptionsRef.current.has(key));
    
    // ✅ 取消旧订阅
    toRemove.forEach(key => {
      const parts = key.split('_');
      const exchange = parts[0];
      const marketType = parts[parts.length - 1];
      const symbol = parts.slice(1, parts.length - 1).join('_');
      
      console.log(`❌ 取消旧 ticker 订阅: ${key}`);
      unsubscribe(exchange, symbol, marketType);
    });
    
    // ✅ 添加新订阅
    toAdd.forEach(key => {
      const parts = key.split('_');
      const exchange = parts[0];
      const marketType = parts[parts.length - 1];
      const symbol = parts.slice(1, parts.length - 1).join('_');
      
      console.log(`➕ 添加新 ticker 订阅: ${key}`);
      subscribe(exchange, symbol, marketType);
    });
  }, [exchanges, connected, subscribe, unsubscribe]);

  /**
   * 初始连接
   */
  useEffect(() => {
    if (!enabled) return;
    
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }
    
    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      setConnected(false);
    };
  }, []);

  /**
   * 监听 enabled 状态变化
   */
  useEffect(() => {
    if (!enabled && wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setConnected(false);
      
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    } else if (enabled && !wsRef.current) {
      connect();
    }
  }, [enabled, connect]);

  return {
    connected,
    error,
    reconnect,
    tickerData,
  };
};












