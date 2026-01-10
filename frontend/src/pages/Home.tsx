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

  const handlePlanApprove = () => {
    // 这里需要通过某种方式调用WebSocket服务的审批方法
    // 由于WebSocket服务是内部的，我们需要在ResearchFlow中处理
    console.log('Plan approved');
  };

  const handlePlanReject = (feedback?: string) => {
    console.log('Plan rejected with feedback:', feedback);
  };

  const handlePlanModify = (modifiedPlan: ResearchPlan) => {
    console.log('Plan modified:', modifiedPlan);
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
          <ResearchFlow onReportGenerated={handleReportGenerated} onStatusChange={handleStatusChange} onPlanReady={handlePlanReady} />
        </Card>
      </div>

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

      {/* 状态指示器 */}
      {taskStatus.taskId && (
        <div className="section">
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
              <span style={{ fontWeight: '500' }}>
                任务ID: {taskStatus.taskId}
              </span>
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
        </div>
      )}

      <div className="section">
        <Title level={4}>WebSocket 调试工具</Title>
        <ResearchWSExample />
      </div>
    </div>
  );
};

export default Home;
