import React, { useMemo } from "react";
import { Table, Tag, Button, Space, Alert } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { formatPrice } from "../utils/formatters";

/**
 * PositionStatusTable - 实时持仓状态表格
 * 
 * 功能：
 * 1. 展示所有交易所的当前持仓
 * 2. 实时更新盈亏情况
 * 3. 支持选中持仓（用于平仓）
 * 4. 支持单个持仓快速平仓
 */
function PositionStatusTable({ 
  positions = [], 
  onSelectionChange, 
  onClosePosition,
  loading = false,
  error = null,
  onRefresh,
  refreshCountdown = 0,
  monitoringInterval = 300 // 单位：秒
}) {
  const [selectedRowKeys, setSelectedRowKeys] = React.useState([]);

  // 使用 useMemo 稳定 columns 引用，避免不必要的重新渲染
  const columns = useMemo(() => [
    {
      title: '交易所',
      dataIndex: 'exchange',
      width: 100,
      render: (text) => <Tag color="blue">{text.toUpperCase()}</Tag>,
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      width: 100,
    },
    {
      title: '类型',
      dataIndex: 'marketType',
      width: 80,
      render: (type) => (
        <Tag color={type === 'spot' ? 'blue' : 'orange'}>
          {type === 'spot' ? '现货' : '合约'}
        </Tag>
      ),
    },
    {
      title: '方向',
      dataIndex: 'side',
      width: 80,
      render: (side) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '做多' : '做空'}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'amount',
      width: 100,
      align: 'right',
    },
    {
      title: '开仓均价',
      dataIndex: 'openPrice',
      width: 100,
      align: 'right',
      render: (price, record) => {
        if (price === null || price === undefined || price === '' || price === '-') {
          return '-';
        }
        // 统一精度：现货和合约都使用相同的精度显示
        // 根据价格大小自动调整精度：大于1显示2位小数，小于1显示更多小数
        const numPrice = typeof price === 'string' ? parseFloat(price) : price;
        if (isNaN(numPrice)) return price;
        
        if (numPrice >= 1) {
          return numPrice.toFixed(2);
        } else if (numPrice >= 0.01) {
          return numPrice.toFixed(4);
        } else if (numPrice >= 0.0001) {
          return numPrice.toFixed(6);
        } else {
          return numPrice.toFixed(8);
        }
      },
    },
    {
      title: '当前价',
      dataIndex: 'currentPrice',
      width: 100,
      align: 'right',
      render: (price, record) => {
        if (price === null || price === undefined || price === '' || price === '-') {
          return '-';
        }
        // 统一精度：现货和合约都使用相同的精度显示
        // 根据价格大小自动调整精度：大于1显示2位小数，小于1显示更多小数
        const numPrice = typeof price === 'string' ? parseFloat(price) : price;
        if (isNaN(numPrice)) return price;
        
        if (numPrice >= 1) {
          return numPrice.toFixed(2);
        } else if (numPrice >= 0.01) {
          return numPrice.toFixed(4);
        } else if (numPrice >= 0.0001) {
          return numPrice.toFixed(6);
        } else {
          return numPrice.toFixed(8);
        }
      },
    },
    {
      title: '手续费',
      dataIndex: 'fee',
      width: 100,
      align: 'right',
      render: (fee) => (
        <span style={{ color: '#ff9800' }}>
          {fee?.toFixed(2) || '0.00'} USDT
        </span>
      ),
    },
    {
      title: '浮动盈亏',
      dataIndex: 'unrealizedPnl',
      width: 120,
      align: 'right',
      render: (pnl, record) => (
        <span 
          key={`pnl-${record.key}-${pnl}`}
          className="unrealized-pnl-cell"
          style={{ 
            color: pnl >= 0 ? '#52c41a' : '#ff4d4f', 
            fontWeight: 'bold',
            display: 'inline-block',
            minWidth: '100px',
            textAlign: 'right'
          }}
        >
          {pnl >= 0 ? '+' : ''}{pnl?.toFixed(2) || '0.00'} USDT
        </span>
      ),
    },
    {
      title: '盈亏率',
      dataIndex: 'pnlPercent',
      width: 100,
      align: 'right',
      render: (percent, record) => (
        <span 
          key={`percent-${record.key}-${percent}`}
          className="pnl-percent-cell"
          style={{ 
            color: percent >= 0 ? '#52c41a' : '#ff4d4f', 
            fontWeight: 'bold',
            display: 'inline-block',
            minWidth: '80px',
            textAlign: 'right'
          }}
        >
          {percent >= 0 ? '+' : ''}{percent?.toFixed(2) || '0.00'}%
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Space size={4}>
          <Button
            type="primary"
            danger
            size="small"
            onClick={() => onClosePosition && onClosePosition(record)}
          >
            平仓
          </Button>
        </Space>
      ),
    },
  ], []);

  // 使用实时持仓数据
  // 使用 useMemo 稳定引用，避免不必要的重新渲染
  const dataSource = useMemo(() => {
    if (!positions || positions.length === 0) return [];
    return positions.map(pos => ({ ...pos }));
  }, [positions]);

  // 计算汇总数据
  const calculateSummary = () => {
    let totalLongAmount = 0;
    let totalShortAmount = 0;
    let totalFee = 0;
    let totalUnrealizedPnl = 0;
    let totalValue = 0; // 用于计算平均盈亏率

    dataSource.forEach(pos => {
      if (pos.side === 'long') {
        totalLongAmount += pos.amount || 0;
      } else {
        totalShortAmount += pos.amount || 0;
      }
      totalFee += pos.fee || 0;
      totalUnrealizedPnl += pos.unrealizedPnl || 0;
      totalValue += (pos.openPrice || 0) * (pos.amount || 0);
    });

    const netAmount = totalLongAmount - totalShortAmount;
    const avgPnlPercent = totalValue > 0 ? (totalUnrealizedPnl / totalValue) * 100 : 0;

    // 生成数量汇总公式（如：+0.05 -0.05 = 0.00）
    const amountFormula = `+${totalLongAmount.toFixed(4)} -${totalShortAmount.toFixed(4)} = ${netAmount.toFixed(4)}`;

    return {
      key: 'summary',
      exchange: '',
      symbol: '',
      marketType: '',
      side: '',
      amount: netAmount,
      amountFormula: amountFormula, // 数量公式
      openPrice: '',
      currentPrice: '',
      fee: totalFee,
      unrealizedPnl: totalUnrealizedPnl,
      pnlPercent: avgPnlPercent,
      isSummary: true, // 标记这是汇总行
    };
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys, rows) => {
      setSelectedRowKeys(keys);
      // 过滤掉汇总行
      const filteredRows = rows.filter(r => !r.isSummary);
      onSelectionChange && onSelectionChange(filteredRows);
    },
    getCheckboxProps: (record) => ({
      disabled: record.isSummary, // 禁用汇总行的复选框
    }),
  };

  // 格式化刷新间隔显示（countdown 是毫秒，interval 是秒）
  const formatRefreshCountdown = (countdown, interval) => {
    if (!countdown && countdown !== 0) return '';
    // countdown 是毫秒，转换为秒
    const countdownSeconds = Math.floor(countdown / 1000);
    const remaining = Math.max(0, interval - countdownSeconds);
    const minutes = Math.floor(remaining / 60);
    const secs = remaining % 60;
    
    if (minutes > 0) {
      return `${minutes}分${secs}秒`;
    }
    return `${secs}秒`;
  };

  const countdownText = formatRefreshCountdown(refreshCountdown, monitoringInterval);

  return (
    <div>
      <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '12px', color: '#666' }}>
          已选中 {selectedRowKeys.length} 个持仓
          {loading && <span style={{ marginLeft: 8, color: '#1890ff', fontSize: '11px' }}>● 更新中</span>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {countdownText && (
            <span style={{ fontSize: '11px', color: '#999' }}>
              下次刷新: {countdownText}
            </span>
          )}
          {onRefresh && (
            <Button
              type="default"
              size="small"
              icon={<ReloadOutlined spin={loading} />}
              onClick={onRefresh}
              loading={loading}
              disabled={loading}
            >
              刷新
            </Button>
          )}
        </div>
      </div>
      
      {error && (
        <Alert
          message="持仓数据加载失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 8 }}
        />
      )}
      
      <div className="position-table-wrapper" style={{ position: 'relative', minHeight: '300px', maxHeight: '300px' }}>
        <style>{`
          .position-table-wrapper {
            min-height: 300px;
            max-height: 300px;
            overflow: hidden;
            contain: layout style paint;
            will-change: contents;
          }
          .position-table .ant-table {
            table-layout: fixed;
            contain: layout style paint;
          }
          .position-table .ant-table-tbody > tr > td {
            transition: none !important;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding: 8px 12px !important;
            height: 32px !important;
            line-height: 16px !important;
            contain: layout style paint;
          }
          .position-table .ant-table-tbody > tr {
            transition: none !important;
            height: 32px !important;
            contain: layout style paint;
          }
          .position-table .ant-table-body {
            overflow-x: auto;
            overflow-y: auto !important;
            max-height: 300px !important;
            min-height: 300px !important;
            contain: layout style paint;
          }
          .position-table .ant-table-placeholder {
            display: none !important;
          }
          .position-table .ant-table-content {
            overflow: visible !important;
            contain: layout style paint;
          }
        `}</style>
        <Table
          className="position-table"
          size="small"
          columns={columns}
          dataSource={dataSource}
          rowKey="key"
          rowSelection={rowSelection}
          pagination={false}
          scroll={{ y: 300, x: 'max-content' }}
          style={{ minHeight: '300px', maxHeight: '300px' }}
          bordered
          loading={loading}
        summary={() => {
          if (dataSource.length === 0) return null;
          
          const summaryData = calculateSummary();
          
          return (
            <Table.Summary fixed>
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={2} align="left" style={{ backgroundColor: '#e6f7ff' }}>
                  <span style={{ color: '#1890ff', fontWeight: 'bold', marginLeft: '4px' }}>📊 汇总</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2} style={{ backgroundColor: '#e6f7ff' }}></Table.Summary.Cell>
                <Table.Summary.Cell index={3} style={{ backgroundColor: '#e6f7ff' }}></Table.Summary.Cell>
                <Table.Summary.Cell index={4} style={{ backgroundColor: '#e6f7ff' }}></Table.Summary.Cell>
                <Table.Summary.Cell index={5} align="right" style={{ backgroundColor: '#e6f7ff' }}>
                  <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                    {summaryData.amount?.toFixed(4) || '0.0000'}
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={6} style={{ backgroundColor: '#e6f7ff' }}></Table.Summary.Cell>
                <Table.Summary.Cell index={7} style={{ backgroundColor: '#e6f7ff' }}></Table.Summary.Cell>
                <Table.Summary.Cell index={8} align="right" style={{ backgroundColor: '#e6f7ff' }}>
                  <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                    {summaryData.fee?.toFixed(2) || '0.00'} USDT
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={9} align="right" style={{ backgroundColor: '#e6f7ff' }}>
                  <span style={{ 
                    color: summaryData.unrealizedPnl >= 0 ? '#52c41a' : '#ff4d4f', 
                    fontWeight: 'bold',
                    fontSize: '14px'
                  }}>
                    {summaryData.unrealizedPnl >= 0 ? '+' : ''}{summaryData.unrealizedPnl?.toFixed(2) || '0.00'} USDT
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={10} align="right" style={{ backgroundColor: '#e6f7ff' }}>
                  <span style={{ 
                    color: summaryData.pnlPercent >= 0 ? '#52c41a' : '#ff4d4f', 
                    fontWeight: 'bold',
                    fontSize: '14px'
                  }}>
                    {summaryData.pnlPercent >= 0 ? '+' : ''}{summaryData.pnlPercent?.toFixed(2) || '0.00'}%
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={11} style={{ backgroundColor: '#e6f7ff' }}></Table.Summary.Cell>
              </Table.Summary.Row>
            </Table.Summary>
          );
        }}
        />
      </div>
    </div>
  );
}

// 使用 React.memo 包装组件，避免不必要的重新渲染
// 注意：React.memo 的第二个参数返回 true 表示 props 相同（不重新渲染），返回 false 表示 props 不同（需要重新渲染）
export default React.memo(PositionStatusTable, (prevProps, nextProps) => {
  // 如果关键属性不同，返回 false（需要重新渲染）
  if (prevProps.loading !== nextProps.loading) return false;
  if (prevProps.error !== nextProps.error) return false;
  if (prevProps.refreshCountdown !== nextProps.refreshCountdown) return false;
  // positions 数组引用比较（浅比较）
  // 如果 positions 引用相同，返回 true（不重新渲染）
  // 如果 positions 引用不同，返回 false（需要重新渲染，因为价格可能更新了）
  return prevProps.positions === nextProps.positions;
});

