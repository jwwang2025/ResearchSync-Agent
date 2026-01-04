import React, { useState, useEffect } from 'react';
import {
  Upload,
  Button,
  Table,
  message,
  Input,
  Space,
  Card,
  Progress,
  Tag,
  Modal,
  Form,
  Select,
  Spin
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlusOutlined,
  SearchOutlined,
  FileTextOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps } from 'antd';

const { TextArea } = Input;
const { Option } = Select;

interface KnowledgeStats {
  collection_name: string;
  document_count: number;
  exists: boolean;
}

interface UploadResult {
  success: boolean;
  chunks_loaded?: number;
  error?: string;
}

interface RAGQueryResult {
  status: string;
  response: string;
  context_used: boolean;
  retrieved_count: number;
  sources?: Array<{
    content: string;
    score: number;
    metadata: any;
  }>;
}

const KnowledgeBase: React.FC = () => {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [querying, setQuerying] = useState(false);
  const [url, setUrl] = useState('');
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState<RAGQueryResult | null>(null);
  const [isQueryModalVisible, setIsQueryModalVisible] = useState(false);
  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/rag/knowledge/stats');
      const data = await response.json();
      setStats(data.stats);
    } catch (error) {
      message.error('获取知识库统计信息失败');
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleUrlUpload = async () => {
    if (!url.trim()) {
      message.error('请输入有效的URL');
      return;
    }

    setUploading(true);
    try {
      const response = await fetch('/api/v1/rag/knowledge/upload-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await response.json();
      if (data.status === 'success') {
        message.success(data.message);
        fetchStats();
        setUrl('');
        setIsUploadModalVisible(false);
      } else {
        message.error(data.error || '上传失败');
      }
    } catch (error) {
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) {
      message.error('请输入查询内容');
      return;
    }

    setQuerying(true);
    try {
      const response = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          include_sources: true
        }),
      });

      const data = await response.json();
      if (data.status === 'success') {
        setQueryResult(data);
        message.success('查询完成');
      } else {
        message.error('查询失败');
      }
    } catch (error) {
      message.error('查询失败');
    } finally {
      setQuerying(false);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/v1/rag/knowledge/upload-file',
    onChange(info) {
      if (info.file.status === 'uploading') {
        setUploading(true);
      } else if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`);
        fetchStats();
        setUploading(false);
        setIsUploadModalVisible(false);
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 上传失败`);
        setUploading(false);
      }
    },
    beforeUpload: (file) => {
      const isValidType = ['.txt', '.pdf', '.md', '.html', '.htm'].some(ext =>
        file.name.toLowerCase().endsWith(ext)
      );
      if (!isValidType) {
        message.error('只支持 txt, pdf, md, html 文件');
        return false;
      }
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB');
        return false;
      }
      return true;
    },
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ marginBottom: '8px' }}>RAG 知识库管理</h1>
        <p style={{ color: '#666', marginBottom: '16px' }}>
          管理和查询本地知识库，支持文档上传、URL导入和智能问答
        </p>
      </div>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 知识库统计 */}
        <Card
          title={
            <Space>
              <FileTextOutlined />
              知识库统计
            </Space>
          }
          extra={
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchStats}
              loading={loading}
            >
              刷新
            </Button>
          }
        >
          {stats ? (
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                  {stats.document_count}
                </div>
                <div style={{ color: '#666' }}>文档块数量</div>
              </div>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {stats.collection_name}
                </div>
                <div style={{ color: '#666' }}>集合名称</div>
              </div>
              <div>
                <Tag color={stats.exists ? 'green' : 'red'}>
                  {stats.exists ? '正常' : '未创建'}
                </Tag>
                <div style={{ color: '#666', marginTop: '4px' }}>状态</div>
              </div>
            </div>
          ) : (
            <Spin tip="加载中..." />
          )}
        </Card>

        {/* 操作按钮 */}
        <Card title="操作">
          <Space wrap>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsUploadModalVisible(true)}
            >
              添加文档
            </Button>
            <Button
              icon={<GlobalOutlined />}
              onClick={() => setIsQueryModalVisible(true)}
            >
              智能查询
            </Button>
          </Space>
        </Card>

        {/* 查询结果显示 */}
        {queryResult && (
          <Card
            title={
              <Space>
                <SearchOutlined />
                查询结果
              </Space>
            }
            extra={
              <Button
                size="small"
                onClick={() => setQueryResult(null)}
              >
                清除
              </Button>
            }
          >
            <div style={{ marginBottom: '16px' }}>
              <Tag color={queryResult.context_used ? 'green' : 'orange'}>
                {queryResult.context_used ? '使用知识库上下文' : '未找到相关上下文'}
              </Tag>
              <span style={{ marginLeft: '8px', color: '#666' }}>
                检索到 {queryResult.retrieved_count} 个相关文档
              </span>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <h4>回答：</h4>
              <div style={{
                padding: '12px',
                backgroundColor: '#f9f9f9',
                borderRadius: '4px',
                whiteSpace: 'pre-wrap'
              }}>
                {queryResult.response}
              </div>
            </div>

            {queryResult.sources && queryResult.sources.length > 0 && (
              <div>
                <h4>参考来源：</h4>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {queryResult.sources.map((source, index) => (
                    <Card
                      key={index}
                      size="small"
                      style={{ backgroundColor: '#fafafa' }}
                    >
                      <div style={{ marginBottom: '8px' }}>
                        <Tag color="blue">相关度: {(source.score * 100).toFixed(1)}%</Tag>
                      </div>
                      <div style={{ fontSize: '14px', color: '#666' }}>
                        {source.content}
                      </div>
                      {source.metadata?.source && (
                        <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
                          来源: {source.metadata.source}
                        </div>
                      )}
                    </Card>
                  ))}
                </Space>
              </div>
            )}
          </Card>
        )}
      </Space>

      {/* URL上传模态框 */}
      <Modal
        title={
          <Space>
            <GlobalOutlined />
            从URL添加文档
          </Space>
        }
        open={isUploadModalVisible}
        onOk={handleUrlUpload}
        onCancel={() => {
          setIsUploadModalVisible(false);
          setUrl('');
        }}
        confirmLoading={uploading}
        okText="添加"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input
            placeholder="输入文档URL (例如: https://example.com/article.html)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onPressEnter={handleUrlUpload}
          />
          <div style={{ fontSize: '12px', color: '#666' }}>
            支持的格式: HTML网页、博客文章等可访问的在线文档
          </div>
        </Space>
      </Modal>

      {/* 智能查询模态框 */}
      <Modal
        title={
          <Space>
            <SearchOutlined />
            RAG智能查询
          </Space>
        }
        open={isQueryModalVisible}
        onOk={handleQuery}
        onCancel={() => {
          setIsQueryModalVisible(false);
          setQuery('');
        }}
        confirmLoading={querying}
        okText="查询"
        cancelText="取消"
        width={800}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <TextArea
            placeholder="输入您的问题，系统将基于知识库内容进行智能回答..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
            maxLength={1000}
            showCount
          />
          <div style={{ fontSize: '12px', color: '#666' }}>
            基于您上传的文档内容进行检索和回答。如果知识库中没有相关信息，系统会说明无法完全回答。
          </div>
        </Space>
      </Modal>
    </div>
  );
};

export default KnowledgeBase;
