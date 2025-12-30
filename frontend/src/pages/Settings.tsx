/**
 * Settings Page Component
 *
 * 设置页面组件
 */

import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Select, InputNumber, Switch, Button, Typography, message, Spin, Divider } from 'antd';
import { configApi } from '../services/api';

const { Title, Text } = Typography;

interface ConfigData {
  llm: {
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
  };
  search: {
    tavily_configured: boolean;
    mcp_configured: boolean;
  };
  workflow: {
    max_iterations: number;
    auto_approve_plan: boolean;
    output_dir: string;
  };
}

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<ConfigData | null>(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await configApi.getConfig();
      setConfig(response);
      form.setFieldsValue({
        llm_provider: response.llm.provider,
        llm_model: response.llm.model,
        llm_temperature: response.llm.temperature,
        llm_max_tokens: response.llm.max_tokens,
        max_iterations: response.workflow.max_iterations,
        auto_approve_plan: response.workflow.auto_approve_plan,
        output_dir: response.workflow.output_dir,
      });
    } catch (error) {
      console.error('获取配置失败:', error);
      message.error('获取配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values: any) => {
    try {
      setSaving(true);
      await configApi.updateConfig({
        llm: {
          provider: values.llm_provider,
          model: values.llm_model,
          temperature: values.llm_temperature,
          max_tokens: values.llm_max_tokens,
        },
        workflow: {
          max_iterations: values.max_iterations,
          auto_approve_plan: values.auto_approve_plan,
          output_dir: values.output_dir,
        },
      });
      message.success('配置已保存');
      fetchConfig(); // 重新获取配置
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('保存配置失败');
    } finally {
      setSaving(false);
    }
  };

  const llmModels: Record<string, string[]> = {
    openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    claude: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229'],
    gemini: ['gemini-pro', 'gemini-pro-vision', 'gemini-ultra'],
    deepseek: ['deepseek-chat', 'deepseek-coder'],
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
        <Title level={3}>系统设置</Title>
        <Text type="secondary">配置LLM、搜索和工作流参数</Text>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            max_iterations: 5,
            auto_approve_plan: false,
          }}
        >
          <Divider orientation="left">LLM 配置</Divider>

          <Form.Item
            name="llm_provider"
            label="LLM 提供商"
          >
            <Select placeholder="选择 LLM 提供商">
              <Select.Option value="openai">OpenAI</Select.Option>
              <Select.Option value="claude">Claude</Select.Option>
              <Select.Option value="gemini">Gemini</Select.Option>
              <Select.Option value="deepseek">DeepSeek</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="llm_model"
            label="LLM 模型"
          >
            <Select placeholder="选择模型">
              {form.getFieldValue('llm_provider') && llmModels[form.getFieldValue('llm_provider')]?.map((model) => (
                <Select.Option key={model} value={model}>
                  {model}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="llm_temperature"
            label="温度 (Temperature)"
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="llm_max_tokens"
            label="最大 Token 数"
          >
            <InputNumber min={1} max={32768} style={{ width: '100%' }} />
          </Form.Item>

          <Divider orientation="left">工作流配置</Divider>

          <Form.Item
            name="max_iterations"
            label="最大迭代次数"
          >
            <InputNumber min={1} max={20} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="auto_approve_plan"
            valuePropName="checked"
          >
            <Switch checkedChildren="自动批准计划" unCheckedChildren="手动审批计划" />
          </Form.Item>

          <Form.Item
            name="output_dir"
            label="输出目录"
          >
            <Input placeholder="输出文件保存目录" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={saving} block>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {config && (
        <Card style={{ marginTop: 16 }}>
          <Divider orientation="left">服务状态</Divider>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <Text strong>Tavily 搜索:</Text>{' '}
              <Text type={config.search.tavily_configured ? 'success' : 'danger'}>
                {config.search.tavily_configured ? '已配置' : '未配置'}
              </Text>
            </div>
            <div>
              <Text strong>MCP 服务:</Text>{' '}
              <Text type={config.search.mcp_configured ? 'success' : 'danger'}>
                {config.search.mcp_configured ? '已配置' : '未配置'}
              </Text>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Settings;
