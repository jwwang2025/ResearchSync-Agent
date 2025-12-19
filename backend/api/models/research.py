"""
Research API Models

定义研究任务相关的 Pydantic 模型，用于 API 请求和响应。
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ResearchRequest(BaseModel):
    """启动研究任务的请求模型"""
    query: str = Field(..., description="研究问题或主题")
    max_iterations: Optional[int] = Field(default=5, ge=1, le=20, description="最大迭代次数")
    auto_approve: bool = Field(default=False, description="是否自动批准研究计划")
    llm_provider: Optional[str] = Field(default=None, description="LLM 提供商")
    llm_model: Optional[str] = Field(default=None, description="LLM 模型名称")
    output_format: str = Field(default="markdown", description="输出格式 (markdown/html)")


class ResearchStatus(str, Enum):
    """研究任务状态枚举"""
    PENDING = "pending"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    RESEARCHING = "researching"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskInfo(BaseModel):
    """任务基本信息"""
    task_id: str = Field(..., description="任务 ID")
    query: str = Field(..., description="研究问题")
    status: ResearchStatus = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    progress: Optional[Dict[str, Any]] = Field(default=None, description="进度信息")


class ResearchPlan(BaseModel):
    """研究计划模型"""
    research_goal: str = Field(..., description="研究目标")
    sub_tasks: List[Dict[str, Any]] = Field(..., description="子任务列表")
    completion_criteria: str = Field(..., description="完成标准")
    estimated_iterations: int = Field(..., description="预计迭代次数")


class PlanApprovalRequest(BaseModel):
    """计划审批请求"""
    approved: bool = Field(..., description="是否批准")
    feedback: Optional[str] = Field(default=None, description="反馈意见（如果拒绝）")


class ResearchProgress(BaseModel):
    """研究进度模型"""
    task_id: str = Field(..., description="任务 ID")
    step: str = Field(..., description="当前步骤")
    iteration: int = Field(..., description="当前迭代次数")
    max_iterations: int = Field(..., description="最大迭代次数")
    current_task: Optional[str] = Field(default=None, description="当前任务描述")
    data: Optional[Dict[str, Any]] = Field(default=None, description="额外数据")


class ResearchResponse(BaseModel):
    """研究任务响应模型"""
    task_id: str = Field(..., description="任务 ID")
    status: ResearchStatus = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")


class ReportInfo(BaseModel):
    """报告信息模型"""
    task_id: str = Field(..., description="任务 ID")
    report: str = Field(..., description="报告内容")
    format: str = Field(..., description="报告格式")
    created_at: datetime = Field(..., description="创建时间")

