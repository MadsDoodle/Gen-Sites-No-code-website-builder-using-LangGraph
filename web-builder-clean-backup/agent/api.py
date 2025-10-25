import logging
import shutil
import uuid
import io
import zipfile
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.graph import agent
from agent.tools import init_project_root

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Website Builder API",
    version="1.0.0",
    description="API for building websites using AI agents"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for task status (use Redis/Database in production)
task_storage: Dict[str, Dict] = {}


# Pydantic Models
class WebsiteRequest(BaseModel):
    user_prompt: str


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: str  # "planner", "architect", "coder", "done"
    project_path: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class BuildResult(BaseModel):
    status: str
    project_path: str
    files: list
    message: str


# Background Task
def run_agent_task(task_id: str, user_prompt: str):
    """Background task to execute the agent"""
    try:
        from agent.tools import set_project_root  # Add this import
        
        task_storage[task_id]["status"] = "processing"
        task_storage[task_id]["progress"] = "planner"
        
        logger.info(f"Starting task {task_id}")
        
        # Initialize project root and SET IT for this thread
        project_path = init_project_root()  # Now returns Path object
        set_project_root(project_path)  # CRITICAL: Set for current thread
        logger.info(f"Initialized project directory: {project_path}")
        
        # Update progress
        task_storage[task_id]["progress"] = "architect"

        # Run the agent with project_root in initial state
        result = agent.invoke(
            {
                "user_prompt": user_prompt,
                "project_root": str(project_path)
            },
            {"recursion_limit": 100}
        )

        
        # Get list of generated files
        files = []
        if project_path.exists():
            for file in project_path.rglob("*"):
                if file.is_file():
                    files.append(str(file.relative_to(project_path)))
        
        # Update task status
        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["progress"] = "done"
        task_storage[task_id]["project_path"] = str(project_path)
        task_storage[task_id]["files"] = files
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()

# API Endpoints
@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "AI Website Builder API is running",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/api/build-website", response_model=TaskResponse)
async def build_website(request: WebsiteRequest, background_tasks: BackgroundTasks):
    """
    Start building a website based on user prompt.
    Returns a task_id to track progress.
    """
    if not request.user_prompt or len(request.user_prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="user_prompt cannot be empty")
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task storage
    task_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": "initialized",
        "user_prompt": request.user_prompt,
        "created_at": datetime.now().isoformat(),
        "project_path": None,
        "files": [],
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(run_agent_task, task_id, request.user_prompt)
    
    logger.info(f"Created task {task_id} for prompt: {request.user_prompt[:100]}...")
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Website build started. Use /api/status/{task_id} to check progress."
    )


@app.get("/api/status/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str):
    """Get the status of a build task"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        project_path=task.get("project_path"),
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )


@app.get("/api/result/{task_id}", response_model=BuildResult)
def get_build_result(task_id: str):
    """Get the final result of a completed build"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task is not completed yet. Current status: {task['status']}"
        )
    
    return BuildResult(
        status="success",
        project_path=task["project_path"],
        files=task.get("files", []),
        message="Website generated successfully"
    )


@app.get("/api/download/{task_id}")
def download_project(task_id: str):
    """Download the generated project as a ZIP file"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Project is not ready for download yet"
        )
    
    project_path = Path(task["project_path"])
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")
    
    # Create ZIP in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in project_path.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(project_path)
                zipf.write(file, arcname)
    
    memory_file.seek(0)
    
    return StreamingResponse(
        memory_file,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=website_{task_id}.zip"}
    )


@app.get("/api/file/{task_id}/{file_path:path}")
def get_file_content(task_id: str, file_path: str):
    """Get the content of a specific file from the generated project"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Project is not ready yet")
    
    project_path = Path(task["project_path"])
    target_file = project_path / file_path
    
    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check: ensure file is within project directory
    if not str(target_file.resolve()).startswith(str(project_path.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"file_path": file_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.delete("/api/task/{task_id}")
def delete_task(task_id: str):
    """Delete a task and its associated project files"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    # Delete project directory if it exists
    if task.get("project_path"):
        project_path = Path(task["project_path"])
        if project_path.exists():
            shutil.rmtree(project_path)
            logger.info(f"Deleted project directory: {project_path}")
    
    # Remove from storage
    del task_storage[task_id]
    
    return {"message": "Task deleted successfully", "task_id": task_id}


@app.get("/api/tasks")
def list_tasks():
    """List all tasks (for debugging/admin)"""
    return {
        "total_tasks": len(task_storage),
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "created_at": task["created_at"]
            }
            for task_id, task in task_storage.items()
        ]
    }