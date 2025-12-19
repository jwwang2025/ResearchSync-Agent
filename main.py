"""
ResearchSync 智能体（ResearchSync-Agent）—— 主入口节点

该模块是 ResearchSync 多智能体系统的主入口，重构后采用了基
于 argparse 库的命令行界面（CLI）。
"""

# # 使用 Click 框架的 CLI (backend.cli.main)
# from backend.cli.main import cli

# 使用 Argparse 框架的 CLI (backend.cli.main_test)
from backend.cli.main_test import main


if __name__ == '__main__':
    # # 使用 Click 框架的 CLI
    # cli()
    
    # 使用 Argparse 框架的 CLI
    raise SystemExit(main())
