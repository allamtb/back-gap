import React from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import { SettingOutlined, DashboardOutlined, BugOutlined, LineChartOutlined, WalletOutlined } from "@ant-design/icons";
import ConfigPage from "./pages/ConfigPage";
import DashboardPage from "./pages/DashboardPage";
import ComponentTest from "./pages/ComponentTest";
import TradingViewTestPage from "./pages/TradingViewTestPage";
import MultiExchangeComparisonPage from "./pages/MultiExchangeComparisonPage";
import AccountManagementPage from "./pages/AccountManagementPage";
import "./App.css";

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
            { key: "/config", icon: <SettingOutlined />, label: "交易所配置" },
            { key: "/account", icon: <WalletOutlined />, label: "账户监控" },
            { key: "/dashboard", icon: <DashboardOutlined />, label: "交易监控" },
            // { key: "/multi-exchange", icon: <LineChartOutlined />, label: "多交易所对比" },

            // { key: "/test", icon: <BugOutlined />, label: "组件调试" },
            // { key: "/tradingview-test", icon: <BugOutlined />, label: "TradingView测试" },
          ]}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <h1 className="app-header-title">稳定套利交易系统</h1>
        </Header>
        <Content style={{ margin: "16px" }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/multi-exchange" element={<MultiExchangeComparisonPage />} />
            <Route path="/account" element={<AccountManagementPage />} />
            <Route path="/test" element={<ComponentTest />} />
            <Route path="/tradingview-test" element={<TradingViewTestPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}