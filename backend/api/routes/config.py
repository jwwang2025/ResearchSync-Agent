"""
Config API Routes

配置管理相关的 API 路由。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional

from ...utils.config import load_config_from_env, save_config_to_file, Config
from pydantic import BaseModel
from pathlib import Path
import os

router = APIRouter()


class LLMUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class SearchUpdate(BaseModel):
    tavily_api_key: Optional[str] = None
    mcp_server_url: Optional[str] = None
    mcp_api_key: Optional[str] = None


class WorkflowUpdate(BaseModel):
    max_iterations: Optional[int] = None
    auto_approve_plan: Optional[bool] = None
    output_dir: Optional[str] = None


class ConfigUpdate(BaseModel):
    llm: Optional[LLMUpdate] = None
    search: Optional[SearchUpdate] = None
    workflow: Optional[WorkflowUpdate] = None


@router.get("/config")
async def get_config():
    """
    获取当前配置信息。
    """
    cfg = load_config_from_env()
    return {
        "llm": {
            "provider": cfg.llm.provider,
            "model": cfg.llm.model,
            "temperature": cfg.llm.temperature,
            "max_tokens": cfg.llm.max_tokens
        },
        "search": {
            "tavily_configured": bool(cfg.search.tavily_api_key),
            "mcp_configured": bool(cfg.search.mcp_server_url)
        },
        "workflow": {
            "max_iterations": cfg.workflow.max_iterations,
            "auto_approve_plan": cfg.workflow.auto_approve_plan,
            "output_dir": cfg.workflow.output_dir
        }
    }


@router.get("/models/{provider}")
async def list_models(provider: str):
    """
    列出指定提供商的可用模型。
    """
    models = {
        'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
        'claude': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229'],
        'gemini': ['gemini-pro', 'gemini-pro-vision', 'gemini-ultra'],
        'deepseek': ['deepseek-chat', 'deepseek-coder']
    }

    if provider.lower() not in models:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {provider}")

    return {
        "provider": provider,
        "models": models[provider.lower()]
    }


@router.put("/config")
async def update_config(payload: ConfigUpdate):
    """
    更新运行时配置并将其保存到仓库根目录的 `config.json`（供 CLI 使用）。
    该接口会更新内存配置并写入文件；某些配置（如 LLM 提供商）也会同步到进程环境变量以立即生效。
    """
    cfg = load_config_from_env()

    # Apply LLM updates
    if payload.llm:
        if payload.llm.provider:
            os.environ["LLM_PROVIDER"] = payload.llm.provider
            cfg.llm.provider = payload.llm.provider
        if payload.llm.model:
            cfg.llm.model = payload.llm.model
            os.environ["LLM_MODEL"] = payload.llm.model
        if payload.llm.temperature is not None:
            cfg.llm.temperature = payload.llm.temperature
        if payload.llm.max_tokens is not None:
            cfg.llm.max_tokens = payload.llm.max_tokens

    # Apply search updates
    if payload.search:
        if payload.search.tavily_api_key is not None:
            cfg.search.tavily_api_key = payload.search.tavily_api_key
            os.environ["TAVILY_API_KEY"] = payload.search.tavily_api_key or ""
        if payload.search.mcp_server_url is not None:
            cfg.search.mcp_server_url = payload.search.mcp_server_url
            os.environ["MCP_SERVER_URL"] = payload.search.mcp_server_url or ""
        if payload.search.mcp_api_key is not None:
            cfg.search.mcp_api_key = payload.search.mcp_api_key
            os.environ["MCP_API_KEY"] = payload.search.mcp_api_key or ""

    # Apply workflow updates
    if payload.workflow:
        if payload.workflow.max_iterations is not None:
            cfg.workflow.max_iterations = payload.workflow.max_iterations
            os.environ["MAX_ITERATIONS"] = str(payload.workflow.max_iterations)
        if payload.workflow.auto_approve_plan is not None:
            cfg.workflow.auto_approve_plan = payload.workflow.auto_approve_plan
            os.environ["AUTO_APPROVE_PLAN"] = "true" if payload.workflow.auto_approve_plan else "false"
        if payload.workflow.output_dir is not None:
            cfg.workflow.output_dir = payload.workflow.output_dir
            os.environ["OUTPUT_DIR"] = payload.workflow.output_dir

    # Persist to repository root config.json for CLI compatibility
    repo_root = Path(__file__).parents[3]
    config_path = repo_root / "config.json"
    saved = save_config_to_file(cfg, str(config_path))
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save configuration")

    return {"message": "配置已更新并保存", "path": str(config_path)}

