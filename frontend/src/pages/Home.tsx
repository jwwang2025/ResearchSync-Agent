/**
 * Home Page Component
 *
 * 首页组件
 */

import React from 'react';
import { Typography, Card, Button } from 'antd';
import { ResearchForm } from '../components/Research/ResearchForm';
import { ResearchProgress } from '../components/Research/ResearchProgress';
import { ResearchWSExample } from '../components/Research/ResearchWSExample';
import { useWebSocket } from '../hooks/useWebSocket';
import { researchApi } from '../services/api';
import type { ResearchRequest, ProgressMessage, PlanReadyMessage, ReportReadyMessage } from '../types/research';

const { Title } = Typography;

const Home: React.FC = () => {
  const [taskId, setTaskId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [progress, setProgress] = React.useState<ProgressMessage | null>(null);
  const [plan, setPlan] = React.useState<PlanReadyMessage | null>(null);
  const [report, setReport] = React.useState<string | null>(null);
  const [currentStep, setCurrentStep] = React.useState<string>('');

  const { connected, onMessage, approvePlan } = useWebSocket(taskId);

  React.useEffect(() => {
    if (!connected) return;

    onMessage('status_update', (message) => {
      setCurrentStep(message.step || '');
    });

    onMessage('progress', (message) => {
      setProgress(message as ProgressMessage);
      setCurrentStep(message.step || '');
    });

    onMessage('plan_ready', (message) => {
      setPlan(message as PlanReadyMessage);
      setCurrentStep('awaiting_approval');
    });

    onMessage('report_ready', (message) => {
      const reportMessage = message as ReportReadyMessage;
      setReport(reportMessage.report);
      setCurrentStep('completed');
    });

    onMessage('error', (message) => {
      console.error('研究错误:', message);
      alert(`研究过程中出错: ${message.message}`);
    });
  }, [connected, onMessage]);

  const handleSubmit = async (request: ResearchRequest) => {
    try {
      setLoading(true);
      setProgress(null);
      setPlan(null);
      setReport(null);
      setCurrentStep('');

      const response = await researchApi.startResearch(request);
      setTaskId(response.task_id);
    } catch (error) {
      console.error('启动研究失败:', error);
      alert('启动研究失败，请检查后端服务是否运行');
    } finally {
      setLoading(false);
    }
  };

  const handleApprovePlan = (approved: boolean, feedback?: string) => {
    approvePlan(approved, feedback);
    if (approved) {
      setPlan(null);
      setCurrentStep('researching');
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
          <ResearchForm onSubmit={handleSubmit} loading={loading} />
        </Card>
      </div>

      {taskId && (
        <div className="section">
          <ResearchProgress progress={progress || undefined} step={currentStep} />

          {plan && (
            <div className="section">
              <Title level={5}>研究计划</Title>
              <pre className="plan-pre">{JSON.stringify(plan.plan, null, 2)}</pre>
              <div style={{ marginTop: 12 }}>
                <Button type="primary" onClick={() => handleApprovePlan(true)}>批准</Button>
                <Button style={{ marginLeft: 8 }} onClick={() => handleApprovePlan(false, '请修改计划')}>拒绝</Button>
              </div>
            </div>
          )}

          {report && (
            <div className="section">
              <Title level={5}>研究报告</Title>
              <div className="plan-pre">
                <pre style={{ whiteSpace: 'pre-wrap', margin:0 }}>{report}</pre>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="section">
        <ResearchWSExample />
      </div>
    </div>
  );
};

export default Home;
