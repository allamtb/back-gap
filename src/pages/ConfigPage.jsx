import React, { useEffect, useState } from "react";
import { Card, Form, Input, AutoComplete, Button, message, Space, Modal, Popconfirm, Spin, Tooltip, Alert, Switch, Tag } from "antd";
import { PlusOutlined, DeleteOutlined, EditOutlined, ApiOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { getExchangeConfig, saveExchangeConfig, isUnifiedAccountExchange } from "../utils/configManager";

const TEST_RESULTS_KEY = 'exchangeTestResults'; // 测试结果存储key

// 默认交易所列表（作为后备）
const DEFAULT_EXCHANGES = [
  'binance',
  'okx',
  'gate',
  'bybit',
  'huobi',
  'kucoin',
  'bitget',
  'htx',
];

// 格式化时间显示（如："5分钟前"）
const formatTimeAgo = (timestamp) => {
  if (!timestamp) return '';
  
  const now = Date.now();
  const diff = now - timestamp;
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  if (seconds > 10) return `${seconds}秒前`;
  return '刚刚';
};

export default function ConfigPage() {
  const [exchangeForm] = Form.useForm();
  
  // 交易所配置列表
  const [exchanges, setExchanges] = useState([]);
  
  // 从后端获取的交易所列表
  const [availableExchanges, setAvailableExchanges] = useState([]);
  
  // 弹窗状态
  const [isExchangeModalOpen, setIsExchangeModalOpen] = useState(false);
  const [editingExchangeIndex, setEditingExchangeIndex] = useState(null);
  
  // 测试连接状态 (记录哪个交易所正在测试)
  const [testingExchangeIndex, setTestingExchangeIndex] = useState(null);
  const [testResults, setTestResults] = useState({}); // 存储测试结果 {index: {success, data/error}}

  // 从后端加载交易所列表
  const loadAvailableExchanges = async () => {
    try {
      const res = await fetch("/api/exchanges", { timeout: 2500 });
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      setAvailableExchanges(Array.isArray(data) ? data : []);
      console.log("✅ 从后端加载交易所列表成功");
    } catch (e) {
      console.error("从后端加载交易所列表失败:", e);
      // 降级到默认交易所列表
      setAvailableExchanges(DEFAULT_EXCHANGES);
    }
  };

  // 从 localStorage 加载配置
  const loadConfig = () => {
    try {
      const exchangesData = getExchangeConfig();
      setExchanges(exchangesData);
      if (exchangesData.length > 0) {
        console.log("✅ 配置已从 localStorage 加载");
      } else {
        console.log("暂无保存的配置");
      }
    } catch (e) {
      console.error("加载配置失败:", e);
      message.error("加载配置失败");
    }
  };

  // 从 localStorage 加载测试结果
  const loadTestResults = () => {
    try {
      const saved = localStorage.getItem(TEST_RESULTS_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        setTestResults(data);
        console.log("✅ 测试结果已从 localStorage 加载");
      }
    } catch (e) {
      console.error("加载测试结果失败:", e);
    }
  };

  // 保存测试结果到 localStorage
  const saveTestResults = (results) => {
    try {
      localStorage.setItem(TEST_RESULTS_KEY, JSON.stringify(results));
    } catch (e) {
      console.error("保存测试结果失败:", e);
    }
  };

  // 保存配置到 localStorage
  const saveConfig = (exchangeList) => {
    try {
      const success = saveExchangeConfig(exchangeList);
      if (success) {
        message.success("配置已自动保存！");
      } else {
        throw new Error("保存失败");
      }
    } catch (e) {
      console.error("保存配置失败:", e);
      message.error("保存配置失败: " + e.message);
    }
  };

  // 初始加载
  useEffect(() => {
    loadAvailableExchanges();
    loadConfig();
    loadTestResults();
  }, []);

  // ===== 交易所管理 =====
  
  const openAddExchangeModal = () => {
    setEditingExchangeIndex(null);
    exchangeForm.resetFields();
    // 设置默认值：统一账户根据交易所智能判断
    exchangeForm.setFieldsValue({
      unifiedAccount: false, // 默认 false，会在交易所选择时自动更新
    });
    setIsExchangeModalOpen(true);
  };

  const openEditExchangeModal = (index) => {
    const exchange = exchanges[index];
    setEditingExchangeIndex(index);
    exchangeForm.setFieldsValue(exchange);
    setIsExchangeModalOpen(true);
  };

  const handleExchangeModalOk = () => {
    exchangeForm.validateFields().then((values) => {
      const newExchanges = [...exchanges];
      
      if (editingExchangeIndex !== null) {
        // 编辑
        newExchanges[editingExchangeIndex] = values;
      } else {
        // 新增
        newExchanges.push(values);
      }
      
      setExchanges(newExchanges);
      saveConfig(newExchanges);
      setIsExchangeModalOpen(false);
      exchangeForm.resetFields();
    });
  };

  const handleDeleteExchange = (index) => {
    const newExchanges = exchanges.filter((_, i) => i !== index);
    setExchanges(newExchanges);
    saveConfig(newExchanges);
    // 清除该交易所的测试结果
    const newTestResults = { ...testResults };
    delete newTestResults[index];
    setTestResults(newTestResults);
    saveTestResults(newTestResults); // 持久化保存
    message.success("交易所配置已删除");
  };

  // 测试交易所连接
  const handleTestConnection = async (index) => {
    const exchange = exchanges[index];
    if (!exchange) return;

    setTestingExchangeIndex(index);
    
    try {
      const response = await fetch('/api/test-exchange', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          exchange: exchange.exchange,
          apiKey: exchange.apiKey,
          apiSecret: exchange.apiSecret,
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // 测试成功（至少有一个市场成功）
        const newResults = {
          ...testResults,
          [index]: {
            success: true,
            data: result.data, // 包含 spot 和 futures
            timestamp: Date.now(), // 保存测试时间戳
          },
        };
        setTestResults(newResults);
        saveTestResults(newResults); // 持久化保存
        
        // 显示成功消息（分别显示现货和合约的状态）
        const spotStatus = result.data.spot?.success ? '✅ 现货' : '❌ 现货';
        const futuresStatus = result.data.futures?.success ? '✅ 合约' : '❌ 合约';
        message.success(`${exchange.exchange} 测试完成: ${spotStatus} ${futuresStatus}`);
      } else {
        // 测试失败
        const newResults = {
          ...testResults,
          [index]: {
            success: false,
            data: result.data, // 可能包含部分测试结果
            error: result.error || '未知错误',
            timestamp: Date.now(), // 保存测试时间戳
          },
        };
        setTestResults(newResults);
        saveTestResults(newResults); // 持久化保存
        message.error(`${exchange.exchange} 连接测试失败: ${result.error || '未知错误'}`);
      }
    } catch (error) {
      console.error('测试连接失败:', error);
      const newResults = {
        ...testResults,
        [index]: {
          success: false,
          error: error.message || '网络请求失败',
          timestamp: Date.now(), // 保存测试时间戳
        },
      };
      setTestResults(newResults);
      saveTestResults(newResults); // 持久化保存
      message.error(`${exchange.exchange} 连接测试失败: ${error.message}`);
    } finally {
      setTestingExchangeIndex(null);
    }
  };

  // 使用从后端获取的交易所列表，如果为空则使用默认列表
  const exchangeOptions = (availableExchanges.length > 0 ? availableExchanges : DEFAULT_EXCHANGES).map((ex) => ({
    label: ex,
    value: ex,
  }));

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
      <Card 
        title="交易所配置管理" 
        extra={
          <Button 
            type="primary"
            icon={<PlusOutlined />} 
            onClick={openAddExchangeModal}
          >
            添加交易所
          </Button>
        }
      >
        <Alert
          message="数据存储说明"
          description="交易所配置信息仅存储于浏览器本地缓存（LocalStorage），服务器端不进行持久化存储。清除浏览器缓存将导致所有配置数据丢失，请谨慎操作。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        {exchanges.length === 0 ? (
          <div style={{ textAlign: "center", color: "#999", padding: "40px 0" }}>
            暂无交易所配置，点击右上角按钮添加
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {exchanges.map((ex, index) => (
              <div
                key={index}
                style={{
                  border: '1px solid #d9d9d9',
                  borderRadius: 8,
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  backgroundColor: '#fff',
                  transition: 'all 0.3s',
                  ...(testResults[index] && (() => {
                    const spotSuccess = testResults[index].data?.spot?.success;
                    const futuresSuccess = testResults[index].data?.futures?.success;
                    const hasAnySuccess = spotSuccess || futuresSuccess;
                    const hasAnyFailure = (testResults[index].data?.spot && !spotSuccess) || 
                                         (testResults[index].data?.futures && !futuresSuccess);
                    
                    // 如果至少有一个成功，显示绿色；如果全部失败，显示红色
                    if (hasAnySuccess) {
                      return {
                        borderColor: '#52c41a',
                        backgroundColor: '#f6ffed',
                      };
                    } else if (hasAnyFailure) {
                      return {
                        borderColor: '#ff4d4f',
                        backgroundColor: '#fff2f0',
                      };
                    }
                    return {};
                  })()),
                }}
                onMouseEnter={(e) => {
                  if (!testResults[index]) {
                    e.currentTarget.style.borderColor = '#40a9ff';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!testResults[index]) {
                    e.currentTarget.style.borderColor = '#d9d9d9';
                    e.currentTarget.style.boxShadow = 'none';
                  }
                }}
              >
                {/* 交易所名称 - 固定宽度 */}
                <div style={{ 
                  minWidth: 100, 
                  fontWeight: 600, 
                  fontSize: 15,
                  textTransform: 'uppercase',
                  color: '#1890ff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}>
                  <span>{ex.exchange}</span>
                  {ex.unifiedAccount && (
                    <Tooltip title="现货和合约共用同一个账户">
                      <Tag color="purple" style={{ fontSize: 10, margin: 0, padding: '0 4px' }}>
                        统一账户
                      </Tag>
                    </Tooltip>
                  )}
                </div>

                {/* API 信息 - 弹性增长 */}
                <div style={{ 
                  flex: 1, 
                  fontSize: 12, 
                  color: '#666',
                  display: 'flex',
                  gap: 16,
                  alignItems: 'center'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: '#999' }}>Key:</span>
                    <code style={{ 
                      background: '#f0f0f0', 
                      padding: '2px 6px', 
                      borderRadius: 3,
                      fontFamily: 'monospace'
                    }}>
                      {ex.apiKey?.slice(0, 8)}...{ex.apiKey?.slice(-4)}
                    </code>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: '#999' }}>Secret:</span>
                    <code style={{ 
                      background: '#f0f0f0', 
                      padding: '2px 6px', 
                      borderRadius: 3 
                    }}>
                      ********
                    </code>
                  </div>
                </div>

                {/* 测试结果状态 - 分别显示现货和合约 */}
                {testResults[index] && (
                  <div style={{ 
                    fontSize: 12,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    flexWrap: 'wrap'
                  }}>
                    {/* 现货测试结果 */}
                    {testResults[index].data?.spot && (
                      <div style={{ 
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '4px 12px',
                        borderRadius: 4,
                        backgroundColor: testResults[index].data.spot.success ? '#d9f7be' : '#ffccc7',
                        color: testResults[index].data.spot.success ? '#389e0d' : '#cf1322',
                        fontWeight: 500,
                      }}>
                        {testResults[index].data.spot.success ? (
                          <>
                            <span>✅ 现货</span>
                            {testResults[index].data.spot.balance && Object.keys(testResults[index].data.spot.balance).length > 0 && (
                              <Tooltip 
                                title={
                                  <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                                    <div style={{ fontWeight: 600, marginBottom: 4 }}>现货余额:</div>
                                    {Object.entries(testResults[index].data.spot.balance).map(([currency, amount]) => (
                                      <div key={currency}>{currency}: {parseFloat(amount).toFixed(8)}</div>
                                    ))}
                                  </div>
                                }
                              >
                                <span style={{ 
                                  cursor: 'pointer',
                                  padding: '2px 6px',
                                  backgroundColor: '#fff',
                                  borderRadius: 3,
                                  color: '#1890ff'
                                }}>
                                  {Object.keys(testResults[index].data.spot.balance).length} 币种
                                </span>
                              </Tooltip>
                            )}
                          </>
                        ) : (
                          <Tooltip title={testResults[index].data.spot.error || '现货连接失败'}>
                            <span style={{ cursor: 'pointer' }}>❌ 现货</span>
                          </Tooltip>
                        )}
                      </div>
                    )}
                    
                    {/* 合约测试结果 */}
                    {testResults[index].data?.futures && (
                      <div style={{ 
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '4px 12px',
                        borderRadius: 4,
                        backgroundColor: testResults[index].data.futures.success ? '#d9f7be' : '#ffccc7',
                        color: testResults[index].data.futures.success ? '#389e0d' : '#cf1322',
                        fontWeight: 500,
                      }}>
                        {testResults[index].data.futures.success ? (
                          <>
                            <span>✅ 合约</span>
                            {testResults[index].data.futures.balance && Object.keys(testResults[index].data.futures.balance).length > 0 && (
                              <Tooltip 
                                title={
                                  <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                                    <div style={{ fontWeight: 600, marginBottom: 4 }}>合约余额:</div>
                                    {Object.entries(testResults[index].data.futures.balance).map(([currency, amount]) => (
                                      <div key={currency}>{currency}: {parseFloat(amount).toFixed(8)}</div>
                                    ))}
                                  </div>
                                }
                              >
                                <span style={{ 
                                  cursor: 'pointer',
                                  padding: '2px 6px',
                                  backgroundColor: '#fff',
                                  borderRadius: 3,
                                  color: '#1890ff'
                                }}>
                                  {Object.keys(testResults[index].data.futures.balance).length} 币种
                                </span>
                              </Tooltip>
                            )}
                          </>
                        ) : (
                          <Tooltip title={testResults[index].data.futures.error || '合约连接失败'}>
                            <span style={{ cursor: 'pointer' }}>❌ 合约</span>
                          </Tooltip>
                        )}
                      </div>
                    )}
                    
                    {/* 显示时间戳 */}
                    {testResults[index].timestamp && (
                      <span style={{ 
                        fontSize: 11,
                        opacity: 0.7,
                        color: '#666'
                      }}>
                        ({formatTimeAgo(testResults[index].timestamp)})
                      </span>
                    )}
                  </div>
                )}

                {/* 操作按钮组 */}
                <Space size="small">
                  <Button
                    type={testResults[index] ? 'default' : 'primary'}
                    size="small"
                    icon={<ApiOutlined />}
                    onClick={() => handleTestConnection(index)}
                    loading={testingExchangeIndex === index}
                  >
                    {testingExchangeIndex === index ? '测试中' : '测试'}
                  </Button>
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => openEditExchangeModal(index)}
                  />
                  <Popconfirm
                    title="确定删除此交易所配置？"
                    onConfirm={() => handleDeleteExchange(index)}
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                    />
                  </Popconfirm>
                </Space>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 交易所弹窗 */}
      <Modal
        title={editingExchangeIndex !== null ? "编辑交易所配置" : "添加交易所配置"}
        open={isExchangeModalOpen}
        onOk={handleExchangeModalOk}
        onCancel={() => setIsExchangeModalOpen(false)}
        width={500}
      >
        <Form form={exchangeForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label="交易所"
            name="exchange"
            rules={[{ required: true, message: "请输入或选择交易所" }]}
          >
            <AutoComplete
              options={exchangeOptions}
              placeholder="输入或选择交易所 (如: binance)"
              filterOption={(inputValue, option) =>
                option.value.toLowerCase().indexOf(inputValue.toLowerCase()) !== -1
              }
              onSelect={(value) => {
                // 🎯 智能默认：根据交易所名称自动设置统一账户
                const normalizedValue = value.toLowerCase();
                const shouldBeUnified = isUnifiedAccountExchange(normalizedValue);
                exchangeForm.setFieldsValue({ 
                  exchange: normalizedValue,
                  unifiedAccount: shouldBeUnified 
                });
                console.log(`✨ 自动设置 ${normalizedValue} 统一账户模式为:`, shouldBeUnified);
              }}
              onBlur={(e) => {
                const value = e.target.value;
                if (value) {
                  const normalizedValue = value.toLowerCase();
                  const shouldBeUnified = isUnifiedAccountExchange(normalizedValue);
                  exchangeForm.setFieldsValue({ 
                    exchange: normalizedValue,
                    unifiedAccount: shouldBeUnified 
                  });
                }
              }}
              allowClear
            />
          </Form.Item>

          <Form.Item
            label="API Key"
            name="apiKey"
            rules={[{ required: true, message: "请输入API Key" }]}
          >
            <Input.Password
              placeholder="输入交易所 API Key"
              autoComplete="off"
            />
          </Form.Item>

          <Form.Item
            label="API Secret"
            name="apiSecret"
            rules={[{ required: true, message: "请输入API Secret" }]}
          >
            <Input.Password
              placeholder="输入交易所 API Secret"
              autoComplete="off"
            />
          </Form.Item>

          <Form.Item
            label={
              <span>
                统一账户模式{' '}
                <Tooltip title="开启后，现货和合约将共用同一个账户（如 Backpack）。关闭则现货和合约使用独立账户（如 Binance）。">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </span>
            }
            name="unifiedAccount"
            valuePropName="checked"
            initialValue={false}
          >
            <Switch 
              checkedChildren="是" 
              unCheckedChildren="否"
              onChange={(checked) => {
                console.log('统一账户模式:', checked);
              }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
