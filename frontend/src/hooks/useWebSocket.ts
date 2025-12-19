/**
 * useWebSocket Hook
 * 
 * 用于在 React 组件中使用 WebSocket
 */

import { useEffect, useRef, useState } from 'react';
import { wsService, type MessageHandler } from '../services/websocket';
import type { WebSocketMessage } from '../types/research';

export function useWebSocket(taskId: string | null) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const handlersRef = useRef<Map<string, MessageHandler>>(new Map());

  useEffect(() => {
    if (!taskId) {
      return;
    }

    let mounted = true;

    // 连接 WebSocket
    wsService
      .connect(taskId)
      .then(() => {
        if (mounted) {
          setConnected(true);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err);
          setConnected(false);
        }
      });

    // 清理函数
    return () => {
      mounted = false;
      // 移除所有注册的处理器
      handlersRef.current.forEach((handler, messageType) => {
        wsService.off(messageType, handler);
      });
      handlersRef.current.clear();
      wsService.disconnect();
      setConnected(false);
    };
  }, [taskId]);

  /**
   * 注册消息处理器
   */
  const onMessage = (messageType: string, handler: MessageHandler) => {
    if (!handlersRef.current.has(messageType)) {
      wsService.on(messageType, handler);
      handlersRef.current.set(messageType, handler);
    }
  };

  /**
   * 发送消息
   */
  const send = (message: Record<string, any>) => {
    wsService.send(message);
  };

  /**
   * 审批计划
   */
  const approvePlan = (approved: boolean, feedback?: string) => {
    wsService.approvePlan(approved, feedback);
  };

  return {
    connected,
    error,
    onMessage,
    send,
    approvePlan,
  };
}

