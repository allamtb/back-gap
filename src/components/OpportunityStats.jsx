import React from "react";
import { Card, Table } from "antd";

const columns = [
  { title: "时间", dataIndex: "time" },
  { title: "交易所 A", dataIndex: "priceA" },
  { title: "交易所 B", dataIndex: "priceB" },
  { title: "差异%", dataIndex: "diffPct" }
];

export default function OpportunityStats() {
  // TODO: 接后端数据
  const data = [];
  return (
    <Card title="机会点统计">
      <Table columns={columns} dataSource={data} rowKey="time" size="small" />
    </Card>
  );
}
