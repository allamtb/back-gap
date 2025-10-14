import React, { useState, useEffect, useMemo, useRef } from "react";
import { Table, Tag, Space, Button, Select, DatePicker, Card, Input, message, Switch, Statistic, Drawer, Checkbox, Divider } from "antd";
import { ReloadOutlined, SearchOutlined, PauseCircleOutlined, PlayCircleOutlined } from "@ant-design/icons";
import { getExchangeCredentials, getExchangeConfig } from "../utils/configManager";
import { readWatchlist, getAllSymbols, getEnabledSymbols, setEnabledSymbols, getSymbolsForQuery } from "../utils/symbolWatchlist";

const { RangePicker } = DatePicker;
const { Countdown } = Statistic;

// API 配置
// const API_BASE_URL = "http://localhost:8000";

export default function OrderMonitor() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [watchDrawerOpen, setWatchDrawerOpen] = useState(false);
  const [enabledDraft, setEnabledDraft] = useState([]); // string[] - 币种列表
  const [filters, setFilters] = useState({
    exchange: "all",
    type: "all",
    side: "all",
    status: "all",
  });
  
  // 实时刷新相关状态
  const [autoRefresh, setAutoRefresh] = useState(false); // 是否自动刷新
  const [refreshInterval, setRefreshInterval] = useState(30); // 刷新间隔（秒）
  const [nextRefreshTime, setNextRefreshTime] = useState(Date.now() + 30000); // 下次刷新时间
  const timerRef = useRef(null); // 定时器引用
  const fetchingRef = useRef(false); // 防止重复请求
  
  // 从配置中获取用户配置的交易所列表
  const configuredExchanges = useMemo(() => {
    return getExchangeConfig();
  }, [orders]); // 当订单更新时重新获取配置（以防用户在其他页面修改了配置）

  // 初始加载
  useEffect(() => {
    // 初始化 enabledDraft（若无 enabled 则回退 all）
    const initEnabled = getEnabledSymbols(true);
    setEnabledDraft(initEnabled);
    fetchOrders();
  }, []);
  
  // 自动刷新定时器 - 改用 setTimeout 实现，确保请求完成后才开始下一次倒计时
  useEffect(() => {
    if (!autoRefresh || refreshInterval <= 0) {
      // 关闭自动刷新时清除定时器
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }
    
    // 清除旧定时器
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [autoRefresh, refreshInterval]);
  
  // 页面可见性变化时的处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面不可见时暂停刷新
        if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
        }
      } else {
        // 页面可见时恢复刷新
        if (autoRefresh) {
          fetchOrders();
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [autoRefresh, refreshInterval]);

  const fetchOrders = async () => {
    // 防止重复请求
    if (fetchingRef.current) {
      console.log('⏳ 订单请求正在进行中，跳过本次请求');
      return;
    }
    
    console.log('🚀 开始获取订单数据...');
    
    try {
      const credentials = getExchangeCredentials();
      
      if (credentials.length === 0) {
        console.warn('⚠️ 未配置交易所账户');
        setOrders([]);
        message.warning('请先在配置页面添加交易所账户');
        return;
      }
      
      fetchingRef.current = true;
      setLoading(true);

      // 生成基于本地 enabled 的币种列表
      const symbols = getSymbolsForQuery();
      
      // 🔍 调试：打印查询参数
      console.log('📡 查询币种列表:', symbols);
      console.log('📡 交易所凭证数量:', credentials.length);
      
      if (symbols.length === 0) {
        console.warn('⚠️ 本地未配置关注币种，返回空列表');
        setOrders([]);
        message.info('未选择关注币种，请在"币种筛选"中选择');
        return;
      }

      // 调用后端批量 API（携带凭证与币种筛选）
      const response = await fetch(`/api/orders/by-symbols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbols, credentials }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // 🔍 调试：打印后端返回的数据
      console.log('📦 后端返回数据:', {
        success: data.success,
        total: data.total,
        订单数量: data.data?.length,
        交易所分布: data.data?.reduce((acc, o) => {
          acc[o.exchange] = (acc[o.exchange] || 0) + 1;
          return acc;
        }, {}),
        首个订单示例: data.data?.[0]
      });

      if (data.success) {
        const apiOrders = data.data;
        
        // 转换数据格式以适配前端显示
        const formattedOrders = apiOrders.map((order, index) => ({
          key: `${order.exchange}-${order.orderId}-${index}`,
          orderId: order.orderId,
          exchange: formatExchangeName(order.exchange),
          type: order.order_type === "spot" ? "现货" : "合约",
          symbol: order.symbol,
          side: order.side === "buy" ? "买入" : "卖出",
          price: order.price,
          amount: order.amount,
          filled: order.filled,
          total: order.total,
          fee: order.fee,
          status: formatOrderStatus(order.status),
          orderTime: order.orderTime,
          fillTime: order.fillTime,
        }));
        
        // 🔍 调试：打印格式化后的订单
        console.log('✅ 格式化后的订单数据:', {
          总数: formattedOrders.length,
          交易所分布: formattedOrders.reduce((acc, o) => {
            acc[o.exchange] = (acc[o.exchange] || 0) + 1;
            return acc;
          }, {}),
          前3条订单: formattedOrders.slice(0, 3)
        });

        setOrders(formattedOrders);
        
        // 仅在手动刷新时显示成功提示
        if (!autoRefresh || loading) {
          message.success(`成功获取 ${formattedOrders.length} 条订单记录`);
        }
      } else {
        throw new Error(data.message || "API 返回失败");
      }
    } catch (error) {
      console.error("获取订单失败:", error);
      
      if (error.code === "ECONNABORTED") {
        message.error("请求超时，请检查网络连接");
      } else if (error.response) {
        message.error(`获取订单失败: ${error.response.data.detail || error.message}`);
      } else if (error.request) {
        message.error("无法连接到后端服务，请确保后端已启动");
      } else {
        message.error(`获取订单失败: ${error.message}`);
      }
      
      // 出错时清空订单列表
      setOrders([]);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
      console.log('✅ 订单请求完成，锁已释放');
      
      // 请求完成后，如果开启了自动刷新，设置下一次刷新
      if (autoRefresh && refreshInterval > 0) {
        const nextTime = Date.now() + refreshInterval * 1000;
        setNextRefreshTime(nextTime);
        
        // 清除旧定时器
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
        
        // 设置新定时器
        timerRef.current = setTimeout(() => {
          fetchOrders();
        }, refreshInterval * 1000);
        
        console.log(`⏰ 已设置下次刷新时间: ${new Date(nextTime).toLocaleTimeString()}`);
      }
    }
  };

  // 币种筛选抽屉
  const openWatchDrawer = () => {
    const enabled = getEnabledSymbols(true);
    setEnabledDraft(enabled);
    setWatchDrawerOpen(true);
  };

  const handleToggleAll = (checked, allList) => {
    setEnabledDraft(checked ? [...allList] : []);
  };

  const handleToggleOne = (symbol, checked) => {
    setEnabledDraft(prev => {
      const current = new Set(prev);
      if (checked) current.add(symbol); else current.delete(symbol);
      return Array.from(current);
    });
  };

  const saveWatchlist = () => {
    setEnabledSymbols(enabledDraft);
    message.success('已保存关注币种');
    setWatchDrawerOpen(false);
    // 保存后立即刷新
    handleManualRefresh();
  };
  
  // 手动刷新（立即刷新）
  const handleManualRefresh = () => {
    // 清除现有定时器
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    // 重置倒计时显示（设置为当前时间，显示0秒）
    setNextRefreshTime(Date.now());
    // 立即刷新，fetchOrders 完成后会自动设置下一次定时器
    fetchOrders();
  };
  
  // 切换自动刷新
  const handleAutoRefreshToggle = (checked) => {
    setAutoRefresh(checked);
    if (checked) {
      message.success(`已开启自动刷新（每 ${refreshInterval} 秒）`);
      // 立即刷新一次，fetchOrders 完成后会自动设置定时器
      fetchOrders();
    } else {
      message.info('已暂停自动刷新');
      // 清除定时器
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }
  };
  
  // 修改刷新间隔
  const handleRefreshIntervalChange = (value) => {
    setRefreshInterval(value);
    if (autoRefresh) {
      // 清除现有定时器
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      // 立即重置倒计时显示（使用新的间隔）
      const nextTime = Date.now() + value * 1000;
      setNextRefreshTime(nextTime);
      // 立即刷新，使用新的间隔（fetchOrders 会再次设置定时器）
      fetchOrders();
      message.success(`刷新间隔已更新为 ${value} 秒`);
    }
  };

  // 格式化交易所名称
  const formatExchangeName = (exchange) => {
    const nameMap = {
      binance: "币安",
      okx: "OKX",
      bybit: "Bybit",
      gate: "Gate.io",
      huobi: "火币",
      kucoin: "KuCoin",
    };
    return nameMap[exchange.toLowerCase()] || exchange.toUpperCase();
  };

  // 格式化订单状态
  const formatOrderStatus = (status) => {
    const statusMap = {
      open: "未成交",
      closed: "已成交",
      canceled: "已取消",
      cancelled: "已取消",
      expired: "已过期",
      rejected: "已拒绝",
      partial: "部分成交",
    };
    return statusMap[status.toLowerCase()] || status;
  };

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      // exchange filter (toolbar)
      if (filters.exchange !== "all") {
        if (order.exchange !== formatExchangeName(filters.exchange)) return false;
      }

      // type filter (toolbar)
      if (filters.type !== "all") {
        const typeMap = { spot: "现货", futures: "合约" };
        if (order.type !== typeMap[filters.type]) return false;
      }

      // side filter (toolbar)
      if (filters.side !== "all") {
        const sideMap = { buy: "买入", sell: "卖出" };
        if (order.side !== sideMap[filters.side]) return false;
      }

      // status filter (toolbar) - values already in Chinese
      if (filters.status !== "all") {
        if (order.status !== filters.status) return false;
      }

      return true;
    });
  }, [orders, filters]);

  const columns = [
    {
      title: "交易所",
      dataIndex: "exchange",
      key: "exchange",
      width: 80,
      fixed: "left",
      render: (text) => <Tag color="blue" style={{ fontSize: "13px", padding: "2px 8px" }}>{text}</Tag>,
      filters: configuredExchanges.map(ex => ({
        text: formatExchangeName(ex.exchange),
        value: formatExchangeName(ex.exchange)
      })),
      onFilter: (value, record) => record.exchange === value,
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      width: 70,
      render: (text) => (
        <Tag color={text === "现货" ? "green" : "orange"} style={{ fontSize: "13px", padding: "2px 8px" }}>{text}</Tag>
      ),
      filters: [
        { text: "现货", value: "现货" },
        { text: "合约", value: "合约" },
      ],
      onFilter: (value, record) => record.type === value,
    },
    {
      title: "交易对",
      dataIndex: "symbol",
      key: "symbol",
      width: 130,
      render: (text) => <strong style={{ fontSize: "14px" }}>{text}</strong>,
    },
    {
      title: "方向",
      dataIndex: "side",
      key: "side",
      width: 85,
      render: (text) => (
        <Tag color={text === "买入" ? "#52c41a" : "#ff4d4f"} style={{ fontSize: "13px", padding: "2px 8px" }}>
          {text}
        </Tag>
      ),
      filters: [
        { text: "买入", value: "买入" },
        { text: "卖出", value: "卖出" },
      ],
      onFilter: (value, record) => record.side === value,
    },
    {
      title: "价格",
      dataIndex: "price",
      key: "price",
      align: "right",
      width: 130,
      render: (value) => <span style={{ fontSize: "14px" }}>${value.toFixed(2)}</span>,
    },
    {
      title: "数量",
      dataIndex: "amount",
      key: "amount",
      align: "right",
      width: 110,
      render: (value) => <span style={{ fontSize: "14px" }}>{value.toFixed(4)}</span>,
    },
    {
      title: "已成交",
      dataIndex: "filled",
      key: "filled",
      align: "right",
      width: 110,
      render: (value, record) => (
        <span style={{ color: value === record.amount ? "#52c41a" : "#faad14", fontSize: "14px" }}>
          {value.toFixed(4)}
        </span>
      ),
    },
    {
      title: "交易金额",
      dataIndex: "total",
      key: "tradeAmount",
      align: "right",
      width: 170,
      render: (value, record) => {
        const fee = Number(record.fee || 0);
        // 根据手续费大小动态调整精度
        const feeDisplay = fee < 0.01 ? fee.toFixed(8) : fee.toFixed(6);
        return (
          <div style={{ textAlign: "right" }}>
            <strong style={{ fontSize: "14px" }}>${value.toFixed(2)}</strong>
            <div style={{ fontSize: "12px", color: "#8c8c8c" }}>
              手续费: {feeDisplay} {record.feeCurrency || ''}
            </div>
          </div>
        );
      },
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (text) => {
        let color = "default";
        if (text === "已成交") color = "success";
        else if (text === "部分成交") color = "warning";
        else if (text === "未成交") color = "default";
        else if (text === "已取消") color = "error";
        return <Tag color={color}>{text}</Tag>;
      },
      filters: [
        { text: "已成交", value: "已成交" },
        { text: "部分成交", value: "部分成交" },
        { text: "未成交", value: "未成交" },
        { text: "已取消", value: "已取消" },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: "下单时间",
      dataIndex: "orderTime",
      key: "orderTime",
      width: 170,
      render: (text) => <span style={{ fontSize: "12px" }}>{text}</span>,
    },
    {
      title: "成交时间",
      dataIndex: "fillTime",
      key: "fillTime",
      width: 170,
      render: (text) => <span style={{ fontSize: "12px" }}>{text}</span>,
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      {/* 自动刷新控制栏 */}
      <Card 
        size="small" 
        style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none'
        }}
      >
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space wrap>
            <span style={{ color: '#fff', fontWeight: 500 }}>
              {autoRefresh ? (
                <PlayCircleOutlined style={{ marginRight: 8 }} />
              ) : (
                <PauseCircleOutlined style={{ marginRight: 8 }} />
              )}
              自动刷新
            </span>
            <Switch 
              checked={autoRefresh} 
              onChange={handleAutoRefreshToggle}
              checkedChildren="开启"
              unCheckedChildren="关闭"
            />
            
            <Select
              value={refreshInterval}
              onChange={handleRefreshIntervalChange}
              style={{ width: 120 }}
              disabled={!autoRefresh}
            >
              <Select.Option value={5}>每 5 秒</Select.Option>
              <Select.Option value={10}>每 10 秒</Select.Option>
              <Select.Option value={30}>每 30 秒</Select.Option>
              <Select.Option value={60}>每 1 分钟</Select.Option>
            </Select>
            
            {autoRefresh && (
              <div style={{ 
                display: 'inline-block',
                padding: '4px 12px',
                background: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
                color: '#fff',
                fontSize: '13px'
              }}>
                <Countdown 
                  value={nextRefreshTime} 
                  format="s 秒后刷新"
                  valueStyle={{ 
                    color: '#fff', 
                    fontSize: '13px',
                    fontWeight: 500
                  }}
                />
              </div>
            )}
            <Button size="small" onClick={openWatchDrawer}>
              币种筛选
            </Button>
          </Space>
          
          <Space>
            <span style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px' }}>
              共 {orders.length} 条订单
            </span>
            <Button
              type="primary"
              size="small"
              icon={<ReloadOutlined spin={loading} />}
              onClick={handleManualRefresh}
              loading={loading}
            >
              立即刷新
            </Button>
          </Space>
        </Space>
      </Card>

      {/* 币种选择抽屉 */}
      <Drawer
        title="选择关注币种"
        placement="right"
        width={360}
        onClose={() => setWatchDrawerOpen(false)}
        open={watchDrawerOpen}
        extra={
          <Space>
            <Button onClick={() => setWatchDrawerOpen(false)}>取消</Button>
            <Button type="primary" onClick={saveWatchlist}>保存</Button>
          </Space>
        }
      >
        {(() => {
          const allSymbols = getAllSymbols();
          if (allSymbols.length === 0) {
            return <div style={{ color: '#999' }}>暂无可选币种，请先在资金/持仓监控获取数据</div>;
          }
          
          const allChecked = allSymbols.length > 0 && enabledDraft.length === allSymbols.length;
          const indeterminate = enabledDraft.length > 0 && enabledDraft.length < allSymbols.length;
          
          return (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card size="small">
                <Checkbox
                  indeterminate={indeterminate}
                  checked={allChecked}
                  onChange={(e) => handleToggleAll(e.target.checked, allSymbols)}
                >
                  全选（共 {allSymbols.length} 个币种）
                </Checkbox>
                <Divider style={{ margin: '8px 0' }} />
                <Space wrap>
                  {allSymbols.map(symbol => (
                    <Checkbox
                      key={symbol}
                      checked={enabledDraft.includes(symbol)}
                      onChange={(e) => handleToggleOne(symbol, e.target.checked)}
                    >
                      {symbol}
                    </Checkbox>
                  ))}
                </Space>
              </Card>
            </Space>
          );
        })()}
      </Drawer>

      {/* 筛选器 */}
      <Card>
        <Space wrap>
          <Input
            placeholder="搜索订单号/交易对"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
          />
          <Select
            placeholder="选择交易所"
            style={{ width: 120 }}
            value={filters.exchange}
            onChange={(value) => setFilters({ ...filters, exchange: value })}
          >
            <Select.Option value="all">全部交易所</Select.Option>
            {configuredExchanges.map(ex => (
              <Select.Option key={ex.exchange} value={ex.exchange}>
                {formatExchangeName(ex.exchange)}
              </Select.Option>
            ))}
          </Select>
          <Select
            placeholder="订单类型"
            style={{ width: 120 }}
            value={filters.type}
            onChange={(value) => setFilters({ ...filters, type: value })}
          >
            <Select.Option value="all">全部类型</Select.Option>
            <Select.Option value="spot">现货</Select.Option>
            <Select.Option value="futures">合约</Select.Option>
          </Select>
          <Select
            placeholder="买卖方向"
            style={{ width: 120 }}
            value={filters.side}
            onChange={(value) => setFilters({ ...filters, side: value })}
          >
            <Select.Option value="all">全部方向</Select.Option>
            <Select.Option value="buy">买入</Select.Option>
            <Select.Option value="sell">卖出</Select.Option>
          </Select>
          <Select
            placeholder="订单状态"
            style={{ width: 120 }}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Select.Option value="all">全部状态</Select.Option>
            <Select.Option value="已成交">已成交</Select.Option>
            <Select.Option value="部分成交">部分成交</Select.Option>
            <Select.Option value="未成交">未成交</Select.Option>
            <Select.Option value="已取消">已取消</Select.Option>
          </Select>
          <RangePicker placeholder={["开始时间", "结束时间"]} />
        </Space>
      </Card>

      {/* 订单表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredOrders}
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条订单`,
          }}
          scroll={{ x: 1400 }}
          size="middle"
          bordered
        />
      </Card>
    </Space>
  );
}
