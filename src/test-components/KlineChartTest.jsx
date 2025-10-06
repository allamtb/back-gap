import React, { useState, useEffect } from 'react';
import { Card, Button, Space, InputNumber, Select } from 'antd';
import KlineChart from '../components/KlineChart';

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

export default function KlineChartTest() {
  const [dataA, setDataA] = useState(generateTestData(50000));
  const [dataB, setDataB] = useState(generateTestData(50000));
  const [labelA, setLabelA] = useState('Binance');
  const [labelB, setLabelB] = useState('Bybit');
  const [upper, setUpper] = useState(0.003);
  const [lower, setLower] = useState(-0.002);

  const handleRegenerateData = () => {
    setDataA(generateTestData(50000));
    setDataB(generateTestData(50000));
  };

  const handleGenerateGapData = () => {
    setDataA(generateTestData(30000)); // 较低价格
    setDataB(generateTestData(70000)); // 较高价格
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card title="KlineChart 组件测试" style={{ marginBottom: '20px' }}>
        <Space wrap>
          <Button onClick={handleRegenerateData}>重新生成数据</Button>
          <Button onClick={handleGenerateGapData}>生成价格差异数据</Button>
          <Button onClick={() => setDataA([])}>清空数据A</Button>
          <Button onClick={() => setDataB([])}>清空数据B</Button>
        </Space>
        
        <div style={{ marginTop: '20px' }}>
          <Space>
            <span>标签A:</span>
            <Select value={labelA} onChange={setLabelA} style={{ width: 120 }}>
              <Select.Option value="Binance">Binance</Select.Option>
              <Select.Option value="Bybit">Bybit</Select.Option>
              <Select.Option value="OKX">OKX</Select.Option>
            </Select>
            
            <span>标签B:</span>
            <Select value={labelB} onChange={setLabelB} style={{ width: 120 }}>
              <Select.Option value="Binance">Binance</Select.Option>
              <Select.Option value="Bybit">Bybit</Select.Option>
              <Select.Option value="OKX">OKX</Select.Option>
            </Select>
            
            <span>上阈值:</span>
            <InputNumber 
              value={upper} 
              onChange={setUpper} 
              step={0.001} 
              precision={3}
              style={{ width: 100 }}
            />
            
            <span>下阈值:</span>
            <InputNumber 
              value={lower} 
              onChange={setLower} 
              step={0.001} 
              precision={3}
              style={{ width: 100 }}
            />
          </Space>
        </div>
      </Card>

      <Card title="图表显示">
        <KlineChart
          dataA={dataA}
          dataB={dataB}
          labelA={labelA}
          labelB={labelB}
          upper={upper}
          lower={lower}
        />
      </Card>

      {/* 调试信息 */}
      <Card title="调试信息" style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', gap: '20px' }}>
          <div>
            <h4>数据A (前3条):</h4>
            <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', maxHeight: '200px', overflow: 'auto' }}>
              {JSON.stringify(dataA.slice(0, 3), null, 2)}
            </pre>
          </div>
          <div>
            <h4>数据B (前3条):</h4>
            <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', maxHeight: '200px', overflow: 'auto' }}>
              {JSON.stringify(dataB.slice(0, 3), null, 2)}
            </pre>
          </div>
          <div>
            <h4>组件Props:</h4>
            <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
              {JSON.stringify({
                dataALength: dataA.length,
                dataBLength: dataB.length,
                labelA,
                labelB,
                upper,
                lower
              }, null, 2)}
            </pre>
          </div>
        </div>
      </Card>
    </div>
  );
}


