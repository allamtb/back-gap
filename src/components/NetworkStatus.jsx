import React, { useEffect, useState, useRef } from "react";
import { Tag, Tooltip } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, QuestionCircleOutlined } from "@ant-design/icons";

function fetchWithTimeout(url, opts = {}, timeout = 8000) {
  return Promise.race([
    fetch(url, opts),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), timeout)),
  ]);
}

export default function NetworkStatus({ refreshInterval = 60000 }) {
  const [isNetworkConnected, setIsNetworkConnected] = useState(null);
  const [failureCount, setFailureCount] = useState(0);
  const timerRef = useRef(null);

  const check = async (retries = 3) => {
    for (let i = 0; i < retries; i++) {
      try {
        const res = await fetchWithTimeout("/health", {}, 8000);
        if (!res.ok) throw new Error("http " + res.status);
        const data = await res.json();
        if (data.status === "healthy") {
          setIsNetworkConnected(true);
          setFailureCount(0); // 成功后重置失败计数
          return;
        }
      } catch (e) {
        console.warn(`健康检查失败 (第${i + 1}/${retries}次):`, e.message);
        if (i < retries - 1) {
          // 重试前等待 1 秒
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }
    
    // 所有重试都失败后，增加失败计数
    setFailureCount(prev => prev + 1);
    
    // 连续失败 2 次才显示为失败状态，避免偶尔的网络波动
    if (failureCount >= 1) {
      setIsNetworkConnected(false);
    }
  };

  useEffect(() => {
    check();
    timerRef.current = setInterval(check, refreshInterval);
    return () => clearInterval(timerRef.current);
  }, [refreshInterval]);

  return (
    <Tooltip title="前端与后端Python代码的连接状态（每分钟自动刷新，自动重试3次，连续失败2次后显示异常）">
      <span style={{ marginLeft: 16, cursor: 'help' }}>
        {isNetworkConnected === null ? (
          <Tag>检测中...</Tag>
        ) : isNetworkConnected ? (
          <Tag icon={<CheckCircleOutlined />} color="success">网络正常</Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">连接失败</Tag>
        )}
        <QuestionCircleOutlined style={{ marginLeft: 4, color: '#999' }} />
      </span>
    </Tooltip>
  );
}

