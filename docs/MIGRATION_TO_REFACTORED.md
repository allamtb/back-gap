# 迁移到重构版本指南

## ✅ 已完成迁移

### 更新的页面

1. **DashboardPage** (`src/pages/DashboardPage.jsx`)
   - ✅ 已切换到 `MultiExchangeChart.refactored`
   
2. **MultiExchangeComparisonPage** (`src/pages/MultiExchangeComparisonPage.jsx`)
   - ✅ 已切换到 `MultiExchangeChart.refactored`
   - ✅ 移除了外部的 `interval` 和 `limit` 状态管理
   - ✅ 简化了控制面板（移除了周期和数据条数选择器）

## 📝 主要变化

### 之前（旧版本）
```jsx
import MultiExchangeChart from "../components/MultiExchangeChart";

// 需要在父组件管理这些状态
const [interval, setInterval] = useState("15m");
const [limit, setLimit] = useState(100);

<MultiExchangeChart
  exchanges={exchanges}
  interval={interval}
  limit={limit}
  height={600}
/>
```

### 现在（重构版本）
```jsx
import MultiExchangeChart from "../components/MultiExchangeChart.refactored";

// 不需要管理 interval 和 limit，组件内部管理

<MultiExchangeChart
  exchanges={exchanges}
  height={600}
/>
```

## 🎯 重构版本的优势

### 1. **内置控制面板**
- ⏰ 周期选择（1m, 5m, 15m, 1h, 4h, 1d）
- 📊 数据条数调整（10-1000条）
- 🔴 差异标注开关
- 📏 差异阈值滑块（1-500）

### 2. **模块化架构**
```
MultiExchangeChart.refactored
├── useExchangeData      # 数据获取和管理
├── useChartManager      # 图表生命周期管理
├── useExchangeManager   # 交易所动态增删
└── usePriceMarkers      # 价格差异标注
```

### 3. **更好的代码组织**
- ✅ 每个 Hook 职责单一
- ✅ 易于测试和维护
- ✅ 代码复用性高

## 🔄 如何迁移其他页面

如果你有其他使用旧版本组件的页面：

1. **更新导入**
   ```jsx
   // 之前
   import MultiExchangeChart from "../components/MultiExchangeChart";
   
   // 之后
   import MultiExchangeChart from "../components/MultiExchangeChart.refactored";
   ```

2. **移除不需要的 props**
   ```jsx
   // 移除 interval 和 limit props
   <MultiExchangeChart
     exchanges={exchanges}
     height={600}
     // ❌ 不再需要 interval={interval}
     // ❌ 不再需要 limit={limit}
   />
   ```

3. **移除相关的状态管理**
   ```jsx
   // ❌ 删除这些
   const [interval, setInterval] = useState("15m");
   const [limit, setLimit] = useState(100);
   ```

## 📦 文件状态

### 保留的文件（向后兼容）
- `src/components/MultiExchangeChart.jsx` - 旧版本，保留用于兼容性

### 新文件
- `src/components/MultiExchangeChart.refactored.jsx` - 重构版本
- `src/hooks/useExchangeData.js` - 数据管理 Hook
- `src/hooks/useChartManager.js` - 图表管理 Hook
- `src/hooks/useExchangeManager.js` - 交易所管理 Hook
- `src/hooks/usePriceMarkers.js` - 价格差异标注 Hook
- `src/utils/chartUtils.js` - 工具函数

## 🎨 新增功能

### 差异标注功能
重构版本新增了强大的价格差异标注功能：

```jsx
// 自动标注价格差异超过阈值的点
// 在图表上显示粉红色 🔴 圆点和差异值 "Δ80.0"
```

**配置选项：**
- 🔘 **开关**：启用/关闭差异标注
- 📏 **阈值**：调整差异阈值（1-500）

## 🚀 运行测试

迁移完成后，请测试以下功能：

- [ ] 添加/删除交易所
- [ ] 切换时间周期
- [ ] 调整数据条数
- [ ] 开启/关闭差异标注
- [ ] 调整差异阈值
- [ ] 图表缩放和拖拽
- [ ] 错误处理（网络错误、API 失败）

## 📞 问题反馈

如果在迁移过程中遇到问题，请检查：

1. 导入路径是否正确
2. 是否移除了不需要的 props
3. 浏览器控制台是否有错误信息

---

**最后更新**: 2024-10-06
**状态**: ✅ 迁移完成










