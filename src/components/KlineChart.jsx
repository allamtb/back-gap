import React, { useEffect, useRef } from "react";
import * as echarts from "echarts";

/**
 * KlineChart
 * props:
 *  - dataA: [{time, open, high, low, close}], 必须包含 time(时间戳或日期字符串) 和 close
 *  - dataB: [{time, open, high, low, close}]
 *  - labelA: string (交易所A标签)
 *  - labelB: string (交易所B标签)
 *  - exchangeA: string (交易所A名称)
 *  - exchangeB: string (交易所B名称)
 *  - symbol: string (交易对，如 BTC/USDT)
 *  - interval: string (时间周期，如 15m)
 *  - upper: number (decimal, e.g. 0.003 = 0.3%)
 *  - lower: number (decimal, e.g. -0.002 = -0.2%)
 */
export default function KlineChart({
  dataA = [],
  dataB = [],
  labelA = "Exchange A",
  labelB = "Exchange B",
  exchangeA = "binance",
  exchangeB = "bybit",
  symbol = "BTC/USDT",
  interval = "15m",
  upper = 0.003,
  lower = -0.002,
}) {
  const chartRef = useRef(null);
  const instanceRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;
    
    // 确保DOM元素有尺寸
    const checkDimensions = () => {
      const element = chartRef.current;
      if (!element) return false;
      
      const rect = element.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };
    
    const updateChart = () => {
      if (!instanceRef.current) return;
      const chart = instanceRef.current;

      // 如果没有数据，显示空图表
      if (!dataA || dataA.length === 0) {
        const option = {
          title: { text: "暂无数据", left: "center", top: "center" },
          xAxis: { type: "category", data: [] },
          yAxis: { type: "value" },
          series: []
        };
        chart.setOption(option);
        chart.resize();
        return;
      }

      // x 轴
      const times = dataA.map((d) =>
        typeof d.time === "number"
          ? new Date(d.time).toLocaleString()
          : d.time
      );

      const pricesA = dataA.map((d) => d.close);
      const pricesB = dataB.map((d) => d.close);

      // 差值序列
      const diff = pricesA.map((p, i) => {
        if (!pricesB[i]) return null;
        return (p - pricesB[i]) / pricesB[i];
      });

      // 找出机会点
      const markPoints = [];
      diff.forEach((d, i) => {
        if (d == null) return;
        if (d > upper || d < lower) {
          markPoints.push({
            coord: [times[i], pricesA[i]],
            value: (d * 100).toFixed(2) + "%",
            itemStyle: { color: d > 0 ? "red" : "green" },
          });
        }
      });

      const option = {
        tooltip: {
          trigger: "axis",
        },
        legend: {
          data: [labelA, labelB],
        },
        xAxis: {
          type: "category",
          data: times,
          axisLabel: { showMaxLabel: true },
        },
        yAxis: {
          type: "value",
          scale: true,
        },
        series: [
          {
            name: labelA,
            type: "line",
            data: pricesA,
            smooth: true,
            symbolSize: 6,
            lineStyle: { width: 2 },
            markPoint: {
              data: markPoints,
            },
          },
          {
            name: labelB,
            type: "line",
            data: pricesB,
            smooth: true,
            symbolSize: 6,
            lineStyle: { width: 2 },
          },
        ],
      };

      chart.setOption(option);
      chart.resize();
    };
    
    // 如果尺寸为0，延迟初始化
    if (!checkDimensions()) {
      const timer = setTimeout(() => {
        if (checkDimensions() && !instanceRef.current) {
          instanceRef.current = echarts.init(chartRef.current);
          updateChart();
        }
      }, 100);
      return () => clearTimeout(timer);
    }
    
    // 初始化图表
    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }
    
    // 更新图表
    updateChart();

    const handleResize = () => {
      if (instanceRef.current) {
        instanceRef.current.resize();
      }
    };
    
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [dataA, dataB, labelA, labelB, exchangeA, exchangeB, symbol, interval, upper, lower]);

  // ResizeObserver 处理动态尺寸变化
  useEffect(() => {
    if (!chartRef.current || !instanceRef.current) return;
    
    const resizeObserver = new ResizeObserver(() => {
      if (instanceRef.current) {
        instanceRef.current.resize();
      }
    });
    
    resizeObserver.observe(chartRef.current);
    
    return () => {
      resizeObserver.disconnect();
    };
  }, [instanceRef.current]);

  // 清理函数
  useEffect(() => {
    return () => {
      if (instanceRef.current) {
        instanceRef.current.dispose();
        instanceRef.current = null;
      }
    };
  }, []);

  return (
    <div 
      ref={chartRef} 
      style={{ 
        width: "100%", 
        height: "500px",
        minHeight: "400px",
        minWidth: "300px"
      }} 
    />
  );
}
