/**
 * ResearchFlow Component
 *
 * 研究流程管理组件，集成表单提交、进度显示和计划审批
 */

import React, { useState, useEffect } from 'react';
import { message, Alert } from 'antd';
import { ResearchForm } from './ResearchForm';
import { ResearchProgress } from './ResearchProgress';
import { ResearchPlanDisplay } from './ResearchPlanDisplay';
import { wsService } from '../../services/websocket';
import type { ResearchRequest, ResearchPlan, WebSocketMessage, PlanReadyMessage, PlanUpdatedMessage, ProgressMessage, ReportReadyMessage } from '../../types/research';

interface ResearchFlowProps {
  onReportGenerated?: (report: string, format: string) => void;
  onStatusChange?: (status: { taskId: string | null; isConnected: boolean; currentStep: string }) => void;
  onPlanReady?: (plan: ResearchPlan | null, currentStep: string) => void;
  onProgressUpdate?: (progress: any) => void;
}

export const ResearchFlow: React.FC<ResearchFlowProps> = ({ onReportGenerated, onStatusChange, onPlanReady, onProgressUpdate }) => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');

  // 通知父组件状态变化
  React.useEffect(() => {
    onStatusChange?.({ taskId, isConnected, currentStep });
  }, [taskId, isConnected, currentStep, onStatusChange]);
  const [progress, setProgress] = useState<ProgressMessage | null>(null);
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket消息处理器
  useEffect(() => {
    const handleMessage = (msg: WebSocketMessage) => {
      console.log('Received message:', msg);

      switch (msg.type) {
        case 'status_update':
          setCurrentStep(msg.step);
          break;

        case 'plan_ready':
          const planMsg = msg as PlanReadyMessage;
          setResearchPlan(planMsg.plan);
          setCurrentStep('awaiting_approval');
          setProgress(null);
          message.info('研究计划已生成，请审批');
          onPlanReady?.(planMsg.plan, 'awaiting_approval');
          break;

        case 'plan_updated':
          const updatedMsg = msg as PlanUpdatedMessage;
          setResearchPlan(updatedMsg.plan);
          message.success('研究计划已更新');
          onPlanReady?.(updatedMsg.plan, currentStep);
          break;

        case 'progress':
          const progressMsg = msg as ProgressMessage;
          setProgress(progressMsg);
          setCurrentStep(progressMsg.step);
          setResearchPlan(null); // 研究开始后隐藏计划
          onPlanReady?.(null, progressMsg.step);
          onProgressUpdate?.(progressMsg);
          break;

        case 'report_ready':
          const reportMsg = msg as ReportReadyMessage;
          setCurrentStep('completed');
          setProgress(null);
          setResearchPlan(null);
          message.success('研究报告已生成');
          onPlanReady?.(null, 'completed');

          if (onReportGenerated) {
            onReportGenerated(reportMsg.report, reportMsg.format);
          }
          break;

        case 'error':
          setError(msg.message);
          setLoading(false);
          message.error(`错误: ${msg.message}`);
          break;

        case 'approval_received':
          message.success(msg.approved ? '计划已批准' : '计划已拒绝');
          break;

        default:
          break;
      }
    };

    wsService.on('*', handleMessage);

    return () => {
      wsService.off('*', handleMessage);
    };
  }, [onReportGenerated]);

  // 处理研究请求提交
  const handleResearchSubmit = async (request: ResearchRequest) => {
    try {
      setLoading(true);
      setError(null);
      setResearchPlan(null);
      setProgress(null);

      // 提交研究请求到后端API
      const response = await fetch('/api/v1/research/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      const newTaskId = result.task_id;

      // 连接WebSocket
      await wsService.connect(newTaskId);
      setTaskId(newTaskId);
      setIsConnected(true);
      setCurrentStep('planning');

      message.success('研究任务已启动');

    } catch (err) {
      console.error('Failed to start research:', err);
      setError(err instanceof Error ? err.message : '启动研究失败');
      setLoading(false);
    }
  };

  // 处理计划批准
  const handlePlanApprove = () => {
    if (wsService.isConnected()) {
      wsService.approvePlan(true);
      setLoading(true);
    }
  };

  // 处理计划拒绝
  const handlePlanReject = (feedback?: string) => {
    if (wsService.isConnected()) {
      wsService.approvePlan(false, feedback);
      setLoading(true);
    }
  };

  // 处理计划修改
  const handlePlanModify = (modifiedPlan: ResearchPlan) => {
    if (wsService.isConnected()) {
      wsService.modifyPlan(modifiedPlan);
    }
  };

  // 渲染当前状态
  const renderCurrentState = () => {
    // 如果有错误，显示错误信息
    if (error) {
      return (
        <Alert
          message="研究出错"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
        />
      );
    }

    // 如果正在等待计划审批，显示计划详情
    // 注意：现在研究计划在父组件中显示，这里只显示表单
    // if (researchPlan && currentStep === 'awaiting_approval') {
    //   return (
    //     <ResearchPlanDisplay
    //       plan={researchPlan}
    //       onApprove={handlePlanApprove}
    //       onReject={handlePlanReject}
    //       onModify={handlePlanModify}
    //       loading={loading}
    //     />
    //   );
    // }

    // 如果有进度信息且正在进行研究任务，显示进度
    if (progress && (currentStep === 'researching' || currentStep === 'synthesizing' || currentStep === 'completed')) {
      return (
        <ResearchProgress
          progress={progress || undefined}
          step={currentStep}
        />
      );
    }

    // 默认显示表单，任务状态在表单上方显示
    return (
      <ResearchForm
        onSubmit={handleResearchSubmit}
        loading={loading}
        disabled={!!taskId} // 任务进行中时禁用表单
      />
    );
  };

  return (
    <div style={{ width: '100%' }}>
      {/* 主内容区域 */}
      {renderCurrentState()}
    </div>
  );
};
