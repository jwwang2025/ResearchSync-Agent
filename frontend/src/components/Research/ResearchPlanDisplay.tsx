/**
 * ResearchPlanDisplay Component
 *
 * 研究计划详情展示组件
 */

import React, { useState } from 'react';
import { Card, Typography, List, Tag, Space, Divider, Button, Modal, Input, Select, Form, message } from 'antd';
import { EditOutlined, CheckOutlined, CloseOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ResearchPlan, SubTask } from '../../types/research';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface ResearchPlanDisplayProps {
  plan: ResearchPlan;
  onApprove: () => void;
  onReject: (feedback?: string) => void;
  onModify?: (modifiedPlan: ResearchPlan) => void;
  loading?: boolean;
}

export const ResearchPlanDisplay: React.FC<ResearchPlanDisplayProps> = ({
  plan,
  onApprove,
  onReject,
  onModify,
  loading = false
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedPlan, setEditedPlan] = useState<ResearchPlan>(plan);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectFeedback, setRejectFeedback] = useState('');

  const handleSavePlan = () => {
    if (onModify) {
      onModify(editedPlan);
      setIsEditing(false);
      message.success('计划已保存');
    }
  };

  const handleCancelEdit = () => {
    setEditedPlan(plan);
    setIsEditing(false);
  };

  const handleAddSubTask = () => {
    const newTask: SubTask = {
      task_id: Math.max(...editedPlan.sub_tasks.map(t => t.task_id), 0) + 1,
      description: '新任务描述',
      search_queries: [''],
      sources: ['tavily'],
      status: 'pending',
      priority: 1
    };
    setEditedPlan({
      ...editedPlan,
      sub_tasks: [...editedPlan.sub_tasks, newTask]
    });
  };

  const handleRemoveSubTask = (taskId: number) => {
    setEditedPlan({
      ...editedPlan,
      sub_tasks: editedPlan.sub_tasks.filter(t => t.task_id !== taskId)
    });
  };

  const handleUpdateSubTask = (taskId: number, updates: Partial<SubTask>) => {
    setEditedPlan({
      ...editedPlan,
      sub_tasks: editedPlan.sub_tasks.map(t =>
        t.task_id === taskId ? { ...t, ...updates } : t
      )
    });
  };

  const handleReject = () => {
    onReject(rejectFeedback || undefined);
    setShowRejectModal(false);
    setRejectFeedback('');
  };

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      tavily: 'blue',
      arxiv: 'green',
      mcp: 'purple'
    };
    return colors[source] || 'default';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'orange',
      in_progress: 'blue',
      completed: 'green'
    };
    return colors[status] || 'default';
  };

  return (
    <Card
      title={
        <Space>
          <span>研究计划详情</span>
          {onModify && (
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => setIsEditing(!isEditing)}
              size="small"
            >
              {isEditing ? '取消编辑' : '编辑计划'}
            </Button>
          )}
        </Space>
      }
      extra={
        <Space>
          <Button
            type="primary"
            onClick={onApprove}
            loading={loading}
            disabled={isEditing}
          >
            批准计划
          </Button>
          <Button
            danger
            onClick={() => setShowRejectModal(true)}
            disabled={isEditing}
          >
            拒绝并修改
          </Button>
        </Space>
      }
    >
      {/* 研究目标 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={4}>🎯 研究目标</Title>
        {isEditing ? (
          <TextArea
            value={editedPlan.research_goal}
            onChange={(e) => setEditedPlan({ ...editedPlan, research_goal: e.target.value })}
            rows={3}
            placeholder="请输入研究目标..."
          />
        ) : (
          <Paragraph style={{ fontSize: '16px', lineHeight: '1.6' }}>
            {plan.research_goal}
          </Paragraph>
        )}
      </div>

      <Divider />

      {/* 计划信息 */}
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <div>
            <Text strong>预估迭代次数：</Text>
            {isEditing ? (
              <Input
                type="number"
                value={editedPlan.estimated_iterations}
                onChange={(e) => setEditedPlan({
                  ...editedPlan,
                  estimated_iterations: parseInt(e.target.value) || 1
                })}
                style={{ width: 80, marginLeft: 8 }}
                min={1}
                max={20}
              />
            ) : (
              <Tag color="blue">{plan.estimated_iterations} 次</Tag>
            )}
          </div>
          <div>
            <Text strong>完成标准：</Text>
            {isEditing ? (
              <TextArea
                value={editedPlan.completion_criteria}
                onChange={(e) => setEditedPlan({ ...editedPlan, completion_criteria: e.target.value })}
                rows={2}
                placeholder="请输入完成标准..."
                style={{ marginTop: 4 }}
              />
            ) : (
              <Paragraph style={{ marginTop: 4, color: '#666' }}>
                {plan.completion_criteria}
              </Paragraph>
            )}
          </div>
        </Space>
      </div>

      <Divider />

      {/* 子任务列表 */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4}>📋 具体研究任务</Title>
          {isEditing && (
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={handleAddSubTask}
              size="small"
            >
              添加任务
            </Button>
          )}
        </div>

        <List
          dataSource={isEditing ? editedPlan.sub_tasks : plan.sub_tasks}
          renderItem={(task: SubTask, index: number) => (
            <List.Item
              style={{
                padding: '16px',
                marginBottom: '12px',
                border: '1px solid #f0f0f0',
                borderRadius: '8px',
                background: '#fafafa'
              }}
              actions={
                isEditing ? [
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => handleRemoveSubTask(task.task_id)}
                    size="small"
                  />
                ] : []
              }
            >
              <div style={{ width: '100%' }}>
                {/* 任务标题和状态 */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Space>
                    <Text strong style={{ fontSize: '16px' }}>
                      任务 {task.task_id}:
                    </Text>
                    <Tag color={getStatusColor(task.status)}>{task.status}</Tag>
                    <Tag color="cyan">优先级 {task.priority}</Tag>
                  </Space>
                </div>

                {/* 任务描述 */}
                <div style={{ marginBottom: 12 }}>
                  {isEditing ? (
                    <TextArea
                      value={task.description}
                      onChange={(e) => handleUpdateSubTask(task.task_id, { description: e.target.value })}
                      rows={2}
                      placeholder="任务描述..."
                    />
                  ) : (
                    <Paragraph style={{ margin: 0, fontSize: '14px' }}>
                      {task.description}
                    </Paragraph>
                  )}
                </div>

                {/* 搜索查询 */}
                <div style={{ marginBottom: 8 }}>
                  <Text strong style={{ fontSize: '12px', color: '#666' }}>搜索查询：</Text>
                  {isEditing ? (
                    <Select
                      mode="tags"
                      value={task.search_queries}
                      onChange={(value) => handleUpdateSubTask(task.task_id, { search_queries: value })}
                      style={{ width: '100%', marginTop: 4 }}
                      placeholder="输入搜索查询..."
                    />
                  ) : (
                    <div style={{ marginTop: 4 }}>
                      {task.search_queries.map((query, idx) => (
                        <Tag key={idx} color="geekblue" style={{ marginBottom: 4 }}>
                          {query}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>

                {/* 数据源 */}
                <div>
                  <Text strong style={{ fontSize: '12px', color: '#666' }}>数据源：</Text>
                  {isEditing ? (
                    <Select
                      mode="multiple"
                      value={task.sources}
                      onChange={(value) => handleUpdateSubTask(task.task_id, { sources: value })}
                      style={{ width: '100%', marginTop: 4 }}
                    >
                      <Option value="tavily">Tavily搜索</Option>
                      <Option value="arxiv">ArXiv学术搜索</Option>
                      <Option value="mcp">MCP服务器</Option>
                    </Select>
                  ) : (
                    <div style={{ marginTop: 4 }}>
                      {task.sources.map((source, idx) => (
                        <Tag key={idx} color={getSourceColor(source)}>
                          {source}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </List.Item>
          )}
        />

        {isEditing && (
          <div style={{ textAlign: 'right', marginTop: 16 }}>
            <Space>
              <Button onClick={handleCancelEdit}>
                取消
              </Button>
              <Button type="primary" onClick={handleSavePlan}>
                保存修改
              </Button>
            </Space>
          </div>
        )}
      </div>

      {/* 拒绝理由弹窗 */}
      <Modal
        title="拒绝研究计划"
        open={showRejectModal}
        onOk={handleReject}
        onCancel={() => {
          setShowRejectModal(false);
          setRejectFeedback('');
        }}
        okText="确认拒绝"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text>请说明拒绝理由或修改建议（可选）：</Text>
        </div>
        <TextArea
          rows={4}
          value={rejectFeedback}
          onChange={(e) => setRejectFeedback(e.target.value)}
          placeholder="例如：需要添加更多关于XXX的搜索任务，或者调整任务优先级..."
        />
      </Modal>
    </Card>
  );
};
