import React, { useEffect, useRef } from "react";
import { createChart } from "lightweight-charts";

export default function ChartPanel({ wsUrl, exchangeA, exchangeB, symbol, timeframe, threshold }) {
  const chartRef = useRef(null);
  const seriesARef = useRef(null);
  const seriesBRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    const chart = createChart(chartRef.current, { width: 900, height: 400 });
    const sA = chart.addLineSeries({ color: "red", title: exchangeA });
    const sB = chart.addLineSeries({ color: "green", title: exchangeB });
    seriesARef.current = sA;
    seriesBRef.current = sB;
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [exchangeA, exchangeB]);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({ exchange_a: exchangeA, exchange_b: exchangeB, symbol, timeframe, threshold }));
    };
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "kline") {
        const p = { time: Math.floor(msg.kline.t / 1000), value: msg.kline.c };
        if (msg.exchange === exchangeA) seriesARef.current.update(p);
        if (msg.exchange === exchangeB) seriesBRef.current.update(p);
      } else if (msg.type === "opportunity") {
        markersRef.current.push({
          time: Math.floor(msg.time / 1000),
          position: "aboveBar",
          color: "blue",
          shape: "circle",
          text: `${(msg.diff_pct * 100).toFixed(2)}%`
        });
        seriesARef.current.setMarkers(markersRef.current);
      }
    };
    return () => ws.close();
  }, [exchangeA, exchangeB, symbol, timeframe, threshold, wsUrl]);

  return <div ref={chartRef} />;
}
