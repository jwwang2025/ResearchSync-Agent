/**
 * App Component
 * 
 * 应用根组件
 */

import React from 'react';
import { Layout, Typography } from 'antd';
import { ResearchForm } from './components/Research/ResearchForm';
import { ResearchProgress } from './components/Research/ResearchProgress';
import { ResearchWSExample } from './components/Research/ResearchWSExample';
import { useWebSocket } from './hooks/useWebSocket';
import { researchApi } from './services/api';
import type { ResearchRequest, ProgressMessage, PlanReadyMessage, ReportReadyMessage } from './types/research';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  const [taskId, setTaskId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [progress, setProgress] = React.useState<ProgressMessage | null>(null);
  const [plan, setPlan] = React.useState<PlanReadyMessage | null>(null);
  const [report, setReport] = React.useState<string | null>(null);
  const [currentStep, setCurrentStep] = React.useState<string>('');

  const { connected, onMessage, approvePlan } = useWebSocket(taskId);

  // 注册 WebSocket 消息处理器
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
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px' }}>
        <Title level={3} style={{ color: '#fff', margin: '16px 0' }}>
          ResearchSync-Agent
        </Title>
      </Header>
      <Content style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        <ResearchForm onSubmit={handleSubmit} loading={loading} />

        {taskId && (
          <div style={{ marginTop: '24px' }}>
            <ResearchProgress progress={progress || undefined} step={currentStep} />

            {plan && (
              <div style={{ marginTop: '24px' }}>
                <h3>研究计划</h3>
                <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                  {JSON.stringify(plan.plan, null, 2)}
                </pre>
                <div style={{ marginTop: '16px' }}>
                  <button onClick={() => handleApprovePlan(true)}>批准</button>
                  <button onClick={() => handleApprovePlan(false, '请修改计划')} style={{ marginLeft: '8px' }}>
                    拒绝
                  </button>
                </div>
              </div>
            )}

            {report && (
              <div style={{ marginTop: '24px' }}>
                <h3>研究报告</h3>
                <div style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                  <pre style={{ whiteSpace: 'pre-wrap' }}>{report}</pre>
                </div>
              </div>
            )}
          </div>
        )}
        <div style={{ marginTop: 24 }}>
          <ResearchWSExample />
        </div>
      </Content>
    </Layout>
  );
}

export default App;