/**
 * ResearchProgress Component
 * 
 * 研究进度显示组件
 */

import React from 'react';
import { Card, Progress, Typography, Tag, Space } from 'antd';
import type { ProgressMessage } from '../../types/research';

const { Text, Title } = Typography;

interface ResearchProgressProps {
  progress?: ProgressMessage;
  step?: string;
}

export const ResearchProgress: React.FC<ResearchProgressProps> = ({ progress, step }) => {
  if (!progress && !step) {
    return null;
  }

  const iteration = progress?.iteration || 0;
  const maxIterations = progress?.max_iterations || 5;
  const currentTask = progress?.current_task || '';
  const currentStep = progress?.step || step || '';

  const stepLabels: Record<string, string> = {
    planning: '正在创建研究计划...',
    awaiting_approval: '等待审批研究计划',
    researching: '正在执行研究...',
    generating_report: '正在生成报告...',
    completed: '研究完成',
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Title level={5}>当前步骤</Title>
          <Tag color="blue">{stepLabels[currentStep] || currentStep}</Tag>
        </div>

        {progress && (
          <>
            <div>
              <Title level={5}>研究进度</Title>
              <Progress
                percent={Math.round((iteration / maxIterations) * 100)}
                status="active"
                format={(percent) => `迭代 ${iteration}/${maxIterations}`}
              />
            </div>

            {currentTask && (
              <div>
                <Title level={5}>当前任务</Title>
                <Text>{currentTask}</Text>
              </div>
            )}
          </>
        )}
      </Space>
    </Card>
  );
};

