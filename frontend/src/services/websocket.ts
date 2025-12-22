/**
 * WebSocket Service
 * 
 * WebSocket 客户端服务，用于实时通信
 */

import type {
  WebSocketMessage,
  StatusUpdateMessage,
  PlanReadyMessage,
  ProgressMessage,
  ReportReadyMessage,
  ErrorMessage,
} from '../types/research';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private taskId: string | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  /**
   * 连接到研究任务的 WebSocket
   */
  connect(taskId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        if (this.taskId === taskId) {
          resolve();
          return;
        }
        this.disconnect();
      }

      this.taskId = taskId;
      const wsUrl = `${WS_BASE_URL}/ws/research/${taskId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket 连接已建立');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket 连接已关闭');
        this.attemptReconnect();
      };
    });
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.taskId = null;
  }

  /**
   * 发送消息
   */
  send(message: Record<string, any>) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket 未连接，无法发送消息');
    }
  }

  /**
   * 审批研究计划
   */
  approvePlan(approved: boolean, feedback?: string) {
    this.send({
      type: 'approve_plan',
      task_id: this.taskId,
      approved,
      feedback,
    });
  }

  /**
   * 注册消息处理器
   */
  on(messageType: string, handler: MessageHandler) {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, []);
    }
    this.handlers.get(messageType)!.push(handler);
  }

  /**
   * 移除消息处理器
   */
  off(messageType: string, handler: MessageHandler) {
    const handlers = this.handlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage) {
    const handlers = this.handlers.get(message.type) || [];
    handlers.forEach((handler) => handler(message));

    // 也触发通用处理器
    const allHandlers = this.handlers.get('*') || [];
    allHandlers.forEach((handler) => handler(message));
  }

  /**
   * 尝试重连
   */
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.taskId) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.connect(this.taskId!).catch((error) => {
          console.error('重连失败:', error);
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// 导出单例
export const wsService = new WebSocketService();

