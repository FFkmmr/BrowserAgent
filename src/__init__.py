"""
AI Browser Agent - Python Package
"""

__version__ = "0.1.0"
__author__ = "FFkmmr"
__description__ = "AI-powered autonomous browser agent"

from src.core.orchestrator import AgentOrchestrator
from src.utils.types import TaskStatus, ActionType

__all__ = [
    'AgentOrchestrator',
    'TaskStatus',
    'ActionType',
]
