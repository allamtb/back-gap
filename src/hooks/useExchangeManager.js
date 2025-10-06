import { useRef, useEffect } from 'react';
import { getExchangeKey } from '../utils/chartUtils';

/**
 * 交易所管理 Hook
 * 负责智能处理交易所的增删改操作
 */
export const useExchangeManager = (
  exchanges,
  addLineSeries,
  removeLineSeries,
  fetchNewData,
  fetchAllData,
  removeData,
  interval,
  limit
) => {
  const prevExchangesRef = useRef([]);

  useEffect(() => {
    const prevKeys = new Set(prevExchangesRef.current.map(getExchangeKey));
    const currentKeys = new Set(exchanges.map(getExchangeKey));

    // 找出新增的交易所配置
    const added = exchanges.filter(config => 
      !prevKeys.has(getExchangeKey(config))
    );

    // 找出删除的交易所配置
    const removed = prevExchangesRef.current.filter(config =>
      !currentKeys.has(getExchangeKey(config))
    );

    // 处理删除的交易所
    removed.forEach(config => {
      const key = getExchangeKey(config);
      removeLineSeries(config);
      removeData(key);
    });

    // 为新增的交易所添加线系列
    added.forEach(config => {
      addLineSeries(config);
    });

    // 获取新增交易所的数据（增量更新）
    if (added.length > 0) {
      fetchNewData(added, interval, limit);
    }

    // 如果是初始化（从空到有数据），则全量加载
    if (prevExchangesRef.current.length === 0 && exchanges.length > 0) {
      fetchAllData(exchanges, interval, limit);
    }

    // 更新 prevExchangesRef
    prevExchangesRef.current = exchanges;

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exchanges]);
};

