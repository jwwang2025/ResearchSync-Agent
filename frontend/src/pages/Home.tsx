/**
 * Home Page Component
 *
 * 首页组件
 */

import React, { useState } from 'react';
import { Typography, Card, Divider } from 'antd';
import { ResearchFlow } from '../components/Research/ResearchFlow';
import { ResearchWSExample } from '../components/Research/ResearchWSExample';
import { ResearchPlanDisplay } from '../components/Research/ResearchPlanDisplay';
import { wsService } from '../services/websocket';
import type { ResearchPlan } from '../types/research';

const { Title } = Typography;

const Home: React.FC = () => {
  const [report, setReport] = useState<string | null>(null);
  const [reportFormat, setReportFormat] = useState<string>('markdown');
  const [taskStatus, setTaskStatus] = useState<{ taskId: string | null; isConnected: boolean; currentStep: string }>({
    taskId: null,
    isConnected: false,
    currentStep: ''
  });
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);
  const [planStep, setPlanStep] = useState<string>('');
  const [currentProgress, setCurrentProgress] = useState<any>(null);

  const handleReportGenerated = (generatedReport: string, format: string) => {
    setReport(generatedReport);
    setReportFormat(format);
  };

  const handleStatusChange = (status: { taskId: string | null; isConnected: boolean; currentStep: string }) => {
    setTaskStatus(status);
  };

  const handlePlanReady = (plan: ResearchPlan | null, currentStep: string) => {
    setResearchPlan(plan);
    setPlanStep(currentStep);
  };

  const handleProgressUpdate = (progress: any) => {
    setCurrentProgress(progress);
  };

  const handlePlanApprove = () => {
    // 通过WebSocket服务批准计划
    console.log('Attempting to approve plan...');
    console.log('WebSocket connected:', wsService.isConnected());
    console.log('Task status connected:', taskStatus.isConnected);

    if (wsService.isConnected() && taskStatus.isConnected) {
      try {
        wsService.approvePlan(true);
        console.log('Plan approved successfully');
      } catch (error) {
        console.error('Failed to approve plan:', error);
      }
    } else {
      console.error('WebSocket not connected - cannot approve plan');
      alert('WebSocket连接已断开，请重新开始研究任务');
    }
  };

  const handlePlanReject = (feedback?: string) => {
    // 通过WebSocket服务拒绝计划
    console.log('Attempting to reject plan...');
    console.log('WebSocket connected:', wsService.isConnected());
    console.log('Task status connected:', taskStatus.isConnected);

    if (wsService.isConnected() && taskStatus.isConnected) {
      try {
        wsService.approvePlan(false, feedback);
        console.log('Plan rejected with feedback:', feedback);
      } catch (error) {
        console.error('Failed to reject plan:', error);
      }
    } else {
      console.error('WebSocket not connected - cannot reject plan');
      alert('WebSocket连接已断开，请重新开始研究任务');
    }
  };

  const handlePlanModify = (modifiedPlan: ResearchPlan) => {
    // 通过WebSocket服务修改计划
    console.log('Attempting to modify plan...');
    console.log('WebSocket connected:', wsService.isConnected());
    console.log('Task status connected:', taskStatus.isConnected);

    if (wsService.isConnected() && taskStatus.isConnected) {
      try {
        wsService.modifyPlan(modifiedPlan);
        console.log('Plan modified:', modifiedPlan);
      } catch (error) {
        console.error('Failed to modify plan:', error);
      }
    } else {
      console.error('WebSocket not connected - cannot modify plan');
      alert('WebSocket连接已断开，请重新开始研究任务');
    }
  };

  return (
    <div>
      <div className="hero">
        <div className="hero-card">
          <div className="hero-title">用 AI 协同推进研究</div>
          <div className="hero-desc">快速创建研究任务、实时跟踪进度并生成结构化报告。支持多种 LLM 提供商和可配置工作流。</div>
          <div className="muted">提示：在表单中填写问题并开始研究，借助实时 WebSocket 获取进展。</div>
        </div>
        <Card className="hero-card main-card">
          <ResearchFlow onReportGenerated={handleReportGenerated} onStatusChange={handleStatusChange} onPlanReady={handlePlanReady} onProgressUpdate={handleProgressUpdate} />
        </Card>
      </div>

      {/* 研究计划审批界面 */}
      {researchPlan && planStep === 'awaiting_approval' && (
        <div className="section">
          <Title level={4} style={{ color: '#1890ff', marginBottom: '16px' }}>
            研究计划审批
          </Title>
          <ResearchPlanDisplay
            plan={researchPlan}
            onApprove={handlePlanApprove}
            onReject={handlePlanReject}
            onModify={handlePlanModify}
          />
        </div>
      )}

      {report && (
        <div className="section">
          <Title level={4} style={{ color: '#238e68', marginBottom: '16px' }}>
            生成的研究报告 ({reportFormat.toUpperCase()})
          </Title>
          <Card className="main-card">
            <div className="report-container">
              <pre className="report-content">
                {report}
              </pre>
            </div>
          </Card>
        </div>
      )}

      <Divider />

      {/* 配置信息和状态显示 - 始终显示 */}
      <div className="section">
        {/* 基础配置信息 */}
        <Card size="small" style={{
          background: '#f8f9fa',
          border: '1px solid #e0e0e0',
          marginBottom: '16px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '14px'
          }}>
            {taskStatus.taskId && (
              <span style={{ fontWeight: '500' }}>
                任务ID: {taskStatus.taskId}
              </span>
            )}
            <span style={{
              color: taskStatus.isConnected ? '#52c41a' : '#ff4d4f',
              fontWeight: '500'
            }}>
              {taskStatus.isConnected ? '● 已连接' : '● 未连接'}
            </span>
            <span style={{ color: '#666' }}>
              状态: {taskStatus.currentStep === 'planning' ? '规划中' :
                     taskStatus.currentStep === 'researching' ? '研究中' :
                     taskStatus.currentStep === 'synthesizing' ? '合成中' :
                     taskStatus.currentStep === 'completed' ? '已完成' :
                     taskStatus.currentStep === 'awaiting_approval' ? '等待审批' :
                     '准备中'}
            </span>
          </div>
        </Card>

        {/* 研究进度详情 - 仅在researching状态时显示 */}
        {currentProgress && taskStatus.currentStep === 'researching' && (
          <Card style={{
            background: 'linear-gradient(135deg, #f6ffed 0%, #b7eb8f 100%)',
            border: '2px solid #52c41a',
            marginBottom: '16px'
          }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              fontSize: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 'bold', color: '#52c41a' }}>📊 研究进度</span>
                <span style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  迭代 {currentProgress.iteration || 0}/{currentProgress.max_iterations || 3}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 'bold', color: '#52c41a' }}>🎯 当前任务</span>
                <span style={{ fontSize: '16px' }}>
                  {currentProgress.current_task || '正在分析研究内容...'}
                </span>
              </div>
            </div>
          </Card>
        )}
      </div>

      <div className="section">
        <Title level={4}>WebSocket 调试工具</Title>
        <ResearchWSExample />
      </div>
    </div>
  );
};

export default Home;
