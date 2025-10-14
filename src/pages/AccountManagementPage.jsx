import React, { useState } from "react";
import { Tabs } from "antd";
import { WalletOutlined, OrderedListOutlined } from "@ant-design/icons";
import PositionMonitor from "../components/PositionMonitor";
import OrderMonitor from "../components/OrderMonitor";

export default function AccountManagementPage() {
  const [activeTab, setActiveTab] = useState("positions");

  const tabItems = [
    {
      key: "positions",
      label: (
        <span>
          <WalletOutlined />
          资金和持仓监控
        </span>
      ),
      children: <PositionMonitor />,
    },
    {
      key: "orders",
      label: (
        <span>
          <OrderedListOutlined />
          订单监控
        </span>
      ),
      children: <OrderMonitor />,
    },
  ];

  return (
    <div style={{ padding: "16px", background: "#f0f2f5", minHeight: "100%" }}>
      <h2 style={{ marginBottom: "16px", marginTop: 0 }}>账户管理</h2>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />
    </div>
  );
}

