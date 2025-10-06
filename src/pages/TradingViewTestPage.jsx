import React, { useState, useEffect } from "react";
import TradingViewKlineChart from "../components/TradingViewKlineChart";

export default function TradingViewTestPage() {
  const [dataA, setDataA] = useState([]);
  const [dataB, setDataB] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // 配置状态
  const [config, setConfig] = useState({
    exchangeA: 'binance',
    exchangeB: 'bybit',
    symbol: 'BTC/USDT',
    interval: '15m',
    limit: 100
  });
  
  // 支持的选项
  const exchanges = [
    { value: 'binance', label: 'Binance' },
    { value: 'bybit', label: 'Bybit' },
    { value: 'okx', label: 'OKX' },
    { value: 'huobi', label: 'Huobi' },
    { value: 'kraken', label: 'Kraken' }
  ];
  
  const symbols = [
    { value: 'BTC/USDT', label: 'BTC/USDT' },
    { value: 'ETH/USDT', label: 'ETH/USDT' },
    { value: 'BNB/USDT', label: 'BNB/USDT' },
    { value: 'ADA/USDT', label: 'ADA/USDT' },
    { value: 'SOL/USDT', label: 'SOL/USDT' }
  ];
  
  const intervals = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '30m', label: '30分钟' },
    { value: '1h', label: '1小时' },
    { value: '4h', label: '4小时' },
    { value: '1d', label: '1天' }
  ];

  // 生成模拟数据（只使用开盘价，生成平滑曲线）
  const generateMockData = (basePrice = 50000, volatility = 0.02) => {
    const data = [];
    let currentPrice = basePrice;
    const now = Date.now();
    
    // 生成过去24小时的15分钟采样数据
    for (let i = 96; i >= 0; i--) {
      const time = now - (i * 15 * 60 * 1000); // 15分钟间隔
      
      // 模拟价格波动
      const change = (Math.random() - 0.5) * volatility * currentPrice;
      currentPrice = currentPrice + change;
      
      data.push({
        time: time,
        value: parseFloat(currentPrice.toFixed(2))
      });
    }
    
    return data;
  };

  // 获取K线数据
  const fetchKlineData = async (configData = config) => {
    try {
      setLoading(true);
      setError(null);
      
      // 构建API URL
      const urlA = `/api/klines?exchange=${configData.exchangeA}&symbol=${configData.symbol}&interval=${configData.interval}&limit=${configData.limit}`;
      const urlB = `/api/klines?exchange=${configData.exchangeB}&symbol=${configData.symbol}&interval=${configData.interval}&limit=${configData.limit}`;
      
      // 并行获取两个交易所的数据
      const [responseA, responseB] = await Promise.all([
        fetch(urlA),
        fetch(urlB)
      ]);
      
      const [resultA, resultB] = await Promise.all([
        responseA.json(),
        responseB.json()
      ]);
      
      if (resultA.success && resultB.success) {
        // 只提取开盘价数据
        const extractedDataA = resultA.data.klines.map(item => ({
          time: item.time,
          value: parseFloat(item.open)
        }));
        const extractedDataB = resultB.data.klines.map(item => ({
          time: item.time,
          value: parseFloat(item.open)
        }));
        
        setDataA(extractedDataA);
        setDataB(extractedDataB);
        setError(null);
      } else {
        const errorMsg = resultA.error || resultB.error || '获取K线数据失败';
        setError(errorMsg);
        console.error('获取K线数据失败:', errorMsg);
        
        // 如果API失败，使用模拟数据作为备选
        setDataA(generateMockData(50000, 0.02));
        setDataB(generateMockData(50050, 0.025));
      }
    } catch (error) {
      const errorMsg = `网络错误: ${error.message}`;
      setError(errorMsg);
      console.error('网络错误:', error);
      
      // 网络错误时使用模拟数据
      setDataA(generateMockData(50000, 0.02));
      setDataB(generateMockData(50050, 0.025));
    } finally {
      setLoading(false);
    }
  };

  // 配置变化时重新获取数据
  useEffect(() => {
    fetchKlineData();
  }, [config]);

  // 处理配置变化
  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // 手动刷新数据
  const handleRefresh = () => {
    fetchKlineData();
  };

  // 样式定义
  const styles = {
    container: {
      padding: '20px',
      maxWidth: '1200px',
      margin: '0 auto'
    },
    header: {
      marginBottom: '20px'
    },
    title: {
      fontSize: '28px',
      fontWeight: 'bold',
      marginBottom: '10px',
      color: '#333'
    },
    subtitle: {
      fontSize: '16px',
      color: '#666',
      marginBottom: '20px'
    },
    controls: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: '15px',
      marginBottom: '20px',
      padding: '20px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #e9ecef'
    },
    controlGroup: {
      display: 'flex',
      flexDirection: 'column',
      minWidth: '150px'
    },
    label: {
      fontSize: '14px',
      fontWeight: '500',
      marginBottom: '5px',
      color: '#495057'
    },
    select: {
      padding: '8px 12px',
      border: '1px solid #ced4da',
      borderRadius: '4px',
      fontSize: '14px',
      backgroundColor: 'white',
      cursor: 'pointer'
    },
    button: {
      padding: '8px 16px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      alignSelf: 'flex-end',
      marginTop: '20px'
    },
    buttonHover: {
      backgroundColor: '#0056b3'
    },
    legend: {
      marginBottom: '20px',
      padding: '15px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #e9ecef'
    },
    legendTitle: {
      fontSize: '16px',
      fontWeight: '600',
      marginBottom: '10px',
      color: '#333'
    },
    legendItem: {
      display: 'flex',
      alignItems: 'center',
      marginBottom: '5px',
      fontSize: '14px'
    },
    colorBox: {
      width: '16px',
      height: '16px',
      marginRight: '8px',
      borderRadius: '2px'
    },
    error: {
      backgroundColor: '#f8d7da',
      color: '#721c24',
      padding: '12px',
      borderRadius: '4px',
      marginBottom: '20px',
      border: '1px solid #f5c6cb'
    },
    loading: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '500px',
      fontSize: '18px',
      color: '#666'
    }
  };

  if (loading) {
    return (
      <div style={styles.loading}>
        <div>🔄 正在加载K线数据...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>📊 交易所K线对比分析</h1>
        <p style={styles.subtitle}>实时对比不同交易所的K线数据，支持多种币种和时间周期</p>
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={styles.error}>
          ⚠️ {error}
        </div>
      )}

      {/* 控制面板 */}
      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>交易所A</label>
          <select 
            style={styles.select}
            value={config.exchangeA}
            onChange={(e) => handleConfigChange('exchangeA', e.target.value)}
          >
            {exchanges.map(exchange => (
              <option key={exchange.value} value={exchange.value}>
                {exchange.label}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>交易所B</label>
          <select 
            style={styles.select}
            value={config.exchangeB}
            onChange={(e) => handleConfigChange('exchangeB', e.target.value)}
          >
            {exchanges.map(exchange => (
              <option key={exchange.value} value={exchange.value}>
                {exchange.label}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>交易对</label>
          <select 
            style={styles.select}
            value={config.symbol}
            onChange={(e) => handleConfigChange('symbol', e.target.value)}
          >
            {symbols.map(symbol => (
              <option key={symbol.value} value={symbol.value}>
                {symbol.label}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>时间周期</label>
          <select 
            style={styles.select}
            value={config.interval}
            onChange={(e) => handleConfigChange('interval', e.target.value)}
          >
            {intervals.map(interval => (
              <option key={interval.value} value={interval.value}>
                {interval.label}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.controlGroup}>
          <label style={styles.label}>数据条数</label>
          <select 
            style={styles.select}
            value={config.limit}
            onChange={(e) => handleConfigChange('limit', parseInt(e.target.value))}
          >
            <option value={50}>50条</option>
            <option value={100}>100条</option>
            <option value={200}>200条</option>
            <option value={500}>500条</option>
          </select>
        </div>

        <button 
          style={styles.button}
          onClick={handleRefresh}
          onMouseOver={(e) => e.target.style.backgroundColor = '#0056b3'}
          onMouseOut={(e) => e.target.style.backgroundColor = '#007bff'}
        >
          🔄 刷新数据
        </button>
      </div>

      {/* 图例说明 */}
      <div style={styles.legend}>
        <h3 style={styles.legendTitle}>📈 图表说明</h3>
        <div style={styles.legendItem}>
          <div style={{...styles.colorBox, backgroundColor: '#ff9800'}}></div>
          <span>交易所A ({exchanges.find(e => e.value === config.exchangeA)?.label}) - 橙色</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{...styles.colorBox, backgroundColor: '#2196f3'}}></div>
          <span>交易所B ({exchanges.find(e => e.value === config.exchangeB)?.label}) - 蓝色</span>
        </div>
      </div>

      {/* K线图表 */}
      <TradingViewKlineChart
        dataA={dataA}
        dataB={dataB}
        labelA={exchanges.find(e => e.value === config.exchangeA)?.label || 'Exchange A'}
        labelB={exchanges.find(e => e.value === config.exchangeB)?.label || 'Exchange B'}
        symbol={config.symbol}
        interval={config.interval}
        colorA="#ff9800"
        colorB="#2196f3"
      />
    </div>
  );
}
