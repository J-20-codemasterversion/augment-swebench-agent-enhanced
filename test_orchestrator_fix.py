#!/usr/bin/env python3
"""
Test script to verify the orchestrator fix works
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.agent_orchestrator import AgentOrchestrator
from rich.console import Console
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_orchestrator():
    """Test the orchestrator with bug-finder"""
    print("🔍 Testing orchestrator with bug-finder...")
    
    try:
        # Create orchestrator
        console = Console()
        client_config = {"client_name": "anthropic-direct", "model_name": "claude-3-5-sonnet-20241022"}
        
        orchestrator = AgentOrchestrator(
            workspace_path=Path("."),
            client_config=client_config,
            console=console,
            logger_for_agent_logs=logger
        )
        
        # Test the orchestrator run method
        print("Testing orchestrator.run() with 1 argument...")
        result = await orchestrator.run("Create a simple Python function")
        print(f"✅ Orchestrator completed successfully: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_orchestrator())
    if success:
        print("✅ Orchestrator fix verified!")
    else:
        print("❌ Orchestrator fix failed!")
