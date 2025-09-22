"""
Brebot - Autonomous AI Agent System for Marketing & Web Design Agencies

A comprehensive system that uses AI agents to help manage and organize your agency's workflow.
"""

__version__ = "1.0.0"
__author__ = "Brebot Team"
__description__ = "Autonomous AI Agent System for Marketing & Web Design Agencies"

# Simple imports that don't require CrewAI
try:
    from .config import settings, load_settings
    from .utils import brebot_logger
    __all__ = ["settings", "load_settings", "brebot_logger"]
except ImportError:
    # If config or utils fail, just provide basic info
    __all__ = []