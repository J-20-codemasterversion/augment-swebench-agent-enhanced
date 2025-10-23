"""
Bug-finder agent that runs in parallel to the coding agent.
Monitors for bugs and injects insights into the main agent's context.
"""

import asyncio
import logging
import subprocess
import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from utils.shared_controller import SharedController, BugInsight

logger = logging.getLogger(__name__)


class BugFinderAgent:
    """Parallel bug-finder agent that monitors for issues."""
    
    def __init__(self, controller: SharedController, workspace_path: Path):
        self.controller = controller
        self.workspace_path = workspace_path
        self.is_running = False
        self.check_interval = 5.0  # Check every 5 seconds
        self.last_check_time = None
        
        # Bug detection tools
        self.linters = {
            "python": ["python", "-m", "flake8", "--max-line-length=100"],
            "javascript": ["npx", "eslint", "--format=json"],
            "typescript": ["npx", "tsc", "--noEmit"]
        }
        
        # Test runners
        self.test_runners = {
            "python": ["python", "-m", "pytest", "--tb=short", "-q"],
            "javascript": ["npm", "test"],
            "typescript": ["npm", "test"]
        }
    
    async def run_loop(self):
        """Main loop for the bug-finder agent."""
        logger.info("🐛 Bug-finder agent started")
        self.is_running = True
        
        try:
            while not self.controller.shutdown_event.is_set():
                await self._check_for_bugs()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Bug-finder agent error: {e}")
        finally:
            self.is_running = False
            logger.info("🐛 Bug-finder agent stopped")
    
    async def _check_for_bugs(self):
        """Check for bugs in the current workspace."""
        try:
            # Run linters
            lint_insights = await self._run_linters()
            
            # Run tests
            test_insights = await self._run_tests()
            
            # Check for common issues
            common_insights = await self._check_common_issues()
            
            # Combine all insights
            all_insights = lint_insights + test_insights + common_insights
            
            # Process insights
            for insight in all_insights:
                if insight.severity in ["high", "critical"]:
                    await self.controller.request_pause(f"Critical bug detected: {insight.bug_type}")
                    await self.controller.inject_insight(insight)
                    await asyncio.sleep(1)  # Give agent time to process
                    await self.controller.request_resume()
                elif insight.severity == "medium":
                    await self.controller.inject_insight(insight)
            
            self.last_check_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in bug checking: {e}")
    
    async def _run_linters(self) -> List[BugInsight]:
        """Run linters and return insights."""
        insights = []
        
        for file_type, linter_cmd in self.linters.items():
            try:
                # Find files of this type
                files = self._find_files_by_type(file_type)
                if not files:
                    continue
                
                # Run linter
                result = await self._run_command(linter_cmd + files)
                if result.returncode != 0:
                    insights.extend(self._parse_linter_output(result.stdout, result.stderr, file_type))
                    
            except Exception as e:
                logger.warning(f"Linter {file_type} failed: {e}")
        
        return insights
    
    async def _run_tests(self) -> List[BugInsight]:
        """Run tests and return insights."""
        insights = []
        
        # Check for test files
        test_files = list(self.workspace_path.rglob("test_*.py")) + list(self.workspace_path.rglob("*_test.py"))
        if not test_files:
            return insights
        
        try:
            # Run Python tests
            result = await self._run_command(["python", "-m", "pytest", "--tb=short", "-q"])
            if result.returncode != 0:
                insights.append(BugInsight(
                    bug_type="test_failure",
                    description=f"Tests failed: {result.stderr[:200]}",
                    severity="high",
                    suggested_fix="Review test failures and fix implementation"
                ))
        except Exception as e:
            logger.warning(f"Test runner failed: {e}")
        
        return insights
    
    async def _check_common_issues(self) -> List[BugInsight]:
        """Check for common code issues."""
        insights = []
        
        # Check for TODO/FIXME comments
        todo_insights = await self._check_todo_comments()
        insights.extend(todo_insights)
        
        # Check for large files
        large_file_insights = await self._check_large_files()
        insights.extend(large_file_insights)
        
        # Check for missing imports
        import_insights = await self._check_missing_imports()
        insights.extend(import_insights)
        
        return insights
    
    async def _check_todo_comments(self) -> List[BugInsight]:
        """Check for TODO/FIXME comments."""
        insights = []
        
        for py_file in self.workspace_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'TODO' in line.upper() or 'FIXME' in line.upper():
                        insights.append(BugInsight(
                            bug_type="todo_comment",
                            description=f"TODO/FIXME found: {line.strip()}",
                            severity="low",
                            file_path=str(py_file),
                            line_number=i,
                            suggested_fix="Address the TODO/FIXME comment"
                        ))
            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")
        
        return insights
    
    async def _check_large_files(self) -> List[BugInsight]:
        """Check for files that are too large."""
        insights = []
        
        for py_file in self.workspace_path.rglob("*.py"):
            try:
                size = py_file.stat().st_size
                if size > 10000:  # 10KB
                    insights.append(BugInsight(
                        bug_type="large_file",
                        description=f"File is large ({size} bytes): {py_file.name}",
                        severity="medium",
                        file_path=str(py_file),
                        suggested_fix="Consider breaking into smaller modules"
                    ))
            except Exception as e:
                logger.warning(f"Error checking file size {py_file}: {e}")
        
        return insights
    
    async def _check_missing_imports(self) -> List[BugInsight]:
        """Actually check for missing packages by trying to import them."""
        insights: List[BugInsight] = []
        
        # Make workspace importable for local packages
        workspace = str(self.workspace_path.resolve())
        if workspace not in sys.path:
            sys.path.insert(0, workspace)

        def top_level(mod: str) -> str:
            return mod.split(".")[0]

        for py_file in self.workspace_path.rglob("*.py"):
            try:
                text = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(text, filename=str(py_file))
            except SyntaxError:
                # Leave syntax errors to a dedicated checker
                continue
            except Exception as e:
                logger.warning(f"AST parse failed for {py_file}: {e}")
                continue

            # Collect all imports from the file
            imported_modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.append((alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    if node.level and node.level > 0:
                        # Skip relative imports
                        continue
                    if node.module:
                        imported_modules.append((node.module, node.lineno))

            # Actually try to import each module
            for module_name, lineno in imported_modules:
                try:
                    # Skip standard library modules
                    if hasattr(sys, "stdlib_module_names") and module_name in sys.stdlib_module_names:
                        continue
                    
                    # Try to actually import the module
                    try:
                        __import__(module_name)
                        logger.debug(f"✅ Successfully imported {module_name}")
                    except ImportError as e:
                        # Module is missing - create insight
                        top_level_module = top_level(module_name)
                        insights.append(BugInsight(
                            bug_type="missing_import",
                            description=f"Missing package: {module_name} - {str(e)}",
                            severity="high",
                            file_path=str(py_file),
                            line_number=lineno,
                            suggested_fix=f"Install missing package: pip install {top_level_module}"
                        ))
                        logger.info(f"❌ Missing import: {module_name} in {py_file.name}:{lineno}")
                    except Exception as e:
                        # Other import errors (like syntax errors in the module)
                        insights.append(BugInsight(
                            bug_type="import_error",
                            description=f"Import error for {module_name}: {str(e)}",
                            severity="medium",
                            file_path=str(py_file),
                            line_number=lineno,
                            suggested_fix=f"Check if {module_name} is properly installed and accessible"
                        ))
                        logger.warning(f"⚠️ Import error: {module_name} in {py_file.name}:{lineno} - {e}")
                        
                except Exception as e:
                    logger.warning(f"Error checking import {module_name}: {e}")

        return insights

    
    def _find_files_by_type(self, file_type: str) -> List[str]:
        """Find files of a specific type."""
        if file_type == "python":
            return [str(f) for f in self.workspace_path.rglob("*.py")]
        elif file_type == "javascript":
            return [str(f) for f in self.workspace_path.rglob("*.js")]
        elif file_type == "typescript":
            return [str(f) for f in self.workspace_path.rglob("*.ts")]
        return []
    
    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )
            stdout, stderr = await process.communicate()
            return subprocess.CompletedProcess(
                cmd, process.returncode, stdout.decode(), stderr.decode()
            )
        except Exception as e:
            logger.warning(f"Command failed: {' '.join(cmd)} - {e}")
            return subprocess.CompletedProcess(cmd, 1, "", str(e))
    
    def _parse_linter_output(self, stdout: str, stderr: str, linter_type: str) -> List[BugInsight]:
        """Parse linter output and return insights."""
        insights = []
        
        # Simple parsing for flake8 output
        if linter_type == "python" and stdout:
            for line in stdout.strip().split('\n'):
                if line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        file_path = parts[0]
                        line_num = int(parts[1])
                        col_num = int(parts[2])
                        message = parts[3].strip()
                        
                        severity = "medium"
                        if "error" in message.lower():
                            severity = "high"
                        elif "warning" in message.lower():
                            severity = "medium"
                        else:
                            severity = "low"
                        
                        insights.append(BugInsight(
                            bug_type="linting_error",
                            description=message,
                            severity=severity,
                            file_path=file_path,
                            line_number=line_num,
                            suggested_fix=f"Fix linting issue: {message}"
                        ))
        
        return insights
