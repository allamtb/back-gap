import React, { useCallback } from "react";
import { Row, Col, Card, Tabs, Input, message, Space } from "antd";
import MultiExchangeChart from "../components/MultiExchangeChart";
import ExchangeManager from "../components/ExchangeManager";
import TradingConfig from "../components/TradingConfig";
import RealtimePriceTable from "../components/RealtimePriceTable";
import OrderBookPanel from "../components/OrderBookPanel";
import DrawerResizeHandle from "../components/DrawerResizeHandle";
import { useWebSocketTicker } from "../hooks/useWebSocketTicker";
import { useWebSocketDepth } from "../hooks/useWebSocketDepth";
import { useTabManager } from "../hooks/useTabManager";
import { useDrawerResize } from "../hooks/useDrawerResize";
import { formatPrice } from "../utils/formatters";

// 默认 Tab 配置
const DEFAULT_TAB_CONFIG = {
  exchanges: [
    { exchange: 'binance', symbol: 'BTC/USDT', market_type: 'spot', label: 'Binance BTC/USDT', color: '#ff9800' },
    { exchange: 'bybit', symbol: 'BTC/USDT', market_type: 'spot', label: 'Bybit BTC/USDT', color: '#2196f3' },
  ]
};

// 生成默认 Tab 名称（根据主要币对）
const generateTabLabel = (exchanges) => {
  if (!exchanges || exchanges.length === 0) {
    return '监控面板';
  }
  // 提取第一个交易所的币对基础币种
  const firstSymbol = exchanges[0].symbol;
  const baseCurrency = firstSymbol.split('/')[0];
  return `${baseCurrency} 监控`;
};

