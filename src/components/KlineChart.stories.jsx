import KlineChart from './KlineChart';

// 生成测试数据
const generateTestData = (basePrice = 50000, count = 50) => {
  const data = [];
  const now = Date.now();
  const interval = 15 * 60 * 1000; // 15分钟
  
  for (let i = count; i >= 0; i--) {
    const time = now - (i * interval);
    const randomChange = (Math.random() - 0.5) * 0.02;
    const price = basePrice * (1 + randomChange);
    
    data.push({
      time: time,
      open: price * (1 + (Math.random() - 0.5) * 0.001),
      high: price * (1 + Math.random() * 0.002),
      low: price * (1 - Math.random() * 0.002),
      close: price
    });
  }
  return data;
};

export default {
  title: 'Components/KlineChart',
  component: KlineChart,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    dataA: { control: 'object' },
    dataB: { control: 'object' },
    labelA: { control: 'text' },
    labelB: { control: 'text' },
    upper: { control: 'number' },
    lower: { control: 'number' },
  },
};

// 默认故事
export const Default = {
  args: {
    dataA: generateTestData(50000),
    dataB: generateTestData(50000),
    labelA: 'Binance',
    labelB: 'Bybit',
    upper: 0.003,
    lower: -0.002,
  },
};

// 价格差异故事
export const WithPriceGap = {
  args: {
    dataA: generateTestData(30000),
    dataB: generateTestData(70000),
    labelA: 'Binance',
    labelB: 'Bybit',
    upper: 0.003,
    lower: -0.002,
  },
};

// 无数据故事
export const NoData = {
  args: {
    dataA: [],
    dataB: [],
    labelA: 'Binance',
    labelB: 'Bybit',
    upper: 0.003,
    lower: -0.002,
  },
};

// 只有A数据故事
export const OnlyDataA = {
  args: {
    dataA: generateTestData(50000),
    dataB: [],
    labelA: 'Binance',
    labelB: 'Bybit',
    upper: 0.003,
    lower: -0.002,
  },
};

// 高阈值故事
export const HighThresholds = {
  args: {
    dataA: generateTestData(50000),
    dataB: generateTestData(50000),
    labelA: 'Binance',
    labelB: 'Bybit',
    upper: 0.01,
    lower: -0.01,
  },
};


