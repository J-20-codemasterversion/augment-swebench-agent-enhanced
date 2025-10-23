"""
AgentOrchestrator manages both the coding agent and bug-finder agent.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from tools.agent import Agent
from tools.bug_finder_agent import BugFinderAgent
from utils.shared_controller import SharedController
from utils.llm_client import get_client
from utils.workspace_manager import WorkspaceManager
from rich.console import Console

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates the coding agent and bug-finder agent."""
    
    def __init__(
        self,
        workspace_path: Path,
        client_config: dict,
        console: Console,
        logger_for_agent_logs: logging.Logger,
        max_output_tokens_per_turn: int = 8192,
        max_turns: int = 30,
        ask_user_permission: bool = False
    ):
        self.workspace_path = workspace_path
        self.console = console
        self.logger_for_agent_logs = logger_for_agent_logs
        
        # Create shared controller
        self.controller = SharedController()
        
        # Create client
        self.client = get_client(**client_config)
        
        # Create workspace manager
        self.workspace_manager = WorkspaceManager(root=workspace_path)
        
        # Create agents
        self.coding_agent = Agent(
            client=self.client,
            workspace_manager=self.workspace_manager,
            console=console,
            logger_for_agent_logs=logger_for_agent_logs,
            max_output_tokens_per_turn=max_output_tokens_per_turn,
            max_turns=max_turns,
            ask_user_permission=ask_user_permission,
            shared_controller=self.controller  # Pass controller to agent
        )
        
        self.bug_finder_agent = BugFinderAgent(
            controller=self.controller,
            workspace_path=workspace_path
        )
        
        # Task management
        self.coding_task: Optional[asyncio.Task] = None
        self.bug_finder_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def run(self, problem_statement: str):
        """Run both agents in parallel."""
        logger.info("🚀 Starting agent orchestrator")
        self.is_running = True
        
        try:
            # Start both agents as tasks
            self.coding_task = asyncio.create_task(
                self._run_coding_agent(problem_statement)
            )
            self.bug_finder_task = asyncio.create_task(
                self.bug_finder_agent.run_loop()
            )
            
            # Wait for coding agent to complete
            await self.coding_task
            
            # Stop bug-finder agent
            await self.controller.shutdown()
            if self.bug_finder_task:
                await self.bug_finder_task
            
            logger.info("✅ Agent orchestrator completed")
            
        except Exception as e:
            logger.error(f"❌ Agent orchestrator error: {e}")
            await self.shutdown()
            raise
        finally:
            self.is_running = False
    
    async def _run_coding_agent(self, problem_statement: str):
        """Run the coding agent with checkpoint integration."""
        logger.info("🤖 Starting coding agent")
        
        try:
            # Inject any existing insights into the problem statement
            insights = await self.controller.get_insights()
            if insights:
                enhanced_statement = self._enhance_problem_statement(problem_statement, insights)
                self.console.print("[yellow]💡 Bug-finder insights injected into agent context[/yellow]")
            else:
                enhanced_statement = problem_statement
            
            # Run the agent (it's not async, so we need to run it in a thread)
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.coding_agent.run_agent, 
                enhanced_statement, 
                True,
                None
            )
            return result
            
        except Exception as e:
            logger.error(f"❌ Coding agent error: {e}")
            raise
    
    def _enhance_problem_statement(self, original: str, insights) -> str:
        """Enhance the problem statement with bug-finder insights."""
        if not insights:
            return original
        
        enhanced = f"{original}\n\n"
        enhanced += "=== BUG-FINDER INSIGHTS ===\n"
        enhanced += "The bug-finder agent has detected the following issues:\n\n"
        
        for insight in insights:
            enhanced += f"🔍 {insight.bug_type.upper()}: {insight.description}\n"
            if insight.file_path:
                enhanced += f"   📁 File: {insight.file_path}"
                if insight.line_number:
                    enhanced += f":{insight.line_number}"
                enhanced += "\n"
            if insight.suggested_fix:
                enhanced += f"   💡 Suggested fix: {insight.suggested_fix}\n"
            enhanced += f"   ⚠️  Severity: {insight.severity}\n\n"
        
        enhanced += "Please address these issues in your implementation.\n"
        enhanced += "==========================================\n"
        
        return enhanced
    
    async def shutdown(self):
        """Shutdown the orchestrator and all agents."""
        logger.info("🔄 Shutting down agent orchestrator")
        
        # Shutdown controller
        await self.controller.shutdown()
        
        # Cancel tasks
        if self.coding_task and not self.coding_task.done():
            self.coding_task.cancel()
            try:
                await self.coding_task
            except asyncio.CancelledError:
                pass
        
        if self.bug_finder_task and not self.bug_finder_task.done():
            self.bug_finder_task.cancel()
            try:
                await self.bug_finder_task
            except asyncio.CancelledError:
                pass
        
        self.is_running = False
        logger.info("✅ Agent orchestrator shutdown complete")
    
    def get_status(self) -> dict:
        """Get the current status of the orchestrator."""
        return {
            "is_running": self.is_running,
            "coding_agent_running": self.coding_task is not None and not self.coding_task.done(),
            "bug_finder_running": self.bug_finder_task is not None and not self.bug_finder_task.done(),
            "is_paused": self.controller.is_paused,
            "pause_reason": self.controller.pause_reason,
            "turn_count": self.controller.agent_turn_count,
            "insights_count": self.controller.insights_queue.qsize()
        }
