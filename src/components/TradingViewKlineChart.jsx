import React, { useEffect, useRef } from "react";
import { createChart } from "lightweight-charts";

/**
 * TradingViewKlineChart - 基于 TradingView 的价格曲线图组件
 * props:
 *  - dataA: [{time, value}] 交易所A的价格数据
 *  - dataB: [{time, value}] 交易所B的价格数据
 *  - labelA: string 交易所A标签
 *  - labelB: string 交易所B标签
 *  - symbol: string 交易对，如 BTC/USDT
 *  - interval: string 时间周期，如 15m
 *  - colorA: string 交易所A的颜色
 *  - colorB: string 交易所B的颜色
 */
export default function TradingViewKlineChart({
  dataA = [],
  dataB = [],
  labelA = "Exchange A",
  labelB = "Exchange B", 
  symbol = "BTC/USDT",
  interval = "15m",
  colorA = "#ff9800",
  colorB = "#2196f3",
}) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const lineSeriesARef = useRef(null);
  const lineSeriesBRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 创建图表实例
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
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

    chartRef.current = chart;

    // 创建两个平滑曲线系列
    const lineSeriesA = chart.addLineSeries({
      title: labelA,
      color: colorA,
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
    });

    const lineSeriesB = chart.addLineSeries({
      title: labelB,
      color: colorB,
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
    });

    lineSeriesARef.current = lineSeriesA;
    lineSeriesBRef.current = lineSeriesB;

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
      }
    };
  }, []);

  // 更新数据
  useEffect(() => {
    if (!lineSeriesARef.current || !lineSeriesBRef.current) return;

    // 转换数据格式（只需要时间和价格值）
    const convertData = (data) => {
      return data.map(item => ({
        time: typeof item.time === 'number' ? Math.floor(item.time / 1000) : Math.floor(new Date(item.time).getTime() / 1000),
        value: parseFloat(item.value),
      })).sort((a, b) => a.time - b.time); // 确保按时间排序
    };

    const convertedDataA = convertData(dataA);
    const convertedDataB = convertData(dataB);

    // 设置数据
    lineSeriesARef.current.setData(convertedDataA);
    lineSeriesBRef.current.setData(convertedDataB);

    // 自动调整时间范围
    if (convertedDataA.length > 0 || convertedDataB.length > 0) {
      const allData = [...convertedDataA, ...convertedDataB];
      const times = allData.map(d => d.time).filter(t => t);
      
      if (times.length > 0) {
        const minTime = Math.min(...times);
        const maxTime = Math.max(...times);
        
        chartRef.current?.timeScale().setVisibleRange({
          from: minTime,
          to: maxTime,
        });
      }
    }
  }, [dataA, dataB]);

  return (
    <div className="tradingview-kline-chart">
      <div 
        ref={chartContainerRef} 
        style={{ 
          width: "100%", 
          height: "500px",
          minHeight: "400px",
          minWidth: "300px"
        }} 
      />
    </div>
  );
}
