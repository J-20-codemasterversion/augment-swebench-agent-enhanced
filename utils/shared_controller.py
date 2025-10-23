"""
SharedController for coordinating between the coding agent and bug-finder agent.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BugInsight:
    """Represents a bug insight from the bug-finder."""
    bug_type: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SharedController:
    """Coordinates between the coding agent and bug-finder agent."""
    
    def __init__(self):
        # Control events
        self.pause_event = asyncio.Event()
        self.resume_event = asyncio.Event()
        self.shutdown_event = asyncio.Event()
        
        # Communication
        self.insights_queue = asyncio.Queue()
        self.agent_context = []  # Current agent context
        
        # State
        self.is_paused = False
        self.pause_reason = None
        self.agent_turn_count = 0
        
        # Initialize resume event as set (agent can run)
        self.resume_event.set()
    
    async def request_pause(self, reason: str = "Bug-finder detected an issue"):
        """Request the agent to pause at the next checkpoint."""
        if not self.is_paused:
            logger.info(f"🛑 Requesting agent pause: {reason}")
            self.pause_event.set()
            self.is_paused = True
            self.pause_reason = reason
            self.resume_event.clear()
    
    async def inject_insight(self, insight: BugInsight):
        """Inject a bug insight into the agent's context."""
        logger.info(f"💡 Injecting bug insight: {insight.bug_type} - {insight.description}")
        self.insights_queue.put_nowait(insight)
        
        # Add to agent context
        context_entry = {
            "type": "bug_insight",
            "insight": insight,
            "timestamp": insight.timestamp
        }
        self.agent_context.append(context_entry)
    
    async def request_resume(self):
        """Request the agent to resume."""
        if self.is_paused:
            logger.info("▶️ Requesting agent resume")
            self.pause_event.clear()
            self.is_paused = False
            self.pause_reason = None
            self.resume_event.set()
    
    async def checkpoint(self) -> bool:
        """
        Checkpoint for the agent. Returns True if agent should continue, False if paused.
        Agent should call this between actions.
        """
        self.agent_turn_count += 1
        
        # Check if we should pause
        if self.pause_event.is_set():
            logger.info(f"⏸️ Agent paused at checkpoint {self.agent_turn_count}: {self.pause_reason}")
            await self.resume_event.wait()  # Wait until resumed
            logger.info(f"▶️ Agent resumed at checkpoint {self.agent_turn_count}")
        
        return not self.shutdown_event.is_set()
    
    async def get_insights(self) -> List[BugInsight]:
        """Get all pending bug insights."""
        insights = []
        while not self.insights_queue.empty():
            try:
                insight = self.insights_queue.get_nowait()
                insights.append(insight)
            except asyncio.QueueEmpty:
                break
        return insights
    
    def get_context_summary(self) -> str:
        """Get a summary of the current context for the agent."""
        if not self.agent_context:
            return "No additional context."
        
        summary = "Additional context from bug-finder:\n"
        for entry in self.agent_context[-5:]:  # Last 5 entries
            if entry["type"] == "bug_insight":
                insight = entry["insight"]
                summary += f"- {insight.severity.upper()}: {insight.bug_type} - {insight.description}\n"
                if insight.suggested_fix:
                    summary += f"  Suggested fix: {insight.suggested_fix}\n"
        
        return summary
    
    async def shutdown(self):
        """Shutdown the controller."""
        logger.info("🔄 Shutting down shared controller")
        self.shutdown_event.set()
        self.resume_event.set()  # Unblock any waiting agents
