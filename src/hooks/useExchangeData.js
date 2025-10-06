import { useState, useCallback } from 'react';
import { getExchangeKey } from '../utils/chartUtils';

/**
 * 数据获取相关的 Hook
 * 负责从后端 API 获取交易所 K线数据
 */
export const useExchangeData = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartData, setChartData] = useState(new Map());

  /**
   * 获取单个交易所的K线数据
   */
  const fetchExchangeData = async (exchange, symbol, interval, limit) => {
    const params = new URLSearchParams({
      exchange,
      symbol,
      interval,
      limit: limit.toString(),
    });

    const response = await fetch(`http://localhost:8000/api/klines?${params}`);
    
    if (!response.ok) {
      throw new Error(`获取${exchange}数据失败: HTTP ${response.status}`);
    }

    const result = await response.json();

    if (result.success && result.data && result.data.klines) {
      // 只提取开盘价数据
      return result.data.klines.map(item => ({
        time: item.time,
        value: parseFloat(item.open)
      }));
    } else {
      throw new Error(result.error || '数据格式错误');
    }
  };

  /**
   * 获取所有交易所数据（用于初始加载和参数变化）
   */
  const fetchAllData = useCallback(async (exchanges, interval, limit) => {
    if (exchanges.length === 0) return;
    
    setLoading(true);
    setError(null);

    try {
      // 并行获取所有交易所数据
      const dataPromises = exchanges.map(async (config) => {
        try {
          const data = await fetchExchangeData(config.exchange, config.symbol, interval, limit);
          return { key: getExchangeKey(config), data, success: true };
        } catch (err) {
          return { 
            key: getExchangeKey(config), 
            data: null, 
            success: false, 
            error: err.message,
            exchange: config.exchange,
            symbol: config.symbol
          };
        }
      });

      const results = await Promise.all(dataPromises);

      // 检查是否有失败的请求
      const failures = results.filter(r => !r.success);
      if (failures.length > 0) {
        const failureMessages = failures.map(f => 
          `${f.exchange} ${f.symbol}: ${f.error}`
        ).join('\n');
        setError(`部分数据加载失败:\n${failureMessages}`);
      }

      // 更新成功的数据
      const newDataMap = new Map();
      results.forEach(({ key, data, success }) => {
        if (success && data) {
          newDataMap.set(key, data);
        }
      });
      setChartData(newDataMap);

      // 如果所有请求都失败，抛出错误
      if (failures.length === results.length) {
        throw new Error('所有交易所数据加载失败');
      }

    } catch (error) {
      setError(error.message || '获取数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 增量获取新增交易所的数据
   */
  const fetchNewData = useCallback(async (newConfigs, interval, limit) => {
    if (newConfigs.length === 0) return;
    
    setLoading(true);
    setError(null);

    try {
      // 并行获取新增交易所数据
      const dataPromises = newConfigs.map(async (config) => {
        try {
          const data = await fetchExchangeData(config.exchange, config.symbol, interval, limit);
          return { key: getExchangeKey(config), data, success: true };
        } catch (err) {
          return { 
            key: getExchangeKey(config), 
            data: null, 
            success: false, 
            error: err.message,
            exchange: config.exchange,
            symbol: config.symbol
          };
        }
      });

      const results = await Promise.all(dataPromises);

      // 检查是否有失败的请求
      const failures = results.filter(r => !r.success);
      if (failures.length > 0) {
        const failureMessages = failures.map(f => 
          `${f.exchange} ${f.symbol}: ${f.error}`
        ).join('\n');
        setError(`部分数据加载失败:\n${failureMessages}`);
      }

      // 增量更新数据（保留旧数据）
      setChartData(prev => {
        const newMap = new Map(prev);
        results.forEach(({ key, data, success }) => {
          if (success && data) {
            newMap.set(key, data);
          }
        });
        return newMap;
      });

    } catch (error) {
      setError(error.message || '获取新增数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 清除错误信息
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * 删除指定交易所的数据
   */
  const removeData = useCallback((key) => {
    setChartData(prev => {
      const newMap = new Map(prev);
      newMap.delete(key);
      return newMap;
    });
  }, []);

  return {
    loading,
    error,
    chartData,
    fetchAllData,
    fetchNewData,
    clearError,
    removeData,
  };
};