export default function DashboardPage() {
  // ==================== Tab 管理 ====================
  const tabManager = useTabManager({
    storageKey: 'dashboard_tabs_config',
    generateTabLabel,
    defaultExchanges: DEFAULT_TAB_CONFIG.exchanges,
    maxTabs: 10
  });

  const {
    tabs,
    activeKey,
    setActiveKey,
    editingKey,
    editingLabel,
    setEditingLabel,
    inputRef,
    onEdit,
    startEdit,
    finishEdit,
    cancelEdit,
    updateCurrentTabExchanges,
    currentExchanges
  } = tabManager;

  // ==================== 可拖动抽屉 ====================
  const {
    drawerWidth,
    isResizing,
    resizeRef,
    startResizing
  } = useDrawerResize({
    storageKey: 'config_drawer_width',
    defaultWidth: 300,
    minWidth: 80,
    maxWidth: 300,
    siderWidth: 200
  });

  // ==================== WebSocket 订阅（Ticker 和 Depth） ====================
  // Ticker 数据回调
  const handleTickerUpdate = useCallback((exchange, symbol, marketType, ticker) => {
    // console.log('📈 Ticker 更新:', exchange, symbol, ticker);
  }, []);

  // Depth 数据回调
  const handleDepthUpdate = useCallback((exchange, symbol, marketType, depth) => {
    // console.log('📊 Depth 更新:', exchange, symbol, depth);
  }, []);

  // 订阅 Ticker 数据（只在有配置时启用）
  const { tickerData } = useWebSocketTicker(
    currentExchanges,
    handleTickerUpdate,
    currentExchanges.length > 0 // 只有配置了交易所才启用
  );

  // 订阅 Depth 数据（只在有配置时启用）
  const { depthData } = useWebSocketDepth(
    currentExchanges,
    handleDepthUpdate,
    currentExchanges.length > 0 // 只有配置了交易所才启用
  );

  // ==================== 订单薄价格点击处理 ====================
  // 处理订单薄价格双击，自动填入限价单
  const handleOrderBookPriceClick = useCallback((exchange, symbol, marketType, price, side) => {
    // 这里需要与RealtimePriceTable组件通信
    // 由于组件间通信复杂，我们使用全局事件或状态管理
    // 暂时使用localStorage作为简单的跨组件通信方式
    const priceData = {
      exchange,
      symbol,
      marketType,
      price,
      side,
      timestamp: Date.now()
    };
    
    localStorage.setItem('orderbook_price_click', JSON.stringify(priceData));
    
    // 触发自定义事件，通知RealtimePriceTable组件
    window.dispatchEvent(new CustomEvent('orderbookPriceClick', { 
      detail: priceData 
    }));
    
    message.success(`已选择${side === 'buy' ? '买入' : '卖出'}价格: ${formatPrice(price)}`);
  }, []);

  // 渲染 Tab 标签（支持双击编辑）
  const renderTabLabel = (tab) => {
    if (editingKey === tab.key) {
      return (
        <Input
          ref={inputRef}
          size="small"
          value={editingLabel}
          onChange={(e) => setEditingLabel(e.target.value)}
          onBlur={finishEdit}
          onPressEnter={finishEdit}
          onKeyDown={(e) => {
            // 阻止 Backspace 和其他编辑键的默认行为（防止触发 Tab 删除）
            if (e.key === 'Escape') {
              e.stopPropagation();
              cancelEdit();
            } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key.length === 1) {
              // 阻止事件冒泡到 Tabs 组件
              e.stopPropagation();
            }
          }}
          style={{ width: 120 }}
          onClick={(e) => e.stopPropagation()}
          placeholder="输入标签名称"
          title="编辑标签名称"
          aria-label="编辑标签名称"
        />
      );
    }

    return (
      <span
        onDoubleClick={(e) => {
          e.stopPropagation();
          startEdit(tab.key, tab.label);
        }}
        style={{ cursor: 'text', userSelect: 'none' }}
        title="双击编辑名称"
      >
        {tab.label}
      </span>
    );
  };

  // 构建 Tabs items
  const tabItems = tabs.map(tab => ({
    key: tab.key,
    label: renderTabLabel(tab),
    children: (
      <div style={{ position: 'relative' }}>
        {/* 主内容区 */}
        <div style={{ 
          marginLeft: `${drawerWidth}px`,
          transition: isResizing ? 'none' : 'margin-left 0.3s ease',
          padding: '0 12px'
        }}>
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            {/* 第一行：下单区域（核心功能上移） */}
            <Row gutter={12}>
              <Col span={24}>
                <Card 
                  title="💹 实时价格监控 & 下单"
                  size="small"
                  bodyStyle={{ padding: '12px' }}
                >
                  <RealtimePriceTable
                    exchanges={tab.exchanges}
                    tickerData={tab.key === activeKey ? tickerData : {}}
                  />
                </Card>
              </Col>
            </Row>

            {/* 第二行：K线图 + 订单簿对比 */}
            <Row gutter={12}>
              {/* K线图（左侧，占60%宽度） */}
              <Col span={14}>
                <Card 
                  title="📈 多交易所价格对比"
                  size="small"
                  bodyStyle={{ padding: '12px', overflow: 'visible' }}
                >
                  <MultiExchangeChart
                    exchanges={tab.exchanges}
                    height={440}
                  />
                </Card>
              </Col>

              {/* 订单簿对比（右侧，占40%宽度） */}
              <Col span={10}>
                <OrderBookPanel
                  exchanges={tab.exchanges}
                  depthData={tab.key === activeKey ? depthData : {}}
                  onPriceClick={handleOrderBookPriceClick}
                  style={{ height: '500px' }}
                />
              </Col>
            </Row>
          </Space>
        </div>

        {/* 可拖动的配置抽屉（从内容区左侧滑出，不覆盖 Sider） */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: `${drawerWidth}px`,
            transition: isResizing ? 'none' : 'width 0.3s ease',
            backgroundColor: '#fff',
            boxShadow: drawerWidth > 0 ? '2px 0 8px rgba(0,0,0,0.15)' : 'none',
            zIndex: 100,
            display: 'flex',
            overflow: 'hidden'
          }}
        >
          {/* 抽屉内容区 */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            overflowX: 'hidden',
            padding: '12px'
          }}>
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              <div style={{ 
                fontSize: '16px', 
                fontWeight: 600, 
                color: '#1890ff',
                marginBottom: 8,
                paddingBottom: 8,
                borderBottom: '2px solid #1890ff'
              }}>
                配置面板
              </div>
              
              {/* 添加币对（交易所配置） */}
              <ExchangeManager
                exchanges={tab.exchanges}
                onChange={updateCurrentTabExchanges}
              />
              
              {/* 交易配置 */}
              <TradingConfig />
            </Space>
          </div>

          {/* 拖动手柄 */}
          <DrawerResizeHandle
            resizeRef={resizeRef}
            onMouseDown={startResizing}
            isResizing={isResizing}
            drawerWidth={drawerWidth}
          />
        </div>
      </div>
    )
  }));

  return (
    <div>
      <Tabs
        type="editable-card"
        activeKey={activeKey}
        onChange={setActiveKey}
        onEdit={onEdit}
        items={tabItems}
        style={{ marginBottom: -12 }}
        aria-label="监控面板标签页"
      />
    </div>
  );
}
