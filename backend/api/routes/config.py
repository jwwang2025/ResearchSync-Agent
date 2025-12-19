"""
Config API Routes

配置管理相关的 API 路由。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ...utils.config import load_config_from_env

router = APIRouter()


@router.get("/config")
async def get_config():
    """
    获取当前配置信息。
    """
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载配置失败: {str(e)}")


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

