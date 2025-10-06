# 多交易所价格曲线对比组件使用说明

## 📊 组件概述

`MultiExchangeChart` 是一个可复用的多交易所价格曲线对比组件，支持动态增减交易所-币对，并实时显示价格曲线对比。

## 🎯 核心特性

- ✅ **动态曲线管理**: 用户可以随时添加/删除交易所-币对，组件自动增减曲线
- ✅ **参数响应式**: 时间周期、数据条数变化时自动重新获取数据
- ✅ **平滑曲线显示**: 使用开盘价数据生成平滑的价格曲线
- ✅ **自定义样式**: 每条曲线可配置独立的颜色和标签
- ✅ **加载状态**: 显示数据加载状态和错误提示
- ✅ **模拟数据后备**: API失败时自动降级到模拟数据

## 📦 组件文件

```
src/
├── components/
│   ├── MultiExchangeChart.jsx      # 主图表组件
│   └── ExchangeManager.jsx         # 交易所配置管理组件
```

## 🔧 使用方法

### 1. 导入组件

```jsx
import MultiExchangeChart from "../components/MultiExchangeChart";
import ExchangeManager from "../components/ExchangeManager";
```

### 2. 配置状态

```jsx
const [exchanges, setExchanges] = useState([
  { 
    exchange: 'binance', 
    symbol: 'BTC/USDT', 
    label: 'Binance BTC/USDT', 
    color: '#ff9800' 
  },
  { 
    exchange: 'bybit', 
    symbol: 'BTC/USDT', 
    label: 'Bybit BTC/USDT', 
    color: '#2196f3' 
  },
]);

const [interval, setInterval] = useState("15m");
const [limit, setLimit] = useState(100);
```

### 3. 使用组件

```jsx
{/* 交易所配置管理 */}
<ExchangeManager
  exchanges={exchanges}
  onChange={setExchanges}
/>

{/* 多交易所价格曲线图 */}
<MultiExchangeChart
  exchanges={exchanges}
  interval={interval}
  limit={limit}
  height={500}
/>
```

## 📋 组件 Props

### MultiExchangeChart

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `exchanges` | Array | `[]` | 交易所配置数组 |
| `interval` | string | `"15m"` | 时间周期 (1m, 5m, 15m, 1h, 4h, 1d) |
| `limit` | number | `100` | 获取的数据条数 |
| `height` | number | `500` | 图表高度（像素） |

#### exchanges 数组元素格式

```javascript
{
  exchange: 'binance',          // 交易所名称
  symbol: 'BTC/USDT',          // 交易对
  label: 'Binance BTC/USDT',   // 显示标签
  color: '#ff9800'             // 曲线颜色
}
```

### ExchangeManager

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `exchanges` | Array | `[]` | 当前的交易所配置数组 |
| `onChange` | Function | - | 配置变化时的回调函数 |

## 🎨 预设颜色

组件提供了8种预设颜色，会按顺序分配给新添加的交易所：

```javascript
const colors = [
  '#ff9800',  // 橙色
  '#2196f3',  // 蓝色
  '#4caf50',  // 绿色
  '#f44336',  // 红色
  '#9c27b0',  // 紫色
  '#ff5722',  // 深橙色
  '#00bcd4',  // 青色
  '#ffeb3b'   // 黄色
];
```

## 🔄 数据更新机制

### 自动重新获取数据的情况

组件会在以下情况自动重新获取所有数据：

1. **交易所配置变化**: 添加/删除/修改交易所-币对
2. **时间周期变化**: 切换 interval (如从 15m 改为 1h)
3. **数据条数变化**: 修改 limit 值

### 数据获取流程

```
用户操作 → 状态更新 → useEffect 触发 → 
并行获取所有交易所数据 → 更新图表 → 自动调整时间范围
```

## 🌐 API 接口要求

### 端点

```
GET http://localhost:8000/api/klines
```

### 请求参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `exchange` | string | 交易所名称 |
| `symbol` | string | 交易对 |
| `interval` | string | 时间周期 |
| `limit` | string | 数据条数 |

