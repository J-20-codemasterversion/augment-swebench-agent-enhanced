#!/usr/bin/env python3
"""
Script to reproduce the Agent.run() error
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.agent import Agent
from utils.llm_client import get_client
from utils.workspace_manager import WorkspaceManager
from rich.console import Console
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reproduce_error():
    """Reproduce the Agent.run() error"""
    print("🔍 Reproducing Agent.run() error...")
    
    try:
        # Create basic components
        console = Console()
        workspace_manager = WorkspaceManager(root=Path("."))
        client = get_client("anthropic-direct", model_name="claude-3-5-sonnet-20241022")
        
        # Create agent
        agent = Agent(
            client=client,
            workspace_manager=workspace_manager,
            console=console,
            logger_for_agent_logs=logger
        )
        
        # Try to call agent.run() with 1 argument (this should work now)
        print("Attempting to call agent.run() with 1 argument...")
        result = agent.run("test instruction")  # This should work
        
    except Exception as e:
        print(f"❌ Error reproduced: {e}")
        print(f"Error type: {type(e).__name__}")
        return str(e)
    
    return None

if __name__ == "__main__":
    error = reproduce_error()
    if error:
        print(f"✅ Successfully reproduced error: {error}")
    else:
        print("❌ Failed to reproduce error")
