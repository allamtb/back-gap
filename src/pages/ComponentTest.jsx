import React from 'react';
import { Card, Space, Typography } from 'antd';

const { Title, Text } = Typography;

export default function ComponentTest() {
  return (
    <div style={{ padding: '20px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card>
          <Title level={3}>组件测试页面</Title>
          <Text type="secondary">这是一个用于测试各种组件的页面</Text>
        </Card>

        <Card title="测试区域">
          <Text>在这里可以添加需要测试的组件</Text>
        </Card>
      </Space>
    </div>
  );
}
