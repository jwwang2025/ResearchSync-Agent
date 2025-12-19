"""
ResearchSync-Agent - Main Entry Point

This is the main entry point for the ResearchSync multi-agent system.
Refactored to use argparse-based CLI.
"""

# 使用 Click 框架的 CLI (backend.cli.main)
from backend.cli.main import cli

# 使用 Argparse 框架的 CLI (backend.cli.main_test)
# from backend.cli.main_test import main


if __name__ == '__main__':
    # 使用 Click 框架的 CLI
    cli()
    
    # 使用 Argparse 框架的 CLI
    # raise SystemExit(main())
