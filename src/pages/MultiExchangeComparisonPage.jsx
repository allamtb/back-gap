import React, { useState } from "react";
import { Row, Col, Card, Space, Typography, Divider } from "antd";
import MultiExchangeChart from "../components/MultiExchangeChart";
import ExchangeManager from "../components/ExchangeManager";

const { Title, Text } = Typography;

/**
 * MultiExchangeComparisonPage - 多交易所价格对比页面
 * 演示如何使用 MultiExchangeChart 和 ExchangeManager 组件
 * （使用重构后的版本，interval 和 limit 由组件内部管理）
 */
export default function MultiExchangeComparisonPage() {
  // 多交易所对比配置
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

  return (
    <div style={{ padding: '20px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>多交易所价格对比</Title>
        <Text type="secondary">
          动态添加/删除交易所，实时对比不同平台的价格走势
        </Text>
      </div>

      <Row gutter={16}>
        {/* 左侧控制面板 */}
        <Col xs={24} md={8} lg={6}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {/* 交易所配置管理 */}
            <ExchangeManager
              exchanges={exchanges}
              onChange={setExchanges}
            />

            {/* 使用说明 */}
            <Card size="small" title="💡 使用说明" style={{ marginTop: 16 }}>
              <Space direction="vertical" size="small">
                <Text style={{ fontSize: '12px' }}>
                  • 点击"添加"按钮新增交易所
                </Text>
                <Text style={{ fontSize: '12px' }}>
                  • 每个配置可单独设置交易所、币种和颜色
                </Text>
                <Text style={{ fontSize: '12px' }}>
                  • 在图表控制面板调整周期和数据条数
                </Text>
                <Text style={{ fontSize: '12px' }}>
                  • 开启"实时数据"开关可接收 WebSocket 推送
                </Text>
                <Text style={{ fontSize: '12px' }}>
                  • 可启用差异标注功能，标记价格差异超过阈值的点
                </Text>
                <Text style={{ fontSize: '12px' }}>
                  • 选择2个交易所可进行价差比对
                </Text>
                <Text style={{ fontSize: '12px' }}>
                  • 图表支持缩放和拖拽查看
                </Text>
              </Space>
            </Card>
          </Space>
        </Col>

        {/* 右侧图表展示 */}
        <Col xs={24} md={16} lg={18}>
          <Card 
            title={
              <Space>
                <span>📈 价格走势对比</span>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                  {exchanges.length}个交易所
                </Text>
              </Space>
            }
          >
            <MultiExchangeChart
              exchanges={exchanges}
              height={600}
            />
          </Card>

          {/* 图表说明 */}
          <Card 
            size="small" 
            title="🎯 图表说明" 
            style={{ marginTop: 16 }}
          >
            <Row gutter={16}>
              <Col span={8}>
                <Text strong>曲线颜色</Text>
                <div style={{ marginTop: 8 }}>
                  {exchanges.map((ex, index) => (
                    <div key={index} style={{ marginBottom: 4 }}>
                      <span
                        style={{
                          display: 'inline-block',
                          width: 40,
                          height: 3,
                          backgroundColor: ex.color,
                          marginRight: 8,
                          verticalAlign: 'middle',
                        }}
                      />
                      <Text style={{ fontSize: '12px' }}>{ex.label}</Text>
                    </div>
                  ))}
                </div>
              </Col>
              <Col span={8}>
                <Text strong>操作说明</Text>
                <div style={{ marginTop: 8, fontSize: '12px' }}>
                  <div>• 鼠标滚轮：缩放时间轴</div>
                  <div>• 拖拽：移动时间范围</div>
                  <div>• 双击：重置视图</div>
                  <div>• 十字线：查看精确数值</div>
                </div>
              </Col>
              <Col span={8}>
                <Text strong>数据说明</Text>
                <div style={{ marginTop: 8, fontSize: '12px' }}>
                  <div>• 使用收盘价生成曲线</div>
                  <div>• 自动按时间排序</div>
                  <div>• WebSocket 实时推送更新</div>
                  <div>• 周期一致（历史+实时）</div>
                  <div>• 差异标注显示价格偏离</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
}