### 响应格式

```json
{
  "success": true,
  "data": {
    "klines": [
      {
        "time": 1703123456789,
        "open": 50000.0,
        "high": 50100.0,
        "low": 49900.0,
        "close": 50050.0
      }
    ]
  }
}
```

**注意**: 组件只使用 `open` (开盘价) 数据来生成平滑曲线。

## 🎯 实际应用示例

### 在 DashboardPage 中集成

```jsx
export default function DashboardPage() {
  // 交易所配置
  const [exchanges, setExchanges] = useState([
    { exchange: 'binance', symbol: 'BTC/USDT', label: 'Binance BTC/USDT', color: '#ff9800' },
    { exchange: 'bybit', symbol: 'BTC/USDT', label: 'Bybit BTC/USDT', color: '#2196f3' },
  ]);

  // 图表参数
  const [interval, setInterval] = useState("15m");
  const [limit, setLimit] = useState(100);

  return (
    <Row gutter={12}>
      <Col span={6}>
        {/* 左侧控制面板 */}
        <Card title="周期选择">
          <Select
            value={interval}
            onChange={setInterval}
            options={[
              { value: "1m", label: "1分钟" },
              { value: "5m", label: "5分钟" },
              { value: "15m", label: "15分钟" },
              { value: "1h", label: "1小时" },
              { value: "4h", label: "4小时" },
              { value: "1d", label: "1天" },
            ]}
          />
        </Card>

        <Card title="数据条数">
          <InputNumber
            value={limit}
            onChange={setLimit}
            min={10}
            max={1000}
            step={10}
          />
        </Card>

        <ExchangeManager
          exchanges={exchanges}
          onChange={setExchanges}
        />
      </Col>

      <Col span={18}>
        {/* 右侧图表展示 */}
        <Card title={`多交易所价格对比 - ${interval} (${limit}条数据)`}>
          <MultiExchangeChart
            exchanges={exchanges}
            interval={interval}
            limit={limit}
            height={500}
          />
        </Card>
      </Col>
    </Row>
  );
}
```

## 🛠️ 高级功能

### 1. 动态添加交易所

```jsx
const addExchange = (exchange, symbol) => {
  const newConfig = {
    exchange,
    symbol,
    label: `${exchange} ${symbol}`,
    color: colors[exchanges.length % colors.length],
  };
  setExchanges([...exchanges, newConfig]);
};
```

### 2. 删除指定交易所

```jsx
const removeExchange = (index) => {
  const newExchanges = exchanges.filter((_, i) => i !== index);
  setExchanges(newExchanges);
};
```

### 3. 修改交易所配置

```jsx
const updateExchange = (index, field, value) => {
  const newExchanges = [...exchanges];
  newExchanges[index] = {
    ...newExchanges[index],
    [field]: value,
  };
  setExchanges(newExchanges);
};
```

## ⚠️ 注意事项

1. **性能优化**: 建议同时对比的交易所数量不超过 6 个，以保证图表渲染性能
2. **数据量控制**: limit 建议设置在 10-1000 之间，过大可能影响性能
3. **颜色区分**: 确保不同交易所使用不同的颜色，便于区分
4. **API 可用性**: 组件在 API 失败时会自动降级到模拟数据，确保用户体验

## 🐛 故障排除

### 图表不显示数据

1. 检查后端 API 是否正常运行
2. 检查浏览器控制台是否有错误信息
3. 确认 exchanges 数组不为空

### 数据不更新

1. 检查 interval 和 limit 是否正确传递
2. 确认 API 返回的数据格式正确
3. 查看网络请求是否成功

### 曲线重叠

1. 为不同交易所设置不同的颜色
2. 检查数据是否真的相同（同一交易所的同一币对）

## 📚 相关文档

- [TradingView Lightweight Charts 文档](https://tradingview.github.io/lightweight-charts/)
- [API 接口规格](../backend/API_REQUIREMENTS.md)
- [实时数据设置指南](../REAL_TIME_SETUP.md)




