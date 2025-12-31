/**
 * History Page Component
 *
 * 历史页面组件
 */

import React, { useEffect, useState } from 'react';
import { Card, List, Typography, Tag, Button, Empty, Spin, message, Pagination } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { researchApi } from '../services/api';
import type { TaskInfo } from '../types/research';

const { Title, Text } = Typography;

const History: React.FC = () => {
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  useEffect(() => {
    fetchTasks(currentPage);
  }, [currentPage]);

  const fetchTasks = async (page: number) => {
    try {
      setLoading(true);
      const response = await researchApi.getTaskHistory(pageSize, (page - 1) * pageSize);
      setTasks(response.tasks);
      setTotal(response.total);
    } catch (error) {
      console.error('获取任务历史失败:', error);
      message.error('获取任务历史失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      case 'running':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
      case 'cancelled':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return '等待中';
      case 'running':
        return '运行中';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'cancelled':
        return '已取消';
      default:
        return status;
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  if (loading && currentPage === 1) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>任务历史</Title>
        <Text type="secondary">查看所有已完成和进行中的研究任务</Text>
      </div>

      <Card>
        {tasks.length > 0 ? (
          <>
            <List
              dataSource={tasks}
              renderItem={(task) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getStatusIcon(task.status)}
                    title={
                      <div>
                        <Text strong style={{ display: 'block', marginBottom: 4 }}>
                          {task.query.length > 100 ? `${task.query.substring(0, 100)}...` : task.query}
                        </Text>
                        <Tag
                          color={
                            task.status === 'completed' ? 'success' :
                            task.status === 'running' ? 'processing' :
                            task.status === 'failed' ? 'error' :
                            task.status === 'cancelled' ? 'default' :
                            'warning'
                          }
                        >
                          {getStatusText(task.status)}
                        </Tag>
                      </div>
                    }
                    description={
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          任务 ID: {task.task_id}
                        </Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          创建时间: {new Date(task.created_at).toLocaleString()}
                        </Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          更新时间: {new Date(task.updated_at).toLocaleString()}
                        </Text>
                        {task.progress && (
                          <>
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              进度: {task.progress.current}/{task.progress.total} - {task.progress.step}
                            </Text>
                          </>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Pagination
                current={currentPage}
                total={total}
                pageSize={pageSize}
                onChange={handlePageChange}
                showSizeChanger={false}
                showQuickJumper
                showTotal={(total, range) =>
                  `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                }
              />
            </div>
          </>
        ) : (
          <Empty
            description="暂无任务历史"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
    </div>
  );
};

export default History;

