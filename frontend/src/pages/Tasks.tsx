/**
 * Tasks Page Component
 *
 * 任务页面组件
 */

import React, { useEffect, useState } from 'react';
import { Card, List, Typography, Tag, Button, Empty, Spin, message } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { researchApi } from '../services/api';
import type { TaskInfo } from '../types/research';
import { ResearchStatus } from '../types/research';

const { Title, Text } = Typography;

const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await researchApi.getTaskHistory(20, 0);
      setTasks(response.tasks);
    } catch (error) {
      console.error('获取任务列表失败:', error);
      message.error('获取任务列表失败');
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

  const handleCancelTask = async (taskId: string) => {
    try {
      await researchApi.cancelTask(taskId);
      message.success('任务已取消');
      fetchTasks();
    } catch (error) {
      console.error('取消任务失败:', error);
      message.error('取消任务失败');
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await researchApi.deleteTask(taskId);
      message.success('任务已删除');
      fetchTasks();
    } catch (error) {
      console.error('删除任务失败:', error);
      message.error('删除任务失败');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>任务管理</Title>
        <Text type="secondary">查看和管理您的研究任务</Text>
      </div>

      <Card>
        {tasks.length > 0 ? (
          <List
            dataSource={tasks}
            renderItem={(task) => (
              <List.Item
                actions={[
                  task.status === ResearchStatus.RESEARCHING || task.status === ResearchStatus.PENDING ? (
                    <Button
                      key="cancel"
                      type="text"
                      danger
                      onClick={() => handleCancelTask(task.task_id)}
                    >
                      取消
                    </Button>
                  ) : null,
                  <Button
                    key="delete"
                    type="text"
                    danger
                    onClick={() => {
                      if (window.confirm('确定要删除此任务吗？此操作不可逆。')) {
                        handleDeleteTask(task.task_id);
                      }
                    }}
                  >
                    删除
                  </Button>
                ].filter(Boolean)}
              >
                <List.Item.Meta
                  avatar={getStatusIcon(task.status)}
                  title={
                    <div>
                      <Text strong>{task.query}</Text>
                      <Tag
                        color={
                          task.status === ResearchStatus.COMPLETED ? 'success' :
                          task.status === ResearchStatus.RESEARCHING ? 'processing' :
                          task.status === ResearchStatus.FAILED ? 'error' :
                          task.status === ResearchStatus.CANCELLED ? 'default' :
                          'warning'
                        }
                        style={{ marginLeft: 8 }}
                      >
                        {getStatusText(task.status)}
                      </Tag>
                    </div>
                  }
                  description={
                    <div>
                      <Text type="secondary">
                        任务 ID: {task.task_id}
                      </Text>
                      <br />
                      <Text type="secondary">
                        创建时间: {new Date(task.created_at).toLocaleString()}
                      </Text>
                      <br />
                      <Text type="secondary">
                        更新时间: {new Date(task.updated_at).toLocaleString()}
                      </Text>
                      {task.progress && (
                        <>
                          <br />
                          <Text type="secondary">
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
        ) : (
          <Empty
            description="暂无任务"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
    </div>
  );
};

export default Tasks;
