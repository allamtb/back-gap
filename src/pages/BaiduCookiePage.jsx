import React, { useState, useEffect } from "react";
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  message,
  Space,
  Card,
  Statistic,
  Row,
  Col,
  Popconfirm,
  Tag,
  Select,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CopyOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";

export default function BaiduCookiePage() {
  const [cookies, setCookies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [limit, setLimit] = useState(1000); // 默认获取1000条
  const [form] = Form.useForm();

  // 获取所有 Cookie 数据
  const fetchCookies = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/cookies/baidu?limit=${limit}`);
      if (response.ok) {
        const data = await response.json();
        setCookies(data);
        message.success(`成功加载 ${data.length} 条记录`);
      } else {
        throw new Error("获取数据失败");
      }
    } catch (error) {
      message.error(`获取 Cookie 数据失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 获取统计数据
  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/cookies/baidu/stats/count`);
      if (response.ok) {
        const data = await response.json();
        setTotalCount(data.total_cookies);
      }
    } catch (error) {
      console.error("获取统计数据失败:", error);
    }
  };

  // 添加 Cookie
  const handleAddCookie = async (values) => {
    try {
      const response = await fetch(`/api/cookies/baidu`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          afd_ip: values.afd_ip,
          baidulocnew: values.baidulocnew || null,
          url: values.url,
          timestamp: values.timestamp || new Date().toISOString(),
        }),
      });

      if (response.ok) {
        message.success("Cookie 数据添加成功");
        setIsModalVisible(false);
        form.resetFields();
        fetchCookies();
        fetchStats();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "添加失败");
      }
    } catch (error) {
      message.error(`添加 Cookie 失败: ${error.message}`);
    }
  };

  // 删除 Cookie
  const handleDelete = async (id) => {
    try {
      const response = await fetch(`/api/cookies/baidu/${id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        message.success("删除成功");
        fetchCookies();
        fetchStats();
      } else {
        throw new Error("删除失败");
      }
    } catch (error) {
      message.error(`删除失败: ${error.message}`);
    }
  };

  // 复制到剪贴板
  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text).then(
      () => {
        message.success(`${label} 已复制到剪贴板`);
      },
      () => {
        message.error("复制失败");
      }
    );
  };

  // 初始加载
  useEffect(() => {
    fetchCookies();
    fetchStats();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 80,
      fixed: "left",
    },
    {
      title: "AFD_IP",
      dataIndex: "afd_ip",
      key: "afd_ip",
      width: 300,
      ellipsis: true,
      render: (text) => (
        <Space>
          <span style={{ fontFamily: "monospace", fontSize: "12px" }}>
            {text ? `${text.substring(0, 40)}...` : "-"}
          </span>
          {text && (
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(text, "AFD_IP")}
            />
          )}
        </Space>
      ),
    },
    {
      title: "BAIDULOCNEW",
      dataIndex: "baidulocnew",
      key: "baidulocnew",
      width: 200,
      ellipsis: true,
      render: (text) => (
        <Space>
          <span style={{ fontFamily: "monospace", fontSize: "12px" }}>
            {text ? `${text.substring(0, 20)}...` : "-"}
          </span>
          {text && (
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(text, "BAIDULOCNEW")}
            />
          )}
        </Space>
      ),
    },
    {
      title: "URL",
      dataIndex: "url",
      key: "url",
      width: 300,
      ellipsis: true,
      render: (text) => (
        <a href={text} target="_blank" rel="noopener noreferrer" style={{ fontSize: "12px" }}>
          {text}
        </a>
      ),
    },
    {
      title: "时间戳",
      dataIndex: "timestamp",
      key: "timestamp",
      width: 180,
      render: (text) => (
        <span style={{ fontSize: "12px" }}>{text}</span>
      ),
    },
    {
      title: "代理 IP",
      dataIndex: "proxy_ip",
      key: "proxy_ip",
      width: 150,
      render: (text) => (
        text ? (
          <Tag color="blue" style={{ fontSize: "12px" }}>
            {text}
          </Tag>
        ) : (
          <span style={{ color: "#ccc" }}>-</span>
        )
      ),
    },
    {
      title: "代理端口",
      dataIndex: "proxy_port",
      key: "proxy_port",
      width: 100,
      render: (text) => (
        text ? (
          <Tag color="cyan" style={{ fontSize: "12px" }}>
            {text}
          </Tag>
        ) : (
          <span style={{ color: "#ccc" }}>-</span>
        )
      ),
    },
    {
      title: "代理城市",
      dataIndex: "proxy_city",
      key: "proxy_city",
      width: 120,
      render: (text) => (
        text ? (
          <Tag color="purple" style={{ fontSize: "12px" }}>
            {text}
          </Tag>
        ) : (
          <span style={{ color: "#ccc" }}>-</span>
        )
      ),
    },
    {
      title: "代理地址",
      dataIndex: "proxy_addr",
      key: "proxy_addr",
      width: 200,
      ellipsis: true,
      render: (text) => (
        text ? (
          <span style={{ fontSize: "12px" }}>{text}</span>
        ) : (
          <span style={{ color: "#ccc" }}>-</span>
        )
      ),
    },
    {
      title: "Headers",
      dataIndex: "headers",
      key: "headers",
      width: 300,
      ellipsis: true,
      render: (headers) => {
        if (!headers) return <span style={{ color: "#ccc" }}>-</span>;
        
        // 如果是字符串，尝试解析为 JSON
        let headersObj = headers;
        if (typeof headers === 'string') {
          try {
            headersObj = JSON.parse(headers);
          } catch (e) {
            return (
              <Space>
                <span style={{ fontFamily: "monospace", fontSize: "12px" }}>
                  {headers.substring(0, 30)}...
                </span>
                <Button
                  type="link"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(headers, "Headers")}
                />
              </Space>
            );
          }
        }
        
        // 显示 JSON 对象的关键信息
        const headerStr = JSON.stringify(headersObj);
        return (
          <Space>
            <span style={{ fontFamily: "monospace", fontSize: "12px" }}>
              {headerStr.substring(0, 30)}...
            </span>
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(headerStr, "Headers")}
            />
          </Space>
        );
      },
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (text) => (
        <span style={{ fontSize: "12px" }}>
          {dayjs(text).format("YYYY-MM-DD HH:mm:ss")}
        </span>
      ),
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 180,
      render: (text) => (
        <span style={{ fontSize: "12px" }}>
          {dayjs(text).format("YYYY-MM-DD HH:mm:ss")}
        </span>
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 120,
      fixed: "right",
      render: (_, record) => (
        <Space>
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: "24px", background: "#f0f2f5", minHeight: "100%" }}>
      <h2 style={{ marginBottom: "24px", marginTop: 0 }}>
        🍪 百度 Cookie 数据管理
      </h2>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: "24px" }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Cookie 总数"
              value={totalCount}
              prefix="📊"
              valueStyle={{ color: "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="当前显示"
              value={cookies.length}
              prefix="📋"
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="最近更新"
              value={
                cookies.length > 0
                  ? dayjs(cookies[0].updated_at).format("MM-DD HH:mm")
                  : "-"
              }
              prefix="🕐"
            />
          </Card>
        </Col>
      </Row>

      {/* 操作按钮 */}
      <Card style={{ marginBottom: "16px" }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalVisible(true)}
          >
            添加 Cookie
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchCookies} loading={loading}>
            刷新
          </Button>
        </Space>
      </Card>

      {/* 数据表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={cookies}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ x: 2700 }}
          size="small"
        />
      </Card>

      {/* 添加 Cookie 弹窗 */}
      <Modal
        title="添加 Cookie 数据"
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={700}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddCookie}
          initialValues={{
            timestamp: new Date().toISOString(),
          }}
        >
          <Form.Item
            label="AFD_IP"
            name="afd_ip"
            rules={[{ required: true, message: "请输入 AFD_IP" }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入 AFD_IP Cookie 值（必填，作为唯一标识）"
            />
          </Form.Item>

          <Form.Item label="BAIDULOCNEW" name="baidulocnew">
            <Input.TextArea rows={2} placeholder="请输入 BAIDULOCNEW Cookie 值（可选）" />
          </Form.Item>

          <Form.Item
            label="URL"
            name="url"
            rules={[{ required: true, message: "请输入 URL" }]}
          >
            <Input placeholder="请输入请求 URL" />
          </Form.Item>

          <Form.Item
            label="时间戳"
            name="timestamp"
            rules={[{ required: true, message: "请输入时间戳" }]}
          >
            <Input placeholder="ISO 8601 格式，例如：2024-01-01T00:00:00Z" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

