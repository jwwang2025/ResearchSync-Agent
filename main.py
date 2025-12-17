"""
ResearchSync-Agent - Main Entry Point

This is the main entry point for the ResearchSync multi-agent system.
Refactored to use argparse-based CLI.
"""

from backend.cli.main import main


if __name__ == '__main__':
    raise SystemExit(main())
