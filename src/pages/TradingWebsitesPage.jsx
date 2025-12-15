import React, { useState, useEffect } from "react";
import { Card, Button, Modal, Form, Input, message, Space, Popconfirm, Row, Col } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, GlobalOutlined } from "@ant-design/icons";
import "../styles/global/App.css";

export default function TradingWebsitesPage() {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingLink, setEditingLink] = useState(null);
  const [form] = Form.useForm();

  // 加载链接列表
  const loadLinks = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/trading-links');
      const result = await response.json();
      
      if (result.success) {
        setLinks(result.data);
      } else {
        message.error("加载链接失败");
      }
    } catch (error) {
      console.error("加载链接失败:", error);
      message.error("加载链接失败: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadLinks();
  }, []);

  // 打开创建/编辑对话框
  const openModal = (link = null) => {
    setEditingLink(link);
    if (link) {
      form.setFieldsValue({
        name: link.name,
        url: link.url,
        description: link.description,
        category: link.category,
      });
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  // 关闭对话框
  const closeModal = () => {
    setModalVisible(false);
    setEditingLink(null);
    form.resetFields();
  };

  // 创建或更新链接
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      const url = editingLink
        ? `/api/trading-links/${editingLink.id}`
        : '/api/trading-links';
      
      const method = editingLink ? "PUT" : "POST";
      
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(values),
      });
      
      const result = await response.json();
      
      if (result.success) {
        message.success(editingLink ? "链接更新成功" : "链接创建成功");
        closeModal();
        loadLinks();
      } else {
        message.error(result.message || "操作失败");
      }
    } catch (error) {
      console.error("操作失败:", error);
      message.error("操作失败: " + error.message);
    }
  };

  // 删除链接
  const handleDelete = async (linkId) => {
    try {
      const response = await fetch(`/api/trading-links/${linkId}`, {
        method: "DELETE",
      });
      
      const result = await response.json();
      
      if (result.success) {
        message.success("链接删除成功");
        loadLinks();
      } else {
        message.error(result.message || "删除失败");
      }
    } catch (error) {
      console.error("删除失败:", error);
      message.error("删除失败: " + error.message);
    }
  };

  // 打开链接
  const handleOpenLink = (url) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div style={{ padding: "24px", background: "#f0f2f5", minHeight: "100vh" }}>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>
          <GlobalOutlined style={{ marginRight: 8 }} />
          交易网站管理
        </h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          size="large"
          onClick={() => openModal()}
        >
          添加网站
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {links.map((link) => (
          <Col xs={24} sm={12} md={8} lg={6} xl={4} key={link.id}>
            <Card
              hoverable
              onClick={() => handleOpenLink(link.url)}
              style={{
                height: "100%",
                cursor: "pointer",
                transition: "all 0.3s ease",
              }}
              bodyStyle={{
                padding: "16px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                height: "100%",
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <h3
                  style={{
                    margin: 0,
                    fontSize: 16,
                    fontWeight: 600,
                    color: "#1890ff",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={link.name}
                >
                  {link.name}
                </h3>
                {link.category && (
                  <div style={{ marginTop: 8, fontSize: 12, color: "#999" }}>
                    {link.category}
                  </div>
                )}
              </div>

               <Space
                 size="small"
                 onClick={(e) => e.stopPropagation()}
                 style={{ marginTop: "auto" }}
               >
                 <Button
                   type="text"
                   size="small"
                   icon={<EditOutlined style={{ fontSize: 12 }} />}
                   onClick={(e) => {
                     e.stopPropagation();
                     openModal(link);
                   }}
                   style={{ fontSize: 12, padding: "0 4px" }}
                 >
                   编辑
                 </Button>
                 <Popconfirm
                   title="确认删除"
                   description="确定要删除这个链接吗？"
                   onConfirm={(e) => {
                     e?.stopPropagation();
                     handleDelete(link.id);
                   }}
                   onCancel={(e) => e?.stopPropagation()}
                   okText="确定"
                   cancelText="取消"
                 >
                   <Button
                     type="text"
                     size="small"
                     danger
                     icon={<DeleteOutlined style={{ fontSize: 12 }} />}
                     onClick={(e) => e.stopPropagation()}
                     style={{ fontSize: 12, padding: "0 4px" }}
                   >
                     删除
                   </Button>
                 </Popconfirm>
               </Space>
            </Card>
          </Col>
        ))}
      </Row>

      {links.length === 0 && !loading && (
        <Card style={{ textAlign: "center", padding: "60px 0" }}>
          <div style={{ color: "#999", fontSize: 16 }}>
            暂无数据，点击右上角"添加网站"按钮创建第一个链接
          </div>
        </Card>
      )}
      <Modal
        title={editingLink ? "编辑网站链接" : "添加网站链接"}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={closeModal}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="name"
            label="网站名称"
            rules={[{ required: true, message: "请输入网站名称" }]}
          >
            <Input placeholder="例如：币安交易所" />
          </Form.Item>

          <Form.Item
            name="url"
            label="网站地址"
            rules={[
              { required: true, message: "请输入网站地址" },
              { type: "url", message: "请输入有效的URL地址" },
            ]}
          >
            <Input placeholder="https://www.example.com" />
          </Form.Item>

          <Form.Item
            name="category"
            label="分类"
          >
            <Input placeholder="例如：交易所、数据分析、新闻资讯" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea
              rows={3}
              placeholder="简单描述这个网站的用途"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

