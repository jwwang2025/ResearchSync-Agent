/**
 * Home Page Component
 *
 * 首页组件
 */

import React, { useState } from 'react';
import { Typography, Card, Divider } from 'antd';
import { ResearchFlow } from '../components/Research/ResearchFlow';
import { ResearchWSExample } from '../components/Research/ResearchWSExample';

const { Title } = Typography;

const Home: React.FC = () => {
  const [report, setReport] = useState<string | null>(null);
  const [reportFormat, setReportFormat] = useState<string>('markdown');

  const handleReportGenerated = (generatedReport: string, format: string) => {
    setReport(generatedReport);
    setReportFormat(format);
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
          <ResearchFlow onReportGenerated={handleReportGenerated} />
        </Card>
      </div>

      {report && (
        <div className="section">
          <Title level={4}>📄 生成的研究报告</Title>
          <Card>
            <div style={{
              maxHeight: '600px',
              overflow: 'auto',
              background: '#f9f9f9',
              padding: '16px',
              borderRadius: '8px'
            }}>
              <pre style={{
                whiteSpace: 'pre-wrap',
                margin: 0,
                fontFamily: 'monospace',
                fontSize: '14px',
                lineHeight: '1.5'
              }}>
                {report}
              </pre>
            </div>
          </Card>
        </div>
      )}

      <Divider />

      <div className="section">
        <Title level={4}>🔧 WebSocket 调试工具</Title>
        <ResearchWSExample />
      </div>
    </div>
  );
};

export default Home;
