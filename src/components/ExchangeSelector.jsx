import React, { useEffect, useState, useRef } from "react";
import { Card, Select, Form, Tag, Space, Button, Divider } from "antd";
import { CheckCircleOutlined, EyeOutlined, SyncOutlined } from "@ant-design/icons";

/**
 * ExchangeSelector
 * props:
 *  - selectedAccount: 当前选择的账户
 *  - onAccountChange: 账户改变回调
 *  - valueA, valueB: current selection
 *  - onChangeA, onChangeB: callbacks
 *  - refreshInterval: ms between auto checks (optional, default 15000)
 *
 * Ensures the two selects cannot pick the same exchange (disables the other value).
 * Loads account and exchange options from backend and shows their trading status.
 */

function fetchWithTimeout(url, opts = {}, timeout = 3000) {
  return Promise.race([
    fetch(url, opts),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), timeout)),
  ]);
}

export default function ExchangeSelector({ 
  valueA, 
  valueB, 
  onChangeA, 
  onChangeB,
  selectedAccount,
  onAccountChange,
  refreshInterval = 15000 
}) {
  // 所有可用的交易所列表（从后台加载）
  const [options, setOptions] = useState([]);
  // ConfigPage 中配置的交易所（可交易的交易所）
  const [configuredExchanges, setConfiguredExchanges] = useState([]);
  // 账户列表
  const [accounts, setAccounts] = useState([]);
  const timerRef = useRef(null);

  // 加载所有可用的交易所列表
  const loadExchanges = async () => {
    try {
      const res = await fetchWithTimeout("/api/exchanges", {}, 2500);
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      setOptions(Array.isArray(data) ? data : []);
    } catch (e) {
      setOptions([]);
    }
  };

  // 加载 ConfigPage 中配置的交易所
  const checkConfiguredExchanges = async () => {
    // 如果是默认账户，不调用 API
    if (!selectedAccount || selectedAccount === "默认") {
      setConfiguredExchanges([]);
      return;
    }
    
    try {
      const res = await fetchWithTimeout(`/api/accounts/${encodeURIComponent(selectedAccount)}/exchanges`, {}, 2500);
      if (!res.ok) throw new Error("http " + res.status);
      const result = await res.json();
      
      // 根据后端返回格式处理：{"success":true,"account":"毛凯","exchanges":["binance"]}
      if (result.success && result.exchanges) {
        setConfiguredExchanges(Array.isArray(result.exchanges) ? result.exchanges : []);
      } else {
        setConfiguredExchanges([]);
      }
    } catch (e) {
      setConfiguredExchanges([]);
    }
  };

  // 加载账户列表
  const loadAccounts = async () => {
    try {
      const res = await fetchWithTimeout("/api/accounts", {}, 2500);
      if (!res.ok) throw new Error("http " + res.status);
      const result = await res.json();
      
      // 根据后端返回格式处理
      if (result.success && result.data) {
        const accountNames = result.data.map(acc => acc.name);
        setAccounts(accountNames.length > 0 ? accountNames : ["默认"]);
      } else {
        setAccounts(["默认"]);
      }
    } catch (e) {
      setAccounts(["默认"]);
    }
  };

  // 刷新所有数据
  const refreshAll = async () => {
    await Promise.all([loadAccounts(), loadExchanges(), checkConfiguredExchanges()]);
  };

  useEffect(() => {
    refreshAll();
    timerRef.current = setInterval(refreshAll, refreshInterval);
    return () => clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshInterval, selectedAccount]);

  const opts = options.map((v) => ({ label: v, value: v }));
  const accountOpts = accounts.map((v) => ({ label: v, value: v }));

  return (
    <Card size="small" title="交易所选择" extra={<Button icon={<SyncOutlined />} onClick={() => refreshAll()}>刷新</Button>}>
      <Form layout="vertical">
        <Form.Item label="账户选择">
          <Select
            value={selectedAccount}
            onChange={onAccountChange}
            options={accountOpts}
            placeholder="选择账户"
          />
        </Form.Item>
        
        <Form.Item label="交易所 A">
          <Select
            value={valueA}
            onChange={onChangeA}
            options={opts.map((o) => ({ ...o, disabled: o.value === valueB }))}
            placeholder="选择交易所 A"
          />
        </Form.Item>
        <Form.Item label="交易所 B">
          <Select
            value={valueB}
            onChange={onChangeB}
            options={opts.map((o) => ({ ...o, disabled: o.value === valueA }))}
            placeholder="选择交易所 B"
          />
        </Form.Item>
      </Form>

      <Divider style={{ margin: "12px 0" }} />

      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>交易所状态</div>
        <Space direction="vertical">
          {!valueA && !valueB && <div style={{ color: "#888" }}>请选择交易所</div>}
          {valueA && (
            <div>
              {valueA}{" "}
              {configuredExchanges.includes(valueA) ? (
                <Tag icon={<CheckCircleOutlined />} color="success">可交易</Tag>
              ) : (
                <Tag icon={<EyeOutlined />} color="default">仅查看</Tag>
              )}
            </div>
          )}
          {valueB && (
            <div>
              {valueB}{" "}
              {configuredExchanges.includes(valueB) ? (
                <Tag icon={<CheckCircleOutlined />} color="success">可交易</Tag>
              ) : (
                <Tag icon={<EyeOutlined />} color="default">仅查看</Tag>
              )}
            </div>
          )}
        </Space>
      </div>
    </Card>
  );
}
