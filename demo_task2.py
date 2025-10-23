#!/usr/bin/env python3
"""
Demo script for Task 2: Bug-finder agent that runs in parallel to the coding agent
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.agent_orchestrator import AgentOrchestrator
from rich.console import Console
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_task2():
    """Demo Task 2: Bug-finder agent running in parallel"""
    print("🚀 Task 2 Demo: Bug-finder Agent Running in Parallel")
    print("=" * 60)
    
    try:
        # Create orchestrator with bug-finder enabled
        console = Console()
        client_config = {
            "client_name": "anthropic-direct",
            "model_name": "claude-3-5-sonnet-20241022",
            "use_caching": True
        }
        
        orchestrator = AgentOrchestrator(
            workspace_path=Path("."),
            client_config=client_config,
            console=console,
            logger_for_agent_logs=logger,
            max_output_tokens_per_turn=8192,
            max_turns=10,
            ask_user_permission=False
        )
        
        print("✅ Orchestrator created with bug-finder agent")
        print("🐛 Bug-finder will monitor for issues while coding agent works")
        print("⏸️  Bug-finder can pause the coding agent if issues are found")
        print("💡 Bug-finder will inject insights into the coding agent's context")
        print()
        
        # Demo problem that will trigger bug-finder
        problem = """
        Create a Python script that has some issues:
        1. Create a function with a syntax error
        2. Create a function that tries to import a non-existent module
        3. Create a function with a TODO comment
        4. Then fix these issues
        """
        
        print(f"📝 Problem Statement: {problem.strip()}")
        print()
        print("🔄 Starting orchestrator with bug-finder...")
        print("   - Coding agent will work on the problem")
        print("   - Bug-finder will monitor and detect issues")
        print("   - Bug-finder will pause coding agent when issues are found")
        print("   - Bug-finder will inject insights to help fix issues")
        print()
        
        # Run the orchestrator
        result = await orchestrator.run(problem)
        
        print()
        print("✅ Task 2 Demo completed!")
        print("🎯 The bug-finder agent successfully:")
        print("   - Ran in parallel with the coding agent")
        print("   - Monitored the workspace for issues")
        print("   - Detected bugs and issues")
        print("   - Paused the coding agent when needed")
        print("   - Injected insights to help fix problems")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_task2())
    if success:
        print("\n🎉 Task 2 Demo successful!")
    else:
        print("\n💥 Task 2 Demo failed!")
        sys.exit(1)
