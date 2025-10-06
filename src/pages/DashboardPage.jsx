import React, { useState } from "react";
import { Row, Col, Card } from "antd";
import MultiExchangeChart from "../components/MultiExchangeChart";
import ExchangeManager from "../components/ExchangeManager";
import StatusPanel from "../components/StatusPanel";

export default function DashboardPage() {
  // 多交易所对比配置
  const [exchanges, setExchanges] = useState([
    { exchange: 'binance', symbol: 'BTC/USDT', label: 'Binance BTC/USDT', color: '#ff9800' },
    { exchange: 'bybit', symbol: 'BTC/USDT', label: 'Bybit BTC/USDT', color: '#2196f3' },
  ]);

  return (
    <div>
      <Row gutter={12}>
        {/* 左侧控制区 */}
        <Col span={6}>
          <StatusPanel />

          <div style={{ marginTop: 12 }}>
            <ExchangeManager
              exchanges={exchanges}
              onChange={setExchanges}
            />
          </div>
        </Col>
        
        {/* 右侧展示区 */}
        <Col span={18}>
          {/* 多交易所价格曲线对比图表 */}
          <Card 
            title="多交易所价格对比"
          >
            <MultiExchangeChart
              exchanges={exchanges}
              height={500}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
