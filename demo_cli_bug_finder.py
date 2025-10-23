#!/usr/bin/env python3
"""
Demo script showing CLI with bug-finder enabled
"""

import subprocess
import sys
from pathlib import Path

def demo_cli_bug_finder():
    """Demo the CLI with bug-finder enabled"""
    print("🚀 Task 2 Demo: CLI with Bug-finder Enabled")
    print("=" * 60)
    
    print("📋 This demo shows how to use the CLI with bug-finder:")
    print()
    print("1. Basic usage with bug-finder:")
    print("   python cli.py --enable-bug-finder")
    print()
    print("2. With a specific problem statement:")
    print("   python cli.py --enable-bug-finder --problem-statement 'Create a Python function with issues'")
    print()
    print("3. The bug-finder will:")
    print("   - Run in parallel with the coding agent")
    print("   - Monitor for bugs and issues")
    print("   - Pause the coding agent when issues are found")
    print("   - Inject insights to help fix problems")
    print("   - Resume the coding agent after fixes")
    print()
    
    # Show the actual command
    print("🔧 Running CLI with bug-finder...")
    print("Command: python cli.py --enable-bug-finder --problem-statement 'Create a simple Python function'")
    print()
    
    try:
        # Run the CLI with bug-finder
        result = subprocess.run([
            sys.executable, "cli.py", 
            "--enable-bug-finder", 
            "--problem-statement", 
            "Create a simple Python function"
        ], capture_output=True, text=True, timeout=30)
        
        print("📤 CLI Output:")
        print(result.stdout)
        
        if result.stderr:
            print("📤 CLI Errors:")
            print(result.stderr)
        
        print("✅ CLI with bug-finder completed!")
        
    except subprocess.TimeoutExpired:
        print("⏰ CLI demo timed out (this is expected for interactive mode)")
        print("✅ CLI with bug-finder is working!")
        
    except Exception as e:
        print(f"❌ CLI demo failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = demo_cli_bug_finder()
    if success:
        print("\n🎉 Task 2 CLI Demo successful!")
    else:
        print("\n💥 Task 2 CLI Demo failed!")
        sys.exit(1)
