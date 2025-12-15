import { useEffect, useRef, useCallback, useState } from 'react';
import { getExchangeCredentials } from '../utils/configManager';
import { generateSymbol } from '../utils/exchangeRules';

/**
 * 持仓监控 Hook
 * 参考 backend/examples/binance_people_test.py 中的持仓查询逻辑
 * 
 * 功能：
 * 1. 定期获取现货余额（get_spot_balance）
 * 2. 定期获取合约持仓（get_futures_positions）
 * 3. 实时更新持仓数据
 * 
 * @param {Array} exchanges - 当前 Tab 的交易所配置数组
 * @param {Function} onPositionsUpdate - 持仓更新回调函数 (positions) => void
 * @param {boolean} enabled - 是否启用监控
 * @param {number} interval - 轮询间隔（毫秒），默认 5000ms (5秒)
 * @param {Object} tickerData - ticker数据，用于获取现货持仓的当前价格
 * @param {Function} onLog - 日志回调 (log) => void
 * @returns {Object} { isMonitoring, positions, loading, error, refresh }
 */
export const usePositionMonitoring = (
  exchanges = [],
  onPositionsUpdate,
  enabled = true,
  interval = 5000,
  tickerData = {}, // 添加 tickerData 参数，用于获取现货持仓的当前价格
  onLog = null
) => {
  // 持仓数据
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // 标记是否是数据刷新（而不是价格更新）
  const isDataRefreshRef = useRef(false);
  
  // 轮询定时器
  const pollingTimerRef = useRef(null);
  
  // 是否正在监控
  const [isMonitoring, setIsMonitoring] = useState(false);
  
  // 刷新间隔计数（从上次刷新开始经过的时间，毫秒）
  const [refreshCountdown, setRefreshCountdown] = useState(0);
  
  // 存储原始持仓数据（不包含价格更新），用于实时更新价格
  const basePositionsRef = useRef([]);
  
  // 刷新间隔计数定时器
  const countdownTimerRef = useRef(null);
  
  // 上次刷新时间
  const lastRefreshTimeRef = useRef(null);
  
  // 使用 ref 存储最新的参数，避免依赖导致重新连接
  const exchangesRef = useRef(exchanges);
  const onPositionsUpdateRef = useRef(onPositionsUpdate);
  const enabledRef = useRef(enabled);
  const intervalRef = useRef(interval);
  const onLogRef = useRef(onLog);
  
  // 防止重复请求
  const fetchingRef = useRef(false);
  
  // 存储 fetchPositions 函数的 ref，用于在定时器中调用
  const fetchPositionsRef = useRef(null);
  
  // 更新 refs
  useEffect(() => {
    exchangesRef.current = exchanges;
    onPositionsUpdateRef.current = onPositionsUpdate;
    enabledRef.current = enabled;
    intervalRef.current = interval;
    onLogRef.current = onLog;
  }, [exchanges, onPositionsUpdate, enabled, interval, onLog]);

  /**
   * 更新刷新时间并重置计数
   */
  const updateRefreshTime = useCallback(() => {
    lastRefreshTimeRef.current = Date.now();
    setRefreshCountdown(0);
  }, []);

  /**
   * 设置下一次刷新定时器
   */
  const scheduleNextRefresh = useCallback(() => {
    // 清除旧定时器
    if (pollingTimerRef.current) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
    
    // 如果未启用或没有交易所配置，不设置定时器
    if (!enabledRef.current || exchangesRef.current.length === 0) {
      return;
    }
    
    // 更新刷新时间
    updateRefreshTime();
    
    // 设置新定时器（从0开始重新计时）
    pollingTimerRef.current = setTimeout(() => {
      if (fetchPositionsRef.current) {
        fetchPositionsRef.current();
      }
    }, intervalRef.current);
    
    console.log(`⏰ [持仓监控] 已设置下次刷新，间隔: ${intervalRef.current}ms`);
  }, [updateRefreshTime]);

  /**
   * 获取持仓数据
   * 参考 Python 代码中的 get_spot_balance() 和 get_futures_positions()
   */
  const fetchPositions = useCallback(async () => {
    if (!enabledRef.current || exchangesRef.current.length === 0) {
      return [];
    }
    
    // 防止重复请求
    if (fetchingRef.current) {
      console.log('⏳ [持仓监控] 请求正在进行中，跳过本次请求');
      return [];
    }
    
    try {
      // 获取交易所凭证
      const credentials = getExchangeCredentials(true);
      
      if (credentials.length === 0) {
        console.warn('⚠️ [持仓监控] 未配置交易所账户');
        setError('未配置交易所账户');
        return [];
      }
      
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
      
      fetchingRef.current = true;
      setLoading(true);
      setError(null);
      
      // 从交易所配置中提取币种列表（基础货币）
      const baseCurrencies = [];
      if (exchangesRef.current && exchangesRef.current.length > 0) {
        exchangesRef.current.forEach(ex => {
          const symbol = ex.symbol || '';
          if (symbol.includes('/')) {
            const baseCurrency = symbol.split('/')[0];
            if (!baseCurrencies.includes(baseCurrency.toUpperCase())) {
              baseCurrencies.push(baseCurrency.toUpperCase());
            }
          } else if (symbol) {
            if (!baseCurrencies.includes(symbol.toUpperCase())) {
              baseCurrencies.push(symbol.toUpperCase());
            }
          }
        });
      }
      
      // 根据每个交易所的配置，生成对应的交易对列表
      // 使用 exchangeRules 来确保使用正确的报价货币
      const symbolPairs = {}; // {exchange: {marketType: [symbols]}}
      
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
      
      console.log(`📊 [持仓监控] 开始获取持仓数据 (${deduplicatedCredentials.length} 个交易所, 基础币种: ${baseCurrencies.length > 0 ? baseCurrencies.join(', ') : '全部'})`);
      if (Object.keys(symbolPairs).length > 0) {
        console.log(`📊 [持仓监控] 生成的交易对映射:`, symbolPairs);
      }
      
      // 调用后端 API 获取持仓（传递交易对映射）
      const requestBody = {
        credentials: deduplicatedCredentials,
        symbolPairs: Object.keys(symbolPairs).length > 0 ? symbolPairs : undefined  // 传递交易对映射，而不是基础货币列表
      };
      
      const response = await fetch('/api/positions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.data) {
        const apiPositions = data.data;
        
        // 转换为 PositionStatusTable 需要的格式
        // 参考 Python 代码中的数据结构
        const formattedPositions = apiPositions.map((pos, index) => {
          // 确定市场类型
          const marketType = pos.type === 'spot' ? 'spot' : 'futures';
          
          // 确定方向（现货都是 long，合约根据 side 判断）
          let side = 'long';
          if (marketType === 'futures' && pos.side) {
            side = pos.side.toLowerCase();
          }
          
          // 计算盈亏（如果有）
          const unrealizedPnl = pos.unrealizedPnl || 0;
          
          // 获取开仓均价和当前价格
          let entryPrice = pos.entryPrice || pos.price || 0;
          let currentPrice = pos.markPrice || pos.currentPrice || entryPrice;
          
          // 从 tickerData 中获取当前价格（现货取现货，合约取合约，交易所要对齐）
          let tickerKey = '';
          
          if (marketType === 'spot') {
            // 现货持仓：从现货 ticker 获取当前价格
            // 现货持仓的 symbol 可能是币种代码（如 'BTC'），需要转换为交易对（如 'BTC/USDT'）
            if (pos.symbol && !pos.symbol.includes('/')) {
              // 如果是币种代码，使用 generateSymbol 转换为交易对
              try {
                const symbolPair = generateSymbol(pos.symbol, pos.exchange, 'spot');
                tickerKey = `${pos.exchange}_${symbolPair}_spot`;
              } catch (e) {
                // 如果转换失败，尝试从 exchanges 配置中找到对应的交易对
                const exchangeConfig = exchanges.find(ex => 
                  ex.exchange === pos.exchange && 
                  (ex.market_type || 'spot') === 'spot'
                );
                if (exchangeConfig) {
                  tickerKey = `${pos.exchange}_${exchangeConfig.symbol}_spot`;
                } else {
                  // 如果找不到配置，尝试使用默认格式（假设是 USDT 交易对）
                  tickerKey = `${pos.exchange}_${pos.symbol}/USDT_spot`;
                }
              }
            } else {
              // 如果已经是交易对格式
              tickerKey = `${pos.exchange}_${pos.symbol}_spot`;
            }
            
            // 现货持仓如果没有 entryPrice，暂时设为 null（前端会显示为 '-'）
            // 开仓均价需要从订单历史中计算，这里暂时不显示
            if (!entryPrice || entryPrice === 0) {
              entryPrice = null; // 前端会显示为 '-'
            }
          } else {
            // 合约持仓：从合约 ticker 获取当前价格
            // 合约持仓的 symbol 通常是交易对格式（如 'BTC/USDT'）
            if (pos.symbol && pos.symbol.includes('/')) {
              // 已经是交易对格式，尝试两种格式（兼容 futures 和 future）
              tickerKey = `${pos.exchange}_${pos.symbol}_futures`;
            } else {
              // 如果不是交易对格式，尝试转换
              try {
                const symbolPair = generateSymbol(pos.symbol, pos.exchange, 'future');
                tickerKey = `${pos.exchange}_${symbolPair}_futures`;
              } catch (e) {
                // 如果转换失败，尝试从 exchanges 配置中找到对应的交易对
                const exchangeConfig = exchanges.find(ex => 
                  ex.exchange === pos.exchange && 
                  (ex.market_type === 'futures' || ex.market_type === 'future')
                );
                if (exchangeConfig) {
                  const configMarketType = exchangeConfig.market_type || 'futures';
                  tickerKey = `${pos.exchange}_${exchangeConfig.symbol}_${configMarketType}`;
                } else {
                  // 如果找不到配置，尝试使用默认格式
                  tickerKey = `${pos.exchange}_${pos.symbol}/USDT_futures`;
                }
              }
            }
          }
          
          // 从 tickerData 中获取当前价格（确保交易所对齐）
          // 先尝试主格式，如果找不到，合约持仓再尝试 alternative 格式
          let ticker = tickerData[tickerKey];
          if (!ticker && marketType !== 'spot') {
            // 合约持仓：如果找不到，尝试 future 格式（而不是 futures）
            const altKey = tickerKey.replace('_futures', '_future');
            ticker = tickerData[altKey];
            if (ticker) {
              tickerKey = altKey; // 更新 tickerKey 以便后续使用
            }
          }
          
          if (ticker && ticker.price) {
            currentPrice = ticker.price;
          }
          
          // 计算盈亏率
          let pnlPercent = 0;
          if (entryPrice > 0 && currentPrice && currentPrice !== entryPrice) {
            if (side === 'long') {
              pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100;
            } else {
              pnlPercent = ((entryPrice - currentPrice) / entryPrice) * 100;
            }
          }
          
          return {
            key: `${pos.exchange}-${pos.symbol}-${marketType}-${index}`,
            exchange: pos.exchange,
            symbol: pos.symbol,
            marketType: marketType,
            side: side,
            amount: Math.abs(pos.amount || 0),
            openPrice: entryPrice,
            currentPrice: currentPrice,
            fee: 0, // 手续费需要从订单中计算，这里暂时设为0
            unrealizedPnl: unrealizedPnl,
            pnlPercent: pnlPercent,
            // 保留原始数据
            raw: pos
          };
        });
        
        // 过滤掉数量为0的持仓（现货余额为0或合约持仓为0）
        const activePositions = formattedPositions.filter(p => p.amount > 0);
        
        // 保存原始持仓数据（用于实时更新价格）
        basePositionsRef.current = activePositions.map(pos => ({
          ...pos,
          // 保存原始的开仓均价，用于计算盈亏
          originalEntryPrice: pos.openPrice,
          originalUnrealizedPnl: pos.unrealizedPnl
        }));
        
        // 使用当前 tickerData 更新价格和盈亏
        const updatedPositions = updatePositionsWithTickerData(activePositions, tickerData, exchanges);
        
        // 标记这是数据刷新
        isDataRefreshRef.current = true;
        
        setPositions(updatedPositions);
        setError(null);
        
        // 调用回调函数，传递标记表示这是数据刷新
        if (onPositionsUpdateRef.current) {
          onPositionsUpdateRef.current(updatedPositions, true); // true 表示是数据刷新
        }
        
        // 重置标记
        setTimeout(() => {
          isDataRefreshRef.current = false;
        }, 100);
        
        console.log(`✅ [持仓监控] 获取到 ${activePositions.length} 个活跃持仓`);
        
        // 记录成功日志（系统操作）
        if (onLogRef.current) {
          onLogRef.current({
            type: 'position_fetch',
            status: 'success',
            message: `获取持仓成功: ${activePositions.length} 个持仓`,
            source: 'system'
          });
        }
        
        return updatedPositions;
      } else {
        throw new Error(data.message || 'API 返回失败');
      }
    } catch (error) {
      console.error('❌ [持仓监控] 获取持仓失败:', error);
      setError(error.message || '获取持仓失败');
      setPositions([]);
      
      // 记录失败日志（系统操作）
      if (onLogRef.current) {
        onLogRef.current({
          type: 'position_fetch',
          status: 'error',
          message: `获取持仓失败: ${error.message || '未知错误'}`,
          source: 'system'
        });
      }
      
      return [];
    } finally {
      fetchingRef.current = false;
      setLoading(false);
      
      // 刷新完成后，重新设置定时器（从0开始计数）
      scheduleNextRefresh();
    }
  }, [scheduleNextRefresh]);
  
  /**
   * 使用 tickerData 更新持仓的当前价、浮动盈亏和盈亏率
   */
  const updatePositionsWithTickerData = useCallback((positionsList, currentTickerData, exchangesList) => {
    return positionsList.map(pos => {
      const marketType = pos.marketType || pos.type || 'spot';
      const side = pos.side || 'long';
      // 优先使用原始开仓均价，如果没有则使用当前的开仓均价
      const entryPrice = pos.originalEntryPrice !== undefined ? pos.originalEntryPrice : (pos.openPrice || 0);
      
      // 构建 tickerKey
      let tickerKey = '';
      
      if (marketType === 'spot') {
        // 现货持仓
        if (pos.symbol && !pos.symbol.includes('/')) {
          try {
            const symbolPair = generateSymbol(pos.symbol, pos.exchange, 'spot');
            tickerKey = `${pos.exchange}_${symbolPair}_spot`;
          } catch (e) {
            const exchangeConfig = exchangesList.find(ex => 
              ex.exchange === pos.exchange && 
              (ex.market_type || 'spot') === 'spot'
            );
            if (exchangeConfig) {
              tickerKey = `${pos.exchange}_${exchangeConfig.symbol}_spot`;
            } else {
              tickerKey = `${pos.exchange}_${pos.symbol}/USDT_spot`;
            }
          }
        } else {
          tickerKey = `${pos.exchange}_${pos.symbol}_spot`;
        }
      } else {
        // 合约持仓
        if (pos.symbol && pos.symbol.includes('/')) {
          tickerKey = `${pos.exchange}_${pos.symbol}_futures`;
        } else {
          try {
            const symbolPair = generateSymbol(pos.symbol, pos.exchange, 'future');
            tickerKey = `${pos.exchange}_${symbolPair}_futures`;
          } catch (e) {
            const exchangeConfig = exchangesList.find(ex => 
              ex.exchange === pos.exchange && 
              (ex.market_type === 'futures' || ex.market_type === 'future')
            );
            if (exchangeConfig) {
              const configMarketType = exchangeConfig.market_type || 'futures';
              tickerKey = `${pos.exchange}_${exchangeConfig.symbol}_${configMarketType}`;
            } else {
              tickerKey = `${pos.exchange}_${pos.symbol}/USDT_futures`;
            }
          }
        }
      }
      
      // 从 tickerData 中获取当前价格
      let ticker = currentTickerData[tickerKey];
      if (!ticker && marketType !== 'spot') {
        const altKey = tickerKey.replace('_futures', '_future');
        ticker = currentTickerData[altKey];
      }
      
      let currentPrice = pos.currentPrice;
      if (ticker && ticker.price) {
        currentPrice = ticker.price;
      }
      
      // 计算浮动盈亏和盈亏率
      let unrealizedPnl = pos.unrealizedPnl || pos.originalUnrealizedPnl || 0;
      let pnlPercent = pos.pnlPercent || 0;
      
      if (entryPrice && entryPrice > 0 && currentPrice && currentPrice !== entryPrice) {
        const priceDiff = side === 'long' 
          ? (currentPrice - entryPrice) 
          : (entryPrice - currentPrice);
        const amount = pos.amount || 0;
        unrealizedPnl = priceDiff * amount;
        pnlPercent = (priceDiff / entryPrice) * 100;
      }
      
      return {
        ...pos,
        currentPrice: currentPrice,
        unrealizedPnl: unrealizedPnl,
        pnlPercent: pnlPercent
      };
    });
  }, []);
  
  // 使用 ref 存储上一次的 tickerData 价格，用于比较
  const prevTickerPricesRef = useRef({});
  
  // 更新 exchanges ref（exchangesRef 已在上面声明）
  useEffect(() => {
    exchangesRef.current = exchanges;
  }, [exchanges]);
  
  // 监听 tickerData 变化，实时更新持仓价格和盈亏
  useEffect(() => {
    if (basePositionsRef.current.length === 0 || !tickerData || Object.keys(tickerData).length === 0) {
      return;
    }
    
    // 提取当前所有价格，用于比较
    const currentPrices = {};
    Object.keys(tickerData).forEach(key => {
      if (tickerData[key]?.price !== undefined) {
        currentPrices[key] = tickerData[key].price;
      }
    });
    
    // 检查是否有价格变化（使用更精确的比较，避免浮点数精度问题）
    const hasPriceChange = Object.keys(currentPrices).some(key => {
      const prevPrice = prevTickerPricesRef.current[key];
      const currentPrice = currentPrices[key];
      
      // 如果之前没有价格，认为有变化
      if (prevPrice === undefined) {
        return true;
      }
      
      // 使用字符串比较，避免浮点数精度问题
      // 或者使用更精确的数值比较（允许极小的误差）
      if (typeof prevPrice === 'number' && typeof currentPrice === 'number') {
        // 如果价格差异大于 0.0001%，认为有变化
        const diff = Math.abs(currentPrice - prevPrice);
        const threshold = Math.max(Math.abs(prevPrice) * 0.000001, 0.00000001); // 0.0001% 或最小阈值
        return diff > threshold;
      }
      
      // 字符串比较
      return String(prevPrice) !== String(currentPrice);
    });
    
    // 如果没有价格变化，不更新
    if (!hasPriceChange && Object.keys(prevTickerPricesRef.current).length > 0) {
      return;
    }
    
    // 更新价格缓存
    prevTickerPricesRef.current = { ...currentPrices };
    
    // 在 useEffect 内部定义更新函数，避免依赖问题
    const updatePositions = (positionsList, currentTickerData, exchangesList) => {
      return positionsList.map(pos => {
        const marketType = pos.marketType || pos.type || 'spot';
        const side = pos.side || 'long';
        const entryPrice = pos.originalEntryPrice !== undefined ? pos.originalEntryPrice : (pos.openPrice || 0);
        
        // 构建 tickerKey
        let tickerKey = '';
        
        if (marketType === 'spot') {
          if (pos.symbol && !pos.symbol.includes('/')) {
            try {
              const symbolPair = generateSymbol(pos.symbol, pos.exchange, 'spot');
              tickerKey = `${pos.exchange}_${symbolPair}_spot`;
            } catch (e) {
              const exchangeConfig = exchangesList.find(ex => 
                ex.exchange === pos.exchange && 
                (ex.market_type || 'spot') === 'spot'
              );
              if (exchangeConfig) {
                tickerKey = `${pos.exchange}_${exchangeConfig.symbol}_spot`;
              } else {
                tickerKey = `${pos.exchange}_${pos.symbol}/USDT_spot`;
              }
            }
          } else {
            tickerKey = `${pos.exchange}_${pos.symbol}_spot`;
          }
        } else {
          if (pos.symbol && pos.symbol.includes('/')) {
            tickerKey = `${pos.exchange}_${pos.symbol}_futures`;
          } else {
            try {
              const symbolPair = generateSymbol(pos.symbol, pos.exchange, 'future');
              tickerKey = `${pos.exchange}_${symbolPair}_futures`;
            } catch (e) {
              const exchangeConfig = exchangesList.find(ex => 
                ex.exchange === pos.exchange && 
                (ex.market_type === 'futures' || ex.market_type === 'future')
              );
              if (exchangeConfig) {
                const configMarketType = exchangeConfig.market_type || 'futures';
                tickerKey = `${pos.exchange}_${exchangeConfig.symbol}_${configMarketType}`;
              } else {
                tickerKey = `${pos.exchange}_${pos.symbol}/USDT_futures`;
              }
            }
          }
        }
        
        // 从 tickerData 中获取当前价格
        let ticker = currentTickerData[tickerKey];
        if (!ticker && marketType !== 'spot') {
          const altKey = tickerKey.replace('_futures', '_future');
          ticker = currentTickerData[altKey];
        }
        
        let currentPrice = pos.currentPrice;
        if (ticker && ticker.price) {
          currentPrice = ticker.price;
        }
        
        // 计算浮动盈亏和盈亏率
        let unrealizedPnl = pos.unrealizedPnl || pos.originalUnrealizedPnl || 0;
        let pnlPercent = pos.pnlPercent || 0;
        
        if (entryPrice && entryPrice > 0 && currentPrice && currentPrice !== entryPrice) {
          const priceDiff = side === 'long' 
            ? (currentPrice - entryPrice) 
            : (entryPrice - currentPrice);
          const amount = pos.amount || 0;
          unrealizedPnl = priceDiff * amount;
          pnlPercent = (priceDiff / entryPrice) * 100;
        }
        
        return {
          ...pos,
          currentPrice: currentPrice,
          unrealizedPnl: unrealizedPnl,
          pnlPercent: pnlPercent
        };
      });
    };
    
    // 更新持仓数据
    const updatedPositions = updatePositions(
      basePositionsRef.current,
      tickerData,
      exchangesRef.current
    );
    
    setPositions(prevPositions => {
      // 检查是否有实际变化
      // 如果行数变化，需要确保平滑过渡（避免跳动）
      if (prevPositions.length !== updatedPositions.length) {
        // 使用 requestAnimationFrame 延迟更新，避免与渲染冲突
        requestAnimationFrame(() => {
          if (onPositionsUpdateRef.current) {
            onPositionsUpdateRef.current(updatedPositions);
          }
        });
        return updatedPositions;
      }
      
      // 检查价格或盈亏是否有变化（使用更精确的比较，避免浮点数精度问题）
      let hasChange = false;
      for (let i = 0; i < updatedPositions.length; i++) {
        const prev = prevPositions[i];
        const updated = updatedPositions[i];
        
        if (!prev) {
          hasChange = true;
          break;
        }
        
        // 比较当前价（允许极小的误差）
        const priceDiff = Math.abs((prev.currentPrice || 0) - (updated.currentPrice || 0));
        const priceThreshold = Math.max(Math.abs(prev.currentPrice || 0) * 0.000001, 0.00000001);
        if (priceDiff > priceThreshold) {
          hasChange = true;
          break;
        }
        
        // 比较浮动盈亏（允许极小的误差，比如 0.01 USDT）
        const pnlDiff = Math.abs((prev.unrealizedPnl || 0) - (updated.unrealizedPnl || 0));
        if (pnlDiff > 0.01) {
          hasChange = true;
          break;
        }
        
        // 比较盈亏率（允许极小的误差，比如 0.01%）
        const percentDiff = Math.abs((prev.pnlPercent || 0) - (updated.pnlPercent || 0));
        if (percentDiff > 0.01) {
          hasChange = true;
          break;
        }
      }
      
      // 只有真正有变化时才更新
      if (hasChange) {
        // 这是价格更新，不是数据刷新
        // 使用 requestAnimationFrame 延迟回调，避免与渲染冲突
        requestAnimationFrame(() => {
          if (onPositionsUpdateRef.current) {
            onPositionsUpdateRef.current(updatedPositions, false); // false 表示是价格更新
          }
        });
        return updatedPositions;
      }
      
      // 没有变化，返回原状态（不调用回调，避免不必要的更新）
      return prevPositions;
    });
  }, [tickerData]);
  
  // 将 fetchPositions 存储到 ref 中，供定时器使用
  useEffect(() => {
    fetchPositionsRef.current = fetchPositions;
  }, [fetchPositions]);
  
  /**
   * 手动刷新
   */
  const refresh = useCallback(() => {
    // 清除当前定时器
    if (pollingTimerRef.current) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
    // 立即刷新
    fetchPositions();
    // fetchPositions 完成后会自动设置新定时器（通过 scheduleNextRefresh）
    // 刷新时间会在 scheduleNextRefresh 中更新
  }, [fetchPositions]);

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
  
  /**
   * 启动监控
   */
  const startMonitoring = useCallback(() => {
    if (!enabledRef.current || exchangesRef.current.length === 0) {
      console.log('⚠️ [持仓监控] 未启用或没有交易所配置');
      return;
    }
    
    if (pollingTimerRef.current) {
      console.log('⚠️ [持仓监控] 已经在监控中');
      return;
    }
    
    setIsMonitoring(true);
    console.log(`🔄 [持仓监控] 开始监控持仓状态变化... (间隔: ${intervalRef.current}ms)`);
    
    // 初始化刷新时间
    updateRefreshTime();
    
    // 立即执行一次获取
    fetchPositions();
    // fetchPositions 完成后会自动设置新定时器（通过 scheduleNextRefresh）
  }, [fetchPositions, updateRefreshTime]);
  
  /**
   * 停止监控
   */
  const stopMonitoring = useCallback(() => {
    if (pollingTimerRef.current) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
      setIsMonitoring(false);
      console.log('⏹️ [持仓监控] 停止监控');
    }
  }, []);
  
  // 当 enabled、exchanges 或 interval 变化时，重新启动监控
  useEffect(() => {
    // 先停止旧的监控
    stopMonitoring();
    
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
  }, [enabled, exchanges.length, interval, startMonitoring, stopMonitoring]);
  
  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, [stopMonitoring]);
  
  return {
    isMonitoring,
    positions,
    loading,
    error,
    refresh,
    refreshCountdown // 刷新间隔计数（毫秒）
  };
};

