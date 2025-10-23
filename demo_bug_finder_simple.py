#!/usr/bin/env python3
"""
Simple demo for Task 2: Bug-finder agent functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.bug_finder_agent import BugFinderAgent
from utils.shared_controller import SharedController, BugInsight
from rich.console import Console
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_bug_finder():
    """Demo the bug-finder agent functionality"""
    print("🐛 Task 2 Demo: Bug-finder Agent")
    print("=" * 50)
    
    try:
        # Create shared controller
        controller = SharedController()
        
        # Create bug-finder agent
        bug_finder = BugFinderAgent(
            workspace_path=Path("."),
            shared_controller=controller
        )
        
        print("✅ Bug-finder agent created")
        print("🔍 Bug-finder will check for:")
        print("   - Missing imports")
        print("   - TODO comments")
        print("   - Large files")
        print("   - Syntax errors")
        print("   - Linting issues")
        print()
        
        # Run bug checks
        print("🔍 Running bug checks...")
        insights = await bug_finder._check_for_bugs()
        
        print(f"📊 Found {len(insights)} potential issues:")
        for i, insight in enumerate(insights, 1):
            print(f"   {i}. {insight.severity.upper()}: {insight.bug_type}")
            print(f"      {insight.description}")
            if insight.suggested_fix:
                print(f"      💡 Fix: {insight.suggested_fix}")
            print()
        
        # Demo pause/resume functionality
        print("⏸️  Demo pause/resume functionality:")
        print("   - Bug-finder can pause the coding agent")
        print("   - Bug-finder can inject insights")
        print("   - Bug-finder can resume the coding agent")
        print()
        
        # Simulate pause/resume
        await controller.request_pause("Demo: Bug-finder detected issues")
        print("🛑 Bug-finder paused the coding agent")
        
        # Inject insights
        demo_insight = BugInsight(
            bug_type="demo_issue",
            description="This is a demo insight from the bug-finder",
            severity="medium",
            suggested_fix="This is how to fix the demo issue"
        )
        await controller.inject_insight(demo_insight)
        print("💡 Bug-finder injected insight into coding agent context")
        
        # Resume
        await controller.request_resume()
        print("▶️  Bug-finder resumed the coding agent")
        
        print()
        print("✅ Task 2 Demo completed!")
        print("🎯 Bug-finder agent successfully:")
        print("   - Detected issues in the workspace")
        print("   - Demonstrated pause/resume functionality")
        print("   - Injected insights into the agent context")
        print("   - Coordinated with the coding agent")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_bug_finder())
    if success:
        print("\n🎉 Task 2 Demo successful!")
    else:
        print("\n💥 Task 2 Demo failed!")
        sys.exit(1)
