import React, { useState, useEffect } from 'react';
import { wsService } from '../../services/websocket';

type MessageType = 'all' | 'status_update' | 'plan_ready' | 'progress' | 'report_ready' | 'error' | 'approval_received';

export const ResearchWSExample: React.FC = () => {
  const [taskId, setTaskId] = useState<string>('');
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [filterType, setFilterType] = useState<MessageType>('all');
  const [showRawData, setShowRawData] = useState(false);

  useEffect(() => {
    // 通用消息处理器
    const handler = (msg: any) => {
      setMessages((prev) => [...prev, msg]);
    };

    wsService.on('*', handler);
    return () => {
      wsService.off('*', handler);
      wsService.disconnect();
    };
  }, []);

  const handleConnect = async () => {
    if (!taskId) return alert('请输入 taskId');
    try {
      await wsService.connect(taskId);
      setConnected(true);
      setMessages([]);
    } catch (e) {
      alert('连接失败，请检查后端或 taskId 是否正确');
      setConnected(false);
    }
  };

  const handleDisconnect = () => {
    wsService.disconnect();
    setConnected(false);
  };

  const handleApprove = (approved: boolean) => {
    wsService.approvePlan(approved, approved ? undefined : '请修改计划');
    setMessages((prev) => [...prev, { type: 'sent_approval', approved, timestamp: new Date().toLocaleTimeString() }]);
  };

  // 格式化消息显示
  const formatMessage = (msg: any) => {
    const timestamp = new Date().toLocaleTimeString();

    switch (msg.type) {
      case 'status_update':
        return {
          time: timestamp,
          type: '状态更新',
          content: msg.message,
          details: `步骤: ${msg.step}`,
          color: '#2196F3'
        };

      case 'plan_ready':
        return {
          time: timestamp,
          type: '计划就绪',
          content: msg.message,
          details: `研究目标: ${msg.plan?.research_goal || 'N/A'}`,
          subTasks: msg.plan?.sub_tasks?.length || 0,
          color: '#4CAF50'
        };

      case 'progress':
        return {
          time: timestamp,
          type: '研究进度',
          content: msg.current_task || '正在执行任务...',
          details: `迭代 ${msg.iteration}/${msg.max_iterations} - ${msg.step}`,
          color: '#FF9800'
        };

      case 'report_ready':
        return {
          time: timestamp,
          type: '报告完成',
          content: '最终报告已生成',
          details: `格式: ${msg.format}`,
          reportLength: msg.report?.length || 0,
          color: '#9C27B0'
        };

      case 'error':
        return {
          time: timestamp,
          type: '错误',
          content: msg.message,
          details: msg.debug ? '包含调试信息' : '',
          color: '#F44336'
        };

      case 'approval_received':
        return {
          time: timestamp,
          type: '审批确认',
          content: msg.approved ? '计划已批准' : '计划已拒绝',
          details: `任务ID: ${msg.task_id}`,
          color: '#607D8B'
        };

      case 'sent_approval':
        return {
          time: timestamp,
          type: '发送审批',
          content: msg.approved ? '已批准计划' : '已拒绝计划',
          details: '',
          color: '#795548'
        };

      default:
        return {
          time: timestamp,
          type: msg.type || '未知',
          content: '未知消息类型',
          details: '',
          color: '#9E9E9E'
        };
    }
  };

  // 过滤消息
  const filteredMessages = messages.filter(msg => {
    if (filterType === 'all') return true;
    return msg.type === filterType;
  });

  return (
    <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 6, fontFamily: 'Arial, sans-serif' }}>
      <h4 style={{ margin: '0 0 12px 0' }}>WebSocket 调试示例</h4>

      {/* 连接控制 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
          placeholder="输入 taskId"
          style={{ flex: 1, padding: '6px 8px', border: '1px solid #ccc', borderRadius: 4 }}
        />
        {!connected ? (
          <button
            onClick={handleConnect}
            style={{ padding: '6px 12px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
          >
            连接
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            style={{ padding: '6px 12px', background: '#F44336', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
          >
            断开
          </button>
        )}
      </div>

      {/* 审批控制 */}
      <div style={{ marginBottom: 12 }}>
        <button
          onClick={() => handleApprove(true)}
          disabled={!connected}
          style={{
            padding: '6px 12px',
            background: connected ? '#2196F3' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: connected ? 'pointer' : 'not-allowed',
            marginRight: 8
          }}
        >
          批准计划
        </button>
        <button
          onClick={() => handleApprove(false)}
          disabled={!connected}
          style={{
            padding: '6px 12px',
            background: connected ? '#FF9800' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: connected ? 'pointer' : 'not-allowed'
          }}
        >
          拒绝计划
        </button>
      </div>

      {/* 过滤器控制 */}
      <div style={{ marginBottom: 12, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <label style={{ fontSize: '14px', fontWeight: 'bold' }}>过滤消息类型:</label>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as MessageType)}
          style={{ padding: '4px 8px', border: '1px solid #ccc', borderRadius: 4 }}
        >
          <option value="all">全部消息</option>
          <option value="status_update">状态更新</option>
          <option value="plan_ready">计划就绪</option>
          <option value="progress">研究进度</option>
          <option value="report_ready">报告完成</option>
          <option value="error">错误消息</option>
          <option value="approval_received">审批确认</option>
        </select>

        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '14px' }}>
          <input
            type="checkbox"
            checked={showRawData}
            onChange={(e) => setShowRawData(e.target.checked)}
          />
          显示原始数据
        </label>

        <button
          onClick={() => setMessages([])}
          style={{ padding: '4px 8px', background: '#9E9E9E', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '12px' }}
        >
          清空消息
        </button>
      </div>

      {/* 消息显示区域 */}
      <div style={{
        maxHeight: 400,
        overflowY: 'auto',
        background: '#fafafa',
        padding: 8,
        borderRadius: 4,
        border: '1px solid #e0e0e0'
      }}>
        {filteredMessages.length === 0 ? (
          <div style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
            {messages.length === 0 ? '暂无消息' : '没有匹配的消息'}
          </div>
        ) : (
          filteredMessages.map((m, i) => {
            const formatted = formatMessage(m);
            return (
              <div key={i} style={{
                margin: '6px 0',
                padding: '10px',
                background: 'white',
                borderRadius: 6,
                border: `2px solid ${formatted.color}`,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{
                    fontSize: '12px',
                    color: formatted.color,
                    fontWeight: 'bold',
                    background: `${formatted.color}20`,
                    padding: '2px 6px',
                    borderRadius: 3
                  }}>
                    {formatted.type}
                  </span>
                  <span style={{ fontSize: '11px', color: '#666' }}>
                    {formatted.time}
                  </span>
                </div>

                <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: 2 }}>
                  {formatted.content}
                </div>

                {formatted.details && (
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: 2 }}>
                    {formatted.details}
                  </div>
                )}

                {/* 额外信息 */}
                {formatted.subTasks !== undefined && (
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    子任务数量: {formatted.subTasks}
                  </div>
                )}

                {formatted.reportLength !== undefined && (
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    报告长度: {formatted.reportLength} 字符
                  </div>
                )}

                {/* 原始数据 */}
                {showRawData && (
                  <details style={{ marginTop: 8 }}>
                    <summary style={{ fontSize: '12px', color: '#666', cursor: 'pointer' }}>
                      原始数据
                    </summary>
                    <pre style={{
                      fontSize: '11px',
                      background: '#f5f5f5',
                      padding: '6px',
                      borderRadius: 3,
                      marginTop: 4,
                      overflow: 'auto',
                      maxHeight: '200px'
                    }}>
                      {JSON.stringify(m, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 消息统计 */}
      <div style={{ marginTop: 8, fontSize: '12px', color: '#666', textAlign: 'right' }}>
        显示 {filteredMessages.length} / 总共 {messages.length} 条消息
      </div>
    </div>
  );
};

export default ResearchWSExample;


