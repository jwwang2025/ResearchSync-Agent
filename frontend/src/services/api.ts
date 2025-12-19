/**
 * API Service
 * 
 * HTTP API 客户端
 */

import axios from 'axios';
import type { ResearchRequest, TaskInfo } from '../types/research';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const researchApi = {
  /**
   * 启动研究任务
   */
  async startResearch(request: ResearchRequest) {
    const response = await apiClient.post<{ task_id: string; status: string; message: string }>(
      '/api/v1/research/start',
      request
    );
    return response.data;
  },

  /**
   * 获取任务状态
   */
  async getTaskStatus(taskId: string) {
    const response = await apiClient.get<TaskInfo>(`/api/v1/research/${taskId}`);
    return response.data;
  },

  /**
   * 取消任务
   */
  async cancelTask(taskId: string) {
    const response = await apiClient.delete(`/api/v1/research/${taskId}`);
    return response.data;
  },

  /**
   * 获取任务历史
   */
  async getTaskHistory(limit = 20, offset = 0) {
    const response = await apiClient.get<{ total: number; tasks: TaskInfo[] }>(
      '/api/v1/research/history',
      { params: { limit, offset } }
    );
    return response.data;
  },
};

export const configApi = {
  /**
   * 获取配置信息
   */
  async getConfig() {
    const response = await apiClient.get('/api/v1/config');
    return response.data;
  },

  /**
   * 获取可用模型列表
   */
  async listModels(provider: string) {
    const response = await apiClient.get(`/api/v1/models/${provider}`);
    return response.data;
  },
};

