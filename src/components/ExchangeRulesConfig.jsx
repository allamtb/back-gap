import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Select, Space, message, Modal, Table, Tooltip } from 'antd';
import { 
  SettingOutlined, 
  SaveOutlined, 
  UndoOutlined, 
  QuestionCircleOutlined,
  EditOutlined,
  CheckOutlined,
  CloseOutlined,
  PlusOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import {
  loadExchangeRules,
  saveExchangeRules,
  resetExchangeRules,
  DEFAULT_EXCHANGE_RULES,
  validateRule,
  generateSymbol
} from '../utils/exchangeRules';

/**
 * 交易所规则配置组件
 * 允许用户在界面上配置不同交易所的交易对规则
 */
export default function ExchangeRulesConfig() {
  const [visible, setVisible] = useState(false);
  const [rules, setRules] = useState({});
  const [editingKey, setEditingKey] = useState('');
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [addForm] = Form.useForm();
  
  useEffect(() => {
    // 加载规则
    const loaded = loadExchangeRules();
    setRules(loaded);
  }, []);
  
  // 准备表格数据
  const tableData = [];
  Object.entries(rules).forEach(([exchange, marketTypes]) => {
    Object.entries(marketTypes).forEach(([marketType, rule]) => {
      tableData.push({
        key: `${exchange}-${marketType}`,
        exchange,
        marketType,
        ...rule,
      });
    });
  });
  
  // 编辑规则
  const startEdit = (record) => {
    form.setFieldsValue({
      quote: record.quote,
      separator: record.separator,
      suffix: record.suffix || '',
    });
    setEditingKey(record.key);
  };
  
  // 保存编辑
  const saveEdit = async (record) => {
    try {
      const values = await form.validateFields();
      
      // 验证规则
      if (!validateRule(values)) {
        message.error('规则验证失败：quote 是必需的，separator 必须明确指定（可以为空字符串）');
        return;
      }
      
      // 更新规则
      const newRules = { ...rules };
      if (!newRules[record.exchange]) {
        newRules[record.exchange] = {};
      }
      newRules[record.exchange][record.marketType] = {
        quote: values.quote.toUpperCase(),
        // 确保 separator 是字符串，空字符串表示无分隔符，空格也转换为空字符串
        separator: (values.separator === undefined || values.separator === null) ? '' : String(values.separator).trim(),
        suffix: values.suffix || '',
      };
      
      setRules(newRules);
      saveExchangeRules(newRules);
      setEditingKey('');
      
      message.success('规则已更新');
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    }
  };
  
  // 取消编辑
  const cancelEdit = () => {
    setEditingKey('');
  };
  
  // 新增规则
  const handleAddRule = async () => {
    try {
      const values = await addForm.validateFields();
      
      // 验证规则
      if (!validateRule({ quote: values.quote, separator: values.separator, suffix: values.suffix })) {
        message.error('规则验证失败：quote 是必需的，separator 必须明确指定（可以为空字符串）');
        return;
      }
      
      // 检查是否已存在
      const key = `${values.exchange}-${values.marketType}`;
      if (rules[values.exchange]?.[values.marketType]) {
        message.error('该交易所的该市场类型规则已存在，请直接编辑');
        return;
      }
      
      // 添加新规则
      const newRules = { ...rules };
      if (!newRules[values.exchange]) {
        newRules[values.exchange] = {};
      }
      newRules[values.exchange][values.marketType] = {
        quote: values.quote.toUpperCase(),
        // 确保 separator 是字符串，空字符串表示无分隔符，空格也转换为空字符串
        separator: (values.separator === undefined || values.separator === null) ? '' : String(values.separator).trim(),
        suffix: values.suffix || '',
      };
      
      setRules(newRules);
      saveExchangeRules(newRules);
      setAddModalVisible(false);
      addForm.resetFields();
      
      message.success(`已添加 ${values.exchange} ${values.marketType === 'spot' ? '现货' : '合约'} 规则`);
    } catch (error) {
      console.error('添加失败:', error);
    }
  };
  
  // 删除规则
  const handleDeleteRule = (record) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 ${record.exchange} ${record.marketType === 'spot' ? '现货' : '合约'} 的规则吗？`,
      onOk: () => {
        const newRules = { ...rules };
        if (newRules[record.exchange]) {
          delete newRules[record.exchange][record.marketType];
          // 如果交易所下没有规则了，删除整个交易所
          if (Object.keys(newRules[record.exchange]).length === 0) {
            delete newRules[record.exchange];
          }
        }
        
        setRules(newRules);
        saveExchangeRules(newRules);
        message.success('规则已删除');
      },
    });
  };
  
  // 重置所有规则
  const handleReset = () => {
    Modal.confirm({
      title: '确认重置',
      content: '确定要重置为默认规则吗？这将清除所有自定义配置。',
      onOk: () => {
        const defaultRules = resetExchangeRules();
        if (defaultRules) {
          setRules(defaultRules);
          message.success('已重置为默认规则');
        }
      },
    });
  };
  
  // 表格列定义
  const columns = [
    {
      title: '交易所',
      dataIndex: 'exchange',
      key: 'exchange',
      width: 120,
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '市场类型',
      dataIndex: 'marketType',
      key: 'marketType',
      width: 100,
      render: (text) => (
        <span style={{ 
          padding: '2px 8px', 
          borderRadius: '4px',
          backgroundColor: text === 'spot' ? '#e6f7ff' : '#fff7e6',
          color: text === 'spot' ? '#1890ff' : '#fa8c16',
          fontSize: '12px'
        }}>
          {text === 'spot' ? '现货' : '合约'}
        </span>
      ),
    },
    {
      title: (
        <Space>
          计价货币
          <Tooltip title="交易对中的计价货币，如 USDT、USDC">
            <QuestionCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'quote',
      key: 'quote',
      width: 120,
      render: (text, record) => {
        if (editingKey === record.key) {
          return (
            <Form.Item
              name="quote"
              style={{ margin: 0 }}
              rules={[{ required: true, message: '请输入计价货币' }]}
            >
              <Input placeholder="USDT" style={{ width: '100%' }} />
            </Form.Item>
          );
        }
        return <code style={{ color: '#52c41a' }}>{text}</code>;
      },
    },
    {
      title: (
        <Space>
          分隔符
          <Tooltip title="币种代码和计价货币之间的分隔符，通常是 '/'">
            <QuestionCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'separator',
      key: 'separator',
      width: 100,
      render: (text, record) => {
        if (editingKey === record.key) {
          return (
            <Form.Item
              name="separator"
              style={{ margin: 0 }}
              rules={[
                {
                  validator: (_, value) => {
                    // 允许空字符串（表示无分隔符），但不允许 undefined 或 null
                    if (value === undefined || value === null) {
                      return Promise.reject(new Error('分隔符必须明确指定（可以为空字符串）'));
                    }
                    // 如果输入的是空格，转换为空字符串
                    if (typeof value === 'string' && value.trim() === '' && value !== '') {
                      return Promise.resolve('');
                    }
                    return Promise.resolve();
                  }
                }
              ]}
            >
              <Input placeholder="留空表示无分隔符（如 btcusdt）" style={{ width: '100%' }} allowClear />
            </Form.Item>
          );
        }
        return <code>{text || '(无)'}</code>;
      },
    },
    {
      title: (
        <Space>
          后缀
          <Tooltip title="交易对的后缀，如 Binance 合约的 ':USDT'">
            <QuestionCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'suffix',
      key: 'suffix',
      width: 100,
      render: (text, record) => {
        if (editingKey === record.key) {
          return (
            <Form.Item
              name="suffix"
              style={{ margin: 0 }}
            >
              <Input placeholder="(可选)" style={{ width: '100%' }} />
            </Form.Item>
          );
        }
        return <code>{text || '(无)'}</code>;
      },
    },
    {
      title: '示例',
      key: 'example',
      width: 150,
      render: (_, record) => {
        const symbol = generateSymbol('BTC', record.exchange, record.marketType, rules);
        return (
          <Tooltip title="BTC 币种的完整交易对">
            <code style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '2px 6px',
              borderRadius: '4px',
              fontWeight: 'bold'
            }}>
              {symbol}
            </code>
          </Tooltip>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => {
        const isEditing = editingKey === record.key;
        
        if (isEditing) {
          return (
            <Space size="small">
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => saveEdit(record)}
              >
                保存
              </Button>
              <Button
                type="link"
                size="small"
                icon={<CloseOutlined />}
                onClick={cancelEdit}
              >
                取消
              </Button>
            </Space>
          );
        }
        
        return (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => startEdit(record)}
            >
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteRule(record)}
            >
              删除
            </Button>
          </Space>
        );
      },
    },
  ];
  
  return (
    <>
      <Button 
        icon={<SettingOutlined />} 
        onClick={() => setVisible(true)}
        size="small"
      >
        规则配置
      </Button>
      
      <Modal
        title={
          <Space>
            <SettingOutlined />
            交易所币种规则配置
          </Space>
        }
        open={visible}
        onCancel={() => {
          setVisible(false);
          cancelEdit();
        }}
        width={1000}
        footer={[
          <Button key="add" type="primary" icon={<PlusOutlined />} onClick={() => setAddModalVisible(true)}>
            新增规则
          </Button>,
          <Button key="reset" icon={<UndoOutlined />} onClick={handleReset}>
            重置为默认
          </Button>,
          <Button key="close" onClick={() => setVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        <div style={{ marginBottom: 16 }}>
          <Card size="small" style={{ backgroundColor: '#f0f9ff' }}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
                💡 规则说明
              </div>
              <div style={{ fontSize: '13px', color: '#666' }}>
                • <strong>计价货币 (quote)</strong>: 交易对中的计价货币，如 USDT、USDC、USD<br/>
                • <strong>分隔符 (separator)</strong>: 币种和计价货币之间的分隔符，通常是 "/"<br/>
                • <strong>后缀 (suffix)</strong>: 交易对的后缀，某些交易所合约需要（可选）<br/>
                • <strong>示例</strong>: 规则 <code>quote=USDC, separator=/</code> 会将 <code>BTC</code> 转换为 <code>BTC/USDC</code>
              </div>
            </Space>
          </Card>
        </div>
        
        <Form form={form} component={false}>
          <Table
            dataSource={tableData}
            columns={columns}
            pagination={false}
            size="small"
            bordered
            rowKey="key"
          />
        </Form>
      </Modal>
      
      {/* 新增规则弹窗 */}
      <Modal
        title={
          <Space>
            <PlusOutlined />
            新增交易所规则
          </Space>
        }
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          addForm.resetFields();
        }}
        onOk={handleAddRule}
        okText="添加"
        cancelText="取消"
      >
        <Form
          form={addForm}
          layout="vertical"
          initialValues={{
            separator: '/',
            suffix: '',
            marketType: 'spot',
          }}
        >
          <Form.Item
            name="exchange"
            label="交易所名称"
            rules={[
              { required: true, message: '请输入交易所名称' },
              { 
                pattern: /^[a-z0-9_-]+$/, 
                message: '只能包含小写字母、数字、下划线和连字符' 
              }
            ]}
            extra="例如: binance, okx, huobi, kraken"
          >
            <Input placeholder="输入交易所名称（小写）" />
          </Form.Item>
          
          <Form.Item
            name="marketType"
            label="市场类型"
            rules={[{ required: true, message: '请选择市场类型' }]}
          >
            <Select>
              <Select.Option value="spot">现货 (spot)</Select.Option>
              <Select.Option value="future">合约 (future)</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="quote"
            label="计价货币"
            rules={[
              { required: true, message: '请输入计价货币' },
              { pattern: /^[A-Z0-9]+$/, message: '只能包含大写字母和数字' }
            ]}
            extra="例如: USDT, USDC, USD, BTC"
          >
            <Input placeholder="USDT" />
          </Form.Item>
          
          <Form.Item
            name="separator"
            label="分隔符"
            rules={[
              {
                validator: (_, value) => {
                  // 允许空字符串（表示无分隔符），但不允许 undefined 或 null
                  if (value === undefined || value === null) {
                    return Promise.reject(new Error('分隔符必须明确指定（可以为空字符串）'));
                  }
                  // 如果输入的是空格，转换为空字符串
                  if (typeof value === 'string' && value.trim() === '' && value !== '') {
                    return Promise.resolve('');
                  }
                  return Promise.resolve();
                }
              }
            ]}
            extra="币种和计价货币之间的分隔符，通常是 /。完全留空表示无分隔符（如 btcusdt，不是空格）"
          >
            <Input placeholder="留空表示无分隔符（如 btcusdt）" maxLength={5} allowClear />
          </Form.Item>
          
          <Form.Item
            name="suffix"
            label="后缀（可选）"
            extra="某些交易所合约需要后缀，如 :USDT"
          >
            <Input placeholder="留空或输入后缀" maxLength={20} />
          </Form.Item>
          
          <div style={{ 
            marginTop: 16, 
            padding: 12, 
            backgroundColor: '#f5f5f5', 
            borderRadius: 4 
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: 8 }}>预览示例：</div>
            <Form.Item noStyle shouldUpdate>
              {() => {
                const exchange = addForm.getFieldValue('exchange') || '(交易所)';
                const quote = addForm.getFieldValue('quote') || 'USDT';
                const separator = addForm.getFieldValue('separator') ?? '';
                const suffix = addForm.getFieldValue('suffix') || '';
                const preview = `BTC${separator}${quote}${suffix}`;
                
                return (
                  <code style={{ 
                    fontSize: '16px', 
                    color: '#52c41a',
                    backgroundColor: '#fff',
                    padding: '4px 8px',
                    borderRadius: 4,
                    border: '1px solid #d9d9d9'
                  }}>
                    {preview}
                  </code>
                );
              }}
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </>
  );
}

