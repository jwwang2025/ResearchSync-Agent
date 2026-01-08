/**
 * Research Types
 * 
 * 研究任务相关的 TypeScript 类型定义
 */

export enum ResearchStatus {
  PENDING = "pending",
  PLANNING = "planning",
  AWAITING_APPROVAL = "awaiting_approval",
  RESEARCHING = "researching",
  GENERATING_REPORT = "generating_report",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export interface ResearchRequest {
  query: string;
  max_iterations?: number;
  auto_approve?: boolean;
  llm_provider?: string;
  llm_model?: string;
  output_format?: "markdown" | "html";
}

export interface SubTask {
  task_id: number;
  description: string;
  search_queries: string[];
  sources: string[];
  status: string;
  priority?: number;
}

export interface ResearchPlan {
  research_goal: string;
  sub_tasks: SubTask[];
  completion_criteria: string;
  estimated_iterations: number;
}

export interface TaskInfo {
  task_id: string;
  query: string;
  status: ResearchStatus;
  created_at: string;
  updated_at: string;
  progress?: Record<string, any>;
}

export interface WebSocketMessage {
  type: string;
  task_id: string;
  [key: string]: any;
}

export interface StatusUpdateMessage extends WebSocketMessage {
  type: "status_update";
  step: string;
  message: string;
}

export interface PlanReadyMessage extends WebSocketMessage {
  type: "plan_ready";
  plan: ResearchPlan;
  message: string;
}

export interface PlanUpdatedMessage extends WebSocketMessage {
  type: "plan_updated";
  plan: ResearchPlan;
  message: string;
}

export interface ProgressMessage extends WebSocketMessage {
  type: "progress";
  step: string;
  iteration: number;
  max_iterations: number;
  current_task?: string;
  data?: Record<string, any>;
}

export interface ReportReadyMessage extends WebSocketMessage {
  type: "report_ready";
  report: string;
  format: string;
}

export interface ErrorMessage extends WebSocketMessage {
  type: "error";
  message: string;
}

