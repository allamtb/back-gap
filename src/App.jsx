import React, { useEffect } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import { SettingOutlined, DashboardOutlined, BugOutlined, LineChartOutlined, WalletOutlined, TwitterOutlined, GlobalOutlined, TransactionOutlined, DatabaseOutlined, BookOutlined } from "@ant-design/icons";
import ConfigPage from "./pages/ConfigPage";
import DashboardPage from "./pages/DashboardPage";
import TradingOrderPage from "./pages/TradingOrderPage";
import AccountManagementPage from "./pages/AccountManagementPage";
import TrumpSentimentPage from "./pages/TrumpSentimentPage";
import TradingWebsitesPage from "./pages/TradingWebsitesPage";
import BaiduCookiePage from "./pages/BaiduCookiePage";

import NetworkStatus from "./components/NetworkStatus";
import "./styles/global/App.css";

const { Header, Content } = Layout;

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = location.pathname === "/" ? "/dashboard" : location.pathname;

  // 根据路径动态设置页面标题
  useEffect(() => {
    const getPageTitle = (pathname) => {
      switch (pathname) {
        case "/config":
          return "📊 交易所配置";
        case "/account":
          return "💰 账户监控";
        case "/dashboard":
          return "📊 行情观察";
        case "/trading-order":
          return "💹 交易下单";
        case "/trump-sentiment":
          return "🐦 特朗普情绪分析";
        case "/trading-websites":
          return "🌐 交易网站";
        case "/baidu-cookie":
          return "🍪 百度Cookie管理";
        default:
          return "稳定套利交易系统";
      }
    };

    const title = getPageTitle(location.pathname);
    document.title = title;
  }, [location.pathname]);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header className="app-header">
        <div className="app-header-left">
          <h1 className="app-header-title">IT支持中心</h1>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[selectedKey]}
            onClick={({ key }) => navigate(key)}
            className="app-header-menu"
            items={[
              { key: "/config", icon: <SettingOutlined />, label: "交易所配置" },
              { key: "/account", icon: <WalletOutlined />, label: "账户监控-全币种" },
              { key: "/dashboard", icon: <LineChartOutlined />, label: "行情观察" },
              { key: "/trading-order", icon: <TransactionOutlined />, label: "交易下单" },
              { key: "/trading-websites", icon: <GlobalOutlined />, label: "交易网站" },
              { key: "/baidu-cookie", icon: <DatabaseOutlined />, label: "百度Cookie管理" },
              { key: "/trump-sentiment", icon: <TwitterOutlined />, label: "特朗普情绪分析" },
            ]}
          />
        </div>
        <NetworkStatus refreshInterval={60000} />
      </Header>
      <Content style={{ margin: "16px" }}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/trading-order" element={<TradingOrderPage />} />
          <Route path="/account" element={<AccountManagementPage />} />
          <Route path="/trading-websites" element={<TradingWebsitesPage />} />
          <Route path="/baidu-cookie" element={<BaiduCookiePage />} />
          <Route path="/trump-sentiment" element={<TrumpSentimentPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}