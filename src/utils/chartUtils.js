/**
 * 图表相关工具函数
 */

/**
 * 转换数据格式为图表所需格式
 * @param {Array} data - 原始数据数组
 * @returns {Array} 转换后的数据数组
 */
export const convertDataToChartFormat = (data) => {
  if (!data || data.length === 0) return [];
  return data.map(item => ({
    time: typeof item.time === 'number' 
      ? Math.floor(item.time / 1000) 
      : Math.floor(new Date(item.time).getTime() / 1000),
    value: parseFloat(item.value),
  })).sort((a, b) => a.time - b.time);
};

/**
 * 生成交易所唯一标识符
 * @param {Object} config - 交易所配置对象
 * @returns {string} 唯一标识符
 */
export const getExchangeKey = (config) => {
  const marketType = config.market_type || 'spot';
  return `${config.exchange}-${config.symbol}-${marketType}`;
};

/**
 * 获取所有时间点的最小值和最大值
 * @param {Array} timeArrays - 多个时间数组的数组
 * @returns {Object} { minTime, maxTime }
 */
export const getTimeRange = (timeArrays) => {
  const allTimes = timeArrays.flat();
  if (allTimes.length === 0) return null;
  
  return {
    minTime: Math.min(...allTimes),
    maxTime: Math.max(...allTimes),
  };
};

/**
 * 创建图表配置对象
 * @param {number} width - 图表宽度
 * @param {number} height - 图表高度
 * @returns {Object} 图表配置
 */
export const createChartConfig = (width, height) => ({
  width,
  height,
  layout: {
    background: { color: '#ffffff' },
    textColor: '#333',
  },
  grid: {
    vertLines: { color: '#f0f0f0' },
    horzLines: { color: '#f0f0f0' },
  },
  crosshair: {
    mode: 1,
  },
  rightPriceScale: {
    borderColor: '#cccccc',
  },
  timeScale: {
    borderColor: '#cccccc',
    timeVisible: true,
    secondsVisible: false,
  },
});

/**
 * 创建线条系列配置
 * @param {Object} config - 交易所配置
 * @returns {Object} 线条配置
 */
export const createLineSeriesConfig = (config) => ({
  title: config.label || `${config.exchange} ${config.symbol}`,
  color: config.color || '#2196f3',
  lineWidth: 2,
  crosshairMarkerVisible: true,
  crosshairMarkerRadius: 4,
});

