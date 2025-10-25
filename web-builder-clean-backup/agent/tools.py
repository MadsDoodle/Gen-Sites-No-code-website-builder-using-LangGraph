# =============================================================================
# FILESYSTEM TOOLS MODULE
# =============================================================================
# This module provides secure file operations for the web builder agent.
# Maps to: Core utilities used by the coder agent to interact with the filesystem
# while maintaining security boundaries within the project root directory.

import pathlib
import subprocess
import threading
import logging
from typing import Tuple

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Thread-local storage for PROJECT_ROOT to support concurrent tasks
_thread_local = threading.local()

# Global fallback for when thread-local doesn't work (e.g., in React agent context)
_global_project_root = None
_global_lock = threading.Lock()


def get_project_root():
    """Get the project root for the current thread, with global fallback."""
    # Try thread-local first
    thread_root = getattr(_thread_local, 'PROJECT_ROOT', None)
    if thread_root is not None:
        return thread_root
    
    # Fallback to global
    with _global_lock:
        return _global_project_root


def set_project_root(path: pathlib.Path):
    """Set the project root for the current thread and globally."""
    global _global_project_root
    
    # Set thread-local
    _thread_local.PROJECT_ROOT = path
    
    # Also set global as fallback
    with _global_lock:
        _global_project_root = path


def get_next_serial_id() -> int:
    """Finds the next available serial ID by checking existing project directories."""
    base_path = pathlib.Path.cwd()
    existing_dirs = [d for d in base_path.glob("generated_project_*") if d.is_dir()]
    
    if not existing_dirs:
        return 1
    
    # Extract serial IDs from existing directories
    serial_ids = []
    for d in existing_dirs:
        try:
            # Extract number from "generated_project_X" format
            serial_id = int(d.name.split("_")[-1])
            serial_ids.append(serial_id)
        except (ValueError, IndexError):
            continue
    
    return max(serial_ids) + 1 if serial_ids else 1


def safe_path_for_project(path: str) -> pathlib.Path:
    """Security function that prevents path traversal attacks."""
    PROJECT_ROOT = get_project_root()
    
    if PROJECT_ROOT is None:
        raise RuntimeError("PROJECT_ROOT not initialized. Call init_project_root() first.")
    
    # Strip leading slashes - treat all paths as relative to project root
    path = path.lstrip('/')
    
    # Build the full path relative to project root
    p = (PROJECT_ROOT / path).resolve()
    root = PROJECT_ROOT.resolve()
    
    # Check if resolved path is within project root
    try:
        p.relative_to(root)
    except ValueError:
        raise ValueError(f"Attempt to write outside project root: {path}")
    
    return p


@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    try:
        p = safe_path_for_project(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"✓ Successfully wrote file: {p}")
        return f"WROTE:{p}"
    except RuntimeError as e:
        logger.error(f"✗ Failed to write {path}: {e}")
        raise


@tool
def read_file(path: str) -> str:
    """Reads content from a file at the specified path within the project root."""
    p = safe_path_for_project(path)
    if not p.exists():
        return ""
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


@tool
def get_current_directory() -> str:
    """Returns the current working directory."""
    PROJECT_ROOT = get_project_root()
    if PROJECT_ROOT is None:
        raise RuntimeError("PROJECT_ROOT not initialized. Call init_project_root() first.")
    return str(PROJECT_ROOT)


@tool
def list_files(directory: str = ".") -> str:
    """Lists all files in the specified directory within the project root."""
    PROJECT_ROOT = get_project_root()
    if PROJECT_ROOT is None:
        raise RuntimeError("PROJECT_ROOT not initialized.")
    
    p = safe_path_for_project(directory)
    if not p.is_dir():
        return f"ERROR: {p} is not a directory"
    
    files = [str(f.relative_to(PROJECT_ROOT)) for f in p.glob("**/*") if f.is_file()]
    return "\n".join(files) if files else "No files found."


@tool
def run_cmd(cmd: str, cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Runs a shell command in the specified directory and returns the result."""
    PROJECT_ROOT = get_project_root()
    if PROJECT_ROOT is None:
        raise RuntimeError("PROJECT_ROOT not initialized.")
    
    cwd_dir = safe_path_for_project(cwd) if cwd else PROJECT_ROOT
    res = subprocess.run(
        cmd, 
        shell=True, 
        cwd=str(cwd_dir), 
        capture_output=True, 
        text=True, 
        timeout=timeout
    )
    return res.returncode, res.stdout, res.stderr


def init_project_root():
    """Initializes a new project root directory with a unique serial ID."""
    serial_id = get_next_serial_id()
    project_path = pathlib.Path.cwd() / f"generated_project_{serial_id}"
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Set the project root for the current thread
    set_project_root(project_path)
    
    return project_path  # Return Path object, not string