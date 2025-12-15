import React from "react";
import { Card, Space, Button, InputNumber, Radio, Alert, Tag } from "antd";
import { FallOutlined } from "@ant-design/icons";

/**
 * ClosePositionPanel - 平仓控件
 * 
 * 功能：
 * 1. 显示选中的持仓
 * 2. 选择平仓数量（全部/部分）
 * 3. 平仓按钮（市价）
 */
export default function ClosePositionPanel({ selectedPositions = [] }) {
  const [closeAmount, setCloseAmount] = React.useState(null);
  const [closeType, setCloseType] = React.useState('all'); // 'all' | 'partial'
  const [loading, setLoading] = React.useState(false);

  // 判断是否可以平仓
  const canClose = selectedPositions.length > 0;

  // 处理平仓
  const handleClosePosition = async () => {
    if (!canClose) {
      alert('请选择要平仓的持仓');
      return;
    }

    if (closeType === 'partial' && (!closeAmount || closeAmount <= 0)) {
      alert('请输入有效的平仓数量');
      return;
    }

    setLoading(true);
    try {
      // TODO: 调用后端API进行平仓
      console.log('平仓参数:', {
        positions: selectedPositions,
        closeType,
        closeAmount
      });

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('平仓成功！（当前为演示模式）');
    } catch (error) {
      console.error('平仓失败:', error);
      alert('平仓失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card 
      title={<span><FallOutlined /> 平仓控件</span>}
      size="small"
      bodyStyle={{ padding: '16px' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        {/* 选中的持仓展示 */}
        {!canClose ? (
          <Alert
            message="请在下方持仓表格中勾选要平仓的持仓"
            type="warning"
            showIcon
          />
        ) : (
          <div>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: 8 }}>已选中持仓：</div>
            {selectedPositions.map((pos, index) => (
              <Tag key={index} color={pos.side === 'long' ? 'green' : 'red'}>
                {pos.exchange} {pos.symbol} {pos.side === 'long' ? '多' : '空'} {pos.amount}
              </Tag>
            ))}
          </div>
        )}

        {/* 平仓类型选择 */}
        <div>
          <div style={{ marginBottom: 4, fontSize: '12px', color: '#666' }}>平仓类型：</div>
          <Radio.Group 
            value={closeType} 
            onChange={(e) => setCloseType(e.target.value)}
            disabled={!canClose}
          >
            <Radio value="all">全部平仓</Radio>
            <Radio value="partial">部分平仓</Radio>
          </Radio.Group>
        </div>

        {/* 部分平仓数量输入 */}
        {closeType === 'partial' && (
          <div>
            <div style={{ marginBottom: 4, fontSize: '12px', color: '#666' }}>平仓数量：</div>
            <InputNumber
              value={closeAmount}
              onChange={setCloseAmount}
              placeholder="输入平仓数量"
              min={0}
              step={0.001}
              style={{ width: '100%' }}
              disabled={!canClose}
            />
          </div>
        )}

        {/* 平仓说明 */}
        <Alert
          message="平仓说明"
          description="平仓将执行反向操作：多单卖出，空单买入。市价平仓可能存在滑点风险。"
          type="info"
          showIcon
          style={{ fontSize: '11px' }}
        />

        {/* 持仓公式展示 */}
        {canClose && (
          <div style={{ fontSize: '11px', color: '#999', padding: '8px', backgroundColor: '#fafafa', borderRadius: '4px' }}>
            <div>平仓后持仓变化：</div>
            <div style={{ marginTop: 4 }}>
              {selectedPositions.map((pos, index) => (
                <div key={index}>
                  {pos.exchange}: {pos.side === 'long' ? '多' : '空'}{pos.amount} → 0
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 平仓按钮 */}
        <Button
          type="primary"
          danger
          size="large"
          block
          loading={loading}
          onClick={handleClosePosition}
          disabled={!canClose}
          style={{ marginTop: 8 }}
        >
          {loading ? '平仓中...' : '平仓'}
        </Button>
      </Space>
    </Card>
  );
}

