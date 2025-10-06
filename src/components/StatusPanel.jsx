import React, { useEffect, useState, useRef } from "react";
import { Card, Tag, Button, Tooltip } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, QuestionCircleOutlined } from "@ant-design/icons";

function fetchWithTimeout(url, opts = {}, timeout = 3000) {
  return Promise.race([
    fetch(url, opts),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), timeout)),
  ]);
}

export default function StatusPanel({ refreshInterval = 15000, onRefresh }) {
  const [isNetworkConnected, setIsNetworkConnected] = useState(null);
  const timerRef = useRef(null);

  const check = async () => {
    let currentNetworkOk = false;
    
    // Check Python backend health endpoint
    try {
      const res = await fetchWithTimeout("/health", {}, 2500);
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      if (data.status === "healthy") {
        setIsNetworkConnected(true);
        currentNetworkOk = true;
      } else {
        setIsNetworkConnected(false);
        currentNetworkOk = false;
      }
    } catch (e) {
      setIsNetworkConnected(false);
      currentNetworkOk = false;
    }

    if (onRefresh) onRefresh({ networkOk: currentNetworkOk });
  };

  useEffect(() => {
    check();
    timerRef.current = setInterval(check, refreshInterval);
    return () => clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshInterval]);

  return (
    <Card 
      size="small" 
      title={
        <span>
          网络状态
          <Tooltip title="表示前端racat与后端python代码的连接状态">
            <QuestionCircleOutlined style={{ marginLeft: 8, color: '#999' }} />
          </Tooltip>
        </span>
      } 
      extra={<Button icon={<SyncOutlined />} onClick={() => check()}>刷新</Button>}
    >
      <div>
        网络状态: {isNetworkConnected === null ? <Tag>检测中...</Tag> : isNetworkConnected ? <Tag icon={<CheckCircleOutlined />} color="success">网络正常</Tag> : <Tag icon={<CloseCircleOutlined />} color="error">连接失败</Tag>}
      </div>
    </Card>
  );
}
