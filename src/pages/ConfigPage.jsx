import React, { useEffect, useState } from "react";
import { Card, Form, Input, Select, Button, message, Spin, Space, List, Modal, Popconfirm } from "antd";
import { SaveOutlined, ReloadOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from "@ant-design/icons";

function fetchWithTimeout(url, opts = {}, timeout = 3000) {
  return Promise.race([
    fetch(url, opts),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), timeout)),
  ]);
}

export default function ConfigPage() {
  const [form] = Form.useForm();
  const [exchangeForm] = Form.useForm();
  
  // 可用交易所列表
  const [exchanges, setExchanges] = useState([]);
  
  // 配置数据：账户列表
  const [accounts, setAccounts] = useState([]);
  
  // 当前选中的账户
  const [selectedAccount, setSelectedAccount] = useState(null);
  
  // 弹窗状态
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false);
  const [isExchangeModalOpen, setIsExchangeModalOpen] = useState(false);
  const [editingAccountIndex, setEditingAccountIndex] = useState(null);
  const [editingExchangeIndex, setEditingExchangeIndex] = useState(null);
  
  // 加载状态
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // 加载交易所列表
  const loadExchanges = async () => {
    try {
      const res = await fetchWithTimeout("/api/exchanges", {}, 2500);
      if (!res.ok) throw new Error("http " + res.status);
      const data = await res.json();
      setExchanges(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("加载交易所列表失败:", e);
      message.error("加载交易所列表失败");
      setExchanges([]);
    }
  };

  // 加载现有配置
  const loadConfig = async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout("/api/config", {}, 2500);
      if (!res.ok) {
        if (res.status === 404) {
          console.log("暂无配置");
          return;
        }
        throw new Error("http " + res.status);
      }
      const data = await res.json();
      
      // 数据结构: { accounts: [{ name: "账户1", exchanges: [{exchange: "binance", apiKey: "...", apiSecret: "..."}] }] }
      if (data.accounts && Array.isArray(data.accounts)) {
        setAccounts(data.accounts);
        if (data.accounts.length > 0) {
          setSelectedAccount(0);
        }
      }
    } catch (e) {
      console.error("加载配置失败:", e);
    } finally {
      setLoading(false);
    }
  };

  // 保存配置到后端
  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetchWithTimeout(
        "/api/config",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ accounts }),
        },
        5000
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.message || "保存失败");
      }

      message.success("配置保存成功！");
    } catch (e) {
      console.error("保存配置失败:", e);
      message.error("保存配置失败: " + e.message);
    } finally {
      setSaving(false);
    }
  };

  // 重新加载配置
  const handleReload = async () => {
    await Promise.all([loadExchanges(), loadConfig()]);
    message.success("配置已刷新");
  };

  // 初始加载
  useEffect(() => {
    loadExchanges();
    loadConfig();
  }, []);

  // ===== 账户管理 =====
  
  const openAddAccountModal = () => {
    setEditingAccountIndex(null);
    form.resetFields();
    setIsAccountModalOpen(true);
  };

  const openEditAccountModal = (index) => {
    setEditingAccountIndex(index);
    form.setFieldsValue({ accountName: accounts[index].name });
    setIsAccountModalOpen(true);
  };

  const handleAccountModalOk = () => {
    form.validateFields().then((values) => {
      const newAccounts = [...accounts];
      
      if (editingAccountIndex !== null) {
        // 编辑
        newAccounts[editingAccountIndex].name = values.accountName;
      } else {
        // 新增
        newAccounts.push({
          name: values.accountName,
          exchanges: []
        });
        setSelectedAccount(newAccounts.length - 1);
      }
      
      setAccounts(newAccounts);
      setIsAccountModalOpen(false);
      form.resetFields();
    });
  };

  const handleDeleteAccount = (index) => {
    const newAccounts = accounts.filter((_, i) => i !== index);
    setAccounts(newAccounts);
    
    if (selectedAccount === index) {
      setSelectedAccount(newAccounts.length > 0 ? 0 : null);
    } else if (selectedAccount > index) {
      setSelectedAccount(selectedAccount - 1);
    }
    
    message.success("账户已删除");
  };

  // ===== 交易所管理 =====
  
  const openAddExchangeModal = () => {
    if (selectedAccount === null) {
      message.warning("请先选择一个账户");
      return;
    }
    setEditingExchangeIndex(null);
    exchangeForm.resetFields();
    setIsExchangeModalOpen(true);
  };

  const openEditExchangeModal = (index) => {
    const exchange = accounts[selectedAccount].exchanges[index];
    setEditingExchangeIndex(index);
    exchangeForm.setFieldsValue(exchange);
    setIsExchangeModalOpen(true);
  };

  const handleExchangeModalOk = () => {
    exchangeForm.validateFields().then((values) => {
      const newAccounts = [...accounts];
      const currentExchanges = [...newAccounts[selectedAccount].exchanges];
      
      if (editingExchangeIndex !== null) {
        // 编辑
        currentExchanges[editingExchangeIndex] = values;
      } else {
        // 新增
        currentExchanges.push(values);
      }
      
      newAccounts[selectedAccount].exchanges = currentExchanges;
      setAccounts(newAccounts);
      setIsExchangeModalOpen(false);
      exchangeForm.resetFields();
    });
  };

  const handleDeleteExchange = (index) => {
    const newAccounts = [...accounts];
    newAccounts[selectedAccount].exchanges = newAccounts[selectedAccount].exchanges.filter((_, i) => i !== index);
    setAccounts(newAccounts);
    message.success("交易所配置已删除");
  };

  const exchangeOptions = exchanges.map((ex) => ({
    label: ex,
    value: ex,
  }));

  const currentAccount = selectedAccount !== null ? accounts[selectedAccount] : null;

  return (
    <div style={{ display: "flex", gap: 16, height: "calc(100vh - 100px)" }}>
      {/* 左侧：账户列表 */}
      <Card 
        title="账户列表" 
        style={{ width: 280, overflowY: "auto" }}
        extra={
          <Button 
            type="text" 
            icon={<PlusOutlined />} 
            onClick={openAddAccountModal}
            size="small"
          />
        }
      >
        <Spin spinning={loading}>
          {accounts.length === 0 ? (
            <div style={{ textAlign: "center", color: "#999", padding: "20px 0" }}>
              暂无账户，点击 + 添加
            </div>
          ) : (
            <List
              dataSource={accounts}
              renderItem={(account, index) => (
                <List.Item
                  onClick={() => setSelectedAccount(index)}
                  style={{
                    cursor: "pointer",
                    background: selectedAccount === index ? "#e6f7ff" : "transparent",
                    padding: "12px",
                    borderRadius: 4,
                    marginBottom: 4,
                  }}
                  actions={[
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        openEditAccountModal(index);
                      }}
                    />,
                    <Popconfirm
                      title="确定删除此账户？"
                      onConfirm={(e) => {
                        e.stopPropagation();
                        handleDeleteAccount(index);
                      }}
                      onCancel={(e) => e.stopPropagation()}
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
                  ]}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500 }}>{account.name}</div>
                    <div style={{ fontSize: 12, color: "#999" }}>
                      {account.exchanges.length} 个交易所
                    </div>
                  </div>
                </List.Item>
              )}
            />
          )}
        </Spin>
      </Card>

      {/* 右侧：交易所配置 */}
      <Card 
        title={currentAccount ? `${currentAccount.name} - 交易所配置` : "交易所配置"}
        style={{ flex: 1, overflowY: "auto" }}
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleReload}
              disabled={loading}
            >
              刷新
            </Button>
            <Button 
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              loading={saving}
            >
              保存全部配置
            </Button>
          </Space>
        }
      >
        {currentAccount ? (
          <>
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={openAddExchangeModal}
              block
              style={{ marginBottom: 16 }}
            >
              添加交易所
            </Button>

            {currentAccount.exchanges.length === 0 ? (
              <div style={{ textAlign: "center", color: "#999", padding: "40px 0" }}>
                暂无交易所配置，点击上方按钮添加
              </div>
            ) : (
              <Space direction="vertical" style={{ width: "100%" }} size="middle">
                {currentAccount.exchanges.map((ex, index) => (
                  <Card
                    key={index}
                    size="small"
                    title={
                      <Space>
                        <span style={{ fontWeight: 600 }}>{ex.exchange}</span>
                      </Space>
                    }
                    extra={
                      <Space>
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
                    }
                  >
                    <div style={{ fontSize: 12, color: "#666" }}>
                      <div>API Key: {ex.apiKey?.slice(0, 8)}...{ex.apiKey?.slice(-4)}</div>
                      <div>API Secret: ********</div>
                    </div>
                  </Card>
                ))}
              </Space>
            )}
          </>
        ) : (
          <div style={{ textAlign: "center", color: "#999", padding: "40px 0" }}>
            请先在左侧选择或添加账户
          </div>
        )}
      </Card>

      {/* 账户弹窗 */}
      <Modal
        title={editingAccountIndex !== null ? "编辑账户" : "添加账户"}
        open={isAccountModalOpen}
        onOk={handleAccountModalOk}
        onCancel={() => setIsAccountModalOpen(false)}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label="账户名称"
            name="accountName"
            rules={[{ required: true, message: "请输入账户名称" }]}
          >
            <Input placeholder="例如：主账户、备用账户" />
          </Form.Item>
        </Form>
      </Modal>

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
            rules={[{ required: true, message: "请选择交易所" }]}
          >
            <Select
              options={exchangeOptions}
              placeholder="选择交易所"
              loading={exchanges.length === 0}
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
        </Form>
      </Modal>
    </div>
  );
}
