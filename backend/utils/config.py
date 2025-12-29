"""
配置管理

该模块负责配置的加载与管理工作。
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pathlib import Path
import json


class LLMConfig(BaseModel):
    """LLM 配置。"""
    provider: str = Field(default="deepseek", description="LLM provider")
    model: Optional[str] = Field(default=None, description="Model name")
    api_key: str = Field(..., description="API key")
    base_url: Optional[str] = Field(default=None, description="API base URL (for proxy)")
    temperature: float = Field(default=0.7, description="Temperature")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens")


class SearchConfig(BaseModel):
    """搜索工具配置。"""
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily API key")
    mcp_server_url: Optional[str] = Field(default=None, description="MCP server URL")
    mcp_api_key: Optional[str] = Field(default=None, description="MCP API key")


class WorkflowConfig(BaseModel):
    """工作流配置。"""
    max_iterations: int = Field(default=5, description="Maximum research iterations")
    auto_approve_plan: bool = Field(default=False, description="Auto-approve research plan")
    output_dir: str = Field(default="./outputs", description="Output directory for reports")


class Config(BaseModel):
    """主配置。"""
    llm: LLMConfig
    search: SearchConfig
    workflow: WorkflowConfig


def load_config_from_env() -> Config:
    """
    从环境变量加载配置。

    返回:
        Config 实例
    """
    # 加载 .env 文件
    load_dotenv()

    # 获取 LLM 提供商并确定 API 密钥
    llm_provider = os.getenv("LLM_PROVIDER", "deepseek").lower()

    # 将提供商映射到 API 密钥环境变量
    # 注意：使用 CLAUDE_API_KEY 和 GEMINI_API_KEY 以匹配用户配置
    api_key_map = {
        "openai": "OPENAI_API_KEY",
        "claude": "CLAUDE_API_KEY",  # 为兼容性也支持 ANTHROPIC_API_KEY
        "gemini": "GEMINI_API_KEY",  # 为兼容性也支持 GOOGLE_API_KEY
        "deepseek": "DEEPSEEK_API_KEY"
    }

    api_key_env = api_key_map.get(llm_provider, "OPENAI_API_KEY")
    llm_api_key = os.getenv(api_key_env)
    
    # 兼容性回退：尝试替代的环境变量名称
    if not llm_api_key:
        if llm_provider == "claude":
            llm_api_key = os.getenv("ANTHROPIC_API_KEY")
        elif llm_provider == "gemini":
            llm_api_key = os.getenv("GOOGLE_API_KEY")

    if not llm_api_key:
        raise ValueError(f"API key not found for {llm_provider}. Please set {api_key_env} in .env file")

    # 获取 API 基础 URL（仅用于代理，仅当配置了 OpenAI 时）
    # 其他提供商（claude、gemini、deepseek）不需要代理配置
    base_url = None
    if llm_provider == "openai":
        base_url = os.getenv("OPENAI_API_BASE")  # 可选：用于代理支持
    
    # 创建 LLM 配置
    llm_config = LLMConfig(
        provider=llm_provider,
        model=os.getenv("LLM_MODEL"),
        api_key=llm_api_key,
        base_url=base_url,
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS")) if os.getenv("LLM_MAX_TOKENS") else None
    )

    # 创建搜索配置
    search_config = SearchConfig(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        mcp_server_url=os.getenv("MCP_SERVER_URL"),
        mcp_api_key=os.getenv("MCP_API_KEY")
    )

    # 创建工作流配置
    workflow_config = WorkflowConfig(
        max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
        auto_approve_plan=os.getenv("AUTO_APPROVE_PLAN", "false").lower() == "true",
        output_dir=os.getenv("OUTPUT_DIR", "./outputs")
    )

    return Config(
        llm=llm_config,
        search=search_config,
        workflow=workflow_config
    )


# Load additional config from repository config.json (optional)
try:
    repo_root = Path(__file__).parents[3]
    config_path = repo_root / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            _cfg = json.load(f)
            # Support top-level "ws_allowed_origins": ["http://..."]
            if "ws_allowed_origins" in _cfg:
                os.environ.setdefault("WS_ALLOWED_ORIGINS", ",".join(_cfg.get("ws_allowed_origins") or []))
            # Or support nested "websocket": {"allowed_origins": [...]}
            elif isinstance(_cfg.get("websocket"), dict) and _cfg["websocket"].get("allowed_origins"):
                os.environ.setdefault("WS_ALLOWED_ORIGINS", ",".join(_cfg["websocket"].get("allowed_origins") or []))
except (FileNotFoundError, json.JSONDecodeError, OSError):
    # 仅对常见的文件读取/解析错误静默处理，避免在启动时中断运行
    # 其他异常将会向上抛出以便定位问题
    pass


def save_config_to_file(config: Config, filepath: str) -> bool:
    """
    将配置保存到文件。

    参数:
        config: 配置实例
        filepath: 保存配置的路径

    返回:
        成功返回 True
    """
    try:
        with open(filepath, 'w') as f:
            f.write(config.model_dump_json(indent=2))
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def load_config_from_file(filepath: str) -> Config:
    """
    从文件加载配置。

    参数:
        filepath: 配置文件路径

    返回:
        Config 实例
    """
    import json

    with open(filepath, 'r') as f:
        data = json.load(f)

    return Config(**data)


def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置值。

    返回:
        默认配置字典
    """
    return {
        "llm": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "temperature": 0.7
        },
        "search": {
            "tavily_api_key": None,
            "mcp_server_url": None,
            "mcp_api_key": None
        },
        "workflow": {
            "max_iterations": 5,
            "auto_approve_plan": False,
            "output_dir": "./outputs"
        }
    }
