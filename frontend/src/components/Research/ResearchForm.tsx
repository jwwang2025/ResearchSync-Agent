/**
 * ResearchForm Component
 * 
 * 研究任务提交表单组件
 */

import React, { useState } from 'react';
import { Form, Input, Button, Select, Switch, InputNumber, Space } from 'antd';
import type { ResearchRequest } from '../../types/research';

const { TextArea } = Input;

interface ResearchFormProps {
  onSubmit: (request: ResearchRequest) => void;
  loading?: boolean;
}

export const ResearchForm: React.FC<ResearchFormProps> = ({ onSubmit, loading = false }) => {
  const [form] = Form.useForm();
  const [llmProvider, setLlmProvider] = useState<string | undefined>();

  const handleSubmit = (values: any) => {
    const request: ResearchRequest = {
      query: values.query,
      max_iterations: values.max_iterations,
      auto_approve: values.auto_approve || false,
      llm_provider: values.llm_provider,
      llm_model: values.llm_model,
      output_format: values.output_format || 'markdown',
    };
    onSubmit(request);
  };

  const llmModels: Record<string, string[]> = {
    openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    claude: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'],
    gemini: ['gemini-pro', 'gemini-1.5-pro'],
    deepseek: ['deepseek-chat', 'deepseek-coder'],
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        max_iterations: 5,
        auto_approve: false,
        output_format: 'markdown',
      }}
    >
      <Form.Item
        name="query"
        label="研究问题"
        rules={[{ required: true, message: '请输入研究问题' }]}
      >
        <TextArea
          rows={4}
          placeholder="请输入您想要研究的问题或主题..."
        />
      </Form.Item>

      <Form.Item
        name="llm_provider"
        label="LLM 提供商"
      >
        <Select
          placeholder="选择 LLM 提供商（可选）"
          allowClear
          onChange={setLlmProvider}
        >
          <Select.Option value="openai">OpenAI</Select.Option>
          <Select.Option value="claude">Claude</Select.Option>
          <Select.Option value="gemini">Gemini</Select.Option>
          <Select.Option value="deepseek">DeepSeek</Select.Option>
        </Select>
      </Form.Item>

      {llmProvider && (
        <Form.Item
          name="llm_model"
          label="LLM 模型"
        >
          <Select placeholder="选择模型（可选）" allowClear>
            {llmModels[llmProvider]?.map((model) => (
              <Select.Option key={model} value={model}>
                {model}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      )}

      <Form.Item
        name="max_iterations"
        label="最大迭代次数"
      >
        <InputNumber min={1} max={20} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name="output_format"
        label="输出格式"
      >
        <Select>
          <Select.Option value="markdown">Markdown</Select.Option>
          <Select.Option value="html">HTML</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="auto_approve"
        valuePropName="checked"
      >
        <Switch checkedChildren="自动批准计划" unCheckedChildren="手动审批计划" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          开始研究
        </Button>
      </Form.Item>
    </Form>
  );
};

