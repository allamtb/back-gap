import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Tag, 
  Rate, 
  Modal, 
  Space, 
  Select, 
  DatePicker, 
  Input,
  Button,
  Empty,
  Spin,
  message,
  Badge
} from 'antd';
import { 
  RiseOutlined, 
  FallOutlined, 
  MinusOutlined,
  ReloadOutlined,
  TwitterOutlined,
  LinkOutlined,
  ClockCircleOutlined,
  FireOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import '../styles/pages/TrumpSentimentPage.css';

const { RangePicker } = DatePicker;
const { Search } = Input;

const TrumpSentimentPage = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analyses, setAnalyses] = useState([]);
  const [filteredAnalyses, setFilteredAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  
  // 筛选条件
  const [filters, setFilters] = useState({
    sentimentType: null, // 'bullish', 'bearish', 'neutral'
    dateRange: null,
    searchKeyword: ''
  });

  // 获取分析列表
  const fetchAnalyses = async () => {
    try {
      const response = await fetch('/api/trump/sentiment/list?limit=1000');
      const result = await response.json();
      if (result.success) {
        setAnalyses(result.data);
        setFilteredAnalyses(result.data);
      }
    } catch (error) {
      console.error('获取分析列表失败:', error);
      message.error('获取分析列表失败');
    }
  };

  // 初始化加载
  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      await fetchAnalyses();
      setLoading(false);
    };
    initData();

    // 定时刷新（30秒）
    const interval = setInterval(() => {
      fetchAnalyses();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // 手动刷新
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalyses();
    setRefreshing(false);
    message.success('数据已刷新');
  };

  // 应用筛选
  useEffect(() => {
    let filtered = [...analyses];

    // 情绪类型筛选
    if (filters.sentimentType) {
      if (filters.sentimentType === 'bullish') {
        filtered = filtered.filter(a => a.analysis.is_bullish === true);
      } else if (filters.sentimentType === 'bearish') {
        filtered = filtered.filter(a => a.analysis.is_bullish === false);
      } else if (filters.sentimentType === 'neutral') {
        filtered = filtered.filter(a => a.analysis.is_bullish === null);
      }
    }

    // 日期范围筛选
    if (filters.dateRange && filters.dateRange.length === 2) {
      const [start, end] = filters.dateRange;
      filtered = filtered.filter(a => {
        const postDate = dayjs(a.post_timestamp);
        return postDate.isAfter(start) && postDate.isBefore(end);
      });
    }

    // 关键词搜索
    if (filters.searchKeyword) {
      const keyword = filters.searchKeyword.toLowerCase();
      filtered = filtered.filter(a => 
        a.post_text.toLowerCase().includes(keyword) ||
        a.analysis.theme.toLowerCase().includes(keyword) ||
        a.analysis.summary.toLowerCase().includes(keyword)
      );
    }

    setFilteredAnalyses(filtered);
  }, [analyses, filters]);

  // 渲染情绪标签
  const renderSentimentTag = (analysis) => {
    if (analysis.is_bullish === true) {
      return <Tag color="success" icon={<RiseOutlined />}>利好</Tag>;
    } else if (analysis.is_bullish === false) {
      return <Tag color="error" icon={<FallOutlined />}>利空</Tag>;
    } else {
      return <Tag color="default" icon={<MinusOutlined />}>中性</Tag>;
    }
  };

  // 渲染情绪标签（文字）
  const renderEmotionTag = (emotion) => {
    const emotionColors = {
      '愤怒': 'red',
      '乐观': 'green',
      '积极': 'green',
      '威胁': 'orange',
      '焦虑': 'gold',
      '悲观': 'default'
    };

    const words = emotion.split(/[、，,]/);
    return words.map((word, index) => (
      <Tag key={index} color={emotionColors[word.trim()] || 'blue'}>
        {word.trim()}
      </Tag>
    ));
  };

  // 渲染星级
  const renderStars = (analysis) => {
    const stars = analysis.rating_stars || 3;
    const color = analysis.is_bullish ? '#52c41a' : (analysis.is_bullish === false ? '#f5222d' : '#8c8c8c');
    return (
      <Rate 
        disabled 
        value={stars} 
        style={{ color }} 
        character="★"
      />
    );
  };

  // 渲染卡片列表
  const renderPostCard = (analysis) => {
    const isBullish = analysis.analysis.is_bullish;
    const isHighRisk = analysis.is_high_risk;
    
    // 根据市场倾向设置边框颜色
    let borderColor = '#d9d9d9';
    if (isBullish === true) borderColor = '#52c41a';
    else if (isBullish === false) borderColor = '#f5222d';
    
    return (
      <Card
        key={analysis.post_id}
        className="post-card"
        hoverable
        onClick={() => {
          setSelectedAnalysis(analysis);
          setModalVisible(true);
        }}
        style={{
          marginBottom: 16,
          borderLeft: `4px solid ${borderColor}`,
          transition: 'all 0.3s'
        }}
      >
        <div className="post-card-header">
          <Space>
            <ClockCircleOutlined />
            <span style={{ color: '#8c8c8c', fontSize: 13 }}>
              {dayjs(analysis.post_timestamp).format('YYYY-MM-DD HH:mm')}
            </span>
            {isHighRisk && (
              <Badge count={<FireOutlined style={{ color: '#ff4d4f' }} />} />
            )}
          </Space>
          <Space>
            {renderSentimentTag(analysis.analysis)}
            {renderStars(analysis.analysis)}
          </Space>
        </div>

        <div className="post-card-content">
          <h3 style={{ margin: '12px 0', fontSize: 16, fontWeight: 600 }}>
            {analysis.analysis.theme || '未提取主题'}
          </h3>
          
          <div style={{ marginBottom: 12 }}>
            {renderEmotionTag(analysis.analysis.emotion)}
          </div>

          <p style={{ 
            color: '#595959', 
            marginBottom: 12,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            lineHeight: '1.6'
          }}>
            {analysis.post_text}
          </p>

          {/* 市场影响 */}
          {analysis.analysis.market_impact && (
            <div 
              className="market-impact-card"
              style={{ 
                marginBottom: 12,
                padding: '10px 14px',
                background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%)',
                borderRadius: 8,
                borderLeft: '4px solid #1890ff',
                boxShadow: '0 1px 4px rgba(24, 144, 255, 0.1)'
              }}
            >
              <div 
                className="market-impact-title"
                style={{ 
                  fontSize: 13, 
                  color: '#1890ff', 
                  marginBottom: 6,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}
              >
                📊 市场影响分析
              </div>
              <p style={{ 
                color: '#434343',
                fontSize: 13,
                margin: 0,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                lineHeight: '1.6',
                fontWeight: 500
              }}>
                {analysis.analysis.market_impact}
              </p>
            </div>
          )}

          {/* 总结 */}
          {analysis.analysis.summary && (
            <div style={{ 
              padding: '8px 12px',
              background: '#fffbe6',
              borderRadius: 6,
              borderLeft: '3px solid #faad14'
            }}>
              <div style={{ 
                fontSize: 12, 
                color: '#8c8c8c', 
                marginBottom: 4,
                fontWeight: 500
              }}>
                💡 总结
              </div>
              <p style={{ 
                color: '#595959',
                fontSize: 13,
                margin: 0,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                lineHeight: '1.5'
              }}>
                {analysis.analysis.summary}
              </p>
            </div>
          )}
        </div>
      </Card>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>加载中...</p>
      </div>
    );
  }

  return (
    <div className="trump-sentiment-page">
      {/* 页面标题栏 */}
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>
            <TwitterOutlined style={{ marginRight: 8 }} /> 
            特朗普情绪分析
          </h2>
          <Space>
            <span style={{ color: '#8c8c8c' }}>共 {filteredAnalyses.length} 条</span>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleRefresh} 
              loading={refreshing}
              type="primary"
            >
              刷新
            </Button>
          </Space>
        </div>

        {/* 筛选器 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            <Select
              placeholder="市场倾向"
              style={{ width: 120 }}
              allowClear
              value={filters.sentimentType}
              onChange={(value) => setFilters({ ...filters, sentimentType: value })}
            >
              <Select.Option value="bullish">💚 利好</Select.Option>
              <Select.Option value="bearish">❤️ 利空</Select.Option>
              <Select.Option value="neutral">⚪ 中性</Select.Option>
            </Select>

            <RangePicker
              placeholder={['开始日期', '结束日期']}
              value={filters.dateRange}
              onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
            />

            <Search
              placeholder="搜索关键词（主题、内容、总结）"
              style={{ width: 300 }}
              value={filters.searchKeyword}
              onChange={(e) => setFilters({ ...filters, searchKeyword: e.target.value })}
              onSearch={(value) => setFilters({ ...filters, searchKeyword: value })}
              allowClear
            />

            <Button onClick={() => setFilters({ sentimentType: null, dateRange: null, searchKeyword: '' })}>
              重置
            </Button>
          </Space>
        </Card>
      </div>

      {/* 帖子卡片列表（滚动） */}
      <div className="posts-scroll-container">
        {filteredAnalyses.length > 0 ? (
          filteredAnalyses.map(analysis => renderPostCard(analysis))
        ) : (
          <Empty 
            description="暂无数据" 
            style={{ padding: '60px 0' }}
          />
        )}
      </div>

      {/* 详情弹窗 */}
      <Modal
        title={
          <Space>
            <TwitterOutlined />
            <span>情绪分析详情</span>
          </Space>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
        style={{ top: 20 }}
      >
        {selectedAnalysis && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto', padding: '8px 0' }}>
            {/* 帖子基本信息 */}
            <Card size="small" title="📌 帖子信息" style={{ marginBottom: 16 }}>
              <p style={{ marginBottom: 8 }}>
                <strong>发布时间：</strong>
                {dayjs(selectedAnalysis.post_timestamp).format('YYYY-MM-DD HH:mm:ss')}
              </p>
              <p style={{ marginBottom: 8 }}>
                <strong>帖子链接：</strong>
                <a href={selectedAnalysis.post_url} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8 }}>
                  查看原帖 <LinkOutlined />
                </a>
              </p>
              {selectedAnalysis.is_high_risk && (
                <Tag color="red" icon={<FireOutlined />}>高风险帖子</Tag>
              )}
            </Card>

            {/* 帖子内容 */}
            <Card size="small" title="📝 帖子内容" style={{ marginBottom: 16 }}>
              <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 15 }}>
                {selectedAnalysis.post_text}
              </p>
            </Card>

            {/* 情绪分析 */}
            <Card size="small" title="🎯 情绪分析" style={{ marginBottom: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <strong>主题：</strong>
                <p style={{ marginTop: 8, fontSize: 15 }}>
                  {selectedAnalysis.analysis.theme || '未提取主题'}
                </p>
              </div>

              <div style={{ marginBottom: 16 }}>
                <strong>情绪：</strong>
                <div style={{ marginTop: 8 }}>
                  {renderEmotionTag(selectedAnalysis.analysis.emotion)}
                </div>
              </div>

              <div style={{ marginBottom: 16, display: 'flex', gap: 32 }}>
                <div>
                  <strong>市场倾向：</strong>
                  <div style={{ marginTop: 8 }}>
                    {renderSentimentTag(selectedAnalysis.analysis)}
                  </div>
                </div>

                <div>
                  <strong>星级评分：</strong>
                  <div style={{ marginTop: 8 }}>
                    {renderStars(selectedAnalysis.analysis)}
                    <span style={{ marginLeft: 12, color: '#8c8c8c' }}>
                      ({selectedAnalysis.analysis.rating_stars || 3} / 5)
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* 市场影响 */}
            {selectedAnalysis.analysis.market_impact && (
              <Card 
                size="small" 
                title={
                  <span style={{ color: '#1890ff', fontWeight: 600 }}>
                    📊 市场影响分析
                  </span>
                }
                style={{ 
                  marginBottom: 16,
                  background: 'linear-gradient(135deg, #f0f5ff 0%, #ffffff 100%)',
                  border: '1px solid #bae7ff'
                }}
              >
                <p style={{ 
                  whiteSpace: 'pre-wrap', 
                  lineHeight: 1.8, 
                  fontSize: 14,
                  color: '#262626',
                  fontWeight: 500,
                  margin: 0
                }}>
                  {selectedAnalysis.analysis.market_impact}
                </p>
              </Card>
            )}

            {/* 总结 */}
            {selectedAnalysis.analysis.summary && (
              <Card size="small" title="💡 总结">
                <p style={{ fontSize: 15, fontWeight: 500, lineHeight: 1.8 }}>
                  {selectedAnalysis.analysis.summary}
                </p>
              </Card>
            )}

            {/* 分析时间 */}
            <p style={{ marginTop: 16, color: '#8c8c8c', textAlign: 'right', fontSize: 12 }}>
              分析时间：{dayjs(selectedAnalysis.analyzed_at).format('YYYY-MM-DD HH:mm:ss')}
            </p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TrumpSentimentPage;


