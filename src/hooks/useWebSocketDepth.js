import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket 实时 Depth (订单薄) 数据 Hook
 * 
 * @param {Array} exchanges - 交易所配置数组
 * @param {Function} onDepthUpdate - depth更新回调 (exchange, symbol, marketType, depth) => void
 * @param {boolean} enabled - 是否启用实时数据
 * @returns {Object} { connected, error, reconnect, depthData }
 */
export const useWebSocketDepth = (exchanges, onDepthUpdate, enabled = true) => {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const subscriptionsRef = useRef(new Set());
  
  // 使用 ref 存储最新的参数
  const exchangesRef = useRef(exchanges);
  const onDepthUpdateRef = useRef(onDepthUpdate);
  const enabledRef = useRef(enabled);
  
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [depthData, setDepthData] = useState({});

  // 更新 refs
  useEffect(() => {
    exchangesRef.current = exchanges;
    onDepthUpdateRef.current = onDepthUpdate;
    enabledRef.current = enabled;
  }, [exchanges, onDepthUpdate, enabled]);

  /**
   * 订阅 depth 数据
   */
  const subscribe = useCallback((exchange, symbol, marketType = 'spot', limit = 5) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法订阅 depth');
      return;
    }

    const subscriptionKey = `${exchange}_${symbol}_${marketType}`;
    
    if (subscriptionsRef.current.has(subscriptionKey)) {
      console.log(`⚠️ 跳过重复订阅 depth: ${subscriptionKey}`);
      return;
    }

    const message = {
      type: 'subscribe_depth',
      data: {
        exchange: exchange,
        symbol: symbol,
        market_type: marketType,
        limit: limit, // 订单薄档位数量
      }
    };

    console.log(`📊 发送 depth 订阅请求: ${subscriptionKey}`, message);
    ws.send(JSON.stringify(message));
    subscriptionsRef.current.add(subscriptionKey);
    console.log(`✅ Depth 订阅成功: ${subscriptionKey}`);
  }, []);

  /**
   * 取消订阅 depth 数据
   */
  const unsubscribe = useCallback((exchange, symbol, marketType = 'spot') => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法取消订阅 depth');
      return;
    }

    const subscriptionKey = `${exchange}_${symbol}_${marketType}`;
    
    if (!subscriptionsRef.current.has(subscriptionKey)) {
      console.log(`⚠️ 未订阅该 depth: ${subscriptionKey}`);
      return;
    }

    const message = {
      type: 'unsubscribe_depth',
      data: {
        exchange: exchange,
        symbol: symbol,
        market_type: marketType
      }
    };

    console.log(`❌ 发送取消 depth 订阅请求: ${subscriptionKey}`, message);
    ws.send(JSON.stringify(message));
    subscriptionsRef.current.delete(subscriptionKey);
    console.log(`✅ 取消 depth 订阅成功: ${subscriptionKey}`);
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
      
      console.log('🔌 正在连接 WebSocket (Depth):', wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket (Depth) 已连接');
        setConnected(true);
        setError(null);
        
        subscriptionsRef.current.clear();
        const currentExchanges = exchangesRef.current;
        
        console.log('📋 准备订阅 depth 的交易所数量:', currentExchanges.length);
        
        currentExchanges.forEach((config) => {
          subscribe(config.exchange, config.symbol, config.market_type || 'spot', 5);
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('🔍 [Depth] 收到 WebSocket 消息:', message.type, message);
          
          if (message.type === 'depth_update') {
            const { exchange, symbol, market_type, depth } = message.data;
            const key = `${exchange}_${symbol}_${market_type}`;
            
            // ✅ 过滤：只处理已订阅的数据
            if (!subscriptionsRef.current.has(key)) {
              console.log(`⏭️ [Depth] 跳过未订阅的数据: ${key}`);
              return;
            }
            
            console.log(`📊 [Depth] 更新数据 - ${key}:`, {
              bids: depth.bids?.length,
              asks: depth.asks?.length,
              timestamp: depth.timestamp
            });
            
            // 更新本地 depth 数据
            setDepthData(prev => ({
              ...prev,
              [key]: {
                bids: depth.bids || [], // [[price, amount], ...]
                asks: depth.asks || [], // [[price, amount], ...]
                timestamp: depth.timestamp || Date.now(),
              },
            }));
            
            // 回调
            onDepthUpdateRef.current?.(exchange, symbol, market_type, depth);
          } else if (message.type === 'depth_subscription_confirmed') {
            console.log('📡 Depth 订阅确认:', message.data);
          }
        } catch (err) {
          console.error('WebSocket depth 消息解析失败:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket (Depth) 错误:', event);
        setError('WebSocket Depth 连接错误');
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket (Depth) 已断开');
        setConnected(false);
        wsRef.current = null;
        
        if (enabledRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            console.log('🔄 尝试重新连接 depth...');
            connect();
          }, 3000);
        }
      };

    } catch (err) {
      console.error('WebSocket depth 连接失败:', err);
      setError(err.message);
    }
  }, [subscribe]);

  /**
   * 手动重连
   */
  const reconnect = useCallback(() => {
    console.log('🔄 手动重连 depth...');
    
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
      
      console.log(`❌ 取消旧 depth 订阅: ${key}`);
      unsubscribe(exchange, symbol, marketType);
    });
    
    // ✅ 添加新订阅
    toAdd.forEach(key => {
      const parts = key.split('_');
      const exchange = parts[0];
      const marketType = parts[parts.length - 1];
      const symbol = parts.slice(1, parts.length - 1).join('_');
      
      console.log(`➕ 添加新 depth 订阅: ${key}`);
      subscribe(exchange, symbol, marketType, 5);
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
    depthData,
  };
};



















