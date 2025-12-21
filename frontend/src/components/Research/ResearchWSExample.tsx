import React, { useState, useEffect } from 'react';
import { wsService } from '../../services/websocket';

export const ResearchWSExample: React.FC = () => {
  const [taskId, setTaskId] = useState<string>('');
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);

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
    setMessages((prev) => [...prev, { type: 'sent_approval', approved }]);
  };

  return (
    <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 6 }}>
      <h4>WebSocket 调试示例</h4>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
          placeholder="输入 taskId"
          style={{ flex: 1 }}
        />
        {!connected ? (
          <button onClick={handleConnect}>连接</button>
        ) : (
          <button onClick={handleDisconnect}>断开</button>
        )}
      </div>

      <div style={{ marginBottom: 8 }}>
        <button onClick={() => handleApprove(true)} disabled={!connected}>
          批准计划
        </button>
        <button onClick={() => handleApprove(false)} disabled={!connected} style={{ marginLeft: 8 }}>
          拒绝计划
        </button>
      </div>

      <div style={{ maxHeight: 300, overflowY: 'auto', background: '#fafafa', padding: 8 }}>
        {messages.length === 0 ? (
          <div style={{ color: '#999' }}>暂无消息</div>
        ) : (
          messages.map((m, i) => (
            <pre key={i} style={{ margin: 4, background: '#fff', padding: 8, borderRadius: 4 }}>
              {JSON.stringify(m, null, 2)}
            </pre>
          ))
        )}
      </div>
    </div>
  );
};

export default ResearchWSExample;


