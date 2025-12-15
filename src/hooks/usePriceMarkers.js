import { useEffect } from 'react';
import { getExchangeKey, convertDataToChartFormat } from '../utils/chartUtils';
import { formatPercent } from '../utils/formatters';

/**
 * 价格差异标注 Hook
 * 负责计算和显示不同交易所之间的价格差异
 * 
 * @param {boolean} enableMarkers - 是否启用标注
 * @param {number} threshold - 差异阈值（百分比）
 * @param {Array} exchanges - 所有交易所配置
 * @param {Map} chartData - 图表数据
 * @param {Function} getLineSeries - 获取线条系列的函数
 * @param {Function} clearAllMarkers - 清空所有标记的函数
 * @param {Array} selectedExchanges - 选中的交易所配置（用于价差比对，必须是2个）
 */
export const usePriceMarkers = (
  enableMarkers,
  threshold,
  exchanges,
  chartData,
  getLineSeries,
  clearAllMarkers,
  selectedExchanges = []
) => {
  useEffect(() => {
    // 如果标注被禁用、没有选中2个交易所、或没有数据，清空所有标记
    if (!enableMarkers || selectedExchanges.length !== 2 || chartData.size === 0) {
      clearAllMarkers(exchanges);
      return;
    }

    // 只为选中的两个交易所获取转换后的数据
    const convertedDataMap = new Map();
    selectedExchanges.forEach(exchange => {
      const key = getExchangeKey(exchange);
      const data = chartData.get(key);
      if (data) {
        convertedDataMap.set(key, convertDataToChartFormat(data));
      }
    });

    // 为选中的两个交易所计算差异标记
    selectedExchanges.forEach((exchange, index) => {
      const key = getExchangeKey(exchange);
      const series = getLineSeries(exchange);
      const data = convertedDataMap.get(key);
      
      if (!series || !data) return;

      const markers = calculatePriceMarkers(
        data,
        selectedExchanges,
        index,
        convertedDataMap,
        threshold
      );

      // 设置标记
      series.setMarkers(markers);
    });

  }, [enableMarkers, threshold, chartData, exchanges, getLineSeries, clearAllMarkers, selectedExchanges]);
};

const calculatePriceMarkers = (
  data,
  exchanges,
  currentIndex,
  convertedDataMap,
  threshold
) => {
  const markers = [];

  // 与其他所有交易所比较，找出差异点
  data.forEach(point => {
    const maxDiff = calculateMaxDifference(
      point,
      exchanges,
      currentIndex,
      convertedDataMap
    );

    // 如果差异超过阈值，添加标记
    if (maxDiff >= threshold) {
      markers.push(createMarker(point.time, maxDiff));
    }
  });

  return markers;
};

/**
 * 计算当前点与其他所有交易所的最大差异（百分比）
 * @param {Object} point - 当前时间点的数据
 * @param {Array} exchanges - 所有交易所配置
 * @param {number} currentIndex - 当前交易所的索引
 * @param {Map} convertedDataMap - 所有交易所的转换后数据
 * @returns {number} 最大差异百分比
 */
const calculateMaxDifference = (
  point,
  exchanges,
  currentIndex,
  convertedDataMap
) => {
  let maxDiffPercent = 0;

  // 与其他交易所比较
  exchanges.forEach((otherConfig, otherIndex) => {
    if (currentIndex === otherIndex) return; // 跳过自己

    const otherKey = getExchangeKey(otherConfig);
    const otherData = convertedDataMap.get(otherKey);
    
    if (!otherData) return;

    // 查找相同时间点的数据
    const otherPoint = otherData.find(p => p.time === point.time);
    if (otherPoint && otherPoint.value !== 0) {
      // 计算百分比差异：|(当前价格 - 对方价格) / 对方价格| * 100
      const diffPercent = Math.abs((point.value - otherPoint.value) / otherPoint.value) * 100;
      if (diffPercent > maxDiffPercent) {
        maxDiffPercent = diffPercent;
      }
    }
  });

  return maxDiffPercent;
};

/**
 * 创建标记对象
 * @param {number} time - 时间戳
 * @param {number} diffPercent - 差异百分比
 * @returns {Object} 标记对象
 */
const createMarker = (time, diffPercent) => ({
  time,
  position: 'aboveBar',
  color: '#e91e63',
  shape: 'circle',
  text: `${diffPercent.toFixed(2)}%`, // 标记点保留2位小数足够
  size: 0,
});

