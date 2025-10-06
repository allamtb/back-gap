import React from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import { SettingOutlined, DashboardOutlined, BugOutlined, LineChartOutlined } from "@ant-design/icons";
import ConfigPage from "./pages/ConfigPage";
import DashboardPage from "./pages/DashboardPage";
import ComponentTest from "./pages/ComponentTest";
import KlineTestPage from "./pages/KlineTestPage";
import TradingViewTestPage from "./pages/TradingViewTestPage";
import MultiExchangeComparisonPage from "./pages/MultiExchangeComparisonPage";

const { Header, Content, Sider } = Layout;

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = location.pathname === "/" ? "/dashboard" : location.pathname;

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => navigate(key)}
          items={[
            { key: "/config", icon: <SettingOutlined />, label: "配置" },
            { key: "/dashboard", icon: <DashboardOutlined />, label: "监控" },
            { key: "/multi-exchange", icon: <LineChartOutlined />, label: "多交易所对比" },
            { key: "/test", icon: <BugOutlined />, label: "组件调试" },
            { key: "/kline-test", icon: <BugOutlined />, label: "K线测试" },
            { key: "/tradingview-test", icon: <BugOutlined />, label: "TradingView测试" },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff" }}>稳定套利交易系统</Header>
        <Content style={{ margin: "16px" }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/multi-exchange" element={<MultiExchangeComparisonPage />} />
            <Route path="/test" element={<ComponentTest />} />
            <Route path="/kline-test" element={<KlineTestPage />} />
            <Route path="/tradingview-test" element={<TradingViewTestPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}