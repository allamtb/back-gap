import React, { useState } from 'react';
import { Card, Row, Col, Typography, Button } from 'antd';
import { RobotOutlined, MedicineBoxOutlined, SettingOutlined, CarOutlined, DribbbleOutlined, ThunderboltOutlined, UserOutlined, BulbOutlined, SmileOutlined, CarFilled, BookOutlined, MessageOutlined, TrophyOutlined, GlobalOutlined, FireOutlined, ShoppingOutlined, TruckOutlined, HeartOutlined, InfoCircleOutlined, ExperimentOutlined, AppstoreOutlined, ApiOutlined, CrownOutlined, DownOutlined, RightOutlined, UpOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export default function RobotNavigationPage() {
  const [expandedCategories, setExpandedCategories] = useState({});
  const [expandedSubcategories, setExpandedSubcategories] = useState({});

  const handleCategoryClick = (groupIndex, categoryIndex) => {
    const key = `${groupIndex}-${categoryIndex}`;
    setExpandedCategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
    // 重置相关的二级分类展开状态
    setExpandedSubcategories(prev => {
      const newState = { ...prev };
      Object.keys(newState).forEach(k => {
        if (k.startsWith(`${key}-`)) {
          delete newState[k];
        }
      });
      return newState;
    });
  };

  const handleSubcategoryClick = (groupIndex, categoryIndex, subIndex) => {
    const key = `${groupIndex}-${categoryIndex}-${subIndex}`;
    setExpandedSubcategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const robotCategoryGroups = [
    {
      groupName: '🏭 核心应用领域',
      groupColor: '#1890ff',
      categories: [
        {
          title: '工业机器人',
          icon: <SettingOutlined style={{ fontSize: '20px', color: '#faad14' }} />,
          subcategories: [
            { name: '焊接机器人', level: 2 },
            { name: '装配机器人', level: 2 },
            { name: '检测机器人', level: 2 },
            { name: '搬运机器人', level: 2 }
          ],
          color: '#faad14'
        },
        {
          title: '服务机器人',
          icon: <RobotOutlined style={{ fontSize: '20px', color: '#1890ff' }} />,
          subcategories: [
            { name: '迎宾机器人', level: 2 },
            { name: '清洁机器人', level: 2 },
            { name: '配送机器人', level: 2 }
          ],
          color: '#1890ff'
        },
        {
          title: '医疗机器人',
          icon: <MedicineBoxOutlined style={{ fontSize: '20px', color: '#52c41a' }} />,
          subcategories: [
            { name: '手术机器人', level: 2 },
            { name: '康复机器人', level: 2 },
            { name: '辅助诊断', level: 2 }
          ],
          color: '#52c41a'
        },
        {
          title: '农业机器人',
          icon: <RobotOutlined style={{ fontSize: '20px', color: '#13c2c2' }} />,
          subcategories: [
            { name: '采摘机器人', level: 2 },
            { name: '耕种机器人', level: 2 },
            { name: '监测机器人', level: 2 }
          ],
          color: '#13c2c2'
        },
        {
          title: '特种机器人',
          icon: <FireOutlined style={{ fontSize: '20px', color: '#eb2f96' }} />,
          subcategories: [
            { name: '消防机器人', level: 2 },
            { name: '水下机器人', level: 2 },
            { name: '太空机器人', level: 2 },
            { name: '救援机器人', level: 3 }
          ],
          color: '#eb2f96'
        }
      ]
    },
    {
      groupName: '🚀 新兴技术领域',
      groupColor: '#722ed1',
      categories: [
        {
          title: '人形机器人',
          icon: <UserOutlined style={{ fontSize: '20px', color: '#1890ff' }} />,
          subcategories: [
            { name: '仿人机器人', level: 2 },
            { name: '协作机器人', level: 2 }
          ],
          color: '#1890ff'
        },
        {
          title: '无人机系统',
          icon: <ThunderboltOutlined style={{ fontSize: '20px', color: '#722ed1' }} />,
          subcategories: [
            { name: '工业无人机', level: 2 },
            { name: '消费级无人机', level: 2 },
            { name: '农业植保无人机', level: 3 }
          ],
          color: '#722ed1'
        },
        {
          title: '自动驾驶',
          icon: <CarOutlined style={{ fontSize: '20px', color: '#eb2f96' }} />,
          subcategories: [
            { name: 'L2级自动驾驶', level: 2 },
            { name: 'L3级自动驾驶', level: 2 },
            { name: 'L4级自动驾驶', level: 2 },
            { name: 'L5级自动驾驶', level: 3 }
          ],
          color: '#eb2f96'
        },
        {
          title: '物流机器人',
          icon: <TruckOutlined style={{ fontSize: '20px', color: '#faad14' }} />,
          subcategories: [
            { name: 'AGV', level: 2 },
            { name: 'AMR', level: 2 },
            { name: '仓储机器人', level: 2 }
          ],
          color: '#faad14'
        }
      ]
    },
    {
      groupName: '🎮 消费娱乐领域',
      groupColor: '#52c41a',
      categories: [
        {
          title: '宠物机器人',
          icon: <HeartOutlined style={{ fontSize: '20px', color: '#52c41a' }} />,
          subcategories: [
            { name: '机器狗', level: 2 },
            { name: '机器猫', level: 2 },
            { name: '智能宠物玩具', level: 3 }
          ],
          color: '#52c41a'
        },
        {
          title: '娱乐机器人',
          icon: <SmileOutlined style={{ fontSize: '20px', color: '#faad14' }} />,
          subcategories: [
            { name: '互动机器人', level: 2 },
            { name: '音乐机器人', level: 2 }
          ],
          color: '#faad14'
        },
        {
          title: '教育机器人',
          icon: <BookOutlined style={{ fontSize: '20px', color: '#13c2c2' }} />,
          subcategories: [
            { name: '编程教育', level: 2 },
            { name: '语言学习', level: 2 },
            { name: 'STEM教育', level: 3 }
          ],
          color: '#13c2c2'
        },
        {
          title: '健身机器人',
          icon: <DribbbleOutlined style={{ fontSize: '20px', color: '#722ed1' }} />,
          subcategories: [
            { name: '健身教练', level: 2 },
            { name: '康复训练', level: 2 }
          ],
          color: '#722ed1'
        }
      ]
    },
    {
      groupName: '🏢 行业生态',
      groupColor: '#fa8c16',
      categories: [
        {
          title: '机器人公司',
          icon: <AppstoreOutlined style={{ fontSize: '20px', color: '#1890ff' }} />,
          subcategories: [
            { name: '创业公司', level: 2 },
            { name: '上市公司', level: 2 },
            { name: '独角兽企业', level: 3 }
          ],
          color: '#1890ff'
        },
        {
          title: '机器人会展',
          icon: <CrownOutlined style={{ fontSize: '20px', color: '#52c41a' }} />,
          subcategories: [
            { name: '国际展会', level: 2 },
            { name: '行业论坛', level: 2 }
          ],
          color: '#52c41a'
        },
        {
          title: '机器人竞赛',
          icon: <TrophyOutlined style={{ fontSize: '20px', color: '#faad14' }} />,
          subcategories: [
            { name: '机器人世界杯', level: 2 },
            { name: '大学生竞赛', level: 2 },
            { name: '创新大赛', level: 3 }
          ],
          color: '#faad14'
        },
        {
          title: '机器人资讯',
          icon: <InfoCircleOutlined style={{ fontSize: '20px', color: '#13c2c2' }} />,
          subcategories: [
            { name: '行业新闻', level: 2 },
            { name: '技术动态', level: 2 },
            { name: '政策法规', level: 3 }
          ],
          color: '#13c2c2'
        }
      ]
    },
    {
      groupName: '🧠 技术研究',
      groupColor: '#eb2f96',
      categories: [
        {
          title: '人工智能应用',
          icon: <BulbOutlined style={{ fontSize: '20px', color: '#722ed1' }} />,
          subcategories: [
            { name: '机器学习', level: 2 },
            { name: '计算机视觉', level: 2 },
            { name: '自然语言处理', level: 2 },
            { name: '深度学习算法', level: 3 }
          ],
          color: '#722ed1'
        }
      ]
    }
  ];

  const toggleCategory = (groupIndex, categoryIndex) => {
    const key = `${groupIndex}-${categoryIndex}`;
    setExpandedCategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const toggleSubcategory = (groupIndex, categoryIndex, subIndex) => {
    const key = `${groupIndex}-${categoryIndex}-${subIndex}`;
    setExpandedSubcategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const renderSubcategory = (subcategory, categoryColor, groupIndex, categoryIndex, subIndex) => {
    const subcategoryKey = `${groupIndex}-${categoryIndex}-${subIndex}`;
    const isExpanded = expandedSubcategories[subcategoryKey];
    const hasLevel3 = subcategory.level === 2;

    return (
      <div key={subIndex} style={{ marginBottom: '6px' }}>
        <Button
          type="text"
          size="small"
          style={{
            width: '100%',
            textAlign: 'left',
            padding: '8px 12px',
            borderRadius: '6px',
            background: isExpanded ? `${categoryColor}15` : 'transparent',
            border: `1px solid ${isExpanded ? categoryColor : 'transparent'}`,
            color: subcategory.level === 3 ? '#666' : categoryColor,
            fontSize: '12px',
            fontWeight: '500',
            height: 'auto',
            whiteSpace: 'normal'
          }}
          onClick={() => hasLevel3 && handleSubcategoryClick(groupIndex, categoryIndex, subIndex)}
          disabled={!hasLevel3}
        >
          <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            <span style={{ marginRight: '8px', minWidth: '12px' }}>
              {subcategory.level === 3 ? '└' :
               hasLevel3 ? (isExpanded ? '▼' : '▶') : '•'}
            </span>
            <span style={{ flex: 1 }}>{subcategory.name}</span>
          </div>
        </Button>

        {/* 三级分类展开 */}
        {isExpanded && hasLevel3 && (
          <div style={{
            marginLeft: '24px',
            marginTop: '6px',
            padding: '8px',
            background: '#f8f9fa',
            borderRadius: '4px',
            border: `1px solid ${categoryColor}20`
          }}>
            {category.subcategories
              .filter(s => s.level === 3)
              .map((level3, level3Index) => (
                <Text
                  key={level3Index}
                  style={{
                    display: 'inline-block',
                    margin: '2px 4px 2px 0',
                    padding: '3px 8px',
                    background: '#fff',
                    color: '#666',
                    borderRadius: '3px',
                    fontSize: '11px',
                    border: `1px solid ${categoryColor}15`
                  }}
                >
                  └ {level3.name}
                </Text>
              ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ padding: '16px', background: '#fff', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{
        textAlign: 'center',
        marginBottom: '24px',
        padding: '16px 0',
        borderBottom: '2px solid #f0f0f0'
      }}>
        <Title level={2} style={{
          color: '#1890ff',
          margin: 0,
          fontSize: '24px'
        }}>
          🤖 机器人导航
        </Title>
      </div>

      {/* 交互式分类展示 */}
      {robotCategoryGroups.map((group, groupIndex) => (
        <div key={groupIndex} style={{ marginBottom: '32px' }}>
          {/* 分组标题 */}
          <div style={{
            background: group.groupColor,
            color: '#fff',
            padding: '12px 16px',
            fontSize: '16px',
            fontWeight: '600',
            borderRadius: '6px',
            marginBottom: '16px',
            display: 'inline-block'
          }}>
            {group.groupName}
          </div>

          {/* 一级分类网格 */}
          <Row gutter={[12, 12]}>
            {group.categories.map((category, categoryIndex) => {
              const categoryKey = `${groupIndex}-${categoryIndex}`;
              const isExpanded = expandedCategories[categoryKey];
              const hasSubcategories = category.subcategories && category.subcategories.length > 0;

              return (
                <Col
                  xs={12}  // 手机端2列
                  sm={8}   // 小屏3列
                  md={6}   // 中屏4列
                  lg={6}   // 大屏4列
                  xl={4}   // 超大屏5列
                  key={categoryIndex}
                >
                  <Card
                    style={{
                      borderRadius: '8px',
                      border: `2px solid ${isExpanded ? category.color : category.color + '30'}`,
                      background: '#fff',
                      transition: 'all 0.2s ease',
                      cursor: hasSubcategories ? 'pointer' : 'default',
                      transform: isExpanded ? 'scale(1.02)' : 'scale(1)'
                    }}
                    bodyStyle={{
                      padding: '16px',
                      textAlign: 'center',
                      height: '120px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center'
                    }}
                    onClick={() => hasSubcategories && handleCategoryClick(groupIndex, categoryIndex)}
                  >
                    {/* 图标和标题 */}
                    <div style={{ marginBottom: '8px' }}>
                      {category.icon}
                    </div>

                    <Text
                      strong
                      style={{
                        color: category.color,
                        fontSize: '14px',
                        display: 'block',
                        marginBottom: '4px'
                      }}
                    >
                      {category.title}
                    </Text>

                    {/* 展开指示器 */}
                    {hasSubcategories && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginTop: '8px'
                      }}>
                        <Text
                          style={{
                            fontSize: '12px',
                            color: category.color,
                            fontWeight: '500'
                          }}
                        >
                          {category.subcategories.length} 个分类
                        </Text>
                        <span style={{
                          marginLeft: '8px',
                          fontSize: '12px',
                          color: category.color,
                          transition: 'transform 0.2s ease'
                        }}>
                          {isExpanded ? <DownOutlined /> : <RightOutlined />}
                        </span>
                      </div>
                    )}
                  </Card>

                  {/* 展开的二级分类 */}
                  {isExpanded && hasSubcategories && (
                    <div style={{
                      marginTop: '8px',
                      background: '#f8f9fa',
                      borderRadius: '8px',
                      padding: '12px',
                      border: `1px solid ${category.color}20`,
                      animation: 'slideDown 0.3s ease-out'
                    }}>
                      <Text
                        strong
                        style={{
                          fontSize: '13px',
                          color: category.color,
                          display: 'block',
                          marginBottom: '12px'
                        }}
                      >
                        📂 二级分类：
                      </Text>

                      <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {category.subcategories.map((sub, subIndex) => (
                          renderSubcategory(sub, category.color, groupIndex, categoryIndex, subIndex)
                        ))}
                      </div>
                    </div>
                  )}
                </Col>
              );
            })}
          </Row>
        </div>
      ))}

      <style jsx>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
