import { useRef, useEffect } from 'react';
import { createChart } from 'lightweight-charts';
import { 
  getExchangeKey, 
  createChartConfig, 
  createLineSeriesConfig,
  convertDataToChartFormat,
  getTimeRange
} from '../utils/chartUtils';

/**
 * 图表管理 Hook
 * 负责图表的初始化、线条管理、数据更新
 */
export const useChartManager = (chartContainerRef, height) => {
  const chartRef = useRef(null);
  const lineSeriesMapRef = useRef(new Map());

  /**
   * 初始化图表
   */
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 创建图表实例
    const config = createChartConfig(
      chartContainerRef.current.clientWidth,
      height
    );
    const chart = createChart(chartContainerRef.current, config);
    chartRef.current = chart;

    // 处理窗口大小变化
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [chartContainerRef, height]);

  /**
   * 添加线条系列
   */
  const addLineSeries = (config) => {
    if (!chartRef.current) return null;
    
    const key = getExchangeKey(config);
    
    if (!lineSeriesMapRef.current.has(key)) {
      const seriesConfig = createLineSeriesConfig(config);
      const lineSeries = chartRef.current.addLineSeries(seriesConfig);
      lineSeriesMapRef.current.set(key, lineSeries);
      return lineSeries;
    }
    
    return lineSeriesMapRef.current.get(key);
  };

  /**
   * 删除线条系列
   */
  const removeLineSeries = (config) => {
    if (!chartRef.current) return;
    
    const key = getExchangeKey(config);
    const series = lineSeriesMapRef.current.get(key);
    
    if (series) {
      chartRef.current.removeSeries(series);
      lineSeriesMapRef.current.delete(key);
    }
  };

  /**
   * 更新线条数据
   */
  const updateSeriesData = (exchanges, chartData) => {
    if (!chartRef.current || chartData.size === 0) return;

    const allTimes = [];

    // 为每个线系列设置数据
    exchanges.forEach(config => {
      const key = getExchangeKey(config);
      const series = lineSeriesMapRef.current.get(key);
      const data = chartData.get(key);

      if (series && data) {
        const convertedData = convertDataToChartFormat(data);
        series.setData(convertedData);
        
        // 收集所有时间点
        allTimes.push(convertedData.map(d => d.time));
      }
    });

    // 自动调整时间范围
    const timeRange = getTimeRange(allTimes);
    if (timeRange && chartRef.current) {
      chartRef.current.timeScale().setVisibleRange({
        from: timeRange.minTime,
        to: timeRange.maxTime,
      });
    }
  };

  /**
   * 获取线条系列
   */
  const getLineSeries = (config) => {
    const key = getExchangeKey(config);
    return lineSeriesMapRef.current.get(key);
  };

  /**
   * 清空所有线条的标记
   */
  const clearAllMarkers = (exchanges) => {
    exchanges.forEach(config => {
      const series = getLineSeries(config);
      if (series) {
        series.setMarkers([]);
      }
    });
  };

  return {
    chartRef,
    lineSeriesMapRef,
    addLineSeries,
    removeLineSeries,
    updateSeriesData,
    getLineSeries,
    clearAllMarkers,
  };
};

